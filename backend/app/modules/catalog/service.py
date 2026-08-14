from app.integrations.ticketmaster.client import TicketmasterClient
from app.modules.catalog.schemas import CatalogEvent


async def search_catalog(
    client: TicketmasterClient, query: str
) -> list[CatalogEvent]:
    return await client.search_events(query.strip())

