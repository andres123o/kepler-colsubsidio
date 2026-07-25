"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { HiXMark } from "react-icons/hi2";
import { getProximaTemporada, type ProximaTemporada } from "@/lib/api";

// Sugerencia proactiva para el equipo, no para el afiliado — lee la próxima
// temporada real del calendario colombiano (agente/contexto_segmento.py:
// proxima_temporada_relevante) y ya la traduce a una acción concreta (qué
// campaña preparar), no a etiquetas de interés abstractas. Hoy vive como una
// tarjeta en el dashboard; en el pitch se explica que esto alimentaría una
// alerta real hacia el canal de comunicación interna del equipo (ej. Slack).
export function AvisoTemporada() {
  const [temporada, setTemporada] = useState<ProximaTemporada | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    getProximaTemporada()
      .then((t) => {
        if (t.disponible) {
          setTemporada(t);
          setVisible(true);
        }
      })
      .catch(() => {});
  }, []);

  const nombresProductos = temporada?.productos_sugeridos?.map((p) => p.nombre) ?? [];
  const temporadaMinuscula = temporada?.temporada
    ? temporada.temporada.charAt(0).toLowerCase() + temporada.temporada.slice(1)
    : "";

  return (
    <AnimatePresence>
      {visible && temporada?.disponible && (
        <motion.div
          initial={{ x: 360, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 360, opacity: 0 }}
          transition={{ type: "spring", stiffness: 260, damping: 30 }}
          className="fixed top-6 right-6 z-50 w-72 rounded-xl shadow-[0_8px_30px_rgba(0,0,0,0.35)] p-4"
          style={{ background: "#2a1040" }}
        >
          <div className="flex items-start justify-between gap-2 mb-3">
            <p className="text-[10px] text-white/50 tracking-wide">Sugerencia</p>
            <button
              type="button"
              onClick={() => setVisible(false)}
              className="text-white/50 hover:text-white transition-colors shrink-0"
            >
              <HiXMark className="w-4 h-4" />
            </button>
          </div>

          <p className="text-sm text-white leading-relaxed">
            Faltan {temporada.dias_faltantes} días para {temporadaMinuscula}
            {nombresProductos.length > 0 && (
              <>
                ; lanzar ya una campaña de{" "}
                <span className="font-semibold">{nombresProductos.join(" y ")}</span> te adelanta a la demanda.
              </>
            )}
          </p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
