<script lang="ts">
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { crearConsulta, ErrorApi } from '#lib/api.js';
	import { ajustes, config, opcionesCliente } from '#lib/config.svelte.js';
	import { ejemplos } from '#lib/datos.js';
	import ArrowUp from '@lucide/svelte/icons/arrow-up';

	let consulta = $state('');
	let enviando = $state(false);
	const ej = ejemplos();
	const listo = $derived(consulta.trim().length >= 3 && !enviando);

	const CATALOGOS = [
		['a', 'Tiendas colombianas'],
		['b', 'Proveedores de prueba']
	] as const;

	async function enviar() {
		if (!listo) return;
		if (!config.clave) {
			ajustes.abierto = true;
			return;
		}
		enviando = true;
		try {
			const r = await crearConsulta(
				{ consulta, corpus: config.corpus, ...opcionesCliente() },
				config.clave,
				config.visitante
			);
			await goto(`/consulta/${r.id}`);
		} catch (e) {
			toast.error(e instanceof ErrorApi ? e.message : 'No se pudo crear la consulta.');
		} finally {
			enviando = false;
		}
	}
</script>

<svelte:head><title>CotIA</title></svelte:head>

<section class="mx-auto flex max-w-2xl flex-col pt-[16vh] pb-16">
	<h1 class="text-3xl font-semibold tracking-tight sm:text-4xl">¿Qué necesita comprar?</h1>
	<p class="mt-3 text-muted-foreground">
		CotIA compara proveedores y le recomienda la mejor oferta, con la fuente de cada precio.
	</p>

	<form
		class="mt-10 rounded-2xl border bg-muted/30 p-2 transition-colors focus-within:border-primary/40"
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
			{#each CATALOGOS as [valor, nombre] (valor)}
				<button
					type="button"
					class="rounded-full px-3 py-1 text-xs transition-colors {config.corpus === valor
						? 'bg-secondary text-foreground'
						: 'text-muted-foreground hover:text-foreground'}"
					onclick={() => (config.corpus = valor)}>{nombre}</button
				>
			{/each}
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

	{#if !config.clave}
		<p class="mt-3 px-2 text-xs text-muted-foreground">
			Para cotizar necesita una clave de OpenRouter.
			<button class="text-foreground underline-offset-4 hover:underline" onclick={() => (ajustes.abierto = true)}
				>Agregarla</button
			>
		</p>
	{/if}

	{#await ej then ejs}
		<ul class="mt-10 space-y-1">
			{#each ejs[config.corpus].slice(0, 3) as e (e.categoria)}
				<li>
					<button
						type="button"
						class="w-full truncate rounded-md px-2 py-1.5 text-left text-sm text-muted-foreground transition-colors hover:bg-muted/40 hover:text-foreground"
						onclick={() => (consulta = e.consulta)}>{e.consulta}</button
					>
				</li>
			{/each}
		</ul>
	{/await}
</section>
