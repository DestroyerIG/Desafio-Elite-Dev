import type { ReservationStatus } from "@/types/api";

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "long",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatCurrency(value: string) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number(value));
}


// Rótulos exibidos ao usuário. O enum da API nunca vai direto para a tela.
export const reservationStatusLabels: Record<ReservationStatus, string> = {
  PENDING: "Aguardando pagamento",
  PAID: "Pago",
  REFUNDED: "Reembolsado",
  CANCELLED: "Cancelado",
  EXPIRED: "Expirado",
};
