"use client";

import { useState, type FormEvent } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { QrScanner } from "@/components/gate/qr-scanner";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { gateValidationSchema } from "@/schemas/gate";
import { ApiError } from "@/services/api";
import { listEvents } from "@/services/events";
import { validateGateTicket } from "@/services/gate";
import type { ValidationResult } from "@/types/api";
import { cn } from "@/utils/cn";


const resultStyles: Record<ValidationResult, string> = {
  VALID: "border-emerald-300 bg-emerald-50 text-emerald-950",
  INVALID: "border-red-300 bg-red-50 text-red-950",
  ALREADY_USED: "border-amber-300 bg-amber-50 text-amber-950",
  WRONG_EVENT: "border-orange-300 bg-orange-50 text-orange-950",
};

const resultLabels: Record<ValidationResult, string> = {
  VALID: "Entrada liberada",
  INVALID: "Ingresso inválido",
  ALREADY_USED: "Ingresso já utilizado",
  WRONG_EVENT: "Evento incorreto",
};

// A linha superior do painel resume a decisão em uma palavra, legível de longe por
// quem opera a portaria. Antes exibia o enum cru da API (`ALREADY_USED`).
const resultEyebrows: Record<ValidationResult, string> = {
  VALID: "Liberado",
  INVALID: "Recusado",
  ALREADY_USED: "Recusado",
  WRONG_EVENT: "Recusado",
};

export function GateConsole() {
  const [eventId, setEventId] = useState("");
  const [credential, setCredential] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const eventsQuery = useQuery({
    queryKey: ["events", "gate"],
    queryFn: () => listEvents(),
  });
  const validationMutation = useMutation({
    mutationFn: ({
      selectedEventId,
      value,
    }: {
      selectedEventId: string;
      value: string;
    }) => validateGateTicket(selectedEventId, value),
    onSuccess: () => setCredential(""),
  });

  if (eventsQuery.isLoading) {
    return <LoadingState label="Carregando eventos da portaria..." />;
  }
  if (eventsQuery.error) {
    return (
      <ErrorMessage
        message={
          eventsQuery.error instanceof ApiError
            ? eventsQuery.error.message
            : "Não foi possível carregar os eventos."
        }
      />
    );
  }
  if (!eventsQuery.data?.length) {
    return (
      <EmptyState
        title="Nenhum evento disponível"
        description="A portaria poderá validar ingressos quando houver um evento publicado."
      />
    );
  }

  const selectedEventId = eventId || eventsQuery.data[0].id;
  const selectedEvent = eventsQuery.data.find(
    (event) => event.id === selectedEventId,
  );

  function submitCredential(value: string) {
    setFormError(null);
    validationMutation.reset();
    const result = gateValidationSchema.safeParse({
      eventId: selectedEventId,
      credential: value,
    });
    if (!result.success) {
      setFormError(result.error.issues[0]?.message ?? "Revise os dados.");
      return;
    }
    validationMutation.mutate({
      selectedEventId: result.data.eventId,
      value: result.data.credential,
    });
  }

  function handleManualValidation(formEvent: FormEvent<HTMLFormElement>) {
    formEvent.preventDefault();
    submitCredential(credential);
  }

  return (
    <div>
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <Label htmlFor="gate-event">Evento desta entrada</Label>
        <select
          id="gate-event"
          value={selectedEventId}
          onChange={(inputEvent) => {
            setEventId(inputEvent.target.value);
            setFormError(null);
            validationMutation.reset();
          }}
          disabled={validationMutation.isPending}
          className="mt-2 flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-950 outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-100 disabled:opacity-50"
        >
          {eventsQuery.data.map((event) => (
            <option key={event.id} value={event.id}>
              {event.title}
            </option>
          ))}
        </select>
        {selectedEvent && (
          <p className="mt-2 text-sm text-slate-600">
            {selectedEvent.venue_name} · {selectedEvent.venue_address}
          </p>
        )}
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
        <QrScanner
          disabled={validationMutation.isPending}
          onScan={submitCredential}
        />

        <form
          onSubmit={handleManualValidation}
          className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <h2 className="font-semibold text-slate-950">Código manual</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            Digite o código no formato ELT-XXXX-XXXX quando a câmera não estiver
            disponível.
          </p>
          <div className="mt-5 space-y-2">
            <Label htmlFor="ticket-credential">Código do ingresso</Label>
            <Input
              id="ticket-credential"
              value={credential}
              placeholder="ELT-8D72-A93C"
              autoComplete="off"
              onChange={(inputEvent) => setCredential(inputEvent.target.value)}
              disabled={validationMutation.isPending}
            />
          </div>
          <Button
            type="submit"
            className="mt-4 w-full"
            disabled={validationMutation.isPending}
          >
            {validationMutation.isPending ? "Validando..." : "Validar ingresso"}
          </Button>
        </form>
      </div>

      {formError && <ErrorMessage message={formError} className="mt-6" />}
      {validationMutation.error && (
        <ErrorMessage
          className="mt-6"
          message={
            validationMutation.error instanceof ApiError
              ? validationMutation.error.message
              : "Não foi possível validar o ingresso."
          }
        />
      )}
      {validationMutation.data && (
        <section
          className={cn(
            "mt-6 rounded-xl border-2 p-6 shadow-sm",
            resultStyles[validationMutation.data.result],
          )}
          aria-live="assertive"
        >
          <p className="text-sm font-semibold uppercase tracking-wide">
            {resultEyebrows[validationMutation.data.result]}
          </p>
          <h2 className="mt-2 text-2xl font-semibold">
            {resultLabels[validationMutation.data.result]}
          </h2>
          <p className="mt-2">{validationMutation.data.message}</p>
          {validationMutation.data.public_code && (
            <p className="mt-4 font-mono text-sm font-semibold">
              {validationMutation.data.public_code}
            </p>
          )}
        </section>
      )}
    </div>
  );
}
