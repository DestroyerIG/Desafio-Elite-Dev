"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/hooks/use-auth";
import { LoadingState } from "@/components/ui/feedback";

export function OrganizerGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (!user) router.replace("/login?next=/organizer/dashboard");
    else if (user.role !== "ORGANIZER") router.replace("/events");
  }, [isLoading, router, user]);

  if (isLoading || !user || user.role !== "ORGANIZER") {
    return <LoadingState label="Verificando acesso..." />;
  }

  return children;
}

