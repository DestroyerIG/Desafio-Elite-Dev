"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ReservationCard } from "@/components/reservations/reservation-card";
import { EmptyState, ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { ApiError } from "@/services/api";
import { refundReservation } from "@/services/payments";
import { cancelReservation, listReservations } from "@/services/reservations";

export function ReservationList() {
  const queryClient = useQueryClient();
  const reservationsQuery = useQuery({
    queryKey: ["reservations"],
    queryFn: () => listReservations(),
  });
  const cancelMutation = useMutation({
    mutationFn: cancelReservation,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["reservations"] }),
        queryClient.invalidateQueries({ queryKey: ["events"] }),
      ]);
    },
  });
  const refundMutation = useMutation({
    mutationFn: refundReservation,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["reservations"] }),
        queryClient.invalidateQueries({ queryKey: ["events"] }),
        queryClient.invalidateQueries({ queryKey: ["tickets"] }),
      ]);
    },
  });
  const requestError = cancelMutation.error ?? refundMutation.error;

  function requestRefund(reservationId: string) {
    const confirmed = window.confirm(
      "Confirmar o cancelamento integral desta compra? Os ingressos serão invalidados e o valor será reembolsado pelo simulador.",
    );
    if (confirmed) refundMutation.mutate(reservationId);
  }

  if (reservationsQuery.isLoading) {
    return <LoadingState label="Carregando reservas..." />;
  }
  if (reservationsQuery.error) {
    return (
      <ErrorMessage
        message={
          reservationsQuery.error instanceof ApiError
            ? reservationsQuery.error.message
            : "Não foi possível carregar suas reservas."
        }
      />
    );
  }
  if (!reservationsQuery.data?.length) {
    return (
      <EmptyState
        title="Você ainda não possui reservas"
        description="Escolha um evento para reservar seus primeiros ingressos."
      />
    );
  }

  return (
    <div className="space-y-6">
      {requestError && (
        <ErrorMessage
          message={
            requestError instanceof ApiError
              ? requestError.message
              : "Não foi possível concluir o cancelamento ou reembolso."
          }
        />
      )}
      {reservationsQuery.data.map((reservation) => (
        <ReservationCard
          key={reservation.id}
          reservation={reservation}
          isCancelling={
            cancelMutation.isPending && cancelMutation.variables === reservation.id
          }
          isRefunding={
            refundMutation.isPending && refundMutation.variables === reservation.id
          }
          onCancel={(reservationId) => cancelMutation.mutate(reservationId)}
          onRefund={requestRefund}
        />
      ))}
    </div>
  );
}
