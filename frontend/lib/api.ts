const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export interface Producto {
  slug: string;
  nombre: string;
  n_segmentos: number;
  n_afiliados: number;
}

export interface KPI {
  etiqueta: string;
  valor: string;
  tipo: "neutro" | "oportunidad" | "riesgo";
}

export interface NodoCampana {
  dia: number;
  etapa: string;
  angulo_asignado: string;
  canal: "whatsapp" | "push" | "email";
  copy: Record<string, string>;
  problemas_gate_l1: string[];
  veredicto_gate_l2: { aprobado: boolean; problemas: string[]; sugerencia_breve?: string };
}

export type EstadoEnvio = "borrador" | "enviada";

export interface ResultadoSegmento {
  clase: number;
  producto: string;
  // Nombre humano de la audiencia (ej. "Viajes", "Educación de los hijos") —
  // esto identifica la campaña en la interfaz, nunca "Grupo N" ni la clase interna.
  interes_dominante?: string;
  perfil?: string;
  tono_comunicacion?: string;
  plan?: { resumen?: string; resumen_kpis?: KPI[] };
  campana_creada?: { nodos: NodoCampana[]; estado_envio?: EstadoEnvio; enviada_en?: string | null };
  error?: string;
}

// Alcance real de un segmento, leído del KPI "Alcance real" que arma el
// backend (agente/datos_mock.py: resumen_mock / claude_client.py) — mismo
// parseo que antes estaba copiado en dashboard/page.tsx y EscenarioResultado.tsx.
export function extraerAlcanceKpis(kpis: KPI[]): number {
  return Number(kpis.find((k) => /alcance/i.test(k.etiqueta))?.valor.replace(/[^\d]/g, "") || 0);
}

// Cada paso real del pipeline (backend: agente/orquestador.py, dict _PASOS) —
// define qué animación muestra PasoAnimacion, nunca se le muestra al usuario
// el nombre de función ni la clase interna.
export type CategoriaPaso = "investigar" | "analizar" | "planear" | "escribir" | "pulir" | "revisar" | "listo";

// Orden real de los pasos del pipeline (agente/orquestador.py) — se usa para
// calcular el progreso del loader (paso N de 6), no solo para mostrar el texto.
export const ORDEN_PASOS: CategoriaPaso[] = ["investigar", "analizar", "planear", "escribir", "pulir", "revisar"];

export const TEXTO_PASO: Record<CategoriaPaso, string> = {
  investigar: "Buscando actualidad",
  analizar: "Analizando el grupo",
  planear: "Planeando mensajes",
  escribir: "Escribiendo la campaña",
  pulir: "Puliendo el tono",
  revisar: "Revisando calidad",
  listo: "Campaña lista",
};

export type EventoProceso =
  | { tipo: "inicio"; producto: string; segmentos: number[] }
  | { tipo: "paso"; clase: number; categoria: CategoriaPaso; mensaje: string; grupo: number; total_grupos: number }
  | { tipo: "segmento_listo"; clase: number; perfil: string }
  | { tipo: "segmento_error"; clase: number; mensaje: string }
  | { tipo: "completado"; resultados: ResultadoSegmento[] }
  | { tipo: "error"; mensaje: string };

export async function getProductos(): Promise<Producto[]> {
  const res = await fetch(`${BACKEND_URL}/api/productos`);
  if (!res.ok) throw new Error("No se pudo cargar el catálogo de productos");
  const data = await res.json();
  return data.productos;
}

export function procesarCampana(
  producto: string,
  onEvento: (evento: EventoProceso) => void,
  onError: (mensaje: string) => void
): () => void {
  const url = `${BACKEND_URL}/api/campanas/procesar?producto=${encodeURIComponent(producto)}`;
  const es = new EventSource(url);

  es.onmessage = (msg) => {
    const evento = JSON.parse(msg.data) as EventoProceso;
    onEvento(evento);
    if (evento.tipo === "completado" || evento.tipo === "error") {
      es.close();
    }
  };

  es.onerror = () => {
    onError("Se perdió la conexión con el motor.");
    es.close();
  };

  return () => es.close();
}

export async function enviarCampana(clase: number, producto: string): Promise<{ estado_envio: EstadoEnvio; enviada_en: string }> {
  const url = `${BACKEND_URL}/api/campanas/enviar?clase=${clase}&producto=${encodeURIComponent(producto)}`;
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) throw new Error("No se pudo enviar la campaña");
  return res.json();
}

export interface ProximaTemporada {
  disponible: boolean;
  temporada?: string;
  fecha?: string;
  dias_faltantes?: number;
  intereses_relevantes?: string[];
  productos_sugeridos?: { slug: string; nombre: string }[];
}

export async function getProximaTemporada(): Promise<ProximaTemporada> {
  const res = await fetch(`${BACKEND_URL}/api/sugerencias/proxima-temporada`);
  if (!res.ok) throw new Error("No se pudo cargar la sugerencia de temporada");
  return res.json();
}

export interface KB {
  productos: string;
  marca_voz: string;
  regulacion: string;
}

export async function getKB(): Promise<KB> {
  const res = await fetch(`${BACKEND_URL}/api/kb`);
  if (!res.ok) throw new Error("No se pudo cargar la KB");
  return res.json();
}

export async function actualizarKB(clave: keyof KB, contenido: string): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/api/kb`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ clave, contenido }),
  });
  if (!res.ok) throw new Error("No se pudo guardar la KB");
}
