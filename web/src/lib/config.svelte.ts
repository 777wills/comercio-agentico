// Configuración del visitante (D82, D86, D91, D110, D114). Solo vive en este navegador.
import { fuentesApi, obtener, type Defensas, type Grupo, type ListaBlanca, type Resumen } from './api';
import { catalogo } from './datos';

export type Proveedor = 'openrouter' | 'anthropic';

/** D114: el proveedor de la clave se reconoce por su prefijo. */
export function proveedorDe(clave: string): Proveedor | null {
	if (clave.startsWith('sk-ant-')) return 'anthropic';
	if (clave.startsWith('sk-or-')) return 'openrouter';
	return null;
}

export const PRESETS: Record<string, [boolean, boolean, boolean]> = {
	C0: [false, false, false],
	C1: [true, false, false],
	C2: [true, true, false],
	C3: [true, true, true]
};
export const UMBRAL_INFORME = 0.5;

const LLAVE = 'cotia.config';
const LLAVE_CLAVE = 'cotia.clave';
const LLAVE_VISITANTE = 'cotia.visitante';

type Guardada = {
	modelo: string;
	clasificador: string;
	defensas: Defensas;
	verificar: boolean;
	politica_n3: 'abstener' | 'excluir';
	corpus: Grupo;
	recordar: boolean;
};

function leer<T>(almacen: Storage, llave: string): T | null {
	try {
		return JSON.parse(almacen.getItem(llave) ?? 'null');
	} catch {
		return null;
	}
}

class Config {
	clave = $state('');
	recordar = $state(false);
	modelo = $state('deepseek-flash');
	clasificador = $state('Horizon-Labs/prompt-injection-guard-small');
	defensas = $state<Defensas>({
		separacion_planos: true,
		clasificador: true,
		precio: false,
		umbral: UMBRAL_INFORME
	});
	verificar = $state(false);
	politica_n3 = $state<'abstener' | 'excluir'>('abstener');
	corpus = $state<Grupo>('vivo'); // D113: arranca el grupo en vivo
	visitante: string;
	proveedor = $derived(proveedorDe(this.clave));

	/** C0–C3 si las capas coinciden con un punto medido en E2; si no, «exploratorio». */
	configuracion = $derived.by(() => {
		const d = this.defensas;
		if (d.clasificador && d.umbral !== UMBRAL_INFORME) return 'exploratorio';
		const capas = [d.separacion_planos, d.clasificador, d.precio].join();
		return Object.keys(PRESETS).find((c) => PRESETS[c].join() === capas) ?? 'exploratorio';
	});

	constructor() {
		const g = leer<Guardada>(localStorage, LLAVE);
		if (g) Object.assign(this, g);
		this.clave =
			(this.recordar ? localStorage.getItem(LLAVE_CLAVE) : sessionStorage.getItem(LLAVE_CLAVE)) ??
			'';
		this.visitante = localStorage.getItem(LLAVE_VISITANTE) ?? crypto.randomUUID();
		localStorage.setItem(LLAVE_VISITANTE, this.visitante);

		$effect.root(() => {
			$effect(() => {
				const g: Guardada = {
					modelo: this.modelo,
					clasificador: this.clasificador,
					defensas: { ...this.defensas },
					verificar: this.verificar,
					politica_n3: this.politica_n3,
					corpus: this.corpus,
					recordar: this.recordar
				};
				localStorage.setItem(LLAVE, JSON.stringify(g));
				// La clave va a sessionStorage salvo que el visitante pida recordarla.
				const [usar, limpiar] = this.recordar
					? [localStorage, sessionStorage]
					: [sessionStorage, localStorage];
				limpiar.removeItem(LLAVE_CLAVE);
				if (this.clave) usar.setItem(LLAVE_CLAVE, this.clave);
				else usar.removeItem(LLAVE_CLAVE);
			});
			// Con una clave de Anthropic solo sirven los modelos Claude de la lista curada.
			$effect(() => {
				if (this.proveedor !== 'anthropic') return;
				const actual = this.modelo;
				catalogo().then((c) => {
					const claude = c.modelos.filter((m) => m.anthropic);
					if (claude.length && !claude.some((m) => m.nombre === actual))
						this.modelo = claude[0].nombre;
				});
			});
		});
	}

	aplicarPreset(c: string) {
		const [s, k, p] = PRESETS[c];
		this.defensas = { separacion_planos: s, clasificador: k, precio: p, umbral: UMBRAL_INFORME };
	}

	olvidarClave() {
		this.clave = '';
	}
}

export const config = new Config();

/** Gasto de la visita con la clave del visitante (D90); lo calcula el servidor desde el historial. */
class Visita {
	consultas = $state<Resumen[]>([]);
	total = $state(0);
	gasto = $state(0);

	async refrescar() {
		const h = await obtener<{ consultas: Resumen[]; total_consultas: number; gasto_usd: number }>(
			'/api/consultas',
			{ headers: { 'X-Visitante': config.visitante } }
		);
		this.consultas = h.consultas;
		this.total = h.total_consultas;
		this.gasto = h.gasto_usd;
	}
}

export const visita = new Visita();

/**
 * Perfil fijo del modo Cliente (D111): C2 (D106) + N3 con política abstener (D110).
 * El cliente solo elige clave, modelo y catálogo; el resto no se muestra.
 */
export function opcionesCliente() {
	const [s, k, p] = PRESETS.C2;
	return {
		modelo: config.modelo,
		defensas: { separacion_planos: s, clasificador: k, precio: p, umbral: UMBRAL_INFORME },
		clasificador: 'Horizon-Labs/prompt-injection-guard-small',
		verificar: true,
		politica_n3: 'abstener' as const
	};
}

/** Diálogo de ajustes del modo Cliente: se abre desde el encabezado o al intentar cotizar sin clave. */
export const ajustes = $state({ abierto: false });

/** Lista blanca del visitante (D113), compartida por el modo Cliente y el Laboratorio. */
class Fuentes {
	lista = $state<ListaBlanca | null>(null);
	ocupado = $state(false);
	panel = $state(false);
	#api = () => fuentesApi(config.visitante);

	grupo(id: Grupo) {
		return this.lista?.grupos.find((g) => g.id === id);
	}
	activas(id: Grupo) {
		return this.grupo(id)?.fuentes.filter((f) => f.activa).length ?? 0;
	}
	/** ID → nombre, para mostrar el proveedor de las ofertas de fuentes propias (U…). */
	nombres(): Record<string, string> {
		return Object.fromEntries(
			(this.lista?.grupos ?? []).flatMap((g) => g.fuentes.map((f) => [f.id, f.nombre]))
		);
	}
	async #hacer(accion: (api: ReturnType<typeof fuentesApi>) => Promise<ListaBlanca>) {
		this.ocupado = true;
		try {
			this.lista = await accion(this.#api());
		} finally {
			this.ocupado = false;
		}
	}
	cargar = () => this.#hacer((a) => a.listar());
	activar = (id: string, activa: boolean) => this.#hacer((a) => a.activar(id, activa));
	agregarUrl = (url: string, nombre?: string) => this.#hacer((a) => a.agregarUrl(url, nombre));
	agregarPdf = (archivo: File) => this.#hacer((a) => a.agregarPdf(archivo));
	eliminar = (id: string) => this.#hacer((a) => a.eliminar(id));
	restablecer = () => this.#hacer((a) => a.restablecer());
}

export const fuentes = new Fuentes();
