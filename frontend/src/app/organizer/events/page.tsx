"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { buttonVariants, Button } from "@/components/ui/button";
import { EmptyState, ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { ApiError } from "@/services/api";
import { deleteEvent, listOrganizerEvents } from "@/services/events";
import { cn } from "@/utils/cn";
import { formatCurrency, formatDate } from "@/utils/format";

const statusLabels = {
  DRAFT: "Rascunho",
  PUBLISHED: "Publicado",
  CANCELLED: "Cancelado",
};

export default function OrganizerEventsPage() {
  const queryClient = useQueryClient();
  const eventsQuery = useQuery({
    queryKey: ["events", "organizer"],
    queryFn: listOrganizerEvents,
  });
  const deleteMutation = useMutation({
    mutationFn: deleteEvent,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["events"] });
    },
  });

  function handleDelete(eventId: string, title: string) {
    if (window.confirm(`Remover o evento “${title}”?`)) {
      deleteMutation.mutate(eventId);
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
      <div className="flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Organizador</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">Meus eventos</h1>
        </div>
        <Link href="/organizer/events/new" className={cn(buttonVariants())}>
          Publicar evento
        </Link>
      </div>

      {deleteMutation.error && (
        <ErrorMessage
          className="mt-6"
          message={
            deleteMutation.error instanceof ApiError
              ? deleteMutation.error.message
              : "Não foi possível remover o evento."
          }
        />
      )}

      {eventsQuery.isLoading && <LoadingState label="Carregando seus eventos..." />}
      {eventsQuery.error && (
        <ErrorMessage
          className="mt-6"
          message={
            eventsQuery.error instanceof ApiError
              ? eventsQuery.error.message
              : "Não foi possível carregar seus eventos."
          }
        />
      )}
      {eventsQuery.data?.length === 0 && (
        <div className="mt-8">
          <EmptyState
            title="Você ainda não publicou eventos"
            description="Pesquise o catálogo Ticketmaster e publique o primeiro evento da sua agenda."
          />
        </div>
      )}

      {Boolean(eventsQuery.data?.length) && (
        <div className="mt-8 overflow-hidden rounded-lg border border-slate-200 bg-white">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-5 py-3 font-medium">Evento</th>
                  <th className="px-5 py-3 font-medium">Data</th>
                  <th className="px-5 py-3 font-medium">Estoque</th>
                  <th className="px-5 py-3 font-medium">Preço</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 text-right font-medium">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {eventsQuery.data?.map((event) => (
                  <tr key={event.id}>
                    <td className="max-w-xs px-5 py-4 font-medium text-slate-950">{event.title}</td>
                    <td className="px-5 py-4 text-slate-600">{formatDate(event.event_date)}</td>
                    <td className="px-5 py-4 text-slate-600">
                      {event.available_tickets}/{event.capacity}
                    </td>
                    <td className="px-5 py-4 text-slate-600">{formatCurrency(event.ticket_price)}</td>
                    <td className="px-5 py-4">
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
                        {statusLabels[event.status]}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        <Link
                          href={`/organizer/events/${event.id}/seats`}
                          className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                        >
                          {event.seating_mode === "ASSIGNED" ? "Editar mapa" : "Criar mapa"}
                        </Link>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          disabled={deleteMutation.isPending}
                          onClick={() => handleDelete(event.id, event.title)}
                        >
                          Remover
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
}
