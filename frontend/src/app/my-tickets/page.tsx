import type { Metadata } from "next";

import { TicketList } from "@/components/tickets/ticket-list";

export const metadata: Metadata = {
  title: "Meus ingressos | Elite Events",
};

export default function MyTicketsPage() {
  return (
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
        Área do cliente
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
        Meus ingressos
      </h1>
      <p className="mt-3 max-w-2xl leading-7 text-slate-600">
        Consulte os ingressos emitidos e abra o QR individual de cada entrada.
      </p>
      <div className="mt-8">
        <TicketList />
      </div>
    </main>
  );
}
