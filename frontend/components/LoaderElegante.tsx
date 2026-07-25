"use client";

import { motion } from "framer-motion";

const TINTA = "#0a0a0a";

// Un solo loader, siempre la misma identidad visual mientras corre (nunca
// cambia de forma por paso ni por acción — solo la palabra de al lado cambia).
// Se reusa tanto en "procesando" (grande) como en la confirmación de "enviar"
// (chico, en el mismo lugar donde estaba el botón) para que sea el mismo
// lenguaje visual: aro fino que gira + un orbe que respira, easing suave. Al
// terminar, el orbe se resuelve en un check trazado.
export function LoaderElegante({ listo, size = 56 }: { listo: boolean; size?: number }) {
  const nucleo = size * 0.43;
  const check = size * 0.25;

  return (
    <div className="relative flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
      {!listo && (
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{ border: `${Math.max(1.2, size * 0.027)}px solid rgba(10,10,10,0.10)`, borderTopColor: "rgba(10,10,10,0.55)" }}
          animate={{ rotate: 360 }}
          transition={{ duration: 1.7, repeat: Infinity, ease: "linear" }}
        />
      )}

      <motion.div
        className="rounded-full"
        style={{
          width: nucleo,
          height: nucleo,
          background: listo ? TINTA : `radial-gradient(circle, rgba(10,10,10,0.6), rgba(10,10,10,0.05) 72%)`,
        }}
        animate={
          listo
            ? { scale: 1, opacity: 1 }
            : { scale: [1, 1.16, 1], opacity: [0.55, 0.95, 0.55] }
        }
        transition={
          listo
            ? { duration: 0.45, ease: "easeOut" }
            : { duration: 2.1, repeat: Infinity, ease: "easeInOut" }
        }
      />

      {listo && (
        <svg viewBox="0 0 24 24" className="absolute" style={{ width: check, height: check }}>
          <motion.path
            d="M5 12.5 L10 17 L19 7"
            fill="none"
            stroke="#FFFEF7"
            strokeWidth="2.6"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 0.35, delay: 0.15, ease: "easeOut" }}
          />
        </svg>
      )}
    </div>
  );
}
