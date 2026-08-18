"use client";

import { useEffect } from "react";

import "./globals.css";

/**
 * Última linha de defesa: cobre falhas no próprio layout raiz, onde `error.tsx`
 * ainda não existe na árvore. Precisa renderizar as próprias tags `html` e `body`
 * e não pode depender de provider algum, porque é justamente o topo que falhou.
 */
export default function GlobalError({
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
    <html lang="pt-BR">
      <body>
        <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center px-5 py-16 text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
            A aplicação encontrou um erro
          </h1>
          <p className="mt-4 leading-7 text-slate-600">
            Recarregue a página para continuar. Se o problema persistir, tente novamente em
            alguns instantes.
          </p>
          <button
            type="button"
            onClick={reset}
            className="mt-8 inline-flex h-10 items-center justify-center rounded-md bg-blue-700 px-4 text-sm font-semibold text-white transition-colors hover:bg-blue-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2"
          >
            Recarregar
          </button>
          {error.digest && (
            <p className="mt-8 text-xs text-slate-400">
              Código da ocorrência: <span className="font-mono">{error.digest}</span>
            </p>
          )}
        </main>
      </body>
    </html>
  );
}
