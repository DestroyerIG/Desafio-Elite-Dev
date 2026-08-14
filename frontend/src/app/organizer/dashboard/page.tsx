"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { buttonVariants } from "@/components/ui/button";
import { ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { ApiError } from "@/services/api";
import { listOrganizerEvents } from "@/services/events";
import { cn } from "@/utils/cn";

export default function OrganizerDashboardPage() {
  const eventsQuery = useQuery({
    queryKey: ["events", "organizer"],
    queryFn: listOrganizerEvents,
  });

  if (eventsQuery.isLoading) return <LoadingState label="Carregando painel..." />;
  if (eventsQuery.error) {
    return (
      <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8">
        <ErrorMessage
          message={
            eventsQuery.error instanceof ApiError
              ? eventsQuery.error.message
              : "Não foi possível carregar o painel."
          }
        />
      </main>
    );
  }

  const events = eventsQuery.data ?? [];
  const published = events.filter((event) => event.status === "PUBLISHED").length;
  const available = events.reduce((total, event) => total + event.available_tickets, 0);

  return (
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
      <div className="flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Organizador</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Visão geral</h1>
        </div>
        <Link href="/organizer/events/new" className={cn(buttonVariants())}>
          Publicar evento
        </Link>
      </div>

      <dl className="mt-8 grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <dt className="text-sm text-slate-500">Eventos cadastrados</dt>
          <dd className="mt-2 text-3xl font-semibold text-slate-950">{events.length}</dd>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <dt className="text-sm text-slate-500">Eventos publicados</dt>
          <dd className="mt-2 text-3xl font-semibold text-slate-950">{published}</dd>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <dt className="text-sm text-slate-500">Ingressos disponíveis</dt>
          <dd className="mt-2 text-3xl font-semibold text-slate-950">{available}</dd>
        </div>
      </dl>
    </main>
  );
}

