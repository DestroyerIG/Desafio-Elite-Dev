"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/services/api";
import {
  getSeatMap,
  holdSeats,
  seatMapStreamUrl,
} from "@/services/seats";
import type { Seat, SeatStatus } from "@/types/api";
import { formatCurrency } from "@/utils/format";


const seatStatusLabels: Record<SeatStatus, string> = {
  AVAILABLE: "Disponível",
  HELD: "Reservado temporariamente",
  SOLD: "Vendido",
};

const seatStatusSymbols: Record<SeatStatus, string> = {
  AVAILABLE: "",
  HELD: "◷",
  SOLD: "×",
};

export function SeatMapPicker({
  eventId,
  eventTitle,
  ticketPrice,
}: {
  eventId: string;
  eventTitle: string;
  ticketPrice: string;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [liveStatus, setLiveStatus] = useState<"connecting" | "online" | "fallback">(
    "connecting",
  );

  const seatMapQuery = useQuery({
    queryKey: ["seat-map", eventId],
    queryFn: () => getSeatMap(eventId),
    refetchInterval: 15_000,
    retry: 1,
  });

  useEffect(() => {
    let stopped = false;
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let attempts = 0;

    function connect() {
      if (stopped) return;
      setLiveStatus("connecting");
      socket = new WebSocket(seatMapStreamUrl(eventId));
      socket.onopen = () => {
        attempts = 0;
        setLiveStatus("online");
      };
      socket.onmessage = (message) => {
        try {
          const data = JSON.parse(message.data) as {
            type?: string;
            version?: number;
          };
          if (data.type === "seat_map_changed") {
            void queryClient.invalidateQueries({
              queryKey: ["seat-map", eventId],
            });
            void queryClient.invalidateQueries({ queryKey: ["events"] });
          }
        } catch {
          // O polling periódico recupera qualquer mensagem inválida ou perdida.
        }
      };
      socket.onclose = () => {
        if (stopped) return;
        setLiveStatus("fallback");
        attempts += 1;
        const delay = Math.min(1_000 * 2 ** (attempts - 1), 15_000);
        reconnectTimer = setTimeout(connect, delay);
      };
      socket.onerror = () => socket?.close();
    }

    connect();
    return () => {
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [eventId, queryClient]);

  const availableSelectedIds = useMemo(() => {
    if (!seatMapQuery.data) return [];
    const available = new Set(
      seatMapQuery.data.sections.flatMap((section) =>
        section.seats
          .filter((seat) => seat.status === "AVAILABLE")
          .map((seat) => seat.id),
      ),
    );
    return selectedIds.filter((seatId) => available.has(seatId));
  }, [seatMapQuery.data, selectedIds]);

  const holdMutation = useMutation({
    mutationFn: () => holdSeats(eventId, availableSelectedIds),
    onSuccess: async (reservation) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["seat-map", eventId] }),
        queryClient.invalidateQueries({ queryKey: ["events"] }),
        queryClient.invalidateQueries({ queryKey: ["reservations"] }),
      ]);
      router.push(`/checkout/${eventId}?reservation=${reservation.id}`);
    },
    onError: async () => {
      await queryClient.invalidateQueries({ queryKey: ["seat-map", eventId] });
    },
  });

  function toggleSeat(seat: Seat) {
    if (seat.status !== "AVAILABLE") return;
    setSelectionError(null);
    setSelectedIds((current) => {
      if (current.includes(seat.id)) {
        return current.filter((seatId) => seatId !== seat.id);
      }
      if (current.length >= 10) {
        setSelectionError("Selecione no máximo 10 assentos por reserva.");
        return current;
      }
      return [...current, seat.id];
    });
  }

  function submitHold() {
    setSelectionError(null);
    if (!user) {
      router.push(
        `/login?next=${encodeURIComponent(`/events/${eventId}/seats`)}`,
      );
      return;
    }
    if (user.role !== "CUSTOMER") {
      setSelectionError("Entre com uma conta de cliente para reservar assentos.");
      return;
    }
    if (!availableSelectedIds.length) {
      setSelectionError("Selecione pelo menos um assento disponível.");
      return;
    }
    holdMutation.mutate();
  }

  if (seatMapQuery.isLoading) {
    return <LoadingState label="Carregando mapa de assentos..." />;
  }
  if (seatMapQuery.error || !seatMapQuery.data) {
    return (
      <ErrorMessage
        message={
          seatMapQuery.error instanceof ApiError
            ? seatMapQuery.error.message
            : "Não foi possível carregar o mapa de assentos."
        }
      />
    );
  }

  const seatMap = seatMapQuery.data;
  const total = Number(ticketPrice) * availableSelectedIds.length;
  const mutationError =
    holdMutation.error instanceof ApiError
      ? holdMutation.error.message
      : holdMutation.error
        ? "Não foi possível reservar os assentos."
        : null;

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <section className="min-w-0 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
              Escolha seus lugares
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">
              {eventTitle}
            </h1>
          </div>
          <p
            className="flex items-center gap-2 text-xs font-medium text-slate-600"
            role="status"
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                liveStatus === "online" ? "bg-emerald-500" : "bg-amber-500"
              }`}
            />
            {liveStatus === "online"
              ? "Atualização em tempo real"
              : liveStatus === "connecting"
                ? "Conectando ao mapa..."
                : "Reconectando · atualização automática ativa"}
          </p>
        </div>

        <div className="mx-auto mt-8 max-w-2xl">
          <div className="rounded-t-[50%] border border-blue-200 bg-blue-50 px-6 py-3 text-center text-xs font-bold uppercase tracking-[0.3em] text-blue-800 shadow-sm">
            {seatMap.stage_label}
          </div>
          <p className="mt-2 text-center text-xs text-slate-500">
            Frente do espaço
          </p>
        </div>

        <div className="mt-10 space-y-10 overflow-x-auto pb-3">
          {seatMap.sections.map((section) => (
            <section key={section.id} aria-labelledby={`section-${section.id}`}>
              <h2
                id={`section-${section.id}`}
                className="sticky left-0 text-center text-sm font-semibold text-slate-800"
              >
                {section.name}
              </h2>
              <div className="mt-4 min-w-max space-y-2">
                {Array.from({ length: section.row_count }, (_, rowIndex) => {
                  const rowSeats = section.seats.slice(
                    rowIndex * section.seats_per_row,
                    (rowIndex + 1) * section.seats_per_row,
                  );
                  const rowLabel = rowSeats[0]?.row_label ?? "";
                  return (
                    <div
                      key={`${section.id}-${rowLabel}`}
                      className="flex items-center justify-center gap-2"
                    >
                      <span className="w-6 text-right text-xs font-semibold text-slate-500">
                        {rowLabel}
                      </span>
                      {rowSeats.map((seat) => {
                        const isSelected = availableSelectedIds.includes(seat.id);
                        return (
                          <button
                            key={seat.id}
                            type="button"
                            disabled={seat.status !== "AVAILABLE"}
                            aria-pressed={isSelected}
                            aria-label={`${section.name}, fileira ${seat.row_label}, assento ${seat.number}: ${
                              isSelected ? "Selecionado" : seatStatusLabels[seat.status]
                            }`}
                            title={`${section.name} · ${seat.label} · ${
                              isSelected ? "Selecionado" : seatStatusLabels[seat.status]
                            }`}
                            onClick={() => toggleSeat(seat)}
                            className={`flex h-9 w-9 items-center justify-center rounded-t-lg rounded-b-sm border text-xs font-bold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 ${
                              isSelected
                                ? "border-blue-700 bg-blue-700 text-white"
                                : seat.status === "AVAILABLE"
                                  ? "border-emerald-500 bg-white text-emerald-800 hover:bg-emerald-50"
                                  : seat.status === "HELD"
                                    ? "cursor-not-allowed border-amber-300 bg-amber-100 text-amber-800"
                                    : "cursor-not-allowed border-slate-300 bg-slate-200 text-slate-600"
                            }`}
                          >
                            {isSelected
                              ? "✓"
                              : seatStatusSymbols[seat.status] || seat.number}
                          </button>
                        );
                      })}
                      <span className="w-6 text-xs font-semibold text-slate-500">
                        {rowLabel}
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>
          ))}
        </div>

        <ul className="mt-8 flex flex-wrap justify-center gap-x-5 gap-y-3 border-t border-slate-100 pt-6 text-xs text-slate-600">
          <li><span className="mr-2 inline-block h-3 w-3 rounded-sm border border-emerald-500 bg-white" />Disponível</li>
          <li><span className="mr-2 inline-block h-3 w-3 rounded-sm bg-blue-700" />Selecionado</li>
          <li><span className="mr-2 inline-block h-3 w-3 rounded-sm bg-amber-200" />Reservado</li>
          <li><span className="mr-2 inline-block h-3 w-3 rounded-sm bg-slate-300" />Vendido</li>
        </ul>
      </section>

      <aside className="self-start rounded-xl border border-slate-200 bg-white p-6 shadow-sm lg:sticky lg:top-6">
        <h2 className="font-semibold text-slate-950">Resumo da seleção</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Após confirmar, os lugares ficarão separados por 10 minutos.
        </p>
        <dl className="mt-5 space-y-3 border-y border-slate-100 py-5 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Assentos</dt>
            <dd className="font-semibold text-slate-900">
              {availableSelectedIds.length}/10
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Preço unitário</dt>
            <dd className="font-medium text-slate-900">
              {formatCurrency(ticketPrice)}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="font-medium text-slate-700">Total</dt>
            <dd className="text-lg font-semibold text-slate-950">
              {formatCurrency(String(total))}
            </dd>
          </div>
        </dl>
        {selectionError && <ErrorMessage message={selectionError} className="mt-4" />}
        {mutationError && <ErrorMessage message={mutationError} className="mt-4" />}
        <Button
          type="button"
          className="mt-5 w-full"
          disabled={!availableSelectedIds.length || holdMutation.isPending}
          onClick={submitHold}
        >
          {holdMutation.isPending
            ? "Reservando..."
            : `Reservar ${availableSelectedIds.length || ""} assento(s)`}
        </Button>
      </aside>
    </div>
  );
}
