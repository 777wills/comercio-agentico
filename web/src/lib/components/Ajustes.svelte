<script lang="ts">
	// Ajustes del modo Cliente (D111): solo la clave de OpenRouter y el modelo.
	import { ajustes, config, visita } from '#lib/config.svelte.js';
	import { catalogo } from '#lib/datos.js';
	import { usd } from '#lib/api.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Input } from '#lib/components/ui/input/index.js';
	import { Label } from '#lib/components/ui/label/index.js';
	import { Switch } from '#lib/components/ui/switch/index.js';
	import Check from '@lucide/svelte/icons/check';

	const cat = catalogo();
	let mostrar = $state(false);
</script>

<Dialog.Root bind:open={ajustes.abierto}>
	<Dialog.Content class="gap-6 p-6 sm:max-w-md">
		<Dialog.Header>
			<Dialog.Title class="text-base">Ajustes</Dialog.Title>
			<Dialog.Description>
				Cada cotización se paga con su propia clave de OpenRouter. El servidor no la guarda.
			</Dialog.Description>
		</Dialog.Header>

		<div class="space-y-2">
			<Label for="clave">Clave de OpenRouter</Label>
			<div class="flex gap-2">
				<Input
					id="clave"
					type={mostrar ? 'text' : 'password'}
					autocomplete="off"
					spellcheck={false}
					placeholder="sk-or-v1-…"
					bind:value={config.clave}
				/>
				<Button variant="ghost" onclick={() => (mostrar = !mostrar)}>
					{mostrar ? 'Ocultar' : 'Ver'}
				</Button>
			</div>
			<div class="flex items-center justify-between pt-1 text-xs text-muted-foreground">
				<label class="flex items-center gap-2">
					<Switch bind:checked={config.recordar} />
					Recordar en este navegador
				</label>
				{#if config.clave}
					<button class="hover:text-foreground" onclick={() => config.olvidarClave()}>Olvidar</button>
				{/if}
			</div>
		</div>

		<div class="space-y-2">
			<Label>Modelo</Label>
			{#await cat then c}
				<div class="divide-y rounded-lg border">
					{#each c.modelos as m (m.nombre)}
						<button
							type="button"
							class="flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm transition-colors hover:bg-muted/50"
							onclick={() => (config.modelo = m.nombre)}
						>
							<span class="flex-1">{m.etiqueta}</span>
							<span class="text-xs text-muted-foreground">≈ {usd(m.costo_usd, 2)} por consulta</span>
							<Check class="size-4 text-primary {config.modelo === m.nombre ? '' : 'invisible'}" />
						</button>
					{/each}
				</div>
			{/await}
		</div>

		{#await cat then c}
			{#if c.trazas}
				<p class="text-xs text-muted-foreground">
					Para diagnóstico, el servidor registra en LangSmith cada paso de la consulta (texto de la
					consulta, páginas leídas y respuestas del modelo), nunca la clave. Se conserva 14 días.
				</p>
			{/if}
		{/await}

		<p class="text-xs text-muted-foreground">
			En esta visita: {visita.total}
			{visita.total === 1 ? 'consulta' : 'consultas'} · {usd(visita.gasto)}
		</p>
	</Dialog.Content>
</Dialog.Root>
