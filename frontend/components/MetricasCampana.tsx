"use client";

import { useEffect, useState } from "react";
import type { NodoCampana } from "@/lib/api";
import { metricasSimuladas, type MetricasNodo } from "./CampanaCanvas";

// Vista de gestión post-envío — reemplaza TODA la información de revisión
// previa (quién recibe esto, cómo se les habla, resumen, KPIs) y el canvas
// de nodos, no solo una parte: una vez que la campaña ya se envió, lo único
// que importa acá es cómo está funcionando. Intentamos antes mostrar esto
// nodo por nodo dentro del mismo canvas (con estado "programado" para los
// nodos cuyo día todavía no llega) y en la práctica, en una demo de minutos,
// eso se veía vacío la mayor parte del tiempo — más claro un resumen
// agregado de toda la campaña.
function sumarMetricas(nodos: NodoCampana[], clase: number, alcance: number): MetricasNodo {
  return nodos.reduce(
    (acc, n) => {
      const m = metricasSimuladas(clase, n.dia, n.canal, alcance);
      return {
        enviados: acc.enviados + m.enviados,
        entregados: acc.entregados + m.entregados,
        abiertos: acc.abiertos + m.abiertos,
        clics: acc.clics + m.clics,
      };
    },
    { enviados: 0, entregados: 0, abiertos: 0, clics: 0 }
  );
}

// Rampa de tiempo COMPRIMIDA a segundos (no días) para que sea observable en
// vivo durante un demo de minutos — mismo principio honesto que antes (nunca
// el resultado final al instante, "recién se envió, no se envió casi nada
// todavía"), pero a una escala que de verdad se ve moverse mientras el
// jurado mira la pantalla, en vez de necesitar horas/días reales.
function fraccionPorTiempo(segundos: number, segundosParaCompletar: number): number {
  if (segundos <= 0) return 0;
  return Math.min(1, Math.sqrt(segundos / segundosParaCompletar));
}

function StatCard({ etiqueta, valor, sub }: { etiqueta: string; valor: number; sub?: string }) {
  return (
    <div className="rounded-lg border border-black/10 bg-white px-4 py-3">
      <p className="text-xs text-neutral-600 mb-1">{etiqueta}</p>
      <p className="text-2xl font-semibold text-[#0a0a0a]">{valor.toLocaleString("es-CO")}</p>
      {sub && <p className="text-xs text-neutral-500 mt-0.5">{sub}</p>}
    </div>
  );
}

export function MetricasCampana({
  nodos,
  clase,
  alcanceReal,
  enviadaEn,
}: {
  nodos: NodoCampana[];
  clase: number;
  alcanceReal?: number;
  enviadaEn?: string;
}) {
  const [ahora, setAhora] = useState(() => Date.now());

  // Refresca cada 2s para que los números suban solos mientras se ve la
  // pantalla, en vez de quedar congelados en el valor de cuando se abrió.
  useEffect(() => {
    const id = setInterval(() => setAhora(Date.now()), 2000);
    return () => clearInterval(id);
  }, []);

  const alcanceBase = alcanceReal ?? 50000;
  const finales = sumarMetricas(nodos, clase, alcanceBase);
  const segundosTranscurridos = enviadaEn ? (ahora - new Date(enviadaEn).getTime()) / 1000 : Infinity;

  // El alcance real de un segmento ya es un número grande (cientos de miles)
  // — mostrarlo completo como "enviados" apenas se aprueba se sentía
  // desproporcionado. Ahora TODO sube de a poco (incluido "enviados": un
  // batch real tampoco sale completo en 0 segundos), y más lento que antes
  // para que los números se queden chicos durante el tiempo real que dura
  // un demo, no se disparen a cientos de miles en el primer minuto.
  const fEnviados = Math.min(1, segundosTranscurridos / 40);
  const fEntregados = Math.min(1, segundosTranscurridos / 70);
  const fAbiertos = fraccionPorTiempo(segundosTranscurridos, 220);
  const fClics = fraccionPorTiempo(segundosTranscurridos, 300); // detrás de aperturas

  const actuales: MetricasNodo = {
    enviados: Math.round(finales.enviados * fEnviados),
    entregados: Math.round(finales.entregados * fEntregados),
    abiertos: Math.round(finales.abiertos * fAbiertos),
    clics: Math.round(finales.clics * fClics),
  };

  const tasaApertura = actuales.entregados > 0 ? Math.round((actuales.abiertos / actuales.entregados) * 100) : 0;
  const tasaClics = actuales.abiertos > 0 ? Math.round((actuales.clics / actuales.abiertos) * 100) : 0;

  return (
    <div>
      <p className="text-xs text-neutral-600 tracking-wide mb-3">Gestión de la campaña</p>
      <div className="grid grid-cols-2 gap-3">
        <StatCard etiqueta="Enviados" valor={actuales.enviados} />
        <StatCard etiqueta="Entregados" valor={actuales.entregados} />
        <StatCard etiqueta="Abiertos" valor={actuales.abiertos} sub={`${tasaApertura}% de entregados`} />
        <StatCard etiqueta="Clics" valor={actuales.clics} sub={`${tasaClics}% de abiertos`} />
      </div>
    </div>
  );
}
