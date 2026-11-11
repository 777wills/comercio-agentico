<script lang="ts">
	import { onMount } from 'svelte';
	import { usd } from '#lib/api.js';
	import { visita } from '#lib/config.svelte.js';

	onMount(() => {
		visita.refrescar().catch(() => {});
	});
	// Las ejecuciones del laboratorio de ataques no son consultas del cliente.
	const propias = $derived(visita.consultas.filter((c) => !c.carga));
</script>

<svelte:head><title>CotIA · mis consultas</title></svelte:head>

<section class="mx-auto max-w-3xl pt-10 pb-16">
	<h1 class="text-2xl font-medium tracking-tight">Mis consultas</h1>
	<p class="mt-2 text-sm text-muted-foreground">
		Guardadas para este navegador · {usd(visita.gasto)} en total
	</p>

	{#if propias.length}
		<ul class="mt-10 divide-y border-y">
			{#each propias as c (c.id)}
				<li>
					<a href="/consulta/{c.id}" class="flex items-baseline gap-4 py-4 transition-colors hover:text-primary">
						<span class="flex-1 truncate">{c.consulta}</span>
						<span class="text-xs whitespace-nowrap text-muted-foreground">
							{c.estado === 'error' ? 'Error · ' : ''}{new Date(c.creada).toLocaleDateString('es-CO', {
								day: 'numeric',
								month: 'short'
							})}
						</span>
					</a>
				</li>
			{/each}
		</ul>
	{:else}
		<p class="mt-10 text-sm text-muted-foreground">
			Aún no tiene consultas. <a href="/" class="text-foreground underline-offset-4 hover:underline">Haga la primera</a>.
		</p>
	{/if}
</section>
