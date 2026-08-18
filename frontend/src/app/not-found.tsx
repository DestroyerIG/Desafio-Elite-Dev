import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/utils/cn";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-2xl flex-col items-center justify-center px-5 py-16 text-center sm:px-8">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
        Página não encontrada
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
        Este endereço não existe
      </h1>
      <p className="mt-4 leading-7 text-slate-600">
        O link pode estar incorreto ou o conteúdo pode ter sido removido. Veja os eventos
        disponíveis na agenda.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <Link href="/events" className={cn(buttonVariants())}>
          Ver eventos
        </Link>
        <Link href="/" className={cn(buttonVariants({ variant: "outline" }))}>
          Voltar para a home
        </Link>
      </div>
    </main>
  );
}
