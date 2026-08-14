import { apiRequest } from "@/services/api";
import type { CatalogEvent, Event } from "@/types/api";

export function listEvents() {
  return apiRequest<Event[]>("/api/v1/events");
}

export function getEvent(eventId: string) {
  return apiRequest<Event>(`/api/v1/events/${eventId}`);
}

export function listOrganizerEvents() {
  return apiRequest<Event[]>("/api/v1/organizer/events");
}

export function searchCatalog(query: string) {
  return apiRequest<CatalogEvent[]>(
    `/api/v1/catalog/events?q=${encodeURIComponent(query)}`,
  );
}

export function publishEvent(data: {
  external_id: string;
  capacity: number;
  ticket_price: string;
}) {
  return apiRequest<Event>("/api/v1/events", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteEvent(eventId: string) {
  return apiRequest<void>(`/api/v1/events/${eventId}`, { method: "DELETE" });
}

