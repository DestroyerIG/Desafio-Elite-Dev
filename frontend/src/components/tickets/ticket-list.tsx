"use client";

import { useQuery } from "@tanstack/react-query";

import { TicketCard } from "@/components/tickets/ticket-card";
import { EmptyState, ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { ApiError } from "@/services/api";
import { listTickets } from "@/services/tickets";

export function TicketList() {
  const ticketsQuery = useQuery({
    queryKey: ["tickets"],
    queryFn: listTickets,
  });

  if (ticketsQuery.isLoading) {
    return <LoadingState label="Carregando ingressos..." />;
  }
  if (ticketsQuery.error) {
    return (
      <ErrorMessage
        message={
          ticketsQuery.error instanceof ApiError
            ? ticketsQuery.error.message
            : "Não foi possível carregar seus ingressos."
        }
      />
    );
  }
  if (!ticketsQuery.data?.length) {
    return (
      <EmptyState
        title="Você ainda não possui ingressos"
        description="Escolha um evento, faça a reserva e conclua o pagamento simulado."
      />
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {ticketsQuery.data.map((ticket) => (
        <TicketCard key={ticket.id} ticket={ticket} />
      ))}
    </div>
  );
}
