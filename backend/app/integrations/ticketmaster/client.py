from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from fastapi import Depends
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.modules.catalog.schemas import CatalogEvent


class TicketmasterClient:
    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.ticketmaster_api_key
        self._client = httpx.AsyncClient(
            base_url=str(settings.ticketmaster_base_url),
            timeout=settings.ticketmaster_timeout_seconds,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def search_events(self, query: str) -> list[CatalogEvent]:
        payload = await self._request(
            "events.json",
            params={"keyword": query, "size": 12, "locale": "*"},
        )
        raw_events = payload.get("_embedded", {}).get("events", [])
        events: list[CatalogEvent] = []
        for raw_event in raw_events:
            try:
                events.append(self._map_event(raw_event))
            except (KeyError, TypeError, ValueError, ValidationError):
                continue
        return events

    async def get_event(self, external_id: str) -> CatalogEvent:
        payload = await self._request(
            f"events/{external_id}.json",
            params={"locale": "*"},
            not_found_code="EXTERNAL_EVENT_NOT_FOUND",
        )
        try:
            return self._map_event(payload)
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise AppError(
                "CATALOG_DATA_INCOMPLETE",
                "O evento externo não possui os dados necessários para publicação.",
                422,
            ) from exc

    async def _request(
        self,
        path: str,
        *,
        params: dict[str, Any],
        not_found_code: str = "CATALOG_NOT_FOUND",
    ) -> dict[str, Any]:
        if not self._api_key:
            raise AppError(
                "CATALOG_NOT_CONFIGURED",
                "A chave da Ticketmaster não está configurada no backend.",
                503,
            )

        request_params = {**params, "apikey": self._api_key}
        try:
            response = await self._client.get(path, params=request_params)
        except httpx.TimeoutException as exc:
            raise AppError(
                "CATALOG_UNAVAILABLE",
                "O catálogo externo demorou demais para responder.",
                504,
            ) from exc
        except httpx.HTTPError as exc:
            raise AppError(
                "CATALOG_UNAVAILABLE",
                "Não foi possível acessar o catálogo externo.",
                502,
            ) from exc

        if response.status_code == 404:
            raise AppError(not_found_code, "Evento externo não encontrado.", 404)
        if response.status_code == 401:
            raise AppError(
                "CATALOG_AUTHENTICATION_FAILED",
                "A Ticketmaster recusou a credencial configurada.",
                502,
            )
        if response.status_code == 429:
            raise AppError(
                "CATALOG_RATE_LIMITED",
                "O limite de consultas ao catálogo foi atingido.",
                503,
            )
        if response.is_error:
            raise AppError(
                "CATALOG_UNAVAILABLE",
                "O catálogo externo está temporariamente indisponível.",
                502,
            )

        try:
            return response.json()
        except ValueError as exc:
            raise AppError(
                "CATALOG_INVALID_RESPONSE",
                "O catálogo externo retornou uma resposta inválida.",
                502,
            ) from exc

    @staticmethod
    def _map_event(payload: dict[str, Any]) -> CatalogEvent:
        venue = (payload.get("_embedded", {}).get("venues") or [{}])[0]
        start = payload.get("dates", {}).get("start", {})
        event_date = TicketmasterClient._parse_event_date(start, venue)
        address = TicketmasterClient._format_address(venue)
        images = payload.get("images") or []
        preferred_images = [image for image in images if image.get("ratio") == "16_9"]
        image_pool = preferred_images or images
        image = max(image_pool, key=lambda item: item.get("width", 0), default={})

        return CatalogEvent(
            external_id=payload["id"],
            title=payload["name"],
            description=payload.get("info") or payload.get("pleaseNote"),
            image_url=image.get("url"),
            venue_name=venue.get("name") or "Local não informado pela Ticketmaster",
            venue_address=address or "Endereço não informado pela Ticketmaster",
            event_date=event_date,
        )

    @staticmethod
    def _parse_event_date(start: dict[str, Any], venue: dict[str, Any]) -> datetime:
        if date_time := start.get("dateTime"):
            return datetime.fromisoformat(date_time.replace("Z", "+00:00"))

        local_date = start.get("localDate")
        if not local_date:
            raise ValueError("Event date is missing")
        local_time = start.get("localTime", "00:00:00")
        event_date = datetime.fromisoformat(f"{local_date}T{local_time}")
        timezone_name = venue.get("timezone")
        if not timezone_name:
            raise ValueError("Event timezone is missing")
        try:
            return event_date.replace(tzinfo=ZoneInfo(timezone_name))
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Event timezone is invalid") from exc

    @staticmethod
    def _format_address(venue: dict[str, Any]) -> str:
        parts = [
            venue.get("address", {}).get("line1"),
            venue.get("city", {}).get("name"),
            venue.get("state", {}).get("stateCode")
            or venue.get("state", {}).get("name"),
            venue.get("postalCode"),
            venue.get("country", {}).get("countryCode")
            or venue.get("country", {}).get("name"),
        ]
        return ", ".join(part.strip() for part in parts if isinstance(part, str) and part.strip())


async def get_ticketmaster_client(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[TicketmasterClient]:
    client = TicketmasterClient(settings)
    try:
        yield client
    finally:
        await client.close()

