"use client";

import { useQuery } from "@tanstack/react-query";

import { EventCard } from "@/components/events/event-card";
import { EmptyState, ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { ApiError } from "@/services/api";
import { listEvents, type EventFilters } from "@/services/events";

export function EventList({
  limit,
  filters = {},
}: {
  limit?: number;
  filters?: EventFilters;
}) {
  const eventsQuery = useQuery({
    queryKey: ["events", "public", filters],
    queryFn: () => listEvents(filters),
  });

  if (eventsQuery.isLoading) return <LoadingState label="Buscando eventos..." />;
  if (eventsQuery.error) {
    const message =
      eventsQuery.error instanceof ApiError
        ? eventsQuery.error.message
        : "Não foi possível carregar os eventos.";
    return <ErrorMessage message={message} />;
  }

  const events = limit ? eventsQuery.data?.slice(0, limit) : eventsQuery.data;
  if (!events?.length) {
    const hasFilters = Boolean(
      filters.query || filters.dateFrom || filters.dateTo || filters.availableOnly,
    );
    return (
      <EmptyState
        title={hasFilters ? "Nenhum evento encontrado" : "Nenhum evento publicado"}
        description={
          hasFilters
            ? "Tente remover algum filtro ou pesquisar por outro termo."
            : "Os eventos publicados pelos organizadores aparecerão aqui."
        }
      />
    );
  }

  return (
    <div>
      {!limit && (
        <p className="mb-4 text-sm text-slate-600" aria-live="polite">
          {events.length} {events.length === 1 ? "evento encontrado" : "eventos encontrados"}
        </p>
      )}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {events.map((event) => (
          <EventCard key={event.id} event={event} />
        ))}
      </div>
    </div>
  );
}
