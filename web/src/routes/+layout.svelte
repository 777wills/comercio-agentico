<script lang="ts">
	import './layout.css';
	import favicon from '#lib/assets/favicon.svg';
	import type { LayoutProps } from './$types';
	import { onMount } from 'svelte';
	import { Toaster } from '#lib/components/ui/sonner/index.js';
	import { ModeWatcher } from 'mode-watcher';
	import { visita } from '#lib/config.svelte.js';

	// Raíz común a los dos modos (D111): Cliente en (cliente)/ y Laboratorio en lab/.
	let { children }: LayoutProps = $props();

	onMount(() => {
		visita.refrescar().catch(() => {});
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<ModeWatcher defaultMode="light" modeStorageKey="cotia.tema" themeColors={{ light: '#f5f7f8', dark: '#1a1a1a' }} />
{@render children()}

<Toaster position="bottom-right" />
