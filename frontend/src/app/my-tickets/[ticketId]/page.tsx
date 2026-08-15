import type { Metadata } from "next";

import { TicketDetails } from "@/components/tickets/ticket-details";

export const metadata: Metadata = {
  title: "Ingresso | Elite Events",
};

export default async function TicketPage({
  params,
}: {
  params: Promise<{ ticketId: string }>;
}) {
  const { ticketId } = await params;

  return (
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
      <TicketDetails ticketId={ticketId} />
    </main>
  );
}
