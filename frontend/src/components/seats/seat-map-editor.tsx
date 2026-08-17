"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button, buttonVariants } from "@/components/ui/button";
import { ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/services/api";
import { listOrganizerEvents } from "@/services/events";
import {
  configureSeatMap,
  getOrganizerSeatMap,
  removeSeatMap,
  type SeatSectionInput,
} from "@/services/seats";
import type { Event, SeatMap } from "@/types/api";
import { cn } from "@/utils/cn";


interface EditableSection {
  key: string;
  name: string;
  rowCount: string;
  seatsPerRow: string;
}

function defaultSections(capacity: number): EditableSection[] {
  const sections: EditableSection[] = [];
  let remaining = capacity;
  let index = 1;
  while (remaining > 0) {
    const count = Math.min(remaining, 100);
    sections.push({
      key: `default-${index}`,
      name: sections.length ? `Setor ${index}` : "Setor principal",
      rowCount: "1",
      seatsPerRow: String(count),
    });
    remaining -= count;
    index += 1;
  }
  return sections;
}

function sectionsFromMap(seatMap: SeatMap): EditableSection[] {
  return seatMap.sections.map((section) => ({
    key: section.id,
    name: section.name,
    rowCount: String(section.row_count),
    seatsPerRow: String(section.seats_per_row),
  }));
}

function SeatMapForm({ event, seatMap }: { event: Event; seatMap?: SeatMap }) {
  const queryClient = useQueryClient();
  const [stageLabel, setStageLabel] = useState(seatMap?.stage_label ?? "Palco");
  const [sections, setSections] = useState<EditableSection[]>(
    seatMap ? sectionsFromMap(seatMap) : defaultSections(event.capacity),
  );
  const [formError, setFormError] = useState<string | null>(null);

  const saveMutation = useMutation({
    mutationFn: (data: {
      stage_label: string;
      sections: SeatSectionInput[];
    }) => configureSeatMap(event.id, data),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["seat-map", event.id] }),
        queryClient.invalidateQueries({ queryKey: ["events"] }),
      ]);
    },
  });
  const removeMutation = useMutation({
    mutationFn: () => removeSeatMap(event.id),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["seat-map", event.id] }),
        queryClient.invalidateQueries({ queryKey: ["events"] }),
      ]);
      queryClient.removeQueries({ queryKey: ["seat-map", event.id] });
    },
  });

  const totalSeats = sections.reduce((total, section) => {
    const rows = Number(section.rowCount);
    const seats = Number(section.seatsPerRow);
    return total + (Number.isInteger(rows) && Number.isInteger(seats) ? rows * seats : 0);
  }, 0);

  function updateSection(
    key: string,
    field: keyof Omit<EditableSection, "key">,
    value: string,
  ) {
    setSections((current) =>
      current.map((section) =>
        section.key === key ? { ...section, [field]: value } : section,
      ),
    );
    setFormError(null);
  }

  function addSection() {
    if (sections.length >= 20) {
      setFormError("O mapa aceita no máximo 20 setores.");
      return;
    }
    setSections((current) => [
      ...current,
      {
        key: `new-${current.length + 1}-${Date.now()}`,
        name: `Setor ${current.length + 1}`,
        rowCount: "1",
        seatsPerRow: "1",
      },
    ]);
  }

  function submit(eventSubmit: FormEvent<HTMLFormElement>) {
    eventSubmit.preventDefault();
    setFormError(null);
    const normalizedStage = stageLabel.trim();
    if (!normalizedStage) {
      setFormError("Informe o nome do palco ou área principal.");
      return;
    }
    if (!sections.length) {
      setFormError("Adicione pelo menos um setor.");
      return;
    }
    const normalizedSections: SeatSectionInput[] = [];
    for (const section of sections) {
      const rowCount = Number(section.rowCount);
      const seatsPerRow = Number(section.seatsPerRow);
      if (!section.name.trim()) {
        setFormError("Todos os setores precisam de um nome.");
        return;
      }
      if (!Number.isInteger(rowCount) || rowCount < 1 || rowCount > 52) {
        setFormError("Cada setor deve possuir entre 1 e 52 fileiras.");
        return;
      }
      if (
        !Number.isInteger(seatsPerRow) ||
        seatsPerRow < 1 ||
        seatsPerRow > 100
      ) {
        setFormError("Cada fileira deve possuir entre 1 e 100 assentos.");
        return;
      }
      normalizedSections.push({
        name: section.name.trim(),
        row_count: rowCount,
        seats_per_row: seatsPerRow,
      });
    }
    if (new Set(normalizedSections.map((section) => section.name.toLocaleLowerCase())).size !== normalizedSections.length) {
      setFormError("Os nomes dos setores não podem se repetir.");
      return;
    }
    if (totalSeats !== event.capacity) {
      setFormError(
        `O mapa precisa totalizar exatamente ${event.capacity} assentos.`,
      );
      return;
    }
    saveMutation.mutate({
      stage_label: normalizedStage,
      sections: normalizedSections,
    });
  }

  function confirmRemoval() {
    if (
      window.confirm(
        "Remover o mapa e voltar o evento para ingressos por quantidade?",
      )
    ) {
      removeMutation.mutate();
    }
  }

  const requestError = saveMutation.error ?? removeMutation.error;
  return (
    <form onSubmit={submit} className="mt-8 space-y-7">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid gap-5 sm:grid-cols-[1fr_auto] sm:items-end">
          <div className="space-y-2">
            <Label htmlFor="stage-label">Nome do palco ou área principal</Label>
            <Input
              id="stage-label"
              maxLength={80}
              value={stageLabel}
              onChange={(inputEvent) => setStageLabel(inputEvent.target.value)}
            />
          </div>
          <div
            className={`rounded-lg px-4 py-3 text-sm font-semibold ${
              totalSeats === event.capacity
                ? "bg-emerald-50 text-emerald-800"
                : "bg-amber-50 text-amber-800"
            }`}
            role="status"
          >
            {totalSeats} de {event.capacity} assentos
          </div>
        </div>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Setores</h2>
            <p className="mt-1 text-sm text-slate-600">
              Cada setor será gerado em fileiras identificadas por letras.
            </p>
          </div>
          <Button type="button" variant="outline" onClick={addSection}>
            Adicionar setor
          </Button>
        </div>

        <div className="mt-6 space-y-4">
          {sections.map((section, index) => (
            <div
              key={section.key}
              className="grid gap-4 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:grid-cols-[1fr_9rem_9rem_auto] sm:items-end"
            >
              <div className="space-y-2">
                <Label htmlFor={`section-name-${section.key}`}>Nome</Label>
                <Input
                  id={`section-name-${section.key}`}
                  maxLength={80}
                  value={section.name}
                  onChange={(inputEvent) =>
                    updateSection(section.key, "name", inputEvent.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`section-rows-${section.key}`}>Fileiras</Label>
                <Input
                  id={`section-rows-${section.key}`}
                  type="number"
                  min="1"
                  max="52"
                  value={section.rowCount}
                  onChange={(inputEvent) =>
                    updateSection(section.key, "rowCount", inputEvent.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`section-seats-${section.key}`}>Por fileira</Label>
                <Input
                  id={`section-seats-${section.key}`}
                  type="number"
                  min="1"
                  max="100"
                  value={section.seatsPerRow}
                  onChange={(inputEvent) =>
                    updateSection(
                      section.key,
                      "seatsPerRow",
                      inputEvent.target.value,
                    )
                  }
                />
              </div>
              <Button
                type="button"
                variant="ghost"
                disabled={sections.length === 1}
                onClick={() =>
                  setSections((current) =>
                    current.filter((item) => item.key !== section.key),
                  )
                }
              >
                Remover {index + 1}
              </Button>
            </div>
          ))}
        </div>
      </section>

      <div className="rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm leading-6 text-blue-900">
        Depois da primeira reserva, a estrutura do mapa ficará bloqueada para
        preservar os lugares vendidos e o histórico dos ingressos.
      </div>
      {formError && <ErrorMessage message={formError} />}
      {requestError && (
        <ErrorMessage
          message={
            requestError instanceof ApiError
              ? requestError.message
              : "Não foi possível salvar o mapa de assentos."
          }
        />
      )}
      {saveMutation.isSuccess && (
        <p className="rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-800" role="status">
          Mapa salvo. O evento agora utiliza assentos marcados.
        </p>
      )}
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="submit"
          disabled={totalSeats !== event.capacity || saveMutation.isPending}
        >
          {saveMutation.isPending ? "Salvando..." : "Salvar mapa"}
        </Button>
        {(seatMap || saveMutation.data) && (
          <>
            <Link
              href={`/events/${event.id}/seats`}
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Visualizar mapa
            </Link>
            <Button
              type="button"
              variant="danger"
              disabled={removeMutation.isPending}
              onClick={confirmRemoval}
            >
              {removeMutation.isPending ? "Removendo..." : "Remover mapa"}
            </Button>
          </>
        )}
      </div>
    </form>
  );
}

export function SeatMapEditor({ eventId }: { eventId: string }) {
  const eventsQuery = useQuery({
    queryKey: ["events", "organizer"],
    queryFn: listOrganizerEvents,
  });
  const event = eventsQuery.data?.find((item) => item.id === eventId);
  const seatMapQuery = useQuery({
    queryKey: ["seat-map", eventId],
    queryFn: () => getOrganizerSeatMap(eventId),
    enabled: event?.seating_mode === "ASSIGNED",
    retry: false,
  });

  if (eventsQuery.isLoading || (event?.seating_mode === "ASSIGNED" && seatMapQuery.isLoading)) {
    return <LoadingState label="Carregando configuração do mapa..." />;
  }
  if (eventsQuery.error) {
    return (
      <ErrorMessage
        message={
          eventsQuery.error instanceof ApiError
            ? eventsQuery.error.message
            : "Não foi possível carregar o evento."
        }
      />
    );
  }
  if (!event) return <ErrorMessage message="Evento não encontrado." />;
  if (event.capacity > 2_000) {
    return (
      <ErrorMessage message="Mapas de assentos aceitam até 2.000 lugares. Reduza a capacidade do evento antes de configurar o mapa." />
    );
  }
  if (seatMapQuery.error && event.seating_mode === "ASSIGNED") {
    return (
      <ErrorMessage
        message={
          seatMapQuery.error instanceof ApiError
            ? seatMapQuery.error.message
            : "Não foi possível carregar o mapa atual."
        }
      />
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-14">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
        Organizador
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
        Mapa de assentos
      </h1>
      <p className="mt-3 max-w-3xl leading-7 text-slate-600">
        Configure os lugares de “{event.title}”. A soma dos setores deve ser
        igual à capacidade publicada.
      </p>
      <SeatMapForm
        key={seatMapQuery.data?.version ?? "new"}
        event={event}
        seatMap={seatMapQuery.data}
      />
    </main>
  );
}
