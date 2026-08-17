import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
import json
import logging
from uuid import UUID

import asyncpg
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.database.session import async_session_factory
from app.modules.seats.service import expire_due_holds_batch


logger = logging.getLogger(__name__)
CHANNEL = "seat_map_updates"


class SeatMapHub:
    def __init__(self) -> None:
        self._subscribers: dict[UUID, set[asyncio.Queue[int]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def subscribe(self, event_id: UUID) -> AsyncIterator[asyncio.Queue[int]]:
        queue: asyncio.Queue[int] = asyncio.Queue(maxsize=1)
        async with self._lock:
            self._subscribers[event_id].add(queue)
        try:
            yield queue
        finally:
            async with self._lock:
                subscribers = self._subscribers.get(event_id)
                if subscribers is not None:
                    subscribers.discard(queue)
                    if not subscribers:
                        self._subscribers.pop(event_id, None)

    async def publish(self, event_id: UUID, version: int) -> None:
        async with self._lock:
            subscribers = tuple(self._subscribers.get(event_id, ()))
        for queue in subscribers:
            if queue.full():
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            queue.put_nowait(version)


seat_map_hub = SeatMapHub()


class SeatMapRuntime:
    def __init__(self) -> None:
        self._tasks: list[asyncio.Task[None]] = []

    async def start(self) -> None:
        if self._tasks:
            return
        self._tasks = [
            asyncio.create_task(self._listen_loop(), name="seat-map-listener"),
            asyncio.create_task(self._expiry_loop(), name="seat-hold-expiry"),
        ]

    async def stop(self) -> None:
        tasks, self._tasks = self._tasks, []
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task

    async def _listen_loop(self) -> None:
        while True:
            connection: asyncpg.Connection | None = None
            try:
                url = make_url(get_settings().database_url).set(
                    drivername="postgresql"
                )
                connection = await asyncpg.connect(
                    url.render_as_string(hide_password=False)
                )

                def handle_notification(
                    _connection: asyncpg.Connection,
                    _pid: int,
                    _channel: str,
                    payload: str,
                ) -> None:
                    try:
                        message = json.loads(payload)
                        event_id = UUID(message["event_id"])
                        version = int(message["version"])
                    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                        logger.warning("Notificação de mapa de assentos inválida.")
                        return
                    asyncio.create_task(seat_map_hub.publish(event_id, version))

                await connection.add_listener(CHANNEL, handle_notification)
                await asyncio.Future()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Listener de assentos desconectado; nova tentativa em 5 segundos."
                )
                await asyncio.sleep(5)
            finally:
                if connection is not None:
                    with suppress(Exception):
                        await connection.close()

    async def _expiry_loop(self) -> None:
        while True:
            try:
                async with async_session_factory() as session:
                    await expire_due_holds_batch(session)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Falha ao expirar reservas temporárias de assentos.")
            await asyncio.sleep(3)


seat_map_runtime = SeatMapRuntime()
