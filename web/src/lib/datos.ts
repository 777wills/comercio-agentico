import { fuentes } from "./config.svelte.js";
import {
    obtener,
    type Catalogo,
    type Ejemplos,
    type IndiceCorpus,
} from "./api";

const cache = new Map<string, Promise<any>>();
function una<T>(ruta: string): Promise<T> {
    if (!cache.has(ruta)) {
        const p = obtener<T>(ruta);
        p.catch(() => cache.delete(ruta));
        cache.set(ruta, p);
    }
    return cache.get(ruta)!;
}

export const catalogo = () => una<Catalogo>("/api/modelos");
export const ejemplos = () => una<Ejemplos>("/api/ejemplos");
export const indiceCorpus = () => una<IndiceCorpus>("/api/corpus");

/** ID de fuente → nombre comercial (P2 → TiendaNova, A1 → Alkosto). */
export async function nombresFuentes(): Promise<Record<string, string>> {
    const ind = await indiceCorpus();
    const base = Object.fromEntries(
        [...ind.corpus.b, ...ind.corpus.a].map((f) => [f.id, f.nombre]),
    );
    // Tiendas en vivo (V…) y fuentes propias (U…) salen de la lista blanca del visitante.
    try {
        if (!fuentes.lista) await fuentes.cargar();
    } catch {
        /* sin lista blanca se muestran los ID */
    }
    // Tiendas retiradas del catálogo (D132) que siguen nombradas en consultas anteriores.
    const retiradas = { V1: "Alkosto", V2: "Ktronix" };
    return { ...retiradas, ...base, ...fuentes.nombres() };
}

export const CLASES: Record<string, string> = {
    desviar_compra: "Desviar la compra",
    inflar_cantidad: "Inflar la cantidad",
    saltar_confirmacion: "Saltar la confirmación",
    exfiltrar_mandato: "Exfiltrar el mandato",
    alterar_precio: "Alterar el precio",
};
export const UBICACIONES: Record<string, string> = {
    visible: "Texto visible (P3)",
    oculto_html: "Oculto en JSON-LD (P2)",
    pdf: "PDF (P4)",
    mensaje: "Mensaje de chat (P5)",
};

// Código de fuente: P1–P5, A1–A3, V1–V20 o tienda propia del visitante (U + 6 hexadecimales).
const CODIGO = String.raw`(?:[PAV]\d{1,2}|U[0-9a-f]{6})`;

/** Nombre de una fuente; sin él (tienda propia de otro visitante), se dice qué es en vez del código. */
export function nombreFuente(
    codigo: string,
    nombres: Record<string, string>,
    propia = "Tienda propia",
): string {
    return nombres[codigo] ?? (/^U[0-9a-f]{6}$/.test(codigo) ? propia : codigo);
}

/** El agente nombra las fuentes por su código (V6, P2…); quien compra ve la tienda (D139). */
export function conNombres(
    texto: string,
    nombres: Record<string, string>,
): string {
    const nombre = (c: string) => nombreFuente(c, nombres, "tienda propia");
    // Entre paréntesis, solos o en lista: «(V5)», «(V3, V4, V5)».
    let t = texto.replace(
        new RegExp(String.raw`\((${CODIGO}(?:,\s*${CODIGO})*)\)`, "g"),
        (_, lista: string) => `(${lista.split(/,\s*/).map(nombre).join(", ")})`,
    );
    // Al final de un paréntesis («(Monitor LG 27U411B-B, V14)»), tras «de»/«en» o al inicio («V5: …»).
    t = t
        .replace(new RegExp(String.raw`,\s*(${CODIGO})\)`, "g"), (_, c) => `, ${nombre(c)})`)
        .replace(new RegExp(String.raw`\b(de|en) (${CODIGO})\b`, "g"), (_, p, c) => `${p} ${nombre(c)}`)
        .replace(new RegExp(String.raw`^(${CODIGO}):`), (_, c) => `${nombre(c)}:`);
    return t
        .replace(/,,/g, ",")
        .replace(
            /no se pudo confirmar con una segunda lectura de su fuente \(discrepancia\)/g,
            "no se pudo confirmar: al leer de nuevo la tienda, el precio u otro dato no coincidió",
        )
        .replace(
            /no se pudo confirmar con una segunda lectura de su fuente \(sin_contraparte\)/g,
            "no se pudo confirmar: al leer de nuevo la tienda no se encontró el producto",
        )
        .replace(/\(sin_contraparte\)/g, "(no se pudo releer en la tienda)")
        .replace(/\(discrepancia\)/g, "(la segunda lectura no coincidió)")
        .replace(
            /(\d+) ofertas quedaron sin juicio de pertinencia tras reintentar y no se consideran\./,
            "No se pudo evaluar si $1 ofertas corresponden a lo pedido, ni siquiera al reintentar; no se tuvieron en cuenta.",
        )
        .replace(/\bsin juicio de pertinencia\b/g, "no se pudo evaluar si corresponde a lo pedido")
        .replace(
            /^N3: se excluyeron (\d+) ofertas que una segunda lectura no confirmó\./,
            "Se excluyeron $1 ofertas cuyo precio no se confirmó en una segunda lectura de la tienda.",
        )
        .replace(/\s*>=\s*/g, " ≥ ")
        .replace(/\s*<=\s*/g, " ≤ ")
        .replace(/\b1 fuentes\b/g, "1 fuente")
        .replace(/\b1 ofertas\b/g, "1 oferta")
        .replace(/\b1 cumplen\b/g, "1 cumple")
        .replace(/\b1 proveedores\b/g, "1 proveedor");
}

/** Primera letra en mayúscula (los motivos del juez llegan en minúscula o en mayúscula). */
export const capital = (t: string) => (t ? t[0].toUpperCase() + t.slice(1) : t);

const HERRAMIENTA_ERROR: Record<string, string> = {
    abrir_pagina: "No se pudo abrir la página",
    leer_documento: "No se pudo leer el documento",
    consultar_mcp: "No se pudo consultar el catálogo del mayorista",
};

/** Alerta del agente en lenguaje de quien compra: sin trazas, nombres de función ni puntajes. */
export function alertaLegible(
    a: { tipo: string; mensaje: string },
    nombres: Record<string, string>,
): string {
    const m = a.mensaje;
    if (a.tipo === "posible_inyeccion") {
        const r = m.match(/^(\S+): se retiraron (\d+) de (\d+) ventanas de (\S+)/);
        if (r) {
            const [, c, n, total, url] = r;
            return `${conNombres(`${c}:`, nombres).slice(0, -1)}: se ignoraron ${n} de ${total} fragmentos de ${url} porque parecían instrucciones dirigidas al agente y no información del producto.`;
        }
    }
    if (a.tipo === "fuente_no_disponible") {
        const r = m.match(/^(\w+)\((.*?)\):\s*(.*)$/s);
        if (r) {
            const [, herramienta, args, error] = r;
            const url = args.match(/'url':\s*'([^']+)'/)?.[1];
            const busqueda = args.match(/'texto':\s*'([^']*)'/)?.[1];
            const que = url ? ` ${url}` : busqueda ? ` (búsqueda «${busqueda}»)` : "";
            const porque = /robots\.txt/.test(error)
                ? "la tienda no permite la lectura automática de esa página"
                : /No hay proveedor MCP/.test(error)
                  ? "el catálogo del mayorista no está activo en esta consulta"
                  : /fuera de las fuentes registradas/.test(error)
                    ? "la dirección no pertenece a una fuente autorizada, así que no se abrió"
                    : /Límite de llamadas/.test(error)
                      ? "se agotó el presupuesto de lecturas de la consulta"
                      : "la página no respondió o tardó demasiado";
            return `${HERRAMIENTA_ERROR[herramienta] ?? "No se pudo leer la fuente"}${que}: ${porque}.`;
        }
    }
    return capital(conNombres(m, nombres));
}
