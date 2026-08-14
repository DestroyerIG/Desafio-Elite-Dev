import type { Metadata } from "next";

import { EventDetails } from "@/components/events/event-details";

export const metadata: Metadata = {
  title: "Detalhe do evento | Elite Events",
};

export default async function EventPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
      <EventDetails eventId={id} />
    </main>
  );
}

