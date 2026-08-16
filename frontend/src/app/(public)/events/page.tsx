import type { Metadata } from "next";

import { EventFiltersForm } from "@/components/events/event-filters";
import { EventList } from "@/components/events/event-list";
import type { EventFilters } from "@/services/events";

export const metadata: Metadata = {
  title: "Eventos | Elite Events",
};

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

function validDate(value: string | undefined) {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return undefined;
  const date = new Date(`${value}T00:00:00.000Z`);
  return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === value
    ? value
    : undefined;
}

export default async function EventsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const filters: EventFilters = {
    query: firstValue(params.q)?.trim().slice(0, 100) || undefined,
    dateFrom: validDate(firstValue(params.date_from)),
    dateTo: validDate(firstValue(params.date_to)),
    availableOnly: firstValue(params.available_only) === "true",
  };
  const filterKey = JSON.stringify(filters);

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
      <EventFiltersForm key={filterKey} filters={filters} />
      <EventList filters={filters} />
    </main>
  );
}
