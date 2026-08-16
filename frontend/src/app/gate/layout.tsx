import type { ReactNode } from "react";

import { GateGuard } from "@/components/gate-guard";
import { SiteHeader } from "@/components/site-header";


export default function GateLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <SiteHeader />
      <GateGuard>{children}</GateGuard>
    </>
  );
}
