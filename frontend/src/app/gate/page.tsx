import type { Metadata } from "next";

import { GateConsole } from "@/components/gate/gate-console";


export const metadata: Metadata = {
  title: "Portaria | Elite Events",
};

export default function GatePage() {
  return (
    <main className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">
        Operação de entrada
      </p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
        Portaria
      </h1>
      <p className="mt-3 max-w-2xl leading-7 text-slate-600">
        Selecione o evento e valide cada ingresso pela câmera ou pelo código
        manual. Cada tentativa fica registrada para auditoria.
      </p>
      <div className="mt-8">
        <GateConsole />
      </div>
    </main>
  );
}
