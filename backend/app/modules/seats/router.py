import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.modules.auth.dependencies import require_roles
from app.modules.reservations.schemas import ReservationResponse
from app.modules.seats.realtime import seat_map_hub
from app.modules.seats.schemas import SeatHoldCreate, SeatMapConfigure, SeatMapResponse
from app.modules.seats.service import (
    configure_seat_map,
    create_seat_hold,
    get_organizer_seat_map,
    get_public_seat_map,
    remove_seat_map,
)


router = APIRouter(prefix="/api/v1", tags=["seats"])
DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]
Customer = Annotated[User, Depends(require_roles(UserRole.CUSTOMER))]
Organizer = Annotated[User, Depends(require_roles(UserRole.ORGANIZER))]


@router.get("/events/{event_id}/seat-map", response_model=SeatMapResponse)
async def public_seat_map(
    event_id: UUID,
    session: DatabaseSession,
) -> SeatMapResponse:
    seat_map = await get_public_seat_map(session, event_id)
    return SeatMapResponse.model_validate(seat_map)


@router.put(
    "/organizer/events/{event_id}/seat-map",
    response_model=SeatMapResponse,
)
async def put_seat_map(
    event_id: UUID,
    data: SeatMapConfigure,
    session: DatabaseSession,
    organizer: Organizer,
) -> SeatMapResponse:
    seat_map = await configure_seat_map(session, organizer, event_id, data)
    return SeatMapResponse.model_validate(seat_map)


@router.get(
    "/organizer/events/{event_id}/seat-map",
    response_model=SeatMapResponse,
)
async def organizer_seat_map(
    event_id: UUID,
    session: DatabaseSession,
    organizer: Organizer,
) -> SeatMapResponse:
    seat_map = await get_organizer_seat_map(
        session, organizer, event_id
    )
    return SeatMapResponse.model_validate(seat_map)


@router.delete(
    "/organizer/events/{event_id}/seat-map",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_seat_map(
    event_id: UUID,
    session: DatabaseSession,
    organizer: Organizer,
) -> Response:
    await remove_seat_map(session, organizer, event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/events/{event_id}/seat-holds",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def hold_seats(
    event_id: UUID,
    data: SeatHoldCreate,
    session: DatabaseSession,
    customer: Customer,
) -> ReservationResponse:
    reservation = await create_seat_hold(session, customer, event_id, data)
    return ReservationResponse.model_validate(reservation)


@router.websocket("/events/{event_id}/seat-map/stream")
async def seat_map_stream(websocket: WebSocket, event_id: UUID) -> None:
    allowed_origin = str(get_settings().frontend_url).rstrip("/")
    origin = websocket.headers.get("origin")
    if origin is not None and origin.rstrip("/") != allowed_origin:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        async with seat_map_hub.subscribe(event_id) as queue:
            await websocket.send_json({"type": "connected", "event_id": str(event_id)})
            while True:
                try:
                    version = await asyncio.wait_for(queue.get(), timeout=25)
                    await websocket.send_json(
                        {
                            "type": "seat_map_changed",
                            "event_id": str(event_id),
                            "version": version,
                        }
                    )
                except TimeoutError:
                    await websocket.send_json({"type": "ping"})
    except (WebSocketDisconnect, RuntimeError):
        return
