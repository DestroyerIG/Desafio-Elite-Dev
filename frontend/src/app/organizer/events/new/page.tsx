"use client";

import { useState } from "react";

import { CustomEventForm } from "@/components/events/custom-event-form";
import { TicketmasterEventImport } from "@/components/events/ticketmaster-event-import";
import { Button } from "@/components/ui/button";

type CreationMode = "custom" | "ticketmaster";

export default function NewOrganizerEventPage() {
  const [mode, setMode] = useState<CreationMode>("custom");

  return (
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Organizador</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
          Publicar evento
        </h1>
        <p className="mt-3 leading-7 text-slate-600">
          Crie um evento com seus próprios dados ou importe as informações da Ticketmaster.
        </p>
      </div>

      <div
        className="mt-7 inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1"
        role="group"
        aria-label="Forma de publicação do evento"
      >
        <Button
          type="button"
          size="sm"
          variant={mode === "custom" ? "default" : "ghost"}
          aria-pressed={mode === "custom"}
          onClick={() => setMode("custom")}
        >
          Criar meu evento
        </Button>
        <Button
          type="button"
          size="sm"
          variant={mode === "ticketmaster" ? "default" : "ghost"}
          aria-pressed={mode === "ticketmaster"}
          onClick={() => setMode("ticketmaster")}
        >
          Importar da Ticketmaster
        </Button>
      </div>

      <div>
        {mode === "custom" ? <CustomEventForm /> : <TicketmasterEventImport />}
      </div>
    </main>
  );
}
