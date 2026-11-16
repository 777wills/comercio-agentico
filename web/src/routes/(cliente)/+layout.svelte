<script lang="ts">
	import type { LayoutProps } from './$types';
	import { ajustes, config } from '#lib/config.svelte.js';
	import Ajustes from '#lib/components/Ajustes.svelte';
	import Tema from '#lib/components/Tema.svelte';

	let { children }: LayoutProps = $props();
</script>

<div class="flex min-h-screen flex-col">
	<header class="mx-auto flex w-full max-w-5xl items-center gap-4 px-4 py-4 text-sm sm:gap-6 sm:px-6 sm:py-5">
		<a href="/" class="text-base font-semibold tracking-tight">Cot<span class="text-primary">IA</span></a>
		<nav class="ml-auto flex items-center gap-4 text-muted-foreground sm:gap-5">
			<a href="/mis-consultas" class="transition-colors hover:text-foreground">Mis consultas</a>
			<button
				class="flex items-center gap-2 transition-colors hover:text-foreground"
				onclick={() => (ajustes.abierto = true)}
			>
				<span class="size-1.5 rounded-full {config.clave ? 'bg-primary' : 'bg-muted-foreground/50'}"></span>
				Ajustes
			</button>
			<Tema />
		</nav>
	</header>

	<main class="mx-auto w-full max-w-5xl flex-1 px-4 sm:px-6">
		{@render children()}
	</main>

	<footer
		class="mx-auto flex w-full max-w-5xl flex-wrap items-center gap-x-4 gap-y-1 border-t px-4 py-6 text-xs text-muted-foreground sm:px-6"
	>
		<span>CotIA recomienda; no ejecuta pagos ni compras.</span>
		<a href="/lab" class="ml-auto transition-colors hover:text-foreground">Laboratorio del experimento</a>
	</footer>
</div>

<Ajustes />
