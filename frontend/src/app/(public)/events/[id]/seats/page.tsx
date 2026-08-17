import type { Metadata } from "next";

import { SeatMapPageContent } from "@/components/seats/seat-map-page-content";

export const metadata: Metadata = {
  title: "Escolher assentos | Elite Events",
};

export default async function EventSeatsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <SeatMapPageContent eventId={id} />;
}
