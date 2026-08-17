import type { Metadata } from "next";

import { SeatMapEditor } from "@/components/seats/seat-map-editor";

export const metadata: Metadata = {
  title: "Mapa de assentos | Elite Events",
};

export default async function OrganizerSeatMapPage({
  params,
}: {
  params: Promise<{ eventId: string }>;
}) {
  const { eventId } = await params;
  return <SeatMapEditor eventId={eventId} />;
}
