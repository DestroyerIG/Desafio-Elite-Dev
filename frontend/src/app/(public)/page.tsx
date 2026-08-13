const foundationItems = [
  "Next.js com App Router e TypeScript",
  "Tailwind CSS configurado",
  "FastAPI com health check do PostgreSQL",
  "Schema inicial versionado pelo Alembic",
];

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
          <span className="text-lg font-semibold tracking-tight">Elite Events</span>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
            Fundação técnica
          </span>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-10 px-5 py-16 sm:px-8 lg:grid-cols-[1.2fr_0.8fr] lg:py-24">
        <section aria-labelledby="page-title" className="max-w-2xl">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.16em] text-blue-700">
            Desafio Elite Dev 2026
          </p>
          <h1 id="page-title" className="text-4xl font-semibold tracking-tight sm:text-5xl">
            Plataforma de eventos e ingressos
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
            O ambiente inicial está pronto. Os fluxos de eventos, reservas, pagamentos e ingressos serão
            adicionados progressivamente nas próximas fases.
          </p>
        </section>

        <section
          aria-labelledby="foundation-title"
          className="self-start rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <div className="flex items-center justify-between gap-4">
            <h2 id="foundation-title" className="font-semibold">
              Estado da fundação
            </h2>
            <span className="inline-flex items-center gap-2 text-sm font-medium text-emerald-700">
              <span aria-hidden="true" className="h-2 w-2 rounded-full bg-emerald-500" />
              Frontend ativo
            </span>
          </div>

          <ul className="mt-5 space-y-3 border-t border-slate-100 pt-5 text-sm text-slate-700">
            {foundationItems.map((item) => (
              <li key={item} className="flex gap-3">
                <span aria-hidden="true" className="mt-1 h-4 w-4 rounded border border-emerald-300 bg-emerald-50" />
                {item}
              </li>
            ))}
          </ul>

          <div className="mt-6 rounded-lg bg-slate-950 px-4 py-3 font-mono text-xs text-slate-100">
            GET http://localhost:8000/health
          </div>
        </section>
      </main>
    </div>
  );
}
