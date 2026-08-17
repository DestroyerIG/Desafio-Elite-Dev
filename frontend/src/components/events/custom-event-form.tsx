"use client";

import Image from "next/image";
import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { ErrorMessage } from "@/components/ui/feedback";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { customEventSchema } from "@/schemas/events";
import { ApiError } from "@/services/api";
import { createOrganizerEvent } from "@/services/events";

export function CustomEventForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [image, setImage] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: createOrganizerEvent,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["events"] });
      router.push("/organizer/events");
    },
  });

  useEffect(
    () => () => {
      if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl);
    },
    [imagePreviewUrl],
  );

  function handleImageChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedImage = event.target.files?.[0] ?? null;
    setImage(selectedImage);
    setImagePreviewUrl(selectedImage ? URL.createObjectURL(selectedImage) : null);
    setFormError(null);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    const rawData = new FormData(event.currentTarget);
    const result = customEventSchema.safeParse({
      title: rawData.get("title"),
      description: rawData.get("description"),
      venueName: rawData.get("venue_name"),
      venueAddress: rawData.get("venue_address"),
      eventDate: rawData.get("event_date"),
      capacity: rawData.get("capacity"),
      ticketPrice: rawData.get("ticket_price"),
      image,
    });

    if (!result.success) {
      setFormError(result.error.issues[0]?.message ?? "Revise os dados do evento.");
      return;
    }

    const payload = new FormData();
    payload.set("title", result.data.title);
    payload.set("venue_name", result.data.venueName);
    payload.set("venue_address", result.data.venueAddress);
    payload.set("event_date", new Date(result.data.eventDate).toISOString());
    payload.set("capacity", String(result.data.capacity));
    payload.set("ticket_price", result.data.ticketPrice.toFixed(2));
    if (result.data.description) payload.set("description", result.data.description);
    if (result.data.image) payload.set("image", result.data.image);

    createMutation.mutate(payload);
  }

  const requestError = createMutation.error;

  return (
    <section className="mt-8" aria-labelledby="custom-event-title">
      <div className="max-w-2xl">
        <h2 id="custom-event-title" className="text-xl font-semibold text-slate-950">
          Dados do seu evento
        </h2>
        <p className="mt-2 leading-6 text-slate-600">
          O evento será publicado imediatamente. Depois, você poderá configurar o mapa de assentos
          em “Meus eventos”.
        </p>
      </div>

      {(formError || requestError) && (
        <ErrorMessage
          className="mt-5 max-w-3xl"
          message={
            formError ??
            (requestError instanceof ApiError
              ? requestError.message
              : "Não foi possível criar o evento.")
          }
        />
      )}

      <form
        onSubmit={handleSubmit}
        className="mt-6 max-w-3xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8"
      >
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="custom-title">Nome do evento</Label>
            <Input
              id="custom-title"
              name="title"
              minLength={2}
              maxLength={255}
              placeholder="Ex.: Festival de Música Independente"
              required
            />
          </div>

          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="custom-description">Descrição</Label>
            <Textarea
              id="custom-description"
              name="description"
              maxLength={10_000}
              placeholder="Conte ao público o que ele encontrará no evento."
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="custom-date">Data e horário</Label>
            <Input id="custom-date" name="event_date" type="datetime-local" required />
          </div>

          <div className="space-y-2">
            <Label htmlFor="custom-venue">Nome do local</Label>
            <Input
              id="custom-venue"
              name="venue_name"
              minLength={2}
              maxLength={255}
              placeholder="Ex.: Centro de Convenções"
              required
            />
          </div>

          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="custom-address">Endereço</Label>
            <Input
              id="custom-address"
              name="venue_address"
              minLength={2}
              maxLength={2_000}
              placeholder="Rua, número, bairro, cidade e estado"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="custom-capacity">Capacidade</Label>
            <Input
              id="custom-capacity"
              name="capacity"
              type="number"
              min="1"
              max="1000000"
              step="1"
              defaultValue="100"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="custom-price">Preço do ingresso (R$)</Label>
            <Input
              id="custom-price"
              name="ticket_price"
              type="number"
              min="0"
              step="0.01"
              placeholder="0,00"
              required
            />
          </div>

          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="custom-image">Imagem de divulgação</Label>
            <Input
              id="custom-image"
              name="image"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="h-auto py-2 file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-slate-700"
              aria-describedby="custom-image-help"
              onChange={handleImageChange}
            />
            <p id="custom-image-help" className="text-xs text-slate-500">
              JPEG, PNG ou WebP, com no máximo 5 MB. A imagem é opcional.
            </p>
          </div>

          {imagePreviewUrl && (
            <div className="sm:col-span-2">
              <p className="mb-2 text-sm font-medium text-slate-800">Pré-visualização</p>
              <div className="relative aspect-[16/7] overflow-hidden rounded-lg border border-slate-200 bg-slate-100">
                <Image
                  src={imagePreviewUrl}
                  alt="Pré-visualização da imagem do evento"
                  fill
                  unoptimized
                  className="object-cover"
                />
              </div>
            </div>
          )}
        </div>

        <div className="mt-7 flex justify-end">
          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Criando evento..." : "Criar e publicar evento"}
          </Button>
        </div>
      </form>
    </section>
  );
}
