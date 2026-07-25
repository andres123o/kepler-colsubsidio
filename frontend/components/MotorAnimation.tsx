"use client";

// Réplica exacta del mecanismo de las 2 animaciones reales de Kepler Prospection
// (kepler-frontend/app/prospection/{klar,KOA}/S2Scroll.tsx, componentes Panel0 y
// Panel2) — mismo terminal tipeado línea a línea + mismo mockup de iPhone con
// notificaciones apiladas. Se quitó SOLO el scroll-tracking (acá no hay scroll,
// es un panel fijo de login) y se cambió el contenido de las líneas/mensajes
// por datos reales de este proyecto (Colombia/Colsubsidio, no México/Klar).

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

const orange = "#FF8C00";
const green = "#22C55E";
const white = "#FFFFFF";
const MONO = `'SF Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace`;

function lc(type: string) {
  const m: Record<string, string> = {
    cmd: orange,
    ok: green,
    wait: "rgba(255,255,255,0.35)",
    info: "rgba(255,255,255,0.42)",
    section: "rgba(255,255,255,0.65)",
    data: "rgba(255,255,255,0.48)",
    quote: "rgba(255,255,255,0.6)",
    meta: "rgba(255,255,255,0.36)",
    hi: "#C2185B",
    run: "rgba(255,255,255,0.48)",
    bar: orange,
    div: "rgba(255,255,255,0.16)",
    res: "#ffffff",
    sub: "rgba(255,255,255,0.52)",
  };
  return m[type] ?? "rgba(255,255,255,0.3)";
}

const LINES: Array<{ text: string; type: string; d: number }> = [
  { text: "$ kepler predict --colsubsidio --target credito --demo", type: "cmd", d: 55 },
  { text: "", type: "blank", d: 32 },
  { text: "  [init]  segmentación LCA · 12 clases reales ............ OK", type: "ok", d: 26 },
  { text: "  [init]  scorer aditivo glass-box · elegibilidad ......... OK", type: "ok", d: 24 },
  { text: "  [init]  θ_k canal + interés + macro + calendario ........ OK", type: "ok", d: 22 },
  { text: "", type: "blank", d: 32 },
  { text: "  [fetch] Perplexity · actualidad real del segmento ......  ", type: "wait", d: 480 },
  { text: "  [fetch] › tasa BanRep + TES + inflación (DANE) .............  ", type: "wait", d: 180 },
  { text: "  [fetch] › calendario Colsubsidio (Feria de Vivienda) .......  ", type: "wait", d: 170 },
  { text: "  [fetch] Perplexity + BanRep / DANE · listo .............. OK", type: "ok", d: 50 },
  { text: "", type: "blank", d: 32 },
  { text: "PIPELINE DEL AGENTE (4 pasos + 2 gates) ────────────────────", type: "section", d: 60 },
  { text: "  1. analista_segmento ......... ángulo + estado mental", type: "quote", d: 175 },
  { text: "  2. planificador_cadencia ..... día 0 · día 3 · día 7", type: "quote", d: 165 },
  { text: "  3. copywriter + humanizador ... copy por canal, tono real", type: "quote", d: 160 },
  { text: "  gate L1 (reglas) + gate L2 (juez LLM) ... antes de enviar", type: "meta", d: 60 },
  { text: "", type: "blank", d: 32 },
  { text: "  escribiendo campaña, segmento por segmento .............", type: "run", d: 480 },
  { text: "  ▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  15%              ", type: "bar", d: 62 },
  { text: "  ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░  33%              ", type: "bar", d: 54 },
  { text: "  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░  56%              ", type: "bar", d: 45 },
  { text: "  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░  78%              ", type: "bar", d: 36 },
  { text: "  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  100%  ✓ done    ", type: "bar", d: 30 },
  { text: "", type: "blank", d: 52 },
  { text: "─────────────────────────────────────────────────────────", type: "div", d: 26 },
  { text: "  1 segmento  →  1 campaña  →  1 producto por persona     ", type: "res", d: 420 },
  { text: "  nunca dos campañas a la vez sobre el mismo afiliado      ", type: "sub", d: 150 },
  { text: "─────────────────────────────────────────────────────────", type: "div", d: 26 },
];

function Terminal({ onCompleto }: { onCompleto: () => void }) {
  const [visible, setVisible] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (visible >= LINES.length) {
      const t = setTimeout(onCompleto, 2600);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setVisible((v) => v + 1), LINES[visible].d);
    return () => clearTimeout(t);
  }, [visible, onCompleto]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [visible]);

  return (
    <div style={{ width: "100%", height: "78vh", background: "#0d1117", borderRadius: 16, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ padding: "12px 20px", borderBottom: "1px solid rgba(255,255,255,0.07)", display: "flex", alignItems: "center", gap: 7, flexShrink: 0, background: "#161b22" }}>
        <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ff5f57" }} />
        <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#febc2e" }} />
        <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#28c840" }} />
        <span style={{ marginLeft: 14, color: "rgba(255,255,255,0.2)", fontSize: 11.5, fontFamily: MONO, letterSpacing: "0.02em" }}>
          kepler@model — bash
        </span>
      </div>

      <style>{`#colsub-term::-webkit-scrollbar{display:none}`}</style>
      <div
        id="colsub-term"
        ref={scrollRef}
        style={{
          padding: "18px 16px 18px 24px",
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          fontFamily: MONO,
          fontSize: 11.5,
          lineHeight: 1.75,
          scrollBehavior: "smooth",
          msOverflowStyle: "none",
          scrollbarWidth: "none",
        } as React.CSSProperties}
      >
        {LINES.slice(0, visible).map((line, i) => (
          <div key={i} style={{ color: lc(line.type), whiteSpace: "pre", letterSpacing: "0.01em" }}>
            {line.text || " "}
          </div>
        ))}
        {visible < LINES.length && (
          <motion.span
            style={{ display: "inline-block", width: 6, height: 13, background: orange, verticalAlign: "text-bottom" }}
            animate={{ opacity: [1, 0, 1] }}
            transition={{ duration: 0.85, repeat: Infinity, ease: "linear" }}
          />
        )}
      </div>
    </div>
  );
}

type Canal = "push" | "whatsapp" | "email";
// 3 combinaciones producto + interés real de la persona, una sola idea por
// mensaje (no 3-4 ideas apiladas): push=libre inversión/viaje (joven
// aspiracional), whatsapp=educativo/graduación (mamá), email=crédito mujer
// — hoy vive dentro de Consumo General en el catálogo real — para
// emprendedora con interés en tecnología.
const NOTIFICACIONES: Array<{ canal: Canal; titulo: string; texto: string }> = [
  {
    canal: "push",
    titulo: "Colsubsidio",
    texto: "Ese viaje que quieres hacer, hazlo real con un crédito de libre inversión.",
  },
  {
    canal: "whatsapp",
    titulo: "Colsubsidio",
    texto: "Hola, sabemos que tu hijo se gradúa pronto. Para que continúe su rumbo profesional, tenemos créditos educativos.",
  },
  {
    canal: "email",
    titulo: "Gmail",
    texto: "Para impulsar tu negocio o renovar tu equipo, tenemos un crédito pensado para emprendedoras como tú.",
  },
];

function IconoCanal({ canal }: { canal: Canal }) {
  if (canal === "whatsapp") {
    return (
      <div style={{ width: 22, height: 22, borderRadius: 6, background: "#25D366", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="#ffffff">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
        </svg>
      </div>
    );
  }
  if (canal === "email") {
    return (
      <div style={{ width: 22, height: 22, borderRadius: 6, background: "#ffffff", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <svg width="16" height="13" viewBox="0 0 20 15" fill="none">
          <rect x="1" y="1" width="18" height="13" rx="1.5" fill="#ffffff" stroke="#EA4335" strokeWidth="1.4" />
          <path d="M1.8 2 10 9l8.2-7" stroke="#EA4335" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    );
  }
  return (
    <div style={{ width: 22, height: 22, borderRadius: 6, overflow: "hidden", flexShrink: 0, background: "#ffffff" }}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/logo-colsubsidio.png" alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
    </div>
  );
}

function Telefono({ onCompleto }: { onCompleto: () => void }) {
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const t1 = setTimeout(() => setShown(true), 200);
    const t2 = setTimeout(onCompleto, 200 + 0.6 * 1000 + NOTIFICACIONES.length * 1400 + 2600);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [onCompleto]);

  // Carcasa completa (cuerpo #1c1c1e + botones laterales + pantalla inset),
  // calcada tal cual de /prospection/KOA — misma posición/tamaño que ya
  // tenía (translateY(24%), centrado abajo), solo restaurando lo que se le
  // había quitado.
  return (
    <div style={{ display: "flex", width: "100%", height: "100%", alignItems: "flex-end", justifyContent: "center", overflow: "hidden" }}>
      <div
        style={{
          width: 380,
          height: 787,
          background: "#1c1c1e",
          borderRadius: 58,
          border: "1px solid rgba(255,255,255,0.09)",
          position: "relative",
          flexShrink: 0,
          transform: "translateY(24%)",
        }}
      >
        <div style={{ position: "absolute", left: -4, top: 175, width: 4, height: 33, background: "rgba(255,255,255,0.18)", borderRadius: "2px 0 0 2px" }} />
        <div style={{ position: "absolute", left: -4, top: 226, width: 4, height: 46, background: "rgba(255,255,255,0.18)", borderRadius: "2px 0 0 2px" }} />
        <div style={{ position: "absolute", left: -4, top: 287, width: 4, height: 46, background: "rgba(255,255,255,0.18)", borderRadius: "2px 0 0 2px" }} />
        <div style={{ position: "absolute", right: -4, top: 252, width: 4, height: 72, background: "rgba(255,255,255,0.18)", borderRadius: "0 2px 2px 0" }} />

        <div style={{ position: "absolute", inset: 13, background: "linear-gradient(165deg, #4A0072 0%, #2A1040 45%, #14081f 100%)", borderRadius: 46, overflow: "hidden" }}>
          <div style={{ position: "absolute", top: 16, left: "50%", transform: "translateX(-50%)", width: 114, height: 30, background: "#0a0a0a", borderRadius: 15, zIndex: 10 }} />

          <div style={{ padding: "66px 18px 22px" }}>
            <div style={{ textAlign: "center", marginBottom: 28 }}>
              <p style={{ color: "rgba(255,255,255,0.9)", fontSize: 66, fontWeight: 200, letterSpacing: "-0.03em", lineHeight: 1, margin: "0 0 6px" }}>9:41</p>
              <p style={{ color: "rgba(255,255,255,0.38)", fontSize: 15, margin: 0 }}>Viernes, 24 de julio</p>
            </div>

            {NOTIFICACIONES.map((n, i) => (
              <motion.div
                key={n.canal}
                initial={{ opacity: 0, y: -18 }}
                animate={shown ? { opacity: 1, y: 0 } : { opacity: 0, y: -18 }}
                transition={{ duration: 0.55, delay: shown ? 0.6 + i * 1.4 : 0, ease: "easeOut" }}
                style={{ background: "rgba(255,255,255,0.07)", borderRadius: 18, padding: "13px 15px", marginBottom: 10 }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <IconoCanal canal={n.canal} />
                  <span style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, fontWeight: 600 }}>{n.titulo}</span>
                  <span style={{ color: "rgba(255,255,255,0.22)", fontSize: 11, marginLeft: "auto" }}>ahora</span>
                </div>
                <p style={{ color: "rgba(255,255,255,0.84)", fontSize: 13, lineHeight: 1.5, margin: 0 }}>{n.texto}</p>
              </motion.div>
            ))}
          </div>
        </div>

        <div style={{ position: "absolute", bottom: 12, left: "50%", transform: "translateX(-50%)", width: 126, height: 5, background: "rgba(255,255,255,0.22)", borderRadius: 3 }} />
      </div>
    </div>
  );
}

export function MotorAnimation() {
  const [fase, setFase] = useState<"terminal" | "telefono">("terminal");
  const fondo = fase === "terminal" ? "#2a1040" : "#0a0a0a";
  // El terminal es una tarjeta flotante — necesita margen alrededor. La
  // pantalla del teléfono NO — su borde de abajo tiene que tocar el borde
  // real del panel, sin padding-bottom dejando una franja de fondo visible.
  const padding = fase === "terminal" ? "48px 40px" : "0px";

  return (
    <div style={{ width: "100%", height: "100%", background: fondo, transition: "background-color 0.8s ease", display: "flex", alignItems: "center", justifyContent: "center", padding, overflow: "hidden" }}>
      {fase === "terminal" ? (
        <Terminal onCompleto={() => setFase("telefono")} />
      ) : (
        <Telefono onCompleto={() => setFase("terminal")} />
      )}
    </div>
  );
}
