"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";

import { LoadingState } from "@/components/ui/feedback";
import { useAuth } from "@/hooks/use-auth";


export function GateGuard({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!user) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    else if (user.role !== "GATE") router.replace("/events");
  }, [isLoading, pathname, router, user]);

  if (isLoading || !user || user.role !== "GATE") {
    return <LoadingState label="Verificando acesso da portaria..." />;
  }

  return children;
}
