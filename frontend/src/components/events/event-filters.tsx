"use client";

import { type FormEvent, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { EventFilters } from "@/services/events";

export function EventFiltersForm({ filters }: { filters: EventFilters }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [query, setQuery] = useState(filters.query ?? "");
  const [dateFrom, setDateFrom] = useState(filters.dateFrom ?? "");
  const [dateTo, setDateTo] = useState(filters.dateTo ?? "");
  const [availableOnly, setAvailableOnly] = useState(
    filters.availableOnly ?? false,
  );

  function navigate(params: URLSearchParams) {
    const queryString = params.toString();
    startTransition(() => {
      router.push(queryString ? `/events?${queryString}` : "/events");
    });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const params = new URLSearchParams();
    const normalizedQuery = query.trim();

    if (normalizedQuery) params.set("q", normalizedQuery);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    if (availableOnly) params.set("available_only", "true");
    navigate(params);
  }

  function clearFilters() {
    setQuery("");
    setDateFrom("");
    setDateTo("");
    setAvailableOnly(false);
    navigate(new URLSearchParams());
  }

  return (
    <form
      className="mb-8 rounded-xl border border-slate-200 bg-slate-50 p-5"
      onSubmit={handleSubmit}
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_1fr_1fr]">
        <label className="text-sm font-medium text-slate-800">
          Buscar evento ou local
          <Input
            className="mt-2 bg-white"
            type="search"
            value={query}
            maxLength={100}
            placeholder="Ex.: festival, arena ou São Paulo"
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <label className="text-sm font-medium text-slate-800">
          Data inicial
          <Input
            className="mt-2 bg-white"
            type="date"
            value={dateFrom}
            max={dateTo || undefined}
            onChange={(event) => setDateFrom(event.target.value)}
          />
        </label>
        <label className="text-sm font-medium text-slate-800">
          Data final
          <Input
            className="mt-2 bg-white"
            type="date"
            value={dateTo}
            min={dateFrom || undefined}
            onChange={(event) => setDateTo(event.target.value)}
          />
        </label>
      </div>

      <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <label className="flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-800">
          <input
            className="h-4 w-4 rounded border-slate-300 text-blue-700 focus:ring-blue-600"
            type="checkbox"
            checked={availableOnly}
            onChange={(event) => setAvailableOnly(event.target.checked)}
          />
          Somente eventos com ingressos disponíveis
        </label>

        <div className="flex gap-3">
          <Button
            type="button"
            variant="outline"
            disabled={isPending}
            onClick={clearFilters}
          >
            Limpar
          </Button>
          <Button type="submit" disabled={isPending}>
            {isPending ? "Aplicando..." : "Aplicar filtros"}
          </Button>
        </div>
      </div>
    </form>
  );
}
