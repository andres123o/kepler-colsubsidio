"use client";

import { useEffect, useRef, useState } from "react";
import { HiChevronDown, HiArrowPath } from "react-icons/hi2";
import { getProductos, procesarCampana, enviarCampana, extraerAlcanceKpis, type Producto, type ResultadoSegmento, type EventoProceso } from "@/lib/api";
import { EscenarioProcesando, type PasoLog } from "@/components/EscenarioProcesando";
import { EscenarioResultado } from "@/components/EscenarioResultado";
import { AvisoTemporada } from "@/components/AvisoTemporada";
import { metricasSimuladas, ETIQUETA_CANAL } from "@/components/CampanaCanvas";

type Estado = "idle" | "procesando" | "resultado";

interface Ejecucion {
  producto: string;
  fecha: string;
  clientesAlcanzados: number;
  entregados: number;
  abiertos: number;
  clics: number;
  canalPrincipal: string;
  // Duración real de la campaña (del primer al último nodo del journey,
  // según la cadencia que devuelve el modelo — 0/3/7 días hoy, ver
  // agente/prompts.py), no el tiempo que tardó en generarse.
  duracionDias: number;
  estado: "completado" | "error";
}

// Cuántas campañas ficticias tiene ya cada producto — solo para variar el
// widget de vista previa (nunca "siempre 1"), no representa un dato real.
const CAMPANAS_FICTICIAS: Record<string, number> = {
  Hipotecario: 1,
  Libre_inversion: 3,
  Educativo: 2,
  Rotativo_cupo: 3,
  Compra_cartera: 2,
};

// Ejemplos para mostrar el historial con contenido — como si el sistema ya
// llevara 7 campañas corridas. clientesAlcanzados usa los n_afiliados reales
// de cada producto (ver /api/productos), el resto de la fila es ilustrativo.
// Se agregan arriba de estos apenas se procesa una ejecución real en la
// sesión (ver contarEstadisticas más abajo).
const HISTORIAL_EJEMPLO: Ejecucion[] = [
  { producto: "Libre_inversion", fecha: "23/07/2026, 9:14 a. m.", clientesAlcanzados: 788652, entregados: 765192, abiertos: 688673, clics: 144621, canalPrincipal: "WhatsApp", duracionDias: 7, estado: "completado" },
  { producto: "Educativo", fecha: "22/07/2026, 4:32 p. m.", clientesAlcanzados: 837730, entregados: 812398, abiertos: 731158, clics: 153543, canalPrincipal: "WhatsApp", duracionDias: 6, estado: "completado" },
  { producto: "Compra_cartera", fecha: "21/07/2026, 11:05 a. m.", clientesAlcanzados: 433231, entregados: 420334, abiertos: 378301, clics: 79443, canalPrincipal: "WhatsApp", duracionDias: 8, estado: "completado" },
  { producto: "Rotativo_cupo", fecha: "20/07/2026, 2:47 p. m.", clientesAlcanzados: 1224111, entregados: 1187388, abiertos: 320595, clics: 51295, canalPrincipal: "Push", duracionDias: 5, estado: "completado" },
  { producto: "Hipotecario", fecha: "19/07/2026, 10:20 a. m.", clientesAlcanzados: 427027, entregados: 414216, abiertos: 86985, clics: 17397, canalPrincipal: "Email", duracionDias: 10, estado: "completado" },
  { producto: "Libre_inversion", fecha: "18/07/2026, 8:03 a. m.", clientesAlcanzados: 788652, entregados: 765192, abiertos: 688673, clics: 144621, canalPrincipal: "WhatsApp", duracionDias: 7, estado: "completado" },
  { producto: "Educativo", fecha: "17/07/2026, 3:56 p. m.", clientesAlcanzados: 837730, entregados: 812398, abiertos: 219347, clics: 35096, canalPrincipal: "Push", duracionDias: 6, estado: "completado" },
];

// Mismas métricas que ve el usuario en el canvas de gestión (CampanaCanvas:
// metricasSimuladas) — agregadas aquí a nivel de ejecución completa (todos
// los segmentos/nodos), para que el historial no muestre nada que no esté
// ya en el canvas. duracionDias es la duración REAL del journey (del nodo
// día 0 al último, según la cadencia que devuelve el modelo — ver
// agente/prompts.py), nunca el tiempo que tardó en generarse la campaña.
function contarEstadisticas(resultados: ResultadoSegmento[]) {
  let entregados = 0;
  let abiertos = 0;
  let clics = 0;
  let ultimoDia = 0;
  const porCanal: Record<string, number> = {};

  for (const r of resultados) {
    const nodosSegmento = r.campana_creada?.nodos ?? [];
    const alcanceReal = extraerAlcanceKpis(r.plan?.resumen_kpis ?? []);

    for (const n of nodosSegmento) {
      const m = metricasSimuladas(r.clase, n.dia, n.canal, alcanceReal);
      entregados += m.entregados;
      abiertos += m.abiertos;
      clics += m.clics;
      porCanal[n.canal] = (porCanal[n.canal] ?? 0) + 1;
      ultimoDia = Math.max(ultimoDia, n.dia);
    }
  }

  const canalPrincipal = Object.entries(porCanal).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "-";
  const etiquetaCanal = ETIQUETA_CANAL[canalPrincipal] ?? canalPrincipal;

  return { entregados, abiertos, clics, canalPrincipal: etiquetaCanal, duracionDias: ultimoDia };
}

type Alcance = "base" | "cohorte";

export default function CampanasPage() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [seleccionado, setSeleccionado] = useState("");
  const [alcance, setAlcance] = useState<Alcance>("base");
  const [estado, setEstado] = useState<Estado>("idle");
  const [pasos, setPasos] = useState<PasoLog[]>([]);
  const [resultados, setResultados] = useState<ResultadoSegmento[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [historial, setHistorial] = useState<Ejecucion[]>(HISTORIAL_EJEMPLO);
  const resultadoRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getProductos()
      .then(setProductos)
      .catch(() => setError("No se pudo conectar con el motor."));
  }, []);

  // Las 2 tarjetas de campaña aparecen debajo del loader, fuera de la vista
  // inicial — sin este scroll, el jurado tiene que buscarlas manualmente.
  useEffect(() => {
    if (estado === "resultado") {
      resultadoRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [estado]);

  function manejarEvento(evento: EventoProceso, producto: string) {
    if (evento.tipo === "paso") {
      setPasos((prev) => [
        ...prev,
        {
          clase: evento.clase,
          categoria: evento.categoria,
          mensaje: evento.mensaje,
          listo: false,
        },
      ]);
    } else if (evento.tipo === "segmento_listo") {
      setPasos((prev) => prev.map((p) => (p.clase === evento.clase ? { ...p, listo: true } : p)));
    } else if (evento.tipo === "segmento_error") {
      setPasos((prev) => [
        ...prev,
        {
          clase: evento.clase,
          categoria: "revisar" as const,
          mensaje: `Error: ${evento.mensaje}`,
          listo: true,
        },
      ]);
    } else if (evento.tipo === "completado") {
      setResultados(evento.resultados);
      setEstado("resultado");
      const stats = contarEstadisticas(evento.resultados);
      const clientesAlcanzados = productos.find((p) => p.slug === producto)?.n_afiliados ?? 0;
      setHistorial((prev) => [
        {
          producto,
          fecha: new Date().toLocaleString("es-CO"),
          clientesAlcanzados,
          ...stats,
          estado: "completado",
        },
        ...prev,
      ]);
    } else if (evento.tipo === "error") {
      setError(evento.mensaje);
      setEstado("idle");
      setHistorial((prev) => [
        {
          producto,
          fecha: new Date().toLocaleString("es-CO"),
          clientesAlcanzados: 0,
          entregados: 0,
          abiertos: 0,
          clics: 0,
          canalPrincipal: "-",
          duracionDias: 0,
          estado: "error",
        },
        ...prev,
      ]);
    }
  }

  // Confirmación humana explícita antes de "enviar" — generar la campaña
  // (arriba) nunca la envía sola, ver salesforce_simulado.crear_campana en el
  // backend (real incluso en modo mock — ver agente/orquestador.py:
  // MODO_MOCK, la simulación de Salesforce nunca se mockea, solo el copy).
  // Devuelve enviada_en real (del backend) para que el canvas pueda mostrar
  // métricas honestas según cuánto tiempo pasó desde el envío real.
  function manejarEnviar(clase: number, producto: string) {
    return enviarCampana(clase, producto);
  }

  function ejecutar() {
    if (!seleccionado) return;
    setError(null);
    setPasos([]);
    setResultados([]);
    setEstado("procesando");
    procesarCampana(
      seleccionado,
      (evento) => manejarEvento(evento, seleccionado),
      (mensaje) => {
        setError(mensaje);
        setEstado("idle");
      }
    );
  }

  const productoActivo = productos.find((p) => p.slug === seleccionado);

  return (
    <div>
      <AvisoTemporada />
      <h1 className="text-3xl font-semibold text-[#0a0a0a] mb-8 tracking-tight">Campañas</h1>

      <div className="flex items-end gap-3 mb-6">
        <div className="w-72 shrink-0">
          <label className="block text-xs font-medium text-neutral-500 mb-1.5">Producto</label>
          <div className="relative">
            <select
              value={seleccionado}
              onChange={(e) => setSeleccionado(e.target.value)}
              disabled={estado === "procesando" || productos.length === 0}
              className="w-full appearance-none bg-white border border-black/10 rounded-lg pl-3 pr-9 py-2.5 text-sm text-[#0a0a0a] focus:outline-none focus:ring-2 focus:ring-[#0a0a0a]/15"
            >
              <option value="" disabled>
                Elegir producto
              </option>
              {productos.map((p) => (
                <option key={p.slug} value={p.slug}>
                  {p.nombre}
                </option>
              ))}
            </select>
            <HiChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
          </div>
        </div>
        <button
          onClick={ejecutar}
          disabled={!seleccionado || estado === "procesando" || alcance === "cohorte"}
          className="bg-[#0a0a0a] hover:bg-neutral-800 disabled:bg-neutral-200 disabled:text-neutral-400 disabled:cursor-not-allowed text-[#fffef7] font-medium rounded-lg px-5 py-2.5 text-sm transition-colors"
        >
          {estado === "procesando" ? "Creando..." : "Crear campaña"}
        </button>
      </div>

      {/* Alcance + estadísticas de vista previa solo tienen sentido ANTES de
          lanzar — una vez que se pidió "Crear campaña" (procesando o ya con
          resultado), ocultarlos: la campaña ya se lanzó sobre lo que se veía
          acá, mantenerlos visibles solo distrae de la campaña real. */}
      {estado === "idle" && (
        <>
          <div className="mb-6">
            <p className="text-xs font-medium text-neutral-500 mb-1.5">Alcance</p>
            <div className="inline-flex bg-black/5 rounded-lg p-1">
              <button
                type="button"
                onClick={() => setAlcance("base")}
                className={
                  alcance === "base"
                    ? "text-sm px-4 py-1.5 rounded-md bg-[#0a0a0a] text-[#fffef7] transition-all"
                    : "text-sm px-4 py-1.5 rounded-md text-neutral-500 hover:text-neutral-700 transition-all"
                }
              >
                Toda la base
              </button>
              <button
                type="button"
                onClick={() => setAlcance("cohorte")}
                className={
                  alcance === "cohorte"
                    ? "text-sm px-4 py-1.5 rounded-md bg-[#0a0a0a] text-[#fffef7] transition-all"
                    : "text-sm px-4 py-1.5 rounded-md text-neutral-500 hover:text-neutral-700 transition-all"
                }
              >
                Grupo específico
              </button>
            </div>
          </div>

          {alcance === "base" && productoActivo && (
            <>
              <div className="flex gap-3 mb-3">
                <div className="bg-white border border-black/10 rounded-lg px-4 py-3">
                  <p className="text-2xl font-semibold text-[#0a0a0a]">{productoActivo.n_afiliados.toLocaleString("es-CO")}</p>
                  <p className="text-xs text-neutral-500">clientes con interés real en {productoActivo.nombre}</p>
                </div>
                <div className="bg-white border border-black/10 rounded-lg px-4 py-3">
                  <p className="text-2xl font-semibold text-[#0a0a0a]">{CAMPANAS_FICTICIAS[productoActivo.slug] ?? 1}</p>
                  <p className="text-xs text-neutral-500">
                    campaña{(CAMPANAS_FICTICIAS[productoActivo.slug] ?? 1) === 1 ? "" : "s"} personalizada
                    {(CAMPANAS_FICTICIAS[productoActivo.slug] ?? 1) === 1 ? "" : "s"}, lista{(CAMPANAS_FICTICIAS[productoActivo.slug] ?? 1) === 1 ? "" : "s"} para lanzar
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 mb-8">
                <p className="text-xs text-neutral-400">Datos actualizados: 23 de julio de 2026</p>
                <label className="flex items-center gap-2 text-xs text-neutral-400 cursor-not-allowed">
                  <input type="checkbox" disabled className="rounded border-black/20" />
                  Sincronizar antes de ejecutar
                  <span className="shrink-0 whitespace-nowrap text-[10px] bg-neutral-100 text-neutral-400 px-2 py-0.5 rounded-full">
                    próximamente
                  </span>
                </label>
              </div>
            </>
          )}

          {/* TODO: cuando el filtro por atributos (Categoría/Rango de edad/Género/
              Ciudad/Grupo familiar/Situación laboral) se conecte de verdad a la
              API de Colsubsidio, quitar el badge "Próximamente" + este párrafo y
              habilitar los selects/botón "Sincronizar" de abajo (hoy disabled). */}
          {alcance === "cohorte" && (
            <div className="mb-8 bg-white border border-black/10 rounded-lg px-5 py-4">
              <div className="flex items-center gap-2 mb-4 bg-neutral-50 border border-black/10 rounded-lg px-3 py-2">
                <span className="text-[10px] font-medium bg-neutral-200 text-neutral-500 px-2 py-0.5 rounded-full shrink-0">
                  Próximamente
                </span>
                <p className="text-xs text-neutral-500">
                  Filtrado por atributos vía la API de Colsubsidio, disponible en una próxima versión.
                  Mientras tanto, las campañas se ejecutan sobre toda la base de afiliados.
                </p>
              </div>

              <div className="opacity-40 pointer-events-none cursor-not-allowed">
                <p className="text-xs font-medium text-neutral-500 mb-3">
                  Filtrar por atributos de la API de Colsubsidio
                </p>
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <select disabled className="bg-neutral-50 border border-black/10 rounded-lg px-3 py-2 text-sm text-neutral-400">
                    <option>Categoría</option>
                  </select>
                  <select disabled className="bg-neutral-50 border border-black/10 rounded-lg px-3 py-2 text-sm text-neutral-400">
                    <option>Rango de edad</option>
                  </select>
                  <select disabled className="bg-neutral-50 border border-black/10 rounded-lg px-3 py-2 text-sm text-neutral-400">
                    <option>Género</option>
                  </select>
                  <select disabled className="bg-neutral-50 border border-black/10 rounded-lg px-3 py-2 text-sm text-neutral-400">
                    <option>Ciudad</option>
                  </select>
                  <select disabled className="bg-neutral-50 border border-black/10 rounded-lg px-3 py-2 text-sm text-neutral-400">
                    <option>Grupo familiar</option>
                  </select>
                  <select disabled className="bg-neutral-50 border border-black/10 rounded-lg px-3 py-2 text-sm text-neutral-400">
                    <option>Situación laboral</option>
                  </select>
                </div>
                <button type="button" disabled className="flex items-center gap-2 bg-neutral-200 text-neutral-400 rounded-lg px-4 py-2 text-sm">
                  <HiArrowPath className="w-4 h-4" />
                  Sincronizar
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2.5 mb-6">
          {error}
        </p>
      )}

      {estado === "procesando" && <EscenarioProcesando pasos={pasos} />}
      {estado === "resultado" && (
        <div ref={resultadoRef}>
          <EscenarioResultado resultados={resultados} productos={productos} onEnviar={manejarEnviar} />
        </div>
      )}

      <div className="mt-24 pt-8 border-t border-black/10">
        <h2 className="text-base font-medium text-[#0a0a0a] mb-4">Historial de ejecuciones</h2>
        <div className="space-y-2">
          {historial.map((h, i) => (
            <div key={i} className="flex items-center gap-6 bg-white border border-black/10 rounded-lg px-4 py-3">
              <div className="w-40 shrink-0">
                <p className="text-sm text-[#0a0a0a] font-medium">{productos.find((p) => p.slug === h.producto)?.nombre ?? h.producto}</p>
                <p className="text-xs text-neutral-400">{h.fecha}</p>
              </div>

              {h.estado === "completado" ? (
                <div className="flex-1 grid grid-cols-6 gap-4">
                  <div>
                    <p className="text-xs text-neutral-400">Clientes alcanzados</p>
                    <p className="text-sm text-[#0a0a0a]">{h.clientesAlcanzados.toLocaleString("es-CO")}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-400">Entregados</p>
                    <p className="text-sm text-[#0a0a0a]">{h.entregados.toLocaleString("es-CO")}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-400">Abiertos</p>
                    <p className="text-sm text-[#0a0a0a]">{h.abiertos.toLocaleString("es-CO")}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-400">Clics</p>
                    <p className="text-sm text-[#0a0a0a]">{h.clics.toLocaleString("es-CO")}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-400">Canal principal</p>
                    <p className="text-sm text-[#0a0a0a]">{h.canalPrincipal}</p>
                  </div>
                  <div>
                    <p className="text-xs text-neutral-400">Duración</p>
                    <p className="text-sm text-[#0a0a0a]">{h.duracionDias} días</p>
                  </div>
                </div>
              ) : (
                <p className="flex-1 text-sm text-red-600">La ejecución no se pudo completar</p>
              )}

              <span
                className={
                  h.estado === "completado"
                    ? "shrink-0 text-xs px-2 py-1 rounded-full bg-emerald-50 text-emerald-700"
                    : "shrink-0 text-xs px-2 py-1 rounded-full bg-red-50 text-red-700"
                }
              >
                {h.estado === "completado" ? "generado" : "error"}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
