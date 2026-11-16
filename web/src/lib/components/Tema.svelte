<script lang="ts">
	// Selector de tema (D139): claro por defecto, oscuro o el del sistema; mode-watcher lo recuerda.
	import { userPrefersMode, setMode } from 'mode-watcher';
	import Sun from '@lucide/svelte/icons/sun';
	import Moon from '@lucide/svelte/icons/moon';
	import Monitor from '@lucide/svelte/icons/monitor';

	const OPCIONES = [
		{ valor: 'light', nombre: 'Tema claro', Icono: Sun },
		{ valor: 'dark', nombre: 'Tema oscuro', Icono: Moon },
		{ valor: 'system', nombre: 'Tema del sistema', Icono: Monitor }
	] as const;
</script>

<div role="radiogroup" aria-label="Tema" class="inline-flex items-center rounded-full border p-0.5">
	{#each OPCIONES as { valor, nombre, Icono } (valor)}
		<button
			type="button"
			role="radio"
			aria-checked={userPrefersMode.current === valor}
			aria-label={nombre}
			title={nombre}
			class="grid size-7 place-items-center rounded-full transition-colors {userPrefersMode.current ===
			valor
				? 'bg-secondary text-foreground'
				: 'text-muted-foreground hover:text-foreground'}"
			onclick={() => setMode(valor)}
		>
			<Icono class="size-3.5" />
		</button>
	{/each}
</div>
