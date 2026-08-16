"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ReservationCard } from "@/components/reservations/reservation-card";
import { EmptyState, ErrorMessage, LoadingState } from "@/components/ui/feedback";
import { ApiError } from "@/services/api";
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
      {cancelMutation.error && (
        <ErrorMessage
          message={
            cancelMutation.error instanceof ApiError
              ? cancelMutation.error.message
              : "Não foi possível cancelar a reserva."
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
          onCancel={(reservationId) => cancelMutation.mutate(reservationId)}
        />
      ))}
    </div>
  );
}
