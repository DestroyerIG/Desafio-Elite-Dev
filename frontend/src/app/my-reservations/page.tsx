import type { Metadata } from "next";

import { ReservationList } from "@/components/reservations/reservation-list";

export const metadata: Metadata = {
  title: "Minhas reservas | Elite Events",
};

export default function MyReservationsPage() {
  return (
    <main className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
        Área do cliente
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
        Minhas reservas
      </h1>
      <p className="mt-3 max-w-2xl leading-7 text-slate-600">
        Retome pagamentos pendentes, acompanhe compras e cancele reservas que
        não deseja manter.
      </p>
      <div className="mt-8">
        <ReservationList />
      </div>
    </main>
  );
}
