import Link from "next/link";

import { EventList } from "@/components/events/event-list";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/utils/cn";

export default function Home() {
  return (
    <main>
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 sm:px-8 lg:grid-cols-[1fr_22rem] lg:py-20">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.14em] text-blue-700">
              Agenda de eventos
            </p>
            <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              Encontre seu próximo evento com informações claras.
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
              Consulte datas, locais, preços e disponibilidade dos eventos publicados na plataforma.
            </p>
            <Link href="/events" className={cn(buttonVariants({ size: "lg" }), "mt-7")}>
              Ver todos os eventos
            </Link>
          </div>
          <div className="self-end rounded-lg border border-slate-200 bg-slate-50 p-6">
            <p className="text-sm font-medium text-slate-500">Para organizadores</p>
            <h2 className="mt-2 text-xl font-semibold text-slate-950">
              Publique a partir do catálogo Ticketmaster
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Entre com uma conta de organizador para pesquisar o catálogo e definir capacidade e preço.
            </p>
            <Link
              href="/login"
              className={cn(buttonVariants({ variant: "outline", size: "sm" }), "mt-5")}
            >
              Acessar plataforma
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-12 sm:px-8 sm:py-16" aria-labelledby="events-title">
        <div className="mb-7 flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-blue-700">Publicados recentemente</p>
            <h2 id="events-title" className="mt-1 text-2xl font-semibold text-slate-950">
              Próximos eventos
            </h2>
          </div>
          <Link href="/events" className="text-sm font-semibold text-blue-700 hover:text-blue-800">
            Ver agenda completa
          </Link>
        </div>
        <EventList carousel />
      </section>
    </main>
  );
}
