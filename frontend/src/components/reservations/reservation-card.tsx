import Link from "next/link";

import { EventArtwork } from "@/components/events/event-artwork";
import { Button, buttonVariants } from "@/components/ui/button";
import type { CustomerReservation, ReservationStatus } from "@/types/api";
import { cn } from "@/utils/cn";
import { formatCurrency, formatDate } from "@/utils/format";


const statusLabels: Record<ReservationStatus, string> = {
  PENDING: "Aguardando pagamento",
  PAID: "Pago",
  CANCELLED: "Cancelado",
  EXPIRED: "Expirado",
};

export function ReservationCard({
  reservation,
  isCancelling,
  onCancel,
}: {
  reservation: CustomerReservation;
  isCancelling: boolean;
  onCancel: (reservationId: string) => void;
}) {
  const isPending = reservation.status === "PENDING";
  const isPaid = reservation.status === "PAID";

  return (
    <article className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="grid sm:grid-cols-[12rem_1fr]">
        <EventArtwork
          imageUrl={reservation.event.image_url}
          title={reservation.event.title}
          className="h-44 sm:h-full"
        />
        <div className="p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
              {formatDate(reservation.event.event_date)}
            </p>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
              {statusLabels[reservation.status]}
            </span>
          </div>
          <h2 className="mt-3 text-xl font-semibold text-slate-950">
            {reservation.event.title}
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {reservation.event.venue_name} · {reservation.event.venue_address}
          </p>
          <dl className="mt-5 flex flex-wrap gap-x-8 gap-y-3 border-y border-slate-100 py-4 text-sm">
            <div>
              <dt className="text-slate-500">Quantidade</dt>
              <dd className="mt-1 font-semibold text-slate-950">
                {reservation.quantity}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Total reservado</dt>
              <dd className="mt-1 font-semibold text-slate-950">
                {formatCurrency(reservation.total_amount)}
              </dd>
            </div>
          </dl>
          <div className="mt-5 flex flex-wrap gap-3">
            {isPending && (
              <>
                <Link
                  href={`/checkout/${reservation.event_id}?reservation=${reservation.id}`}
                  className={cn(buttonVariants())}
                >
                  Continuar pagamento
                </Link>
                <Button
                  type="button"
                  variant="danger"
                  disabled={isCancelling}
                  onClick={() => onCancel(reservation.id)}
                >
                  {isCancelling ? "Cancelando..." : "Cancelar reserva"}
                </Button>
              </>
            )}
            {isPaid && (
              <Link href="/my-tickets" className={cn(buttonVariants())}>
                Ver ingressos
              </Link>
            )}
            <Link
              href={`/events/${reservation.event_id}`}
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Ver evento
            </Link>
          </div>
        </div>
      </div>
    </article>
  );
}
