<script lang="ts">
	import './layout.css';
	import favicon from '#lib/assets/favicon.svg';
	import type { LayoutProps } from './$types';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { Toaster } from '#lib/components/ui/sonner/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import { config, visita } from '#lib/config.svelte.js';
	import { usd } from '#lib/api.js';
	import KeyRound from '@lucide/svelte/icons/key-round';
	import ShieldCheck from '@lucide/svelte/icons/shield-check';

	let { children }: LayoutProps = $props();

	const secciones = [
		['/', 'Consulta'],
		['/laboratorio', 'Laboratorio de ataques'],
		['/corpus', 'Corpus'],
		['/resultados', 'Resultados'],
		['/historial', 'Historial'],
		['/configuracion', 'Configuración']
	];

	const activa = (ruta: string) =>
		ruta === '/' ? page.url.pathname === '/' : page.url.pathname.startsWith(ruta);

	onMount(() => {
		visita.refrescar().catch(() => {});
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="flex min-h-screen flex-col">
	<header class="sticky top-0 z-40 border-b bg-background/85 backdrop-blur">
		<div class="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
			<a href="/" class="flex items-center gap-2 font-semibold tracking-tight">
				<ShieldCheck class="size-5 text-primary" />
				<span class="text-lg">Cot<span class="text-primary">IA</span></span>
			</a>
			<nav class="flex flex-wrap gap-1 text-sm">
				{#each secciones as [ruta, nombre] (ruta)}
					<a
						href={ruta}
						class="rounded-md px-2.5 py-1.5 transition-colors hover:bg-muted {activa(ruta)
							? 'bg-muted text-foreground'
							: 'text-muted-foreground'}">{nombre}</a
					>
				{/each}
			</nav>
			<div class="ml-auto flex items-center gap-2 text-xs">
				<Badge variant="outline" title="Consultas y gasto de esta visita con su clave (D90)">
					{visita.total} {visita.total === 1 ? 'consulta' : 'consultas'} · {usd(visita.gasto)}
				</Badge>
				<a href="/configuracion">
					<Badge variant={config.clave ? 'secondary' : 'destructive'}>
						<KeyRound class="size-3" />
						{config.clave ? 'Clave configurada' : 'Sin clave'}
					</Badge>
				</a>
			</div>
		</div>
	</header>

	<main class="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
		{@render children()}
	</main>

	<footer class="border-t py-4 text-center text-xs text-muted-foreground">
		CotIA recomienda; <strong>no ejecuta pagos ni compras</strong>. Cada consulta corre en vivo con
		la clave de OpenRouter del visitante. Prototipo académico · Maestría en IA Aplicada, Universidad
		Icesi.
	</footer>
</div>

<Toaster richColors position="bottom-right" />
