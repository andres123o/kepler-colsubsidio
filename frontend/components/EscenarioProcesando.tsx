"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ORDEN_PASOS, type CategoriaPaso } from "@/lib/api";
import { LoaderElegante } from "./LoaderElegante";

export interface PasoLog {
  clase: number;
  categoria: CategoriaPaso;
  mensaje: string;
  listo: boolean;
}

// Un solo loader compartido para todo el lote (nunca uno por grupo, aunque
// haya 2 corriendo en paralelo detrás) — ocupa el ancho completo del panel,
// centrado, en vez de columnas lado a lado.
export function EscenarioProcesando({ pasos }: { pasos: PasoLog[] }) {
  const ultimoPaso = pasos[pasos.length - 1];
  const indicePaso = ultimoPaso ? ORDEN_PASOS.indexOf(ultimoPaso.categoria) : -1;
  const progreso = ultimoPaso?.listo ? 1 : indicePaso >= 0 ? (indicePaso + 1) / ORDEN_PASOS.length : 0;

  return (
    <div className="w-full flex flex-col items-center justify-center gap-4 py-16">
      <LoaderElegante listo={ultimoPaso?.listo ?? false} />

      <AnimatePresence mode="wait">
        <motion.p
          key={ultimoPaso?.mensaje ?? "esperando"}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="text-sm text-neutral-700"
        >
          {ultimoPaso?.mensaje ?? "Preparando..."}
        </motion.p>
      </AnimatePresence>

      <div className="w-48 h-[2px] rounded-full bg-black/[0.06] overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-[#0a0a0a]/50"
          animate={{ width: `${progreso * 100}%` }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
