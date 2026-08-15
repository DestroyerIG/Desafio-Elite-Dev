import type { Metadata } from "next";

import { Checkout } from "@/components/reservations/checkout";

export const metadata: Metadata = {
  title: "Reservar ingressos | Elite Events",
};

export default async function CheckoutPage({
  params,
}: {
  params: Promise<{ eventId: string }>;
}) {
  const { eventId } = await params;

  return <Checkout eventId={eventId} />;
}
