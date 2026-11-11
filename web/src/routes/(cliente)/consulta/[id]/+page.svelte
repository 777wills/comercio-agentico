<script lang="ts">
	import { page } from '$app/state';
	import { onDestroy, onMount } from 'svelte';
	import { obtener, seguirEventos, type Detalle, type Evento, type Resumen } from '#lib/api.js';
	import { visita } from '#lib/config.svelte.js';
	import { nombresFuentes } from '#lib/datos.js';
	import ResultadoCliente from '#lib/components/ResultadoCliente.svelte';
	import Check from '@lucide/svelte/icons/check';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';

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

	const paso = $derived(
		ultima ? PASOS.findIndex((p) => p.etapas.includes(ultima!.etapa)) : 0
	);
	const terminada = $derived(ultima?.etapa === 'fin');

	function explicarError(m: string): string {
		if (/Unauthorized|401/.test(m)) return 'OpenRouter rechazó la clave. Revísela en Ajustes.';
		if (/PaymentRequired|402|credits/i.test(m)) return 'Su cuenta de OpenRouter no tiene saldo suficiente.';
		if (/TooManyRequests|429/.test(m)) return 'El proveedor del modelo está saturado; intente en unos minutos.';
		return 'La consulta no pudo completarse.';
	}

	onMount(async () => {
		const id = page.params.id!;
		nombresFuentes().then((n) => (nombres = n));
		resumen = await obtener<Resumen>(`/api/consultas/${id}`);
		cerrar = seguirEventos(
			id,
			async (e) => {
				ultima = e;
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

<svelte:head><title>CotIA · cotización</title></svelte:head>

<section class="mx-auto max-w-4xl pt-10 pb-16">
	<a href="/" class="text-xs text-muted-foreground hover:text-foreground">← Nueva consulta</a>
	<h1 class="mt-4 text-2xl font-medium tracking-tight">{resumen?.consulta ?? ''}</h1>

	{#if !terminada && !fallo}
		<ol class="mt-12 space-y-4">
			{#each PASOS as p, i (p.nombre)}
				<li class="flex items-center gap-3 text-sm {i > paso ? 'text-muted-foreground/50' : ''}">
					{#if i < paso}
						<Check class="size-4 text-primary" />
					{:else if i === paso}
						<LoaderCircle class="size-4 animate-spin text-primary" />
					{:else}
						<span class="grid size-4 place-items-center"><span class="size-1.5 rounded-full bg-current"></span></span>
					{/if}
					{p.nombre}
				</li>
			{/each}
		</ol>
		<p class="mt-8 text-xs text-muted-foreground">Suele tardar entre uno y tres minutos.</p>
	{:else if fallo || detalle?.error || (terminada && ultima?.estado === 'error')}
		<p class="mt-12 text-destructive">{explicarError(detalle?.error ?? ultima?.error ?? fallo ?? '')}</p>
		<a href="/" class="mt-4 inline-block text-sm text-muted-foreground hover:text-foreground">Intentar de nuevo</a>
	{:else if detalle?.propuesta}
		<div class="mt-12">
			<ResultadoCliente propuesta={detalle.propuesta} {nombres} segundos={detalle.segundos} />
		</div>
	{:else}
		<LoaderCircle class="mt-12 size-4 animate-spin text-muted-foreground" />
	{/if}
</section>
