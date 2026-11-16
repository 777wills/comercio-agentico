<script lang="ts">
	import { page } from '$app/state';
	import VistaConsulta from '#lib/components/VistaConsulta.svelte';
</script>

<svelte:head><title>CotIA · cotización</title></svelte:head>

{#key page.params.id}
	<VistaConsulta id={page.params.id!} />
{/key}
