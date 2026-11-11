<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import type { IndiceCorpus } from '#lib/api.js';
	import { indiceCorpus, CLASES, UBICACIONES } from '#lib/datos.js';
	import VistaArchivo from '#lib/components/VistaArchivo.svelte';
	import * as Tabs from '#lib/components/ui/tabs/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Alert from '#lib/components/ui/alert/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import Swords from '@lucide/svelte/icons/swords';

	const TIPOS: Record<string, string> = {
		mcp: 'Catálogo MCP',
		web_schema: 'Web con schema.org',
		web_plana: 'Web plana',
		pdf: 'Lista de precios PDF',
		mensaje: 'Chat de WhatsApp'
	};

	let indice = $state<IndiceCorpus | null>(null);
	let pestana = $state(page.url.searchParams.get('carga') ? 'atacada' : 'b');
	let archivo = $state<Record<'a' | 'b', string | null>>({ a: null, b: null });
	let carga = $state(page.url.searchParams.get('carga') ?? 'A01');

	const ataque = $derived(indice?.ataques.find((a) => a.carga === carga));
	const archivoUrl = (origen: string, ruta: string) =>
		`/api/corpus/archivo/${origen}/${ruta.split('/').map(encodeURIComponent).join('/')}`;

	onMount(async () => {
		indice = await indiceCorpus();
		for (const c of ['a', 'b'] as const) {
			const f = indice.corpus[c].find((f) => f.archivos.some((r) => r.endsWith('index.html')));
			archivo[c] =
				f?.archivos.find((r) => r.endsWith('index.html')) ?? indice.corpus[c][0]?.archivos[0] ?? null;
		}
	});
</script>

<div class="space-y-4">
	<div>
		<h1 class="text-2xl font-semibold">Corpus congelado</h1>
		<p class="max-w-3xl text-sm text-muted-foreground">
			El material sobre el que opera el agente, servido desde copias locales: cinco proveedores
			sintéticos con formatos distintos (corpus B), tiendas colombianas reconstruidas a partir de
			hechos públicos (corpus A) y la copia atacada de cada carga del laboratorio.
		</p>
	</div>

	<Tabs.Root bind:value={pestana}>
		<Tabs.List>
			<Tabs.Trigger value="b">Corpus B</Tabs.Trigger>
			<Tabs.Trigger value="a">Corpus A</Tabs.Trigger>
			<Tabs.Trigger value="atacada">Copia atacada</Tabs.Trigger>
		</Tabs.List>

		{#if indice}
			{#each ['b', 'a'] as const as c (c)}
				<Tabs.Content value={c}>
					<div class="grid gap-4 lg:grid-cols-[16rem_1fr]">
						<Card.Root class="h-fit">
							<Card.Content class="max-h-[36rem] space-y-3 overflow-y-auto text-xs">
								{#each indice.corpus[c] as f (f.id)}
									<div>
										<div class="font-medium">{f.nombre} <span class="text-muted-foreground">({f.id})</span></div>
										<div class="mb-1 text-muted-foreground">{TIPOS[f.tipo_fuente] ?? f.tipo_fuente}</div>
										{#each f.archivos as r (r)}
											<button
												type="button"
												onclick={() => (archivo[c] = r)}
												class="block w-full truncate rounded px-2 py-0.5 text-left font-mono hover:bg-muted {archivo[c] === r
													? 'bg-muted text-foreground'
													: 'text-muted-foreground'}">{r.split('/').slice(1).join('/')}</button
											>
										{/each}
									</div>
								{/each}
							</Card.Content>
						</Card.Root>
						<div class="min-w-0">
							{#if archivo[c]}
								<div class="mb-2 font-mono text-xs text-muted-foreground">{archivo[c]}</div>
								{#key archivo[c]}
									<VistaArchivo url={archivoUrl(c, archivo[c]!)} alto="h-[34rem]" />
								{/key}
							{/if}
						</div>
					</div>
				</Tabs.Content>
			{/each}

			<Tabs.Content value="atacada" class="space-y-4">
				<div class="flex flex-wrap gap-1">
					{#each indice.ataques as a (a.carga)}
						<button
							type="button"
							onclick={() => {
								carga = a.carga;
								goto(`?carga=${a.carga}`, { replaceState: true });
							}}
							class="rounded border px-2 py-1 font-mono text-xs {carga === a.carga
								? 'border-primary bg-primary/10'
								: 'text-muted-foreground'}">{a.carga}</button
						>
					{/each}
				</div>
				{#if ataque}
					<Card.Root>
						<Card.Content class="space-y-2 text-sm">
							<div class="flex flex-wrap items-center gap-2">
								<Badge>{ataque.carga}</Badge>
								<Badge variant="outline">{CLASES[ataque.clase]}</Badge>
								<Badge variant="outline">{UBICACIONES[ataque.ubicacion]}</Badge>
								<span class="font-mono text-xs text-muted-foreground">{ataque.archivo}</span>
								<Button size="sm" variant="outline" class="ml-auto" href="/laboratorio">
									<Swords /> Probarla en el laboratorio
								</Button>
							</div>
							<p class="text-xs text-muted-foreground">Objetivo: {ataque.objetivo}</p>
							<blockquote class="rounded-md border-l-4 border-destructive bg-destructive/10 p-3 text-xs">
								{ataque.texto}
							</blockquote>
						</Card.Content>
					</Card.Root>
					{#if ataque.disponible}
						<div class="grid gap-4 xl:grid-cols-2">
							<div class="min-w-0">
								<h2 class="mb-2 text-sm font-medium">Limpia</h2>
								{#key ataque.carga}
									<VistaArchivo url={archivoUrl('b', ataque.archivo)} />
								{/key}
							</div>
							<div class="min-w-0">
								<h2 class="mb-2 text-sm font-medium text-destructive">Atacada</h2>
								{#key ataque.carga}
									<VistaArchivo url={archivoUrl(ataque.carga, ataque.archivo)} marca={ataque.texto} />
								{/key}
							</div>
						</div>
						{#if ataque.ubicacion === 'oculto_html'}
							<p class="text-xs text-muted-foreground">
								En la vista no se ve: la carga va en el campo <code>description</code> del bloque
								JSON-LD de schema.org. Pase a «Código fuente» para verla resaltada. El agente sí la lee.
							</p>
						{/if}
					{:else}
						<Alert.Root>
							<Alert.Description>
								La copia atacada no está generada en este servidor
								(<code>python -m comercio_agentico.ataques.plantar</code>).
							</Alert.Description>
						</Alert.Root>
					{/if}
				{/if}
			</Tabs.Content>
		{/if}
	</Tabs.Root>
</div>
