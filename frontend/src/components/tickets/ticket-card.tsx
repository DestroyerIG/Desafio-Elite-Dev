import Link from "next/link";

import { EventArtwork } from "@/components/events/event-artwork";
import type { Ticket, TicketStatus } from "@/types/api";
import { formatDate } from "@/utils/format";


const statusLabels: Record<TicketStatus, string> = {
  ACTIVE: "Ativo",
  USED: "Utilizado",
  REFUNDED: "Reembolsado",
  CANCELLED: "Cancelado",
};

const statusStyles: Record<TicketStatus, string> = {
  ACTIVE: "bg-emerald-50 text-emerald-800",
  USED: "bg-amber-50 text-amber-800",
  REFUNDED: "bg-slate-100 text-slate-700",
  CANCELLED: "bg-slate-100 text-slate-700",
};

export function TicketCard({ ticket }: { ticket: Ticket }) {
  return (
    <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition-shadow hover:shadow-md">
      <EventArtwork
        imageUrl={ticket.event.image_url}
        title={ticket.event.title}
        className="h-40"
      />
      <div className="p-5">
        <div className="flex items-center justify-between gap-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
            {formatDate(ticket.event.event_date)}
          </p>
          <span
            className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusStyles[ticket.status]}`}
          >
            {statusLabels[ticket.status]}
          </span>
        </div>
        <h2 className="mt-3 text-lg font-semibold leading-6 text-slate-950">
          {ticket.event.title}
        </h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          {ticket.event.venue_name} · {ticket.event.venue_address}
        </p>
        {ticket.seat && (
          <p className="mt-3 rounded-md bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-900">
            {ticket.seat.section.name} · Fileira {ticket.seat.row_label} · Assento {ticket.seat.number}
          </p>
        )}
        <div className="mt-5 flex items-center justify-between gap-4 border-t border-slate-100 pt-4">
          <span className="font-mono text-xs font-medium text-slate-600">
            {ticket.public_code}
          </span>
          <Link
            href={`/my-tickets/${ticket.id}`}
            className="text-sm font-semibold text-blue-700 hover:text-blue-900"
          >
            Abrir ingresso
          </Link>
        </div>
      </div>
    </article>
  );
}
