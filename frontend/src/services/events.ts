import { apiRequest } from "@/services/api";
import type { CatalogEvent, Event } from "@/types/api";

export interface EventFilters {
  query?: string;
  dateFrom?: string;
  dateTo?: string;
  availableOnly?: boolean;
}

function dateBoundaryToIso(value: string, endOfDay = false) {
  const suffix = endOfDay ? "T23:59:59.999" : "T00:00:00.000";
  const date = new Date(`${value}${suffix}`);
  return Number.isNaN(date.getTime()) ? undefined : date.toISOString();
}

export function listEvents(filters: EventFilters = {}) {
  const params = new URLSearchParams();
  const query = filters.query?.trim();
  const dateFrom = filters.dateFrom
    ? dateBoundaryToIso(filters.dateFrom)
    : undefined;
  const dateTo = filters.dateTo
    ? dateBoundaryToIso(filters.dateTo, true)
    : undefined;

  if (query) params.set("q", query);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  if (filters.availableOnly) params.set("available_only", "true");

  const queryString = params.toString();
  return apiRequest<Event[]>(`/api/v1/events${queryString ? `?${queryString}` : ""}`);
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

export function createOrganizerEvent(data: FormData) {
  return apiRequest<Event>("/api/v1/organizer/events", {
    method: "POST",
    body: data,
  });
}

export function deleteEvent(eventId: string) {
  return apiRequest<void>(`/api/v1/events/${eventId}`, { method: "DELETE" });
}
