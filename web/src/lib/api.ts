// Cliente de la API de CotIA (contrato en /docs). La clave de OpenRouter solo viaja en POST /api/consultas.

export type Etapa =
    | "en_cola"
    | "inicio"
    | "interpretacion"
    | "plan"
    | "lecturas"
    | "emparejamiento"
    | "propuesta"
    | "fin";
export const ETAPAS: Etapa[] = [
    "en_cola",
    "inicio",
    "interpretacion",
    "plan",
    "lecturas",
    "emparejamiento",
    "propuesta",
    "fin",
];

export type Evento = { etapa: Etapa; [k: string]: any };

export type Defensas = {
    separacion_planos: boolean;
    clasificador: boolean;
    precio: boolean;
    umbral: number;
};

export type Procedencia = {
    fuente: string;
    tipo_fuente: string;
    consulta: string;
    marca_tiempo: string;
    fragmento_original: string;
    ruta_extraccion: string;
    modelo_extraccion: string | null;
    suma_verificacion: string;
};

export type Oferta = {
    titulo: string;
    precio: number;
    moneda: string;
    gtin: string | null;
    marca: string | null;
    modelo: string | null;
    disponibilidad: "en_stock" | "bajo_pedido" | "agotado" | "desconocida";
    costo_envio: number | null;
    plazo_entrega_dias: number | null;
    url_detalle: string | null;
    producto_catalogo: string | null;
    verificacion: "verificada" | "discrepancia" | "sin_contraparte" | null;
    procedencia: Procedencia;
};

export type Alerta = { tipo: string; mensaje: string; oferta: number | null };

export type Propuesta = {
    consulta: string;
    perfil: string;
    ofertas: Oferta[];
    recomendada: number | null;
    justificacion: string;
    abstencion: boolean;
    motivo_abstencion: string | null;
    alertas: Alerta[];
    modelo: string | null;
    costo_usd: number;
};

export type Resumen = {
    id: string;
    consulta: string;
    corpus: string;
    carga: string | null;
    modelo: string;
    opciones: Record<string, any>;
    estado: string;
    costo_usd: number;
    segundos: number | null;
    creada: string;
};

export type Detalle = Resumen & {
    propuesta: Propuesta | null;
    detalle: Record<string, any> | null;
    error: string | null;
};

export type Modelo = {
    nombre: string;
    etiqueta: string;
    id_modelo: string;
    costo_usd: number;
    segundos: number;
    acierto?: boolean;
    m2_e3: { m2_media: number; m2_bajo: number; m2_alto: number } | null;
};

export type Clasificador = {
    etiqueta: string;
    descripcion: string;
    licencia: string;
    latencia_p50_ms: number;
    idiomas: string;
};

export type Catalogo = {
    modelos: Modelo[];
    por_defecto: string | null;
    clasificadores: Record<string, Clasificador>;
    clasificador_por_defecto: string;
};

export type Ejemplos = {
    b: { categoria: string; consulta: string }[];
    a: { categoria: string; consulta: string }[];
    laboratorio: {
        carga: string;
        clase: string;
        ubicacion: string;
        proveedor: string;
        archivo: string;
        consulta: string;
    }[];
};

export type FuenteCorpus = {
    id: string;
    nombre: string;
    tipo_fuente: string;
    archivos: string[];
};
export type AtaqueCorpus = {
    carga: string;
    clase: string;
    ubicacion: string;
    proveedor: string;
    archivo: string;
    objetivo: string;
    texto: string;
    disponible: boolean;
};
export type IndiceCorpus = {
    corpus: { b: FuenteCorpus[]; a: FuenteCorpus[] };
    ataques: AtaqueCorpus[];
};

export type PeticionConsulta = {
    consulta?: string;
    corpus: Grupo;
    carga?: string;
    modelo: string;
    defensas: Defensas;
    clasificador: string;
    verificar: boolean;
    politica_n3: "abstener" | "excluir";
};

// Lista blanca por visitante (D113)
export type Grupo = "vivo" | "a" | "b";
export type FuenteLista = {
    id: string;
    nombre: string;
    tipo_fuente: string;
    url: string;
    origen: "corpus" | "vivo" | "usuario";
    activa: boolean;
    eliminable: boolean;
};
export type ListaBlanca = {
    grupos: { id: Grupo; nombre: string; fuentes: FuenteLista[] }[];
    limites: { urls: number; pdfs: number; mb_pdf: number };
};

export class ErrorApi extends Error {
    constructor(
        public estado: number,
        mensaje: string,
    ) {
        super(mensaje);
    }
}

async function leer<T>(r: Response): Promise<T> {
    if (!r.ok) {
        let mensaje = `${r.status} ${r.statusText}`;
        try {
            const cuerpo = await r.json();
            if (typeof cuerpo.detail === "string") mensaje = cuerpo.detail;
            else if (Array.isArray(cuerpo.detail))
                mensaje = cuerpo.detail.map((d: any) => d.msg).join("; ");
        } catch {
            /* respuesta sin JSON */
        }
        throw new ErrorApi(r.status, mensaje);
    }
    return r.json();
}

export const obtener = <T>(ruta: string, init?: RequestInit) =>
    fetch(ruta, init).then((r) => leer<T>(r));

export function crearConsulta(
    peticion: PeticionConsulta,
    clave: string,
    visitante: string,
) {
    return obtener<{ id: string; eventos: string }>("/api/consultas", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-OpenRouter-Key": clave,
            "X-Visitante": visitante,
        },
        body: JSON.stringify(peticion),
    });
}

/** Sigue el flujo SSE de una consulta (en curso o terminada) hasta el evento `fin`. */
export function seguirEventos(
    id: string,
    alRecibir: (e: Evento) => void,
    alFallar: (mensaje: string) => void,
): () => void {
    const fuente = new EventSource(`/api/consultas/${id}/eventos`);
    let terminado = false;
    for (const etapa of ETAPAS) {
        fuente.addEventListener(etapa, (m) => {
            const e = JSON.parse((m as MessageEvent).data) as Evento;
            alRecibir(e);
            if (e.etapa === "fin") {
                terminado = true;
                fuente.close(); // sin esto, EventSource reconecta y repite el flujo
            }
        });
    }
    fuente.onerror = () => {
        if (!terminado && fuente.readyState === EventSource.CLOSED)
            alFallar("Se perdió la conexión con el servidor.");
    };
    return () => fuente.close();
}

const num = (v: number, d: number) =>
    v.toLocaleString("es-CO", {
        minimumFractionDigits: d,
        maximumFractionDigits: d,
    });

export const usd = (v: number | null | undefined, decimales = 4) =>
    v == null ? "—" : `US$${num(v, decimales)}`;

export const cop = (v: number | null | undefined) =>
    v == null ? "—" : `$${Math.round(v).toLocaleString("es-CO")}`;

export const pct = (p: number, d = 1) => `${num(p * 100, d)} %`;

/** Lista blanca del visitante: cada cambio devuelve la lista completa actualizada. */
export const fuentesApi = (visitante: string) => {
    const h = { "X-Visitante": visitante };
    const json = { ...h, "Content-Type": "application/json" };
    return {
        listar: () => obtener<ListaBlanca>("/api/fuentes", { headers: h }),
        activar: (id: string, activa: boolean) =>
            obtener<ListaBlanca>(`/api/fuentes/${id}`, {
                method: "PATCH",
                headers: json,
                body: JSON.stringify({ activa }),
            }),
        agregarUrl: (url: string, nombre?: string) =>
            obtener<ListaBlanca>("/api/fuentes/url", {
                method: "POST",
                headers: json,
                body: JSON.stringify({ url, nombre: nombre || null }),
            }),
        agregarPdf: (archivo: File) => {
            const datos = new FormData();
            datos.append("archivo", archivo);
            return obtener<ListaBlanca>("/api/fuentes/pdf", {
                method: "POST",
                headers: h,
                body: datos,
            });
        },
        eliminar: (id: string) =>
            obtener<ListaBlanca>(`/api/fuentes/${id}`, { method: "DELETE", headers: h }),
        restablecer: () =>
            obtener<ListaBlanca>("/api/fuentes/restablecer", { method: "POST", headers: h }),
    };
};
