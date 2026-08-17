"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { EventCard } from "@/components/events/event-card";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { ApiError } from "@/services/api";
import { listEvents, type EventFilters } from "@/services/events";

export function EventList({
  limit,
  filters = {},
  carousel = false,
}: {
  limit?: number;
  filters?: EventFilters;
  carousel?: boolean;
}) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [scrollState, setScrollState] = useState({
    canScrollLeft: false,
    canScrollRight: false,
  });
  const eventsQuery = useQuery({
    queryKey: ["events", "public", filters],
    queryFn: () => listEvents(filters),
  });

  const updateScrollState = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const nextState = {
      canScrollLeft: container.scrollLeft > 1,
      canScrollRight:
        container.scrollLeft + container.clientWidth < container.scrollWidth - 1,
    };

    setScrollState((currentState) =>
      currentState.canScrollLeft === nextState.canScrollLeft &&
      currentState.canScrollRight === nextState.canScrollRight
        ? currentState
        : nextState,
    );
  }, []);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!carousel || !container) return;

    const animationFrame = requestAnimationFrame(updateScrollState);
    const resizeObserver = new ResizeObserver(updateScrollState);

    container.addEventListener("scroll", updateScrollState, { passive: true });
    resizeObserver.observe(container);

    return () => {
      cancelAnimationFrame(animationFrame);
      container.removeEventListener("scroll", updateScrollState);
      resizeObserver.disconnect();
    };
  }, [carousel, eventsQuery.data?.length, updateScrollState]);

  function scrollEvents(direction: -1 | 1) {
    const container = scrollContainerRef.current;
    const firstCard = container?.firstElementChild as HTMLElement | null;
    if (!container || !firstCard) return;

    const gap = Number.parseFloat(getComputedStyle(container).columnGap) || 0;
    container.scrollBy({
      left: direction * (firstCard.offsetWidth + gap),
      behavior: "smooth",
    });
  }

  if (eventsQuery.isLoading) return <LoadingState label="Buscando eventos..." />;
  if (eventsQuery.error) {
    const message =
      eventsQuery.error instanceof ApiError
        ? eventsQuery.error.message
        : "Não foi possível carregar os eventos.";
    return <ErrorMessage message={message} />;
  }

  const events = !carousel && limit ? eventsQuery.data?.slice(0, limit) : eventsQuery.data;
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

  if (carousel) {
    return (
      <div className="relative">
        <div
          ref={scrollContainerRef}
          className="flex snap-x snap-mandatory scroll-smooth gap-6 overflow-x-auto [scrollbar-width:none] motion-reduce:scroll-auto [&::-webkit-scrollbar]:hidden"
          role="region"
          aria-label="Eventos publicados"
          tabIndex={0}
        >
          {events.map((event) => (
            <div
              key={event.id}
              className="min-w-[88%] snap-start sm:min-w-[calc(50%-0.75rem)] lg:min-w-[calc(33.333%-1rem)]"
            >
              <EventCard event={event} />
            </div>
          ))}
        </div>
        <Button
          type="button"
          variant="outline"
          className="absolute left-2 top-1/2 z-10 h-11 w-11 -translate-y-1/2 rounded-full border-slate-200 bg-white/95 px-0 text-slate-700 shadow-md backdrop-blur-sm hover:bg-white disabled:opacity-0"
          aria-label="Ver eventos anteriores"
          title="Ver eventos anteriores"
          disabled={!scrollState.canScrollLeft}
          onClick={() => scrollEvents(-1)}
        >
          <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m15 18-6-6 6-6" />
          </svg>
        </Button>
        <Button
          type="button"
          variant="outline"
          className="absolute right-2 top-1/2 z-10 h-11 w-11 -translate-y-1/2 rounded-full border-slate-200 bg-white/95 px-0 text-slate-700 shadow-md backdrop-blur-sm hover:bg-white disabled:opacity-0"
          aria-label="Ver próximos eventos"
          title="Ver próximos eventos"
          disabled={!scrollState.canScrollRight}
          onClick={() => scrollEvents(1)}
        >
          <svg
            aria-hidden="true"
            viewBox="0 0 24 24"
            className="h-5 w-5"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m9 18 6-6-6-6" />
          </svg>
        </Button>
      </div>
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
