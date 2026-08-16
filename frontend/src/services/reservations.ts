import { apiRequest } from "@/services/api";
import type { CustomerReservation, Reservation } from "@/types/api";

export function listReservations() {
  return apiRequest<CustomerReservation[]>("/api/v1/me/reservations");
}

export function createReservation(eventId: string, quantity: number) {
  return apiRequest<Reservation>(`/api/v1/events/${eventId}/reservations`, {
    method: "POST",
    body: JSON.stringify({ quantity }),
  });
}

export function getReservation(reservationId: string) {
  return apiRequest<Reservation>(`/api/v1/reservations/${reservationId}`);
}

export function cancelReservation(reservationId: string) {
  return apiRequest<Reservation>(
    `/api/v1/reservations/${reservationId}/cancel`,
    { method: "POST" },
  );
}
