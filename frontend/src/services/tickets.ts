import { apiBlobRequest, apiRequest } from "@/services/api";
import type { Ticket } from "@/types/api";

export function listTickets() {
  return apiRequest<Ticket[]>("/api/v1/me/tickets");
}

export function getTicket(ticketId: string) {
  return apiRequest<Ticket>(`/api/v1/tickets/${ticketId}`);
}

export function getTicketQr(ticketId: string) {
  return apiBlobRequest(`/api/v1/tickets/${ticketId}/qr`);
}
