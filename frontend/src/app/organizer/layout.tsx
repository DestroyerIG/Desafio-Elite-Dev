import Link from "next/link";

import { OrganizerGuard } from "@/components/organizer-guard";
import { SiteHeader } from "@/components/site-header";

export default function OrganizerLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteHeader />
      <OrganizerGuard>
        <div className="border-b border-slate-200 bg-slate-950 text-white">
          <nav
            className="mx-auto flex h-12 max-w-6xl items-center gap-6 px-5 text-sm sm:px-8"
            aria-label="Navegação do organizador"
          >
            <Link href="/organizer/dashboard" className="hover:text-blue-200">
              Visão geral
            </Link>
            <Link href="/organizer/events" className="hover:text-blue-200">
              Meus eventos
            </Link>
            <Link href="/organizer/events/new" className="hover:text-blue-200">
              Publicar evento
            </Link>
          </nav>
        </div>
        {children}
      </OrganizerGuard>
    </>
  );
}

