"use client";

import { useEffect } from "react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/utils/cn";

/**
 * Fronteira de erro das rotas. Recebe a exceção real, mas nunca a exibe: o texto
 * de `error.message` pode conter detalhe técnico ou nome de recurso interno. A
 * causa vai para o console do navegador, onde só quem investiga a alcança.
 */
export default function RouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto flex min-h-[60vh] max-w-2xl flex-col items-center justify-center px-5 py-16 text-center sm:px-8">
      <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
        Algo deu errado
      </h1>
      <p className="mt-4 leading-7 text-slate-600">
        Não conseguimos carregar esta página. A falha foi registrada e você pode tentar de
        novo agora mesmo.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <button type="button" onClick={reset} className={cn(buttonVariants())}>
          Tentar novamente
        </button>
        <Link href="/" className={cn(buttonVariants({ variant: "outline" }))}>
          Voltar para a home
        </Link>
      </div>
      {error.digest && (
        <p className="mt-8 text-xs text-slate-400">
          Código da ocorrência: <span className="font-mono">{error.digest}</span>
        </p>
      )}
    </main>
  );
}
