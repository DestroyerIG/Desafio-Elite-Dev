"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { EventArtwork } from "@/components/events/event-artwork";
import { buttonVariants } from "@/components/ui/button";
import { ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { ApiError } from "@/services/api";
import { getSharedTicket, getSharedTicketQr } from "@/services/tickets";
import type { TicketStatus } from "@/types/api";
import { cn } from "@/utils/cn";
import { formatDate } from "@/utils/format";


const statusLabels: Record<TicketStatus, string> = {
  ACTIVE: "Ativo",
  USED: "Utilizado",
  CANCELLED: "Cancelado",
};

export function SharedTicketDetails({ token }: { token: string }) {
  const ticketQuery = useQuery({
    queryKey: ["shared-tickets", token],
    queryFn: () => getSharedTicket(token),
    retry: false,
  });
  const qrQuery = useQuery({
    queryKey: ["shared-tickets", token, "qr"],
    queryFn: () => getSharedTicketQr(token),
    retry: false,
  });
  const qrUrl = useMemo(
    () => (qrQuery.data ? URL.createObjectURL(qrQuery.data) : null),
    [qrQuery.data],
  );

  useEffect(
    () => () => {
      if (qrUrl) URL.revokeObjectURL(qrUrl);
    },
    [qrUrl],
  );

  if (ticketQuery.isLoading) {
    return <LoadingState label="Carregando ingresso compartilhado..." />;
  }
  if (ticketQuery.error || !ticketQuery.data) {
    return (
      <ErrorMessage
        message={
          ticketQuery.error instanceof ApiError
            ? ticketQuery.error.message
            : "Não foi possível abrir este ingresso compartilhado."
        }
      />
    );
  }

  const ticket = ticketQuery.data;
  return (
    <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="grid lg:grid-cols-[1fr_22rem]">
        <div>
          <EventArtwork
            imageUrl={ticket.event.image_url}
            title={ticket.event.title}
            className="h-56 sm:h-72"
          />
          <div className="p-6 sm:p-8">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
                {formatDate(ticket.event.event_date)}
              </p>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {statusLabels[ticket.status]}
              </span>
            </div>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
              {ticket.event.title}
            </h1>
            <p className="mt-4 leading-7 text-slate-600">
              {ticket.event.venue_name} · {ticket.event.venue_address}
            </p>
            <div className="mt-8 border-y border-slate-100 py-6">
              <p className="text-sm font-medium text-slate-500">Código público</p>
              <p className="mt-2 font-mono text-lg font-semibold text-slate-950">
                {ticket.public_code}
              </p>
            </div>
            <p className="mt-5 text-sm leading-6 text-slate-600">
              Este é um acesso público somente para visualização. Alterações no
              ingresso exigem autenticação do proprietário.
            </p>
            <Link
              href="/events"
              className={cn(buttonVariants({ variant: "outline" }), "mt-6")}
            >
              Ver eventos
            </Link>
          </div>
        </div>

        <aside className="flex min-h-96 flex-col items-center justify-center border-t border-slate-200 bg-slate-50 p-8 text-center lg:border-l lg:border-t-0">
          <p className="text-sm font-semibold text-slate-950">QR do ingresso</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Apresente este código na entrada do evento.
          </p>
          {qrQuery.isLoading && <LoadingState label="Gerando QR..." />}
          {qrQuery.error && (
            <ErrorMessage
              className="mt-5"
              message={
                qrQuery.error instanceof ApiError
                  ? qrQuery.error.message
                  : "Não foi possível gerar o QR."
              }
            />
          )}
          {qrUrl && (
            <div className="mt-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <Image
                src={qrUrl}
                alt={`QR do ingresso ${ticket.public_code}`}
                width={264}
                height={264}
                unoptimized
                className="h-auto w-64"
              />
            </div>
          )}
          <p className="mt-5 font-mono text-xs text-slate-500">
            {ticket.public_code}
          </p>
        </aside>
      </div>
    </article>
  );
}
