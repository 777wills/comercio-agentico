<script lang="ts">
	import type { LayoutProps } from './$types';
	import { page } from '$app/state';
	import { config, visita } from '#lib/config.svelte.js';
	import { usd } from '#lib/api.js';
	import Tema from '#lib/components/Tema.svelte';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';

	// Modo Laboratorio (D111): todo el instrumental del experimento. Barra lateral en escritorio y
	// barra superior en móvil, con el regreso al modo cliente siempre visible (D139).
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

<div class="min-h-screen lg:grid lg:grid-cols-[15rem_1fr]">
	<aside
		class="sticky top-0 z-40 flex flex-col gap-3 border-b bg-background/95 px-4 pt-3 backdrop-blur lg:h-screen lg:gap-4 lg:border-r lg:border-b-0 lg:bg-muted/40 lg:px-3 lg:py-6"
	>
		<div class="flex items-center gap-3 lg:px-2">
			<a href="/lab" class="text-sm font-semibold tracking-tight">
				Cot<span class="text-primary">IA</span>
				<span class="ml-1 font-normal text-muted-foreground">laboratorio</span>
			</a>
			<a
				href="/"
				class="ml-auto inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:text-foreground lg:hidden"
				><ArrowLeft class="size-3" /> Modo cliente</a
			>
			<div class="lg:hidden"><Tema /></div>
		</div>
		<nav class="sin-barra -mx-4 flex gap-1 overflow-x-auto px-4 pb-2 text-sm lg:mx-0 lg:flex-col lg:px-0 lg:pb-0">
			{#each SECCIONES as [ruta, nombre] (ruta)}
				<a
					href={ruta}
					aria-current={activa(ruta) ? 'page' : undefined}
					class="shrink-0 rounded-md px-2.5 py-1.5 whitespace-nowrap transition-colors {activa(ruta)
						? 'bg-secondary font-medium text-foreground'
						: 'text-muted-foreground hover:text-foreground'}">{nombre}</a
				>
			{/each}
		</nav>
		<a
			href="/lab/configuracion"
			class="-mt-1 flex items-center gap-2 pb-2.5 text-xs text-muted-foreground lg:hidden"
		>
			<span class="size-1.5 shrink-0 rounded-full {config.clave ? 'bg-primary' : 'bg-destructive'}"></span>
			<span class="truncate"
				>{config.clave ? 'Clave configurada' : 'Sin clave'} · defensas {config.configuracion} · {visita.total}
				consultas · {usd(visita.gasto)}</span
			>
		</a>
		<div class="mt-auto hidden space-y-3 px-2 text-xs text-muted-foreground lg:block">
			<a href="/lab/configuracion" class="flex items-center gap-2 hover:text-foreground">
				<span class="size-1.5 rounded-full {config.clave ? 'bg-primary' : 'bg-destructive'}"></span>
				{config.clave ? 'Clave configurada' : 'Sin clave'}
			</a>
			<div class="cifra">Defensas {config.configuracion} · {visita.total} consultas · {usd(visita.gasto)}</div>
			<Tema />
			<a href="/" class="flex items-center gap-1 hover:text-foreground"
				><ArrowLeft class="size-3" /> Modo cliente</a
			>
		</div>
	</aside>

	<main class="min-w-0 px-4 py-6 lg:px-10 lg:py-8">
		<div class="mx-auto max-w-6xl">
			{@render children()}
		</div>
	</main>
</div>
