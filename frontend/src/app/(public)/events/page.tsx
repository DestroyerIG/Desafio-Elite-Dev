import type { Metadata } from "next";

import { EventList } from "@/components/events/event-list";

export const metadata: Metadata = {
  title: "Eventos | Elite Events",
};

export default function EventsPage() {
  return (
    <main className="mx-auto max-w-6xl px-5 py-12 sm:px-8 sm:py-16">
      <div className="mb-8 max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Agenda</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">
          Eventos publicados
        </h1>
        <p className="mt-3 text-slate-600">
          Dados armazenados na plataforma e atualizados pelos organizadores.
        </p>
      </div>
      <EventList />
    </main>
  );
}

