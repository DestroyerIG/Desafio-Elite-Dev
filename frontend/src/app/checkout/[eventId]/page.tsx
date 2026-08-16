import type { Metadata } from "next";

import { Checkout } from "@/components/reservations/checkout";

export const metadata: Metadata = {
  title: "Reservar ingressos | Elite Events",
};

export default async function CheckoutPage({
  params,
  searchParams,
}: {
  params: Promise<{ eventId: string }>;
  searchParams: Promise<{ reservation?: string | string[] }>;
}) {
  const { eventId } = await params;
  const { reservation } = await searchParams;
  const reservationId = Array.isArray(reservation) ? reservation[0] : reservation;

  return <Checkout eventId={eventId} reservationId={reservationId} />;
}
