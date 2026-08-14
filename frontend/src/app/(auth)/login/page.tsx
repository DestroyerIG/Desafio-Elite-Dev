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

function destinationFor(user: User) {
  if (user.role === "ORGANIZER") return "/organizer/dashboard";
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

        <div className="mt-8 rounded-lg border border-slate-200 bg-white p-5 text-sm">
          <p className="font-semibold text-slate-900">Credenciais de desenvolvimento</p>
          <dl className="mt-3 grid gap-2 text-slate-600 sm:grid-cols-[8rem_1fr]">
            <dt>Organizador</dt>
            <dd className="font-mono text-xs">organizer@example.com</dd>
            <dt>Cliente</dt>
            <dd className="font-mono text-xs">customer1@example.com</dd>
            <dt>Senha</dt>
            <dd className="font-mono text-xs">DevOnly123!</dd>
          </dl>
        </div>
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
