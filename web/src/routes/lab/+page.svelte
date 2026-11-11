<script lang="ts">
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { crearConsulta, ErrorApi } from '#lib/api.js';
	import { config } from '#lib/config.svelte.js';
	import { catalogo, ejemplos } from '#lib/datos.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Tabs from '#lib/components/ui/tabs/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Textarea } from '#lib/components/ui/textarea/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import Send from '@lucide/svelte/icons/send';
	import Settings from '@lucide/svelte/icons/settings';

	let consulta = $state('');
	let enviando = $state(false);
	const ej = ejemplos();
	const cat = catalogo();
	const CATEGORIAS: Record<string, string> = {
		especifica: 'Producto específico',
		mas_barato: 'El más barato',
		vaga: 'Necesidad vaga',
		restricciones: 'Con restricciones',
		sin_respuesta: 'Sin respuesta válida'
	};

	async function enviar() {
		if (!config.clave) {
			toast.error('Configure su clave de OpenRouter para ejecutar consultas.');
			return;
		}
		enviando = true;
		try {
			const r = await crearConsulta(
				{
					consulta,
					corpus: config.corpus,
					modelo: config.modelo,
					defensas: config.defensas,
					clasificador: config.clasificador,
					verificar: config.verificar,
					politica_n3: config.politica_n3
				},
				config.clave,
				config.visitante
			);
			await goto(`/lab/consultas/${r.id}`);
		} catch (e) {
			toast.error(e instanceof ErrorApi ? e.message : 'No se pudo crear la consulta.');
		} finally {
			enviando = false;
		}
	}
</script>

<section class="max-w-3xl space-y-6">
	<div>
		<h1 class="text-2xl font-semibold tracking-tight">Consulta</h1>
		<p class="text-sm text-muted-foreground">
			Consulta con todos los controles del experimento: corpus, modelo, capas de defensa y N3 (se
			cambian en Configuración). Muestra los eventos del agente y la procedencia completa.
		</p>
	</div>

	<Card.Root>
		<Card.Content class="space-y-4">
			<Tabs.Root bind:value={config.corpus}>
				<Tabs.List class="w-full">
					<Tabs.Trigger value="b">Corpus B · proveedores sintéticos (P1–P5)</Tabs.Trigger>
					<Tabs.Trigger value="a">Corpus A · tiendas colombianas reconstruidas</Tabs.Trigger>
				</Tabs.List>
			</Tabs.Root>

			<Textarea
				bind:value={consulta}
				rows={3}
				maxlength={500}
				placeholder="Ej.: Necesito 2 monitores de 27 pulgadas 4K por menos de 3 millones con entrega en 5 días"
				onkeydown={(e) => {
					if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && consulta.trim().length >= 3) enviar();
				}}
			/>

			{#await ej then ejs}
				<div class="flex flex-wrap gap-2">
					{#each ejs[config.corpus] as e (e.categoria)}
						<button
							type="button"
							class="rounded-full border px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
							title={e.consulta}
							onclick={() => (consulta = e.consulta)}>{CATEGORIAS[e.categoria] ?? e.categoria}</button
						>
					{/each}
				</div>
			{/await}

			<div class="flex flex-wrap items-center gap-2 border-t pt-4 text-xs text-muted-foreground">
				{#await cat then c}
					<Badge variant="outline">
						{c.modelos.find((m) => m.nombre === config.modelo)?.etiqueta ?? config.modelo}
					</Badge>
				{/await}
				<Badge variant="outline">Defensas {config.configuracion}</Badge>
				{#if config.verificar}<Badge variant="outline">N3 · {config.politica_n3}</Badge>{/if}
				<a href="/lab/configuracion" class="inline-flex items-center gap-1 hover:text-foreground">
					<Settings class="size-3" /> cambiar
				</a>
				<Button
					class="ml-auto"
					disabled={enviando || consulta.trim().length < 3}
					onclick={enviar}
				>
					<Send /> Cotizar
				</Button>
			</div>
			{#if !config.clave}
				<p class="text-xs text-amber-400">
					Puede navegar todo CotIA sin clave; para ejecutar una consulta, configure su clave de
					OpenRouter en <a class="underline" href="/lab/configuracion">Configuración</a>. La clave no se
					guarda en el servidor.
				</p>
			{/if}
		</Card.Content>
	</Card.Root>

	</section>
