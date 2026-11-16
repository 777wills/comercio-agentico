<script lang="ts">
	// Las consultas viven ahora en la barra lateral (D140); la ruta se conserva para no romper enlaces.
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => goto('/', { replaceState: true }));
</script>
