<script lang="ts">
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { obtener, type Resumen } from '#lib/api.js';
	import { nombresFuentes } from '#lib/datos.js';
	import Ejecucion from '#lib/components/Ejecucion.svelte';
	import { Badge } from '#lib/components/ui/badge/index.js';

	let nombres = $state<Record<string, string>>({});
	let resumen = $state<Resumen | null>(null);
	onMount(async () => {
		nombres = await nombresFuentes();
	});
	$effect(() => {
		obtener<Resumen>(`/api/consultas/${page.params.id}`).then((r) => (resumen = r));
	});
</script>

<div class="mb-4 space-y-1">
	<h1 class="text-xl font-semibold">{resumen?.consulta ?? 'Consulta'}</h1>
	{#if resumen}
		<div class="flex flex-wrap gap-2 text-xs">
			<Badge variant="outline">Corpus {resumen.corpus.toUpperCase()}</Badge>
			{#if resumen.carga}<Badge variant="destructive">Carga {resumen.carga}</Badge>{/if}
			<Badge variant="outline">{resumen.modelo}</Badge>
			<Badge variant="outline">Defensas {resumen.opciones.configuracion}</Badge>
			{#if resumen.opciones.verificar}
				<Badge variant="outline">N3 · {resumen.opciones.politica_n3}</Badge>
			{/if}
		</div>
	{/if}
</div>

{#key page.params.id}
	<Ejecucion id={page.params.id!} {nombres} />
{/key}
