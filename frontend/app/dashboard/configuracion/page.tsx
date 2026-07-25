"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { getKB, actualizarKB, type KB } from "@/lib/api";

const PESTANAS: { clave: keyof KB; etiqueta: string }[] = [
  { clave: "productos", etiqueta: "Catálogo de productos" },
  { clave: "marca_voz", etiqueta: "Marca y voz" },
  { clave: "regulacion", etiqueta: "Regulación" },
];

export default function ConfiguracionPage() {
  const [kb, setKb] = useState<KB | null>(null);
  const [activa, setActiva] = useState<keyof KB>("productos");
  const [guardando, setGuardando] = useState(false);
  const [guardado, setGuardado] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getKB().then(setKb);
  }, []);

  if (!kb) {
    return <p className="text-sm text-neutral-500">Cargando KB...</p>;
  }

  async function guardar() {
    if (!kb) return;
    setGuardando(true);
    setGuardado(false);
    setError(null);
    try {
      await actualizarKB(activa, kb[activa]);
      setGuardado(true);
      setTimeout(() => setGuardado(false), 2000);
    } catch {
      setError("No se pudo guardar, intenta de nuevo.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-lg font-medium text-[#0a0a0a] mb-8">Configuración</h1>

      <div className="flex gap-1 mb-4 border-b border-black/10">
        {PESTANAS.map((p) => (
          <button
            key={p.clave}
            onClick={() => setActiva(p.clave)}
            className={clsx(
              "px-3.5 py-2 text-sm border-b-2 -mb-px transition-colors",
              activa === p.clave
                ? "border-[#0a0a0a] text-[#0a0a0a]"
                : "border-transparent text-neutral-500 hover:text-neutral-700"
            )}
          >
            {p.etiqueta}
          </button>
        ))}
      </div>

      <textarea
        value={kb[activa]}
        onChange={(e) => setKb({ ...kb, [activa]: e.target.value })}
        spellCheck={false}
        className="w-full h-[420px] bg-white border border-black/10 rounded-lg p-4 text-sm text-[#0a0a0a] font-mono leading-relaxed focus:outline-none focus:ring-2 focus:ring-[#0a0a0a]/15 resize-none"
      />

      <div className="flex items-center gap-3 mt-4">
        <button
          onClick={guardar}
          disabled={guardando}
          className="bg-[#0a0a0a] hover:bg-neutral-800 disabled:opacity-50 text-[#fffef7] font-semibold rounded-lg px-5 py-2 text-sm transition-colors"
        >
          {guardando ? "Guardando..." : "Guardar"}
        </button>
        {guardado && <span className="text-xs text-neutral-500">Guardado</span>}
      </div>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2.5 mt-4">
          {error}
        </p>
      )}
    </div>
  );
}
