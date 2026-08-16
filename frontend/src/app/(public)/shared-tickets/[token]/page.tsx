import type { Metadata } from "next";

import { SharedTicketDetails } from "@/components/tickets/shared-ticket-details";


export const metadata: Metadata = {
  title: "Ingresso compartilhado | Elite Events",
};

export default async function SharedTicketPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;

  return (
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
      <SharedTicketDetails token={token} />
    </main>
  );
}
