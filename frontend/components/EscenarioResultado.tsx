"use client";

import { useState } from "react";
import clsx from "clsx";
import { extraerAlcanceKpis, type EstadoEnvio, type Producto, type ResultadoSegmento } from "@/lib/api";
import { CampanaCanvas } from "./CampanaCanvas";
import { MetricasCampana } from "./MetricasCampana";
import { LoaderElegante } from "./LoaderElegante";

function TarjetaKPI({ etiqueta, valor, tipo }: { etiqueta: string; valor: string; tipo: string }) {
  return (
    <div
      className={clsx(
        "rounded-lg border px-3.5 py-3",
        tipo === "oportunidad" ? "border-black/15 bg-black/[0.03]" : "border-black/10 bg-white"
      )}
    >
      <p className="text-xs text-neutral-600 mb-1">{etiqueta}</p>
      <p className="text-sm text-[#0a0a0a] leading-snug">{valor}</p>
    </div>
  );
}

type EstadoAccion = "borrador" | "enviando" | "enviada" | "error";

function ChipsPerfil({ perfil }: { perfil: string }) {
  const rasgos = perfil
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  return (
    <div className="flex flex-wrap gap-1.5">
      {rasgos.map((rasgo, i) => (
        <span key={i} className="text-xs px-2 py-1 rounded-full bg-neutral-100 text-neutral-700">
          {rasgo}
        </span>
      ))}
    </div>
  );
}

// "Borrador" (el estado por defecto antes de aprobar) no se muestra — no
// aporta nada mientras el usuario está justo decidiendo si aprobar, y
// competía visualmente con el nombre de la audiencia. Solo se marca cuando
// pasa algo que sí importa: se envió, o falló.
function EstadoPill({ estado }: { estado: EstadoAccion }) {
  if (estado === "enviada") {
    return <span className="text-xs px-2 py-1 rounded-full bg-[#0a0a0a] text-white shrink-0">Enviada</span>;
  }
  if (estado === "error") {
    return <span className="text-xs px-2 py-1 rounded-full bg-red-50 text-red-600 shrink-0">Error</span>;
  }
  return null;
}

function TarjetaSegmento({
  resultado,
  indice,
  productos,
  onEnviar,
}: {
  resultado: ResultadoSegmento;
  indice: number;
  productos: Producto[];
  onEnviar: (clase: number, producto: string) => Promise<{ estado_envio: EstadoEnvio; enviada_en: string }>;
}) {
  const nombreAudiencia = resultado.interes_dominante ?? `Campaña ${indice + 1}`;
  const nombreProducto = productos.find((p) => p.slug === resultado.producto)?.nombre ?? resultado.producto;
  const [estado, setEstado] = useState<EstadoAccion>(
    resultado.campana_creada?.estado_envio === "enviada" ? "enviada" : "borrador"
  );
  // Cuándo se envió DE VERDAD (respuesta real del backend) — para que el
  // canvas muestre métricas honestas según el tiempo transcurrido, no el
  // resultado final instantáneo apenas se aprueba.
  const [enviadaEn, setEnviadaEn] = useState<string | undefined>(resultado.campana_creada?.enviada_en ?? undefined);

  if (resultado.error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-5">
        <p className="text-sm text-red-700">
          {nombreAudiencia}: {resultado.error}
        </p>
      </div>
    );
  }

  const nodos = resultado.campana_creada?.nodos ?? [];
  const kpis = resultado.plan?.resumen_kpis ?? [];
  const alcanceReal = extraerAlcanceKpis(kpis) || undefined;

  // Mínimo 3s de "enviando" antes de pasar a gestión — aunque el backend
  // responda antes, aprobar y enviar es una acción real (dispara el evento
  // de Journey de verdad) y merece una confirmación visible, no un parpadeo.
  async function manejarEnviar() {
    setEstado("enviando");
    try {
      const [respuesta] = await Promise.all([
        onEnviar(resultado.clase, resultado.producto),
        new Promise((resolve) => setTimeout(resolve, 3000)),
      ]);
      setEnviadaEn(respuesta.enviada_en);
      setEstado("enviada");
    } catch {
      setEstado("error");
    }
  }

  return (
    <div className="rounded-xl border border-black/10 bg-white overflow-hidden">
      <div className="p-5">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <p className="text-xs font-medium text-neutral-600 tracking-wide mb-1">Interés</p>
            <p className="text-lg font-semibold text-[#0a0a0a]">{nombreAudiencia}</p>
          </div>
          <EstadoPill estado={estado} />
        </div>

        {/* Al aprobar y enviar, TODO este bloque (quién recibe esto, cómo se
            les habla, resumen, KPIs) cambia — antes de enviar es material de
            revisión, después de enviar lo único relevante es cómo va la
            campaña. Reemplaza el div completo, no solo el canvas de abajo. */}
        {estado === "enviando" ? (
          <div className="py-16 flex flex-col items-center justify-center gap-3">
            <LoaderElegante listo={false} />
            <p className="text-sm text-neutral-600">Enviando campaña...</p>
          </div>
        ) : estado === "enviada" ? (
          <MetricasCampana nodos={nodos} clase={resultado.clase} alcanceReal={alcanceReal} enviadaEn={enviadaEn} />
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
              {resultado.perfil && (
                <div className="rounded-lg border border-black/10 bg-neutral-50 px-3 py-2.5">
                  <p className="text-xs font-medium text-neutral-600 tracking-wide mb-1.5">Quién recibe esto</p>
                  <ChipsPerfil perfil={resultado.perfil} />
                </div>
              )}

              {resultado.tono_comunicacion && (
                <div className="rounded-lg border border-black/10 bg-neutral-50 px-3 py-2.5">
                  <p className="text-xs font-medium text-neutral-600 tracking-wide mb-1.5">Cómo se les habla</p>
                  <p className="text-sm text-neutral-800 leading-snug">{resultado.tono_comunicacion}</p>
                </div>
              )}
            </div>

            <p className="text-sm text-neutral-700 leading-relaxed mb-4">{resultado.plan?.resumen}</p>

            {kpis.length > 0 && (
              <div className="grid grid-cols-2 gap-2 mb-4">
                {kpis.map((k, i) => (
                  <TarjetaKPI key={i} {...k} />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {estado === "borrador" && nodos.length > 0 && (
        <div className="border-t border-black/10 p-5 pt-4">
          <CampanaCanvas nodos={nodos} nombreProducto={nombreProducto} />
        </div>
      )}

      {(estado === "borrador" || estado === "error") && (
        <div className="border-t border-black/10 px-5 py-4">
          <button
            type="button"
            onClick={manejarEnviar}
            className="bg-[#0a0a0a] hover:bg-neutral-800 text-[#fffef7] font-medium rounded-lg px-4 py-2 text-xs transition-colors"
          >
            Aprobar y enviar
          </button>
          {estado === "error" && <p className="text-xs text-red-600 mt-2">No se pudo enviar, intenta de nuevo.</p>}
        </div>
      )}
    </div>
  );
}

export function EscenarioResultado({
  resultados,
  productos,
  onEnviar,
}: {
  resultados: ResultadoSegmento[];
  productos: Producto[];
  onEnviar: (clase: number, producto: string) => Promise<{ estado_envio: EstadoEnvio; enviada_en: string }>;
}) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      {resultados.map((r, i) => (
        <TarjetaSegmento key={r.clase} resultado={r} indice={i} productos={productos} onEnviar={onEnviar} />
      ))}
    </div>
  );
}
