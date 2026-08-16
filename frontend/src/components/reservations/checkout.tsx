"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button, buttonVariants } from "@/components/ui/button";
import { ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { paymentSchema } from "@/schemas/payments";
import { reservationSchema } from "@/schemas/reservations";
import { ApiError } from "@/services/api";
import { getEvent } from "@/services/events";
import { payReservation, refundReservation } from "@/services/payments";
import {
  cancelReservation,
  createReservation,
  getReservation,
} from "@/services/reservations";
import type { Reservation } from "@/types/api";
import { cn } from "@/utils/cn";
import { formatCurrency, formatDate } from "@/utils/format";

export function Checkout({
  eventId,
  reservationId,
}: {
  eventId: string;
  reservationId?: string;
}) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user, isLoading: authIsLoading } = useAuth();
  const [quantity, setQuantity] = useState("1");
  const [cardNumber, setCardNumber] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [createdReservation, setCreatedReservation] =
    useState<Reservation | null>(null);
  const isCustomer = user?.role === "CUSTOMER";
  const checkoutPath = reservationId
    ? `/checkout/${eventId}?reservation=${reservationId}`
    : `/checkout/${eventId}`;

  useEffect(() => {
    if (authIsLoading) return;
    if (!user) {
      router.replace(`/login?next=${encodeURIComponent(checkoutPath)}`);
    } else if (!isCustomer) {
      router.replace(`/events/${eventId}`);
    }
  }, [authIsLoading, checkoutPath, eventId, isCustomer, router, user]);

  const eventQuery = useQuery({
    queryKey: ["events", eventId],
    queryFn: () => getEvent(eventId),
    enabled: isCustomer,
  });
  const reservationQuery = useQuery({
    queryKey: ["reservations", reservationId],
    queryFn: () => getReservation(reservationId as string),
    enabled: isCustomer && Boolean(reservationId),
  });
  const createMutation = useMutation({
    mutationFn: (selectedQuantity: number) =>
      createReservation(eventId, selectedQuantity),
    onSuccess: async (createdReservation) => {
      setCreatedReservation(createdReservation);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["events"] }),
        queryClient.invalidateQueries({ queryKey: ["reservations"] }),
      ]);
      router.replace(
        `/checkout/${eventId}?reservation=${createdReservation.id}`,
      );
    },
  });
  const cancelMutation = useMutation({
    mutationFn: (reservationId: string) => cancelReservation(reservationId),
    onSuccess: async (cancelledReservation) => {
      setCreatedReservation(cancelledReservation);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["events"] }),
        queryClient.invalidateQueries({ queryKey: ["reservations"] }),
      ]);
    },
  });
  const paymentMutation = useMutation({
    mutationFn: ({
      reservationId,
      normalizedCardNumber,
    }: {
      reservationId: string;
      normalizedCardNumber: string;
    }) => payReservation(reservationId, normalizedCardNumber),
    onSuccess: async (payment) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["events"] }),
        queryClient.invalidateQueries({ queryKey: ["reservations"] }),
        queryClient.invalidateQueries({ queryKey: ["tickets"] }),
      ]);
      const firstTicketId = payment.ticket_ids[0];
      router.push(
        firstTicketId ? `/my-tickets/${firstTicketId}` : "/my-tickets",
      );
    },
  });
  const refundMutation = useMutation({
    mutationFn: (reservationId: string) => refundReservation(reservationId),
    onSuccess: async (refund) => {
      setCreatedReservation(refund.reservation);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["events"] }),
        queryClient.invalidateQueries({ queryKey: ["reservations"] }),
        queryClient.invalidateQueries({ queryKey: ["tickets"] }),
      ]);
    },
  });

  if (authIsLoading || !isCustomer) {
    return <LoadingState label="Verificando acesso..." />;
  }
  if (eventQuery.isLoading || reservationQuery.isLoading) {
    return <LoadingState label="Carregando checkout..." />;
  }
  const pageError = reservationQuery.error ?? eventQuery.error;
  if (pageError || !eventQuery.data) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8">
        <ErrorMessage
          message={
            pageError instanceof ApiError
              ? pageError.message
              : "Não foi possível carregar o checkout."
          }
        />
      </main>
    );
  }

  const event = eventQuery.data;
  const reservation = createdReservation ?? reservationQuery.data ?? null;
  if (reservation && reservation.event_id !== eventId) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8">
        <ErrorMessage message="Esta reserva não pertence ao evento informado." />
      </main>
    );
  }
  const parsedQuantity = Number(quantity);
  const estimatedTotal = Number.isFinite(parsedQuantity)
    ? Number(event.ticket_price) * parsedQuantity
    : 0;
  const requestError =
    createMutation.error ??
    cancelMutation.error ??
    paymentMutation.error ??
    refundMutation.error;

  function handleSubmit(formEvent: FormEvent<HTMLFormElement>) {
    formEvent.preventDefault();
    setFormError(null);
    const result = reservationSchema.safeParse({ quantity });
    if (!result.success) {
      setFormError(result.error.issues[0]?.message ?? "Revise a quantidade.");
      return;
    }
    if (result.data.quantity > event.available_tickets) {
      setFormError("A quantidade selecionada supera a disponibilidade atual.");
      return;
    }
    createMutation.mutate(result.data.quantity);
  }

  function handlePayment(formEvent: FormEvent<HTMLFormElement>) {
    formEvent.preventDefault();
    if (!reservation) return;
    setFormError(null);
    const result = paymentSchema.safeParse({ cardNumber });
    if (!result.success) {
      setFormError(result.error.issues[0]?.message ?? "Revise o cartão.");
      return;
    }
    paymentMutation.mutate({
      reservationId: reservation.id,
      normalizedCardNumber: result.data.cardNumber,
    });
  }

  function handleRefund() {
    if (!reservation) return;
    const confirmed = window.confirm(
      "Confirmar o cancelamento integral desta compra? Os ingressos serão invalidados e o valor será reembolsado pelo simulador.",
    );
    if (confirmed) refundMutation.mutate(reservation.id);
  }

  if (reservation) {
    const wasCancelled = reservation.status === "CANCELLED";
    const wasPaid = reservation.status === "PAID";
    const wasRefunded = reservation.status === "REFUNDED";
    const isPending = reservation.status === "PENDING";
    const paymentWasDeclined =
      paymentMutation.error instanceof ApiError &&
      paymentMutation.error.code === "PAYMENT_DECLINED";
    return (
      <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8 sm:py-16">
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
            {wasCancelled
              ? "Reserva cancelada"
              : wasRefunded
                ? "Compra reembolsada"
                : wasPaid
                  ? "Pagamento aprovado"
                  : "Reserva confirmada"}
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
            {event.title}
          </h1>
          <p className="mt-3 leading-7 text-slate-600">
            {wasCancelled
              ? "Os ingressos foram devolvidos à disponibilidade do evento."
              : wasRefunded
                ? "O pagamento foi reembolsado, os ingressos foram invalidados e o estoque foi devolvido ao evento."
                : wasPaid
                  ? "Seus ingressos foram emitidos e já estão disponíveis."
                  : "O estoque foi separado. Conclua o pagamento simulado para emitir seus ingressos."}
          </p>

          <dl className="mt-8 grid gap-5 border-y border-slate-100 py-6 text-sm sm:grid-cols-2">
            <div>
              <dt className="font-medium text-slate-500">Código da reserva</dt>
              <dd className="mt-1 break-all font-mono text-xs text-slate-900">
                {reservation.id}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Status</dt>
              <dd className="mt-1 font-semibold text-slate-900">{reservation.status}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Quantidade</dt>
              <dd className="mt-1 text-slate-900">{reservation.quantity}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Total congelado</dt>
              <dd className="mt-1 text-lg font-semibold text-slate-950">
                {formatCurrency(reservation.total_amount)}
              </dd>
            </div>
          </dl>

          {isPending && (
            <form
              onSubmit={handlePayment}
              className="mt-6 rounded-lg border border-blue-100 bg-blue-50/50 p-5"
            >
              <h2 className="font-semibold text-slate-950">Pagamento simulado</h2>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                Use 4242 4242 4242 4242 para aprovar. Números terminados em
                0000 são recusados. O número não é armazenado.
              </p>
              <div className="mt-4 space-y-2">
                <Label htmlFor="card-number">Número do cartão de teste</Label>
                <Input
                  id="card-number"
                  name="card-number"
                  inputMode="numeric"
                  autoComplete="cc-number"
                  placeholder="4242 4242 4242 4242"
                  value={cardNumber}
                  onChange={(inputEvent) => {
                    setCardNumber(inputEvent.target.value);
                    setFormError(null);
                    if (paymentWasDeclined) paymentMutation.reset();
                  }}
                  disabled={paymentMutation.isPending}
                />
              </div>
              {paymentWasDeclined && (
                <p className="mt-3 text-sm leading-6 text-slate-700">
                  Troque o número do cartão e tente novamente. Sua reserva continua
                  ativa e o estoque permanece separado.
                </p>
              )}
              {formError && <ErrorMessage message={formError} className="mt-4" />}
              <Button
                type="submit"
                className="mt-4 w-full sm:w-auto"
                disabled={paymentMutation.isPending}
              >
                {paymentMutation.isPending
                  ? "Processando..."
                  : paymentWasDeclined
                    ? "Tentar pagamento novamente"
                    : "Pagar e emitir ingressos"}
              </Button>
            </form>
          )}

          {requestError && (
            <ErrorMessage
              className="mt-5"
              message={
                requestError instanceof ApiError
                  ? requestError.message
                  : "Não foi possível concluir a operação."
              }
            />
          )}
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href={`/events/${eventId}`}
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Voltar ao evento
            </Link>
            {wasPaid && (
              <>
                <Link href="/my-tickets" className={cn(buttonVariants())}>
                  Ver meus ingressos
                </Link>
                <Button
                  type="button"
                  variant="danger"
                  disabled={refundMutation.isPending}
                  onClick={handleRefund}
                >
                  {refundMutation.isPending
                    ? "Reembolsando..."
                    : "Solicitar reembolso"}
                </Button>
              </>
            )}
            {isPending && (
              <Button
                type="button"
                variant="danger"
                disabled={cancelMutation.isPending || paymentMutation.isPending}
                onClick={() => cancelMutation.mutate(reservation.id)}
              >
                {cancelMutation.isPending ? "Cancelando..." : "Cancelar reserva"}
              </Button>
            )}
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="mx-auto grid max-w-5xl gap-8 px-5 py-10 sm:px-8 sm:py-14 lg:grid-cols-[1fr_22rem]">
      <section>
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Checkout</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
          Reserve seus ingressos
        </h1>
        <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-blue-700">{formatDate(event.event_date)}</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-950">{event.title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {event.venue_name} · {event.venue_address}
          </p>
        </div>
      </section>

      <form
        onSubmit={handleSubmit}
        className="self-start rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div className="space-y-2">
          <Label htmlFor="quantity">Quantidade</Label>
          <Input
            id="quantity"
            type="number"
            min="1"
            max={event.available_tickets}
            step="1"
            value={quantity}
            onChange={(inputEvent) => setQuantity(inputEvent.target.value)}
            disabled={event.available_tickets === 0 || createMutation.isPending}
          />
          <p className="text-xs text-slate-500">
            {event.available_tickets} ingresso(s) disponível(is)
          </p>
        </div>
        <dl className="mt-6 space-y-3 border-y border-slate-100 py-5 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Preço unitário</dt>
            <dd className="font-medium text-slate-900">
              {formatCurrency(event.ticket_price)}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="font-medium text-slate-700">Total estimado</dt>
            <dd className="text-lg font-semibold text-slate-950">
              {formatCurrency(String(Math.max(0, estimatedTotal)))}
            </dd>
          </div>
        </dl>
        {formError && <ErrorMessage message={formError} className="mt-5" />}
        {requestError && (
          <ErrorMessage
            className="mt-5"
            message={
              requestError instanceof ApiError
                ? requestError.message
                : "Não foi possível criar a reserva."
            }
          />
        )}
        <Button
          type="submit"
          className="mt-6 w-full"
          disabled={event.available_tickets === 0 || createMutation.isPending}
        >
          {event.available_tickets === 0
            ? "Evento esgotado"
            : createMutation.isPending
              ? "Reservando..."
              : "Confirmar reserva"}
        </Button>
      </form>
    </main>
  );
}
