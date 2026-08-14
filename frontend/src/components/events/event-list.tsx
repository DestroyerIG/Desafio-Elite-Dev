"use client";

import { useQuery } from "@tanstack/react-query";

import { EventCard } from "@/components/events/event-card";
import { EmptyState, ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { ApiError } from "@/services/api";
import { listEvents } from "@/services/events";

export function EventList({ limit }: { limit?: number }) {
  const eventsQuery = useQuery({
    queryKey: ["events", "public"],
    queryFn: listEvents,
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
    return (
      <EmptyState
        title="Nenhum evento publicado"
        description="Os eventos publicados pelos organizadores aparecerão aqui."
      />
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  );
}

