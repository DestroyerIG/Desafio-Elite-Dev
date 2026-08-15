import type { ReactNode } from "react";

import { CustomerGuard } from "@/components/customer-guard";
import { SiteHeader } from "@/components/site-header";

export default function MyTicketsLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <SiteHeader />
      <CustomerGuard>{children}</CustomerGuard>
    </>
  );
}
