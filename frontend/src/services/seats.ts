import { API_URL, apiRequest } from "@/services/api";
import type { Reservation, SeatMap } from "@/types/api";

export interface SeatSectionInput {
  name: string;
  row_count: number;
  seats_per_row: number;
}

export function getSeatMap(eventId: string) {
  return apiRequest<SeatMap>(`/api/v1/events/${eventId}/seat-map`);
}

export function getOrganizerSeatMap(eventId: string) {
  return apiRequest<SeatMap>(
    `/api/v1/organizer/events/${eventId}/seat-map`,
  );
}

export function configureSeatMap(
  eventId: string,
  data: { stage_label: string; sections: SeatSectionInput[] },
) {
  return apiRequest<SeatMap>(
    `/api/v1/organizer/events/${eventId}/seat-map`,
    { method: "PUT", body: JSON.stringify(data) },
  );
}

export function removeSeatMap(eventId: string) {
  return apiRequest<void>(
    `/api/v1/organizer/events/${eventId}/seat-map`,
    { method: "DELETE" },
  );
}

export function holdSeats(eventId: string, seatIds: string[]) {
  return apiRequest<Reservation>(`/api/v1/events/${eventId}/seat-holds`, {
    method: "POST",
    body: JSON.stringify({ seat_ids: seatIds }),
  });
}

export function seatMapStreamUrl(eventId: string) {
  const url = new URL(API_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `/api/v1/events/${eventId}/seat-map/stream`;
  url.search = "";
  return url.toString();
}
