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
//
// Bug real corregido acá: antes se sumaba "enviados" de los 3 nodos (día 0,
// día X, día Y), triplicando el alcance real — los 3 nodos le llegan al
// MISMO grupo de personas en momentos distintos, no a 3 grupos distintos, así
// que sumarlos infla el número sin sentido. Un solo cálculo representativo
// (canal del primer nodo) sobre el alcance ya alcanza para mostrar la
// cascada real (entrega/apertura/clic).
function metricasFinales(nodos: NodoCampana[], clase: number, alcance: number): MetricasNodo {
  const canalDominante = nodos[0]?.canal ?? "whatsapp";
  return metricasSimuladas(clase, 0, canalDominante, alcance);
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

  // El alcance real de un segmento es un número grande (cientos de miles,
  // hasta 1.2M) — mostrarlo completo como "enviados" se sentía
  // desproporcionado para una vista de gestión que se ve en vivo durante un
  // demo de minutos. Techo duro de 15.000 (cómodamente bajo los 20.000
  // pedidos), independiente del alcance real del segmento — el "Alcance
  // real" de antes de enviar (KPI ya mostrado) sigue siendo el número
  // honesto de a quién le llega; esto es una vista de gestión simplificada,
  // no pretende ser el mismo número.
  const alcanceBase = Math.min(alcanceReal ?? 12000, 15000);
  const finales = metricasFinales(nodos, clase, alcanceBase);
  const segundosTranscurridos = enviadaEn ? (ahora - new Date(enviadaEn).getTime()) / 1000 : Infinity;

  // Todo sube de a poco (incluido "enviados": un batch real tampoco sale
  // completo en 0 segundos) — mismo principio honesto de antes, solo que
  // ahora sobre una base ya chica, así que los números se quedan bajos
  // incluso una vez completada la rampa.
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
