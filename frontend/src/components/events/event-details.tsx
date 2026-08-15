"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { EventArtwork } from "@/components/events/event-artwork";
import { buttonVariants } from "@/components/ui/button";
import { ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api";
import { getEvent } from "@/services/events";
import { cn } from "@/utils/cn";
import { formatCurrency, formatDate } from "@/utils/format";

export function EventDetails({ eventId }: { eventId: string }) {
  const { user } = useAuth();
  const eventQuery = useQuery({
    queryKey: ["events", eventId],
    queryFn: () => getEvent(eventId),
  });

  if (eventQuery.isLoading) return <LoadingState label="Carregando evento..." />;
  if (eventQuery.error || !eventQuery.data) {
    const message =
      eventQuery.error instanceof ApiError
        ? eventQuery.error.message
        : "Não foi possível carregar o evento.";
    return <ErrorMessage message={message} />;
  }

  const event = eventQuery.data;
  return (
    <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <EventArtwork
        imageUrl={event.image_url}
        title={event.title}
        className="h-64 sm:h-96"
      />
      <div className="grid gap-10 p-6 sm:p-8 lg:grid-cols-[1fr_18rem]">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
            {formatDate(event.event_date)}
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
            {event.title}
          </h1>
          <div className="mt-7 border-t border-slate-100 pt-6">
            <h2 className="font-semibold text-slate-950">Sobre o evento</h2>
            <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-600">
              {event.description || "O organizador ainda não adicionou uma descrição."}
            </p>
          </div>
        </div>

        <aside className="self-start rounded-lg border border-slate-200 bg-slate-50 p-5">
          <dl className="space-y-5 text-sm">
            <div>
              <dt className="font-medium text-slate-500">Local</dt>
              <dd className="mt-1 font-medium text-slate-900">{event.venue_name}</dd>
              <dd className="mt-1 text-slate-600">{event.venue_address}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Ingresso</dt>
              <dd className="mt-1 text-xl font-semibold text-slate-950">
                {formatCurrency(event.ticket_price)}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Disponibilidade</dt>
              <dd className="mt-1 text-slate-900">
                {event.available_tickets} de {event.capacity} ingressos
              </dd>
            </div>
          </dl>
          <div className="mt-6 border-t border-slate-200 pt-5">
            {event.available_tickets === 0 ? (
              <p className="rounded-md bg-slate-200 px-4 py-3 text-center text-sm font-semibold text-slate-600">
                Evento esgotado
              </p>
            ) : user && user.role !== "CUSTOMER" ? (
              <p className="text-xs leading-5 text-slate-500">
                Entre com uma conta de cliente para reservar ingressos.
              </p>
            ) : (
              <Link
                href={
                  user
                    ? `/checkout/${event.id}`
                    : `/login?next=/checkout/${event.id}`
                }
                className={cn(buttonVariants(), "w-full")}
              >
                Reservar ingressos
              </Link>
            )}
          </div>
        </aside>
      </div>
    </article>
  );
}
