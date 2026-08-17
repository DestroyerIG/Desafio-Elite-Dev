"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { EventArtwork } from "@/components/events/event-artwork";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { publishEventSchema } from "@/schemas/events";
import { ApiError } from "@/services/api";
import { publishEvent, searchCatalog } from "@/services/events";
import type { CatalogEvent } from "@/types/api";
import { formatDate } from "@/utils/format";

export function TicketmasterEventImport() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [searchInput, setSearchInput] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedEvent, setSelectedEvent] = useState<CatalogEvent | null>(null);
  const [capacity, setCapacity] = useState("100");
  const [ticketPrice, setTicketPrice] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const catalogQuery = useQuery({
    queryKey: ["catalog", searchTerm],
    queryFn: () => searchCatalog(searchTerm),
    enabled: searchTerm.length >= 2,
    retry: false,
  });
  const publishMutation = useMutation({
    mutationFn: publishEvent,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["events"] });
      router.push("/organizer/events");
    },
  });

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = searchInput.trim();
    setSelectedEvent(null);
    setFormError(null);
    if (query.length < 2) {
      setFormError("Digite pelo menos dois caracteres para pesquisar.");
      return;
    }
    setSearchTerm(query);
  }

  function handlePublish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    if (!selectedEvent) {
      setFormError("Selecione um evento do catálogo.");
      return;
    }

    const result = publishEventSchema.safeParse({ capacity, ticketPrice });
    if (!result.success) {
      setFormError(result.error.issues[0]?.message ?? "Revise capacidade e preço.");
      return;
    }

    publishMutation.mutate({
      external_id: selectedEvent.external_id,
      capacity: result.data.capacity,
      ticket_price: result.data.ticketPrice.toFixed(2),
    });
  }

  const requestError = publishMutation.error ?? catalogQuery.error;

  return (
    <section className="mt-8" aria-labelledby="ticketmaster-title">
      <div className="max-w-2xl">
        <h2 id="ticketmaster-title" className="text-xl font-semibold text-slate-950">
          Importar da Ticketmaster
        </h2>
        <p className="mt-2 leading-6 text-slate-600">
          Pesquise o catálogo e copie os dados essenciais para a plataforma.
        </p>
      </div>

      <form onSubmit={handleSearch} className="mt-6 flex max-w-2xl gap-3">
        <div className="flex-1">
          <Label htmlFor="catalog-query" className="sr-only">
            Nome do evento
          </Label>
          <Input
            id="catalog-query"
            placeholder="Ex.: festival, artista ou espetáculo"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
        </div>
        <Button type="submit">Pesquisar</Button>
      </form>

      {formError && <ErrorMessage message={formError} className="mt-5 max-w-2xl" />}
      {requestError && (
        <ErrorMessage
          className="mt-5 max-w-2xl"
          message={
            requestError instanceof ApiError
              ? requestError.message
              : "Não foi possível concluir a operação."
          }
        />
      )}

      {catalogQuery.isFetching && <LoadingState label="Consultando a Ticketmaster..." />}

      {catalogQuery.data?.length === 0 && (
        <div className="mt-8">
          <EmptyState
            title="Nenhum resultado encontrado"
            description="Tente pesquisar pelo nome completo do artista, evento ou espetáculo."
          />
        </div>
      )}

      {Boolean(catalogQuery.data?.length) && (
        <section className="mt-8" aria-labelledby="catalog-results">
          <h3 id="catalog-results" className="text-lg font-semibold text-slate-950">
            Resultados do catálogo
          </h3>
          <div className="mt-4 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {catalogQuery.data?.map((event) => {
              const isSelected = selectedEvent?.external_id === event.external_id;
              return (
                <article
                  key={event.external_id}
                  className={`overflow-hidden rounded-lg border bg-white shadow-sm ${
                    isSelected ? "border-blue-600 ring-2 ring-blue-100" : "border-slate-200"
                  }`}
                >
                  <EventArtwork imageUrl={event.image_url} title={event.title} />
                  <div className="p-5">
                    <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
                      {formatDate(event.event_date)}
                    </p>
                    <h4 className="mt-2 font-semibold leading-6 text-slate-950">{event.title}</h4>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{event.venue_name}</p>
                    <Button
                      type="button"
                      variant={isSelected ? "secondary" : "outline"}
                      className="mt-4 w-full"
                      onClick={() => setSelectedEvent(event)}
                    >
                      {isSelected ? "Selecionado" : "Selecionar"}
                    </Button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}

      {selectedEvent && (
        <form
          onSubmit={handlePublish}
          className="mt-10 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 pb-5">
            <div>
              <p className="text-sm font-medium text-blue-700">Evento selecionado</p>
              <h3 className="mt-1 text-xl font-semibold text-slate-950">{selectedEvent.title}</h3>
              <p className="mt-1 text-sm text-slate-600">{selectedEvent.venue_name}</p>
            </div>
            <Button type="button" variant="ghost" size="sm" onClick={() => setSelectedEvent(null)}>
              Trocar evento
            </Button>
          </div>

          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="capacity">Capacidade</Label>
              <Input
                id="capacity"
                type="number"
                min="1"
                step="1"
                value={capacity}
                onChange={(event) => setCapacity(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ticket-price">Preço do ingresso (R$)</Label>
              <Input
                id="ticket-price"
                type="number"
                min="0"
                step="0.01"
                placeholder="0,00"
                value={ticketPrice}
                onChange={(event) => setTicketPrice(event.target.value)}
              />
            </div>
          </div>
          <div className="mt-6 flex justify-end">
            <Button type="submit" disabled={publishMutation.isPending}>
              {publishMutation.isPending ? "Publicando..." : "Publicar evento"}
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}
