import { apiBlobRequest, apiRequest } from "@/services/api";
import type { SharedTicket, Ticket, TicketShare } from "@/types/api";

export function listTickets() {
  return apiRequest<Ticket[]>("/api/v1/me/tickets");
}

export function getTicket(ticketId: string) {
  return apiRequest<Ticket>(`/api/v1/tickets/${ticketId}`);
}

export function getTicketQr(ticketId: string) {
  return apiBlobRequest(`/api/v1/tickets/${ticketId}/qr`);
}

export function shareTicket(ticketId: string) {
  return apiRequest<TicketShare>(`/api/v1/tickets/${ticketId}/share`, {
    method: "POST",
  });
}

export function getSharedTicket(token: string) {
  return apiRequest<SharedTicket>(
    `/api/v1/shared-tickets/${encodeURIComponent(token)}`,
  );
}

export function getSharedTicketQr(token: string) {
  return apiBlobRequest(
    `/api/v1/shared-tickets/${encodeURIComponent(token)}/qr`,
  );
}
