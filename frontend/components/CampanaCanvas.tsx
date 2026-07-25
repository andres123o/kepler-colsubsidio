"use client";

import { useEffect, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { HiXMark, HiOutlinePencil } from "react-icons/hi2";
import clsx from "clsx";
import type { NodoCampana } from "@/lib/api";

// Canvas de campaña, mismo patrón que el de Trii/Kepler
// (kepler-frontend/app/(internal)/app/estrategia/page.tsx): flexbox vertical
// (nunca coordenadas x/y calculadas), pan/zoom hand-rolled con Pointer Events
// + wheel nativo, panel lateral deslizante para el detalle de un nodo. El
// texto de cada mensaje se puede editar en el panel (copia local, no escribe
// a ningún sistema real todavía). Tema claro monocromático (#0a0a0a sobre
// #FFFEF7/blanco), sin colores de marca de Colsubsidio.
//
// Regla de esta pantalla (encontrada probando con el usuario real): todo tiene
// que entenderse solo con mirarlo, sin que nadie lo explique. Por eso cada
// nodo muestra el texto real del mensaje (nunca la etapa interna del pipeline)
// y hay una leyenda fija arriba que dice qué es esto y qué hacer con el mouse.
//
// Este canvas es SOLO para revisar/editar antes de enviar (el "Cronograma").
// Una vez que la campaña ya se envió, la tarjeta (EscenarioResultado.tsx) deja
// de mostrar este canvas del todo y muestra en su lugar MetricasCampana.tsx —
// intentamos antes mezclar los dos estados en el mismo canvas (nodo por nodo,
// con "Programado"/rampa de tiempo) y era confuso e ilegible en vivo; más
// claro tener dos vistas separadas para dos momentos distintos.

export const ETIQUETA_CANAL: Record<string, string> = { whatsapp: "WhatsApp", push: "Push", email: "Email" };
// Los campos de copy vienen tal cual los devuelve el backend (mensaje, titulo,
// cuerpo, asunto, preheader) — mostrarlos en minúscula cruda se leía como
// nombre de variable interna, no como etiqueta para un humano.
const ETIQUETA_CAMPO: Record<string, string> = {
  mensaje: "Mensaje",
  titulo: "Título",
  cuerpo: "Cuerpo",
  asunto: "Asunto",
  preheader: "Preheader",
};
const ANCHO_NODO = 220;

// Benchmarks reales de industria por canal (Fiserv/Engage Hub, investigado en
// sesiones anteriores de este proyecto) — usados acá y también por
// MetricasCampana.tsx para la vista de gestión post-envío.
const RANGOS_ENTREGA: Record<string, [number, number]> = {
  whatsapp: [0.96, 0.99],
  push: [0.97, 0.995],
  email: [0.94, 0.98],
};
const RANGOS_APERTURA: Record<string, [number, number]> = {
  whatsapp: [0.85, 0.95],
  push: [0.2, 0.35],
  email: [0.18, 0.25],
};
const RANGOS_CLICK: Record<string, [number, number]> = {
  whatsapp: [0.15, 0.28],
  push: [0.1, 0.22],
  email: [0.15, 0.25],
};

function azarEstable(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

function enRango(seed: number, [min, max]: [number, number]): number {
  return min + azarEstable(seed) * (max - min);
}

export interface MetricasNodo {
  enviados: number;
  entregados: number;
  abiertos: number;
  clics: number;
}

export function metricasSimuladas(clase: number, dia: number, canal: string, alcance: number): MetricasNodo {
  const semilla = clase * 131 + dia * 17;
  const entregados = Math.round(alcance * enRango(semilla + 1, RANGOS_ENTREGA[canal] ?? [0.95, 0.98]));
  const abiertos = Math.round(entregados * enRango(semilla + 2, RANGOS_APERTURA[canal] ?? [0.2, 0.3]));
  const clics = Math.round(abiertos * enRango(semilla + 3, RANGOS_CLICK[canal] ?? [0.15, 0.25]));
  return { enviados: alcance, entregados, abiertos, clics };
}

// El primer campo que un humano leería de cada canal — lo que se ve en la
// tarjeta sin necesidad de abrir el panel.
function textoPrevio(nodo: NodoCampana): string {
  const primerValor = Object.values(nodo.copy)[0] ?? "";
  if (nodo.canal === "whatsapp") return nodo.copy.mensaje ?? primerValor;
  if (nodo.canal === "push") return nodo.copy.titulo ?? primerValor;
  if (nodo.canal === "email") return nodo.copy.asunto ?? primerValor;
  return primerValor;
}

function NodoInicio({ nombreProducto }: { nombreProducto: string }) {
  return (
    <div
      className="rounded-full bg-[#0a0a0a] text-white text-[11px] text-center px-4 py-1.5 tracking-wide"
      style={{ width: ANCHO_NODO }}
    >
      {nombreProducto}
    </div>
  );
}

function NodoObjetivo() {
  return (
    <div
      className="rounded-full border border-[#0a0a0a] text-[#0a0a0a] text-[11px] text-center px-4 py-1.5 tracking-wide"
      style={{ width: ANCHO_NODO }}
    >
      Meta
    </div>
  );
}

function Conector({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center" style={{ width: ANCHO_NODO }}>
      <div className="w-px h-5 bg-black/15" />
      {label && (
        <span className="text-[11px] text-neutral-700 bg-white px-2 py-0.5 rounded-full border border-black/10 -my-0.5 tracking-wide shrink-0">
          {label}
        </span>
      )}
      <div className="w-px h-5 bg-black/15" />
    </div>
  );
}

function NodoMensaje({
  nodo,
  seleccionado,
  onClick,
}: {
  nodo: NodoCampana;
  seleccionado: boolean;
  onClick: () => void;
}) {
  const aprobado = nodo.veredicto_gate_l2?.aprobado;

  return (
    <button
      type="button"
      data-no-drag
      onClick={onClick}
      className={clsx(
        "rounded-xl border bg-white text-left px-4 py-3 transition-shadow",
        seleccionado ? "border-[#0a0a0a] shadow-[0_0_0_3px_rgba(10,10,10,0.08)]" : "border-black/10 hover:border-black/25"
      )}
      style={{ width: ANCHO_NODO }}
    >
      <div className="flex items-center justify-between mb-1.5 gap-2">
        <span className="text-xs text-neutral-700 tracking-wide truncate">
          Día {nodo.dia} · {ETIQUETA_CANAL[nodo.canal] ?? nodo.canal}
        </span>
        <span
          className={clsx(
            "text-[9px] px-1.5 py-0.5 rounded-full shrink-0",
            aprobado ? "bg-black/[0.06] text-[#0a0a0a]" : "bg-neutral-100 text-neutral-500"
          )}
        >
          {aprobado ? "Listo" : "Revisar"}
        </span>
      </div>
      <p className="text-xs text-neutral-700 leading-snug line-clamp-2">{textoPrevio(nodo)}</p>
    </button>
  );
}

function ajustarAltura(el: HTMLTextAreaElement) {
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
}

function CampoEditable({ valor, onCambiar }: { valor: string; onCambiar: (valor: string) => void }) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const [guardado, setGuardado] = useState(false);
  const mostrar = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ocultar = useRef<ReturnType<typeof setTimeout> | null>(null);

  // La caja crece con el contenido en vez de mostrar scroll interno; push
  // y WhatsApp suelen pasarse de las 2-3 líneas fijas que tenía antes.
  useEffect(() => {
    if (ref.current) ajustarAltura(ref.current);
  }, [valor]);

  useEffect(
    () => () => {
      if (mostrar.current) clearTimeout(mostrar.current);
      if (ocultar.current) clearTimeout(ocultar.current);
    },
    []
  );

  return (
    <div className="relative">
      <textarea
        ref={ref}
        value={valor}
        onChange={(e) => {
          ajustarAltura(e.target);
          onCambiar(e.target.value);
          // No hay botón de guardar (edición en vivo); "Guardado" confirma
          // que el cambio quedó, ya que tampoco hay ninguna señal de que
          // este texto sea editable hasta hacer click directo encima.
          if (mostrar.current) clearTimeout(mostrar.current);
          if (ocultar.current) clearTimeout(ocultar.current);
          setGuardado(false);
          mostrar.current = setTimeout(() => {
            setGuardado(true);
            ocultar.current = setTimeout(() => setGuardado(false), 1500);
          }, 700);
        }}
        rows={1}
        className="w-full text-sm text-neutral-800 leading-relaxed bg-transparent border border-transparent hover:border-black/10 focus:border-black/20 focus:outline-none rounded-md px-1.5 py-1 -mx-1.5 resize-none overflow-hidden"
      />
      <AnimatePresence>
        {guardado && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute -bottom-5 left-0 text-xs font-medium text-neutral-600"
          >
            Guardado
          </motion.span>
        )}
      </AnimatePresence>
    </div>
  );
}

function PanelNodo({
  nodo,
  onCerrar,
  onCambiarCampo,
}: {
  nodo: NodoCampana;
  onCerrar: () => void;
  onCambiarCampo: (campo: string, valor: string) => void;
}) {
  const aprobado = nodo.veredicto_gate_l2?.aprobado;
  const problemas = nodo.veredicto_gate_l2?.problemas?.length
    ? nodo.veredicto_gate_l2.problemas
    : nodo.problemas_gate_l1;

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-neutral-700 tracking-wide">
          Día {nodo.dia} · {ETIQUETA_CANAL[nodo.canal] ?? nodo.canal}
        </p>
        <button
          type="button"
          onClick={onCerrar}
          className="text-neutral-500 hover:text-[#0a0a0a] transition-colors"
        >
          <HiXMark className="w-5 h-5" />
        </button>
      </div>
      <p className="text-sm text-neutral-700 mb-4 leading-relaxed">
        <span className="font-medium text-neutral-900 tracking-wide">Por qué: </span>
        {nodo.angulo_asignado}
      </p>

      <div className="space-y-3 mb-4">
        {Object.entries(nodo.copy).map(([campo, valor]) => (
          <div key={campo}>
            <p className="flex items-center gap-1.5 text-xs font-medium text-neutral-600 mb-1 tracking-wide">
              {ETIQUETA_CAMPO[campo] ?? campo}
              <HiOutlinePencil className="w-3.5 h-3.5 text-neutral-500" />
            </p>
            <CampoEditable valor={valor} onCambiar={(nuevoValor) => onCambiarCampo(campo, nuevoValor)} />
          </div>
        ))}
      </div>

      <div
        className={clsx(
          "text-xs px-2.5 py-2 rounded-md leading-relaxed",
          aprobado ? "bg-black/[0.04] text-neutral-700" : "bg-neutral-100 text-neutral-700"
        )}
      >
        {aprobado ? "Aprobado por el revisor de calidad." : `Revisión sugerida: ${problemas?.join(", ") || "sin detalle."}`}
      </div>
    </div>
  );
}

export function CampanaCanvas({
  nodos,
  nombreProducto,
}: {
  nodos: NodoCampana[];
  nombreProducto: string;
}) {
  const [zoom, setZoom] = useState(0.9);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [diaSeleccionado, setDiaSeleccionado] = useState<number | null>(null);
  // Copia editable local — si quieren ajustar el texto de un mensaje, se
  // edita acá mismo en el panel, sin depender de ningún sistema externo.
  const [nodosEditables, setNodosEditables] = useState<NodoCampana[]>(nodos);
  const contenedorRef = useRef<HTMLDivElement>(null);
  const contenidoRef = useRef<HTMLDivElement>(null);
  const arrastre = useRef({ activo: false, arrastro: false, startX: 0, startY: 0, panX: 0, panY: 0 });

  useEffect(() => {
    setNodosEditables(nodos);
  }, [nodos]);

  // El zoom inicial fijo (0.9) no ajustaba según cuántos mensajes/días tiene
  // la campaña — en journeys más largos el nodo "Meta" quedaba fuera de los
  // 420px visibles y nadie lo encontraba (bug real: jurado nunca lo vio).
  // scrollHeight no lo afecta el transform:scale (es medida de layout, no de
  // pintura), así que se puede leer sin importar el zoom actual.
  useEffect(() => {
    const el = contenidoRef.current;
    if (!el) return;
    const ALTO_VISIBLE = 420 - 48; // deja algo de aire arriba/abajo
    const alturaNatural = el.scrollHeight;
    if (alturaNatural <= 0) return;
    const ajustado = Math.min(0.9, ALTO_VISIBLE / alturaNatural);
    setZoom(Math.max(0.35, ajustado));
    setPan({ x: 0, y: 0 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodosEditables.length]);

  function cambiarCampoCopy(dia: number, campo: string, valor: string) {
    setNodosEditables((actual) =>
      actual.map((n) => (n.dia === dia ? { ...n, copy: { ...n.copy, [campo]: valor } } : n))
    );
  }

  useEffect(() => {
    const el = contenedorRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      if ((e.target as HTMLElement).closest("[data-no-drag]")) return;
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.08 : 0.92;
      setZoom((z) => Math.min(1.6, Math.max(0.5, z * factor)));
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  function onPointerDown(e: ReactPointerEvent<HTMLDivElement>) {
    // Siempre resetea "arrastro" acá, incluso al arrancar sobre un nodo: si no,
    // después del primer pan real del canvas, arrastro queda en true para
    // siempre (el pointerdown sobre un botón nunca llegaba a resetearlo) y
    // todos los clicks a nodos quedan bloqueados sin poder abrir el panel.
    const esControl = !!(e.target as HTMLElement).closest("[data-no-drag]");
    arrastre.current = { activo: !esControl, arrastro: false, startX: e.clientX, startY: e.clientY, panX: pan.x, panY: pan.y };
  }
  function onPointerMove(e: ReactPointerEvent<HTMLDivElement>) {
    if (!arrastre.current.activo) return;
    const dx = e.clientX - arrastre.current.startX;
    const dy = e.clientY - arrastre.current.startY;
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) arrastre.current.arrastro = true;
    setPan({ x: arrastre.current.panX + dx, y: arrastre.current.panY + dy });
  }
  function onPointerUp() {
    arrastre.current.activo = false;
  }

  const nodoSeleccionado = diaSeleccionado !== null ? nodosEditables.find((n) => n.dia === diaSeleccionado) : undefined;
  const duracionTotal = nodosEditables.length > 0 ? nodosEditables[nodosEditables.length - 1].dia : 0;

  return (
    <div>
      <p className="text-xs text-neutral-600 tracking-wide mb-2">Cronograma · {duracionTotal} días</p>

      <div
        ref={contenedorRef}
        className="relative w-full h-[420px] rounded-lg border border-black/10 overflow-hidden cursor-grab active:cursor-grabbing select-none"
        style={{
          background: "#FFFEF7",
          backgroundImage: "radial-gradient(rgba(10,10,10,0.09) 1px, transparent 1px)",
          backgroundSize: "20px 20px",
        }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
      >
        <div
          ref={contenidoRef}
          className="flex flex-col items-center pt-8 pb-8"
          style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: "top center" }}
        >
          <NodoInicio nombreProducto={nombreProducto} />
          {nodosEditables.map((nodo, i) => (
            <div key={nodo.dia} className="flex flex-col items-center">
              <Conector label={i === 0 ? `Día ${nodo.dia}` : `+${nodo.dia - nodosEditables[i - 1].dia} días`} />
              <NodoMensaje
                nodo={nodo}
                seleccionado={diaSeleccionado === nodo.dia}
                onClick={() => {
                  if (arrastre.current.arrastro) return;
                  setDiaSeleccionado((actual) => (actual === nodo.dia ? null : nodo.dia));
                }}
              />
            </div>
          ))}
          <Conector />
          <NodoObjetivo />
        </div>

        <AnimatePresence>
          {nodoSeleccionado && (
            <motion.div
              data-no-drag
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", stiffness: 320, damping: 32 }}
              className="absolute top-0 right-0 h-full w-72 bg-white border-l border-black/10 p-4 overflow-y-auto"
            >
              <PanelNodo
                nodo={nodoSeleccionado}
                onCerrar={() => setDiaSeleccionado(null)}
                onCambiarCampo={(campo, valor) => cambiarCampoCopy(nodoSeleccionado.dia, campo, valor)}
              />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="absolute bottom-2 left-2 text-xs text-neutral-600 pointer-events-none">
          Arrastra · zoom
        </div>
      </div>
    </div>
  );
}
