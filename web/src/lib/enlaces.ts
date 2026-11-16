// Enlace de cada oferta a su fuente (D145): quien cotiza abre la página o el documento que
// respalda la cifra. `url_detalle` sale del contenido de la página (dato no confiable, D21):
// solo se enlaza si es http(s) y del mismo sitio que la página leída.
import type { Oferta } from "./api";

// Servidores locales del corpus → origen del visor (/api/corpus/archivo/{origen}/…).
const CORPUS_LOCAL: Record<string, string> = { "8800": "b", "8802": "a" };
const LOCALES = new Set(["127.0.0.1", "localhost"]);

function analizar(url: string, base?: string): URL | null {
    try {
        const u = new URL(url, base);
        return u.protocol === "http:" || u.protocol === "https:" ? u : null;
    } catch {
        return null;
    }
}

const sitio = (host: string) => host.toLowerCase().replace(/^www\./, "");
function mismoSitio(a: URL, b: URL): boolean {
    const x = sitio(a.hostname);
    const y = sitio(b.hostname);
    return x === y || x.endsWith(`.${y}`) || y.endsWith(`.${x}`);
}

/** URL que el navegador del comprador puede abrir, o null (MCP, PDF del visitante, texto). */
export function abrible(url: string | null | undefined, carga?: string | null): string | null {
    const u = url ? analizar(url) : null;
    if (!u) return null;
    if (!LOCALES.has(u.hostname)) return u.href;
    // Corpus servido en local: la copia atacada usa un puerto libre, el corpus limpio el suyo.
    const origen = carga ?? CORPUS_LOCAL[u.port];
    if (!origen) return null;
    const ruta = u.pathname.replace(/^\/+/, "").split("/").map(encodeURIComponent).join("/");
    return ruta ? `/api/corpus/archivo/${origen}/${ruta}` : null;
}

export type EnlaceOferta = { href: string; ficha: boolean };

/** Ficha del producto si es del mismo sitio; si no, la página o el documento leído. */
export function enlace(
    fuente: string | null | undefined,
    detalle: string | null | undefined,
    carga?: string | null,
): EnlaceOferta | null {
    const leida = fuente ? analizar(fuente) : null;
    if (leida && detalle) {
        const ficha = analizar(detalle, leida.href);
        if (ficha && mismoSitio(ficha, leida)) {
            const href = abrible(ficha.href, carga);
            if (href) return { href, ficha: true };
        }
    }
    const href = abrible(leida?.href, carga);
    return href ? { href, ficha: false } : null;
}

export const enlaceOferta = (o: Oferta, carga?: string | null) =>
    enlace(o.procedencia.consulta, o.url_detalle, carga);

/** Texto del enlace según lo que abre. */
export function etiquetaEnlace(o: Oferta, e: EnlaceOferta): string {
    if (e.ficha) return "Ver el producto en la tienda";
    if (o.procedencia.tipo_fuente === "pdf") return "Abrir el documento PDF";
    if (o.procedencia.tipo_fuente === "mensaje") return "Abrir la conversación";
    return "Abrir la página consultada";
}
