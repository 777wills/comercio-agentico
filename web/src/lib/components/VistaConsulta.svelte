<script lang="ts">
	// Vista de una consulta del modo Cliente. La página la envuelve en {#key id} para que cambiar de
	// consulta desde la barra lateral (D140) la recree, con su propio flujo de eventos.
	import { onDestroy, onMount } from 'svelte';
	import {
		cancelarConsulta,
		ErrorApi,
		obtener,
		seguirEventos,
		usd,
		type Detalle,
		type Evento,
		type Resumen
	} from '#lib/api.js';
	import { toast } from 'svelte-sonner';
	import { config, visita } from '#lib/config.svelte.js';
	import { nombresFuentes } from '#lib/datos.js';
	import ResultadoCliente from '#lib/components/ResultadoCliente.svelte';
	import Check from '@lucide/svelte/icons/check';
	import FileText from '@lucide/svelte/icons/file-text';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import TriangleAlert from '@lucide/svelte/icons/triangle-alert';

	let { id }: { id: string } = $props();

	// Cuatro pasos legibles que agrupan los eventos del agente (D111).
	const PASOS = [
		{ nombre: 'Entendiendo su necesidad', etapas: ['en_cola', 'inicio', 'interpretacion'] },
		{ nombre: 'Consultando proveedores', etapas: ['plan', 'lecturas'] },
		{ nombre: 'Comparando ofertas', etapas: ['emparejamiento'] },
		{ nombre: 'Preparando la recomendación', etapas: ['propuesta', 'fin'] }
	];

	let resumen = $state<Resumen | null>(null);
	let detalle = $state<Detalle | null>(null);
	let nombres = $state<Record<string, string>>({});
	let ultima = $state<Evento | null>(null);
	let fallo = $state<string | null>(null);
	let cerrar: (() => void) | null = null;

	// Avance por fuente (D119): el plan anuncia qué se lee y el evento de lecturas, cómo terminó.
	type Herramienta = { nombre: string; args: Record<string, unknown>; estado?: string };
	let lecturas = $state<{ clave: string; texto: string; estado: string }[]>([]);

	function rotulo(h: Herramienta): string {
		const url = typeof h.args?.url === 'string' ? h.args.url : null;
		if (!url) return h.nombre === 'consultar_mcp' ? 'Catálogo del mayorista (MCP)' : h.nombre;
		try {
			const u = new URL(url);
			const ruta = decodeURIComponent(u.pathname + u.search).replace(/\/$/, '');
			const sitio = /^127\.|localhost/.test(u.hostname) ? 'proveedor de prueba' : u.hostname.replace(/^www\./, '');
			return ruta ? `${sitio} · ${ruta.length > 48 ? ruta.slice(0, 47) + '…' : ruta}` : sitio;
		} catch {
			return url;
		}
	}
	const claveDe = (h: Herramienta) => h.nombre + JSON.stringify(h.args ?? {});

	function registrar(e: Evento) {
		const lista = (e as { herramientas?: Herramienta[]; lecturas?: Herramienta[] });
		if (e.etapa === 'plan')
			for (const h of lista.herramientas ?? [])
				lecturas.push({ clave: claveDe(h), texto: rotulo(h), estado: 'leyendo' });
		if (e.etapa === 'lecturas')
			for (const h of lista.lecturas ?? []) {
				const l = lecturas.findLast((x) => x.clave === claveDe(h) && x.estado === 'leyendo');
				if (l) l.estado = h.estado ?? 'ok';
			}
	}

	const paso = $derived(
		ultima ? PASOS.findIndex((p) => p.etapas.includes(ultima!.etapa)) : 0
	);
	const terminada = $derived(ultima?.etapa === 'fin');
	const cancelada = $derived(
		(terminada && ultima?.estado === 'cancelada') || detalle?.estado === 'cancelada'
	);

	// D141: cancelar detiene la consulta en el servidor; lo ya consumido no se recupera.
	let cancelando = $state(false);
	async function cancelar() {
		cancelando = true;
		try {
			await cancelarConsulta(id, config.visitante);
		} catch (e) {
			cancelando = false;
			toast.error(e instanceof ErrorApi ? e.message : 'No se pudo cancelar la consulta.');
		}
	}

	function explicarError(m: string): string {
		if (/Unauthorized|401/.test(m)) return 'El proveedor del modelo rechazó la clave. Revísela en Ajustes.';
		if (/PaymentRequired|402|credit/i.test(m)) return 'Su cuenta del proveedor del modelo no tiene saldo suficiente.';
		if (/TooManyRequests|429|overloaded|529/i.test(m)) return 'El proveedor del modelo está saturado; intente en unos minutos.';
		return 'La consulta no pudo completarse.';
	}

	onMount(async () => {
		nombresFuentes().then((n) => (nombres = n));
		resumen = await obtener<Resumen>(`/api/consultas/${id}`);
		cerrar = seguirEventos(
			id,
			async (e) => {
				ultima = e;
				registrar(e);
				if (e.etapa === 'fin') {
					detalle = await obtener<Detalle>(`/api/consultas/${id}`);
					visita.refrescar().catch(() => {});
				}
			},
			(m) => (fallo = m)
		);
	});
	onDestroy(() => cerrar?.());
</script>

<section class="mx-auto max-w-4xl pt-10 pb-16">
	<a href="/" class="text-xs text-muted-foreground hover:text-foreground">← Nueva consulta</a>
	<h1 class="mt-4 text-2xl font-medium tracking-tight">{resumen?.consulta ?? ''}</h1>

	{#if !terminada && !fallo}
		<ol class="mt-12 space-y-4">
			{#each PASOS as p, i (p.nombre)}
				<li class="text-sm {i > paso ? 'text-muted-foreground/50' : ''}">
					<div class="flex items-center gap-3">
						{#if i < paso}
							<Check class="size-4 text-primary" />
						{:else if i === paso}
							<LoaderCircle class="size-4 animate-spin text-primary" />
						{:else}
							<span class="grid size-4 place-items-center"><span class="size-1.5 rounded-full bg-current"></span></span>
						{/if}
						{p.nombre}
					</div>
					{#if i === 1 && paso >= 1 && lecturas.length}
						<ul class="mt-3 ml-7 space-y-1.5 text-xs text-muted-foreground">
							{#each lecturas as l, j (j)}
								<li class="flex items-center gap-2">
									{#if l.estado === 'leyendo'}
										<LoaderCircle class="size-3 shrink-0 animate-spin" />
									{:else if l.estado === 'error'}
										<TriangleAlert class="size-3 shrink-0 text-warning" />
									{:else}
										<Check class="size-3 shrink-0 text-primary" />
									{/if}
									<span class="truncate">{l.texto}</span>
								</li>
							{/each}
						</ul>
					{/if}
				</li>
			{/each}
		</ol>
		<div class="mt-8 flex flex-wrap items-center gap-x-4 gap-y-2">
			<p class="text-xs text-muted-foreground">
				Suele tardar entre uno y tres minutos; con tiendas en vivo, varios minutos más.
			</p>
			<button
				type="button"
				class="rounded-full border px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-destructive/50 hover:text-destructive disabled:opacity-50"
				disabled={cancelando}
				onclick={cancelar}>{cancelando ? 'Cancelando…' : 'Cancelar consulta'}</button
			>
		</div>
	{:else if cancelada}
		<div class="mt-12 rounded-xl border bg-card p-5 sm:p-6">
			<p class="font-medium">Consulta cancelada</p>
			<p class="mt-1 text-sm text-muted-foreground">
				Se detuvo antes de terminar. Lo consumido hasta ese momento fue
				{usd(detalle?.costo_usd ?? ultima?.costo_usd ?? 0)}.
			</p>
			<a href="/" class="mt-4 inline-block text-sm text-primary hover:underline">Hacer una nueva consulta</a>
		</div>
	{:else if fallo || detalle?.error || (terminada && ultima?.estado === 'error')}
		<p class="mt-12 text-destructive">{explicarError(detalle?.error ?? ultima?.error ?? fallo ?? '')}</p>
		<a href="/" class="mt-4 inline-block text-sm text-muted-foreground hover:text-foreground">Intentar de nuevo</a>
	{:else if detalle?.propuesta}
		<div class="mt-12">
			<ResultadoCliente
				propuesta={detalle.propuesta}
				{nombres}
				segundos={detalle.segundos}
				estimado={!!detalle.detalle?.costo_estimado}
				carga={detalle.carga}
			/>
			<!-- D142: evidencia de todo lo cotizado y del porqué de la recomendación. -->
			<div class="mt-8 flex flex-wrap items-center gap-x-4 gap-y-2 border-t pt-6">
				<a
					href="/informe/{id}"
					class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition-colors hover:border-primary/50 hover:text-primary"
					><FileText class="size-4" />Informe de cotización</a
				>
				<p class="text-xs text-muted-foreground">
					Todo lo investigado, lo descartado y la procedencia de cada dato, listo para imprimir o guardar en PDF.
				</p>
			</div>
		</div>
	{:else}
		<LoaderCircle class="mt-12 size-4 animate-spin text-muted-foreground" />
	{/if}
</section>
