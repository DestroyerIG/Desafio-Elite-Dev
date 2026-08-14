"use client";

import Link from "next/link";

import { useAuth } from "@/hooks/use-auth";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/utils/cn";

export function SiteHeader() {
  const { user, isLoading, logout } = useAuth();

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex min-h-16 max-w-6xl items-center justify-between gap-6 px-5 sm:px-8">
        <Link href="/" className="text-lg font-semibold tracking-tight text-slate-950">
          Elite Events
        </Link>

        <nav className="flex items-center gap-1" aria-label="Navegação principal">
          <Link href="/events" className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}>
            Eventos
          </Link>
          {user?.role === "ORGANIZER" && (
            <Link
              href="/organizer/dashboard"
              className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
            >
              Área do organizador
            </Link>
          )}
          {!isLoading && !user && (
            <Link href="/login" className={cn(buttonVariants({ size: "sm" }))}>
              Entrar
            </Link>
          )}
          {user && (
            <button
              type="button"
              className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
              onClick={logout}
            >
              Sair
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}

