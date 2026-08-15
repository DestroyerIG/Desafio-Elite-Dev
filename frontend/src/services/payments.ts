import { apiRequest } from "@/services/api";
import type { Payment } from "@/types/api";

export function payReservation(reservationId: string, cardNumber: string) {
  return apiRequest<Payment>(`/api/v1/reservations/${reservationId}/payments`, {
    method: "POST",
    body: JSON.stringify({ card_number: cardNumber }),
  });
}
