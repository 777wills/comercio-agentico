<script lang="ts">
	import type { LayoutProps } from './$types';
	import * as Sidebar from '#lib/components/ui/sidebar/index.js';
	import Ajustes from '#lib/components/Ajustes.svelte';
	import BarraConsultas from '#lib/components/BarraConsultas.svelte';
	import CabeceraCliente from '#lib/components/CabeceraCliente.svelte';

	// Modo Cliente (D111) con el historial en una barra lateral (D140).
	let { children }: LayoutProps = $props();
</script>

<Sidebar.Provider>
	<BarraConsultas />
	<Sidebar.Inset class="min-w-0">
		<CabeceraCliente />
		<main class="mx-auto w-full max-w-5xl flex-1 px-4 sm:px-6">
			{@render children()}
		</main>
		<footer class="mx-auto w-full max-w-5xl px-4 py-6 text-xs text-muted-foreground sm:px-6">
			CotIA recomienda; no ejecuta pagos ni compras.
		</footer>
	</Sidebar.Inset>
</Sidebar.Provider>

<Ajustes />
