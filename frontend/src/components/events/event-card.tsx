import Link from "next/link";

import { EventArtwork } from "@/components/events/event-artwork";
import type { Event } from "@/types/api";
import { formatCurrency, formatDate } from "@/utils/format";

export function EventCard({ event }: { event: Event }) {
  return (
    <article className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition-shadow hover:shadow-md">
      <EventArtwork imageUrl={event.image_url} title={event.title} />
      <div className="p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
          {formatDate(event.event_date)}
        </p>
        <h2 className="mt-2 text-lg font-semibold leading-6 text-slate-950">
          <Link href={`/events/${event.id}`} className="hover:text-blue-700">
            {event.title}
          </Link>
        </h2>
        <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">
          {event.venue_name} · {event.venue_address}
        </p>
        <div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4">
          <span className="text-sm text-slate-600">
            {event.available_tickets} disponíveis
          </span>
          <span className="font-semibold text-slate-950">
            {formatCurrency(event.ticket_price)}
          </span>
        </div>
      </div>
    </article>
  );
}

