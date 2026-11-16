<script lang="ts">
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { crearConsulta, ErrorApi } from '#lib/api.js';
	import { onMount } from 'svelte';
	import { ajustes, config, fuentes, opcionesCliente, PROFUNDIDAD, visita, type Profundidad } from '#lib/config.svelte.js';
	import { ejemplos } from '#lib/datos.js';
	import Fuentes from '#lib/components/Fuentes.svelte';
	import ArrowUp from '@lucide/svelte/icons/arrow-up';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';

	let consulta = $state('');
	let enviando = $state(false);
	const ej = ejemplos();
	const listo = $derived(consulta.trim().length >= 3 && !enviando);

	// En vivo no hay tareas con respuesta conocida: ejemplos genéricos de compra.
	const EJEMPLOS_VIVO = [
		'Un portátil con 16 GB de RAM y 512 GB de SSD por menos de 3 millones',
		'El Samsung Galaxy A57 de 256 GB más barato con envío',
		'Audífonos inalámbricos con cancelación de ruido por menos de 600 mil pesos'
	];
	onMount(() => fuentes.cargar().catch(() => {}));
	const activas = $derived(fuentes.activas(config.corpus));
	// D146: profundidad de búsqueda; las lecturas crecen con las fuentes activas por encima de 5.
	const lecturas = $derived(fuentes.acciones(config.profundidad, config.corpus));

	async function enviar() {
		if (!listo) return;
		if (!config.clave) {
			ajustes.abierto = true;
			return;
		}
		if (fuentes.lista && activas === 0) {
			fuentes.panel = true;
			return;
		}
		enviando = true;
		try {
			const r = await crearConsulta(
				{ consulta, corpus: config.corpus, ...opcionesCliente() },
				config.clave,
				config.visitante
			);
			visita.refrescar().catch(() => {});
			await goto(`/consulta/${r.id}`);
		} catch (e) {
			toast.error(e instanceof ErrorApi ? e.message : 'No se pudo crear la consulta.');
		} finally {
			enviando = false;
		}
	}
</script>

<svelte:head><title>CotIA</title></svelte:head>

<section class="mx-auto flex max-w-2xl flex-col pt-[8vh] pb-16 sm:pt-[14vh]">
	<h1 class="text-3xl font-semibold tracking-tight sm:text-4xl">¿Qué necesita comprar?</h1>
	<p class="mt-3 text-muted-foreground">
		CotIA compara proveedores y le recomienda la mejor oferta, con la fuente de cada precio.
	</p>

	<form
		class="mt-8 rounded-2xl border bg-card p-2 shadow-[0_1px_0_var(--border)] transition-colors focus-within:border-primary/60 sm:mt-10"
		onsubmit={(e) => {
			e.preventDefault();
			enviar();
		}}
	>
		<textarea
			bind:value={consulta}
			rows={3}
			maxlength={500}
			class="block w-full resize-none bg-transparent px-3 py-2 text-base outline-none placeholder:text-muted-foreground/70"
			placeholder="Ej.: dos monitores 4K de 27 pulgadas por menos de 3 millones, entrega en 5 días"
			onkeydown={(e) => {
				if (e.key === 'Enter' && !e.shiftKey) {
					e.preventDefault();
					enviar();
				}
			}}
		></textarea>
		<div class="flex items-center gap-1 px-1">
			<button
				type="button"
				class="rounded-full px-3 py-1 text-xs text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
				onclick={() => (fuentes.panel = true)}
				>{fuentes.lista
					? `${fuentes.grupo(config.corpus)?.nombre ?? ''} · ${activas} ${activas === 1 ? 'fuente' : 'fuentes'}`
					: 'Fuentes'}</button
			>
			<label class="relative">
				<span class="sr-only">Profundidad de la búsqueda</span>
				<select
					bind:value={config.profundidad}
					class="cursor-pointer appearance-none rounded-full bg-transparent py-1 pr-7 pl-3 text-xs text-muted-foreground transition-colors outline-none hover:bg-secondary hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
				>
					{#each Object.entries(PROFUNDIDAD) as [valor, p] (valor)}
						<option value={valor as Profundidad}>Búsqueda {p.etiqueta.toLowerCase()}</option>
					{/each}
				</select>
				<ChevronDown class="pointer-events-none absolute top-1/2 right-2.5 size-3 -translate-y-1/2 text-muted-foreground" />
			</label>
			<button
				type="submit"
				aria-label="Cotizar"
				disabled={!listo}
				class="ml-auto grid size-9 place-items-center rounded-full bg-primary text-primary-foreground transition-opacity disabled:opacity-30"
			>
				<ArrowUp class="size-4" />
			</button>
		</div>
	</form>

	<p class="mt-2 px-3 text-xs text-muted-foreground">
		Búsqueda {PROFUNDIDAD[config.profundidad].etiqueta.toLowerCase()}{lecturas != null
			? `: hasta ${lecturas} lecturas de páginas y documentos`
			: ''}, {PROFUNDIDAD[config.profundidad].relativo}. Más lecturas, más ofertas revisadas.
	</p>

	{#if !config.clave}
		<p class="mt-3 px-2 text-xs text-muted-foreground">
			Para cotizar necesita una clave de OpenRouter o de Anthropic.
			<button class="text-foreground underline-offset-4 hover:underline" onclick={() => (ajustes.abierto = true)}
				>Agregarla</button
			>
		</p>
	{/if}

	{#await ej then ejs}
		<p class="mt-10 px-2 text-xs text-muted-foreground">Pruebe con un ejemplo</p>
		<ul class="mt-1 space-y-0.5">
			{#each config.corpus === 'vivo' ? EJEMPLOS_VIVO : ejs[config.corpus].slice(0, 3).map((e) => e.consulta) as texto (texto)}
				<li>
					<button
						type="button"
						class="w-full rounded-md px-2 py-2 text-left text-sm leading-snug text-muted-foreground transition-colors hover:bg-muted hover:text-foreground sm:truncate sm:py-1.5"
						onclick={() => (consulta = texto)}>{texto}</button
					>
				</li>
			{/each}
		</ul>
	{/await}
</section>

<Fuentes />
