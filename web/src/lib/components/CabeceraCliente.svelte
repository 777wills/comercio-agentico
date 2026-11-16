<script lang="ts">
	// Cabecera del modo Cliente (D140): abre o colapsa la barra lateral; la marca aparece cuando la barra no
	// está a la vista (móvil o colapsada).
	import * as Sidebar from '#lib/components/ui/sidebar/index.js';

	const sidebar = Sidebar.useSidebar();
</script>

<header class="sticky top-0 z-20 flex items-center gap-2 bg-background/90 px-3 py-3 backdrop-blur sm:px-4">
	<Sidebar.Trigger class="size-9" aria-label="Mostrar u ocultar las consultas" />
	{#if sidebar.isMobile || !sidebar.open}
		<a href="/" class="text-base font-semibold tracking-tight">Cot<span class="text-primary">IA</span></a>
	{/if}
</header>
