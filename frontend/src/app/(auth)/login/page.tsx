"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { ErrorMessage } from "@/components/ui/feedback";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/use-auth";
import { loginSchema } from "@/schemas/auth";
import { ApiError } from "@/services/api";
import type { User } from "@/types/api";

const developmentAccounts = [
  {
    role: "Organizador",
    description: "Publicação e gestão de eventos",
    email: "organizer@example.com",
  },
  {
    role: "Cliente 1",
    description: "Reservas, pagamentos e ingressos",
    email: "customer1@example.com",
  },
  {
    role: "Cliente 2",
    description: "Testes de concorrência entre clientes",
    email: "customer2@example.com",
  },
  {
    role: "Portaria",
    description: "Leitura e validação de ingressos",
    email: "gate@example.com",
  },
] as const;

const developmentPassword = "DevOnly123!";

function destinationFor(user: User) {
  if (user.role === "ORGANIZER") return "/organizer/dashboard";
  if (user.role === "GATE") return "/gate";
  if (user.role === "CUSTOMER" && typeof window !== "undefined") {
    const requestedPath = new URLSearchParams(window.location.search).get("next");
    if (
      requestedPath?.startsWith("/") &&
      !requestedPath.startsWith("//")
    ) {
      return requestedPath;
    }
  }
  return "/events";
}

export default function LoginPage() {
  const router = useRouter();
  const { user, isLoading: authIsLoading, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (user) router.replace(destinationFor(user));
  }, [router, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const result = loginSchema.safeParse({ email, password });
    if (!result.success) {
      setError(result.error.issues[0]?.message ?? "Revise os dados informados.");
      return;
    }

    setIsSubmitting(true);
    try {
      const loggedUser = await login(result.data.email, result.data.password);
      router.replace(destinationFor(loggedUser));
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Não foi possível entrar. Tente novamente.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function selectDevelopmentAccount(emailAddress: string) {
    setEmail(emailAddress);
    setPassword(developmentPassword);
    setError(null);
  }

  return (
    <main className="mx-auto grid max-w-5xl gap-10 px-5 py-12 sm:px-8 lg:grid-cols-[1fr_22rem] lg:py-20">
      <section className="self-center">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Acesso</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
          Entre na sua conta
        </h1>
        <p className="mt-3 max-w-lg leading-7 text-slate-600">
          O destino após o login é definido pelo papel da conta. Organizadores acessam publicação;
          clientes seguem para os eventos.
        </p>

        {process.env.NODE_ENV === "development" && (
          <section
            className="mt-8 rounded-xl border border-blue-200 bg-blue-50/60 p-5"
            aria-labelledby="development-accounts-title"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2
                  id="development-accounts-title"
                  className="font-semibold text-slate-950"
                >
                  Acessos de desenvolvimento
                </h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Escolha um perfil para preencher o formulário automaticamente.
                </p>
              </div>
              <span className="rounded-full bg-blue-100 px-2.5 py-1 text-xs font-semibold text-blue-800">
                Somente ambiente local
              </span>
            </div>

            <ul className="mt-5 grid gap-3 sm:grid-cols-2">
              {developmentAccounts.map((account) => (
                <li
                  key={account.email}
                  className="rounded-lg border border-blue-100 bg-white p-4"
                >
                  <p className="font-semibold text-slate-950">{account.role}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {account.description}
                  </p>
                  <dl className="mt-3 space-y-1 text-xs">
                    <div>
                      <dt className="sr-only">E-mail</dt>
                      <dd className="break-all font-mono text-slate-700">
                        {account.email}
                      </dd>
                    </div>
                    <div className="flex gap-2">
                      <dt className="text-slate-500">Senha:</dt>
                      <dd className="font-mono font-semibold text-slate-700">
                        {developmentPassword}
                      </dd>
                    </div>
                  </dl>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-3 w-full"
                    onClick={() => selectDevelopmentAccount(account.email)}
                    disabled={isSubmitting || authIsLoading}
                  >
                    Usar este acesso
                  </Button>
                </li>
              ))}
            </ul>
          </section>
        )}
      </section>

      <form
        onSubmit={handleSubmit}
        className="self-start rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        noValidate
      >
        <div className="space-y-2">
          <Label htmlFor="email">E-mail</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            disabled={isSubmitting || authIsLoading}
          />
        </div>
        <div className="mt-5 space-y-2">
          <Label htmlFor="password">Senha</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            disabled={isSubmitting || authIsLoading}
          />
        </div>
        {error && <ErrorMessage message={error} className="mt-5" />}
        <Button className="mt-6 w-full" type="submit" disabled={isSubmitting || authIsLoading}>
          {isSubmitting ? "Entrando..." : "Entrar"}
        </Button>
      </form>
    </main>
  );
}
