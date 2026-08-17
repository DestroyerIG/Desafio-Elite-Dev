"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { EventArtwork } from "@/components/events/event-artwork";
import { Button, buttonVariants } from "@/components/ui/button";
import { ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/services/api";
import { getTicket, getTicketQr, shareTicket } from "@/services/tickets";
import type { TicketStatus } from "@/types/api";
import { cn } from "@/utils/cn";
import { formatDate } from "@/utils/format";

const statusLabels: Record<TicketStatus, string> = {
  ACTIVE: "Ativo",
  USED: "Utilizado",
  REFUNDED: "Reembolsado",
  CANCELLED: "Cancelado",
};

export function TicketDetails({ ticketId }: { ticketId: string }) {
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);
  const ticketQuery = useQuery({
    queryKey: ["tickets", ticketId],
    queryFn: () => getTicket(ticketId),
  });
  const ticketIsActive = ticketQuery.data?.status === "ACTIVE";
  const qrQuery = useQuery({
    queryKey: ["tickets", ticketId, "qr"],
    queryFn: () => getTicketQr(ticketId),
    enabled: ticketIsActive,
  });
  const qrUrl = useMemo(
    () =>
      ticketIsActive && qrQuery.data
        ? URL.createObjectURL(qrQuery.data)
        : null,
    [qrQuery.data, ticketIsActive],
  );
  const shareMutation = useMutation({
    mutationFn: () => shareTicket(ticketId),
    onSuccess: (share) => {
      setShareUrl(`${window.location.origin}/shared-tickets/${share.token}`);
      setCopyFeedback(null);
    },
  });

  useEffect(
    () => () => {
      if (qrUrl) URL.revokeObjectURL(qrUrl);
    },
    [qrUrl],
  );

  if (ticketQuery.isLoading) {
    return <LoadingState label="Carregando ingresso..." />;
  }
  if (ticketQuery.error || !ticketQuery.data) {
    return (
      <ErrorMessage
        message={
          ticketQuery.error instanceof ApiError
            ? ticketQuery.error.message
            : "Não foi possível carregar o ingresso."
        }
      />
    );
  }

  const ticket = ticketQuery.data;

  async function copyShareUrl() {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopyFeedback("Link copiado.");
    } catch {
      setCopyFeedback("Selecione o endereço e copie manualmente.");
    }
  }

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
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
              {formatDate(ticket.event.event_date)}
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
              {ticket.event.title}
            </h1>
            <p className="mt-4 leading-7 text-slate-600">
              {ticket.event.venue_name} · {ticket.event.venue_address}
            </p>
            <dl className="mt-8 grid gap-5 border-y border-slate-100 py-6 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-medium text-slate-500">Código público</dt>
                <dd className="mt-1 font-mono font-semibold text-slate-950">
                  {ticket.public_code}
                </dd>
              </div>
              <div>
                <dt className="font-medium text-slate-500">Status</dt>
                <dd className="mt-1 font-semibold text-slate-950">
                  {statusLabels[ticket.status]}
                </dd>
              </div>
              {ticket.seat && (
                <div>
                  <dt className="font-medium text-slate-500">Lugar marcado</dt>
                  <dd className="mt-1 font-semibold text-slate-950">
                    {ticket.seat.section.name} · Fileira {ticket.seat.row_label} · Assento {ticket.seat.number}
                  </dd>
                </div>
              )}
            </dl>
            {ticket.status === "ACTIVE" ? (
              <section className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-5">
                <h2 className="font-semibold text-slate-950">
                  Compartilhar ingresso
                </h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  O link permite visualizar somente este ingresso e seu QR Code.
                  Quem receber o endereço poderá apresentá-lo na portaria.
                </p>
                {!shareUrl && (
                  <Button
                    type="button"
                    variant="secondary"
                    className="mt-4"
                    disabled={shareMutation.isPending}
                    onClick={() => shareMutation.mutate()}
                  >
                    {shareMutation.isPending
                      ? "Gerando link..."
                      : "Gerar link compartilhável"}
                  </Button>
                )}
                {shareMutation.error && (
                  <ErrorMessage
                    className="mt-4"
                    message={
                      shareMutation.error instanceof ApiError
                        ? shareMutation.error.message
                        : "Não foi possível compartilhar este ingresso."
                    }
                  />
                )}
                {shareUrl && (
                  <div className="mt-4">
                    <div className="flex flex-col gap-2 sm:flex-row">
                      <Input
                        aria-label="Link público do ingresso"
                        readOnly
                        value={shareUrl}
                        onFocus={(event) => event.currentTarget.select()}
                      />
                      <Button type="button" onClick={copyShareUrl}>
                        Copiar link
                      </Button>
                    </div>
                    {copyFeedback && (
                      <p className="mt-2 text-sm text-slate-600" role="status">
                        {copyFeedback}
                      </p>
                    )}
                  </div>
                )}
              </section>
            ) : (
              <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-5 text-sm leading-6 text-slate-600">
                Este ingresso não está ativo. Seu QR Code e compartilhamento
                permanecem indisponíveis.
              </div>
            )}
            <Link
              href="/my-tickets"
              className={cn(buttonVariants({ variant: "outline" }), "mt-6")}
            >
              Voltar aos ingressos
            </Link>
          </div>
        </div>

        <aside className="flex min-h-96 flex-col items-center justify-center border-t border-slate-200 bg-slate-50 p-8 text-center lg:border-l lg:border-t-0">
          <p className="text-sm font-semibold text-slate-950">QR do ingresso</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Apresente este código na entrada do evento.
          </p>
          {ticketIsActive && qrQuery.isLoading && (
            <LoadingState label="Gerando QR..." />
          )}
          {ticketIsActive && qrQuery.error && (
            <ErrorMessage
              className="mt-5"
              message={
                qrQuery.error instanceof ApiError
                  ? qrQuery.error.message
                  : "Não foi possível gerar o QR."
              }
            />
          )}
          {ticketIsActive && qrUrl && (
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
          {!ticketIsActive && (
            <p className="mt-5 text-sm leading-6 text-slate-600">
              QR Code indisponível para ingresso{" "}
              {statusLabels[ticket.status].toLowerCase()}.
            </p>
          )}
          <p className="mt-5 font-mono text-xs text-slate-500">
            {ticket.public_code}
          </p>
        </aside>
      </div>
    </article>
  );
}
