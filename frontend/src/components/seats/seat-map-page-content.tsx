"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { SeatMapPicker } from "@/components/seats/seat-map-picker";
import { buttonVariants } from "@/components/ui/button";
import { ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { ApiError } from "@/services/api";
import { getEvent } from "@/services/events";
import { cn } from "@/utils/cn";

export function SeatMapPageContent({ eventId }: { eventId: string }) {
  const eventQuery = useQuery({
    queryKey: ["events", eventId],
    queryFn: () => getEvent(eventId),
  });

  if (eventQuery.isLoading) return <LoadingState label="Carregando evento..." />;
  if (eventQuery.error || !eventQuery.data) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8">
        <ErrorMessage
          message={
            eventQuery.error instanceof ApiError
              ? eventQuery.error.message
              : "Não foi possível carregar o evento."
          }
        />
      </main>
    );
  }

  if (eventQuery.data.seating_mode !== "ASSIGNED") {
    return (
      <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8">
        <ErrorMessage message="Este evento não utiliza assentos marcados." />
        <Link
          href={`/events/${eventId}`}
          className={cn(buttonVariants({ variant: "outline" }), "mt-5")}
        >
          Voltar ao evento
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-14">
      <SeatMapPicker
        eventId={eventId}
        eventTitle={eventQuery.data.title}
        ticketPrice={eventQuery.data.ticket_price}
      />
    </main>
  );
}
