<script lang="ts">
	import type { LayoutProps } from './$types';
	import { page } from '$app/state';
	import { config, visita } from '#lib/config.svelte.js';
	import { usd } from '#lib/api.js';

	// Modo Laboratorio (D111): todo el instrumental del experimento, con navegación lateral.
	let { children }: LayoutProps = $props();

	const SECCIONES = [
		['/lab', 'Consulta'],
		['/lab/ataques', 'Ataques C0 / C3'],
		['/lab/corpus', 'Corpus'],
		['/lab/resultados', 'Resultados E1–E3'],
		['/lab/historial', 'Historial'],
		['/lab/configuracion', 'Configuración']
	];
	const activa = (ruta: string) =>
		ruta === '/lab'
			? page.url.pathname === '/lab' || page.url.pathname.startsWith('/lab/consultas')
			: page.url.pathname.startsWith(ruta);
</script>

<svelte:head><title>CotIA · laboratorio</title></svelte:head>

<div class="min-h-screen lg:grid lg:grid-cols-[14rem_1fr]">
	<aside
		class="sticky top-0 z-40 flex flex-col gap-4 border-b bg-background px-4 py-4 lg:h-screen lg:border-r lg:border-b-0 lg:px-3 lg:py-6"
	>
		<a href="/lab" class="px-2 text-sm font-semibold tracking-tight">
			Cot<span class="text-primary">IA</span>
			<span class="ml-1 font-normal text-muted-foreground">laboratorio</span>
		</a>
		<nav class="-mx-1 flex gap-0.5 overflow-x-auto text-sm lg:mx-0 lg:flex-col">
			{#each SECCIONES as [ruta, nombre] (ruta)}
				<a
					href={ruta}
					class="rounded-md px-2 py-1.5 whitespace-nowrap transition-colors {activa(ruta)
						? 'bg-secondary text-foreground'
						: 'text-muted-foreground hover:text-foreground'}">{nombre}</a
				>
			{/each}
		</nav>
		<div class="mt-auto hidden space-y-3 px-2 text-xs text-muted-foreground lg:block">
			<a href="/lab/configuracion" class="flex items-center gap-2 hover:text-foreground">
				<span class="size-1.5 rounded-full {config.clave ? 'bg-primary' : 'bg-destructive'}"></span>
				{config.clave ? 'Clave configurada' : 'Sin clave'}
			</a>
			<div>Defensas {config.configuracion} · {visita.total} consultas · {usd(visita.gasto)}</div>
			<a href="/" class="block hover:text-foreground">← Modo cliente</a>
		</div>
	</aside>

	<main class="min-w-0 px-4 py-6 lg:px-10 lg:py-8">
		<div class="mx-auto max-w-6xl">
			{@render children()}
		</div>
	</main>
</div>
