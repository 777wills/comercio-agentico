import { obtener, type Catalogo, type Ejemplos, type IndiceCorpus } from './api';

const cache = new Map<string, Promise<any>>();
function una<T>(ruta: string): Promise<T> {
	if (!cache.has(ruta)) {
		const p = obtener<T>(ruta);
		p.catch(() => cache.delete(ruta));
		cache.set(ruta, p);
	}
	return cache.get(ruta)!;
}

export const catalogo = () => una<Catalogo>('/api/modelos');
export const ejemplos = () => una<Ejemplos>('/api/ejemplos');
export const indiceCorpus = () => una<IndiceCorpus>('/api/corpus');

/** ID de fuente → nombre comercial (P2 → TiendaNova, A1 → Alkosto). */
export async function nombresFuentes(): Promise<Record<string, string>> {
	const ind = await indiceCorpus();
	return Object.fromEntries([...ind.corpus.b, ...ind.corpus.a].map((f) => [f.id, f.nombre]));
}

export const CLASES: Record<string, string> = {
	desviar_compra: 'Desviar la compra',
	inflar_cantidad: 'Inflar la cantidad',
	saltar_confirmacion: 'Saltar la confirmación',
	exfiltrar_mandato: 'Exfiltrar el mandato',
	alterar_precio: 'Alterar el precio'
};
export const UBICACIONES: Record<string, string> = {
	visible: 'Texto visible (P3)',
	oculto_html: 'Oculto en JSON-LD (P2)',
	pdf: 'PDF (P4)',
	mensaje: 'Mensaje de chat (P5)'
};
