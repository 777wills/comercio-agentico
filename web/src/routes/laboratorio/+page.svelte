<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { crearConsulta, ErrorApi, pct, type AtaqueCorpus } from '#lib/api.js';
	import { config, PRESETS, UMBRAL_INFORME } from '#lib/config.svelte.js';
	import { indiceCorpus, nombresFuentes, CLASES, UBICACIONES } from '#lib/datos.js';
	import { obtener } from '#lib/api.js';
	import Ejecucion from '#lib/components/Ejecucion.svelte';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Alert from '#lib/components/ui/alert/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import Swords from '@lucide/svelte/icons/swords';
	import Eye from '@lucide/svelte/icons/eye';

	const LADOS = ['C0', 'C3'] as const;

	let ataques = $state<AtaqueCorpus[]>([]);
	let nombres = $state<Record<string, string>>({});
	let elegida = $state('A20');
	let ids = $state<Record<string, string | null>>({ C0: null, C3: null });
	let enviando = $state(false);
	let m5 = $state<Record<string, { k: number; n: number; p: number }>>({});

	const carga = $derived(ataques.find((a) => a.carga === elegida));

	onMount(async () => {
		[ataques, nombres] = await Promise.all([
			indiceCorpus().then((i) => i.ataques),
			nombresFuentes()
		]);
		const res = await obtener<any>('/api/resultados');
		m5 = Object.fromEntries(
			(res.e2.datos?.puntos ?? []).map((p: any) => [p.configuracion, p.m5])
		);
	});

	async function correr() {
		if (!config.clave) {
			toast.error('Configure su clave de OpenRouter para ejecutar el laboratorio.');
			return;
		}
		enviando = true;
		ids = { C0: null, C3: null };
		try {
			for (const lado of LADOS) {
				const [s, k, p] = PRESETS[lado];
				const r = await crearConsulta(
					{
						carga: elegida,
						corpus: 'b',
						modelo: config.modelo,
						defensas: { separacion_planos: s, clasificador: k, precio: p, umbral: UMBRAL_INFORME },
						clasificador: config.clasificador,
						verificar: false,
						politica_n3: 'abstener'
					},
					config.clave,
					config.visitante
				);
				ids[lado] = r.id;
			}
		} catch (e) {
			toast.error(e instanceof ErrorApi ? e.message : 'No se pudo iniciar el laboratorio.');
		} finally {
			enviando = false;
		}
	}
</script>

<div class="space-y-6">
	<div>
		<h1 class="flex items-center gap-2 text-2xl font-semibold">
			<Swords class="size-6 text-primary" /> Laboratorio de ataques
		</h1>
		<p class="max-w-3xl text-sm text-muted-foreground">
			Elija una de las 20 cargas de inyección indirecta plantadas en una copia local del corpus B. La
			misma tarea corre dos veces con su modelo: sin defensas (C0) y con todas las capas (C3). Así se ve
			la tesis en vivo: el texto de un proveedor intenta dar órdenes al agente.
		</p>
	</div>

	{#if Object.keys(m5).length}
		<div class="flex flex-wrap gap-2 text-xs">
			<span class="text-muted-foreground">Éxito del ataque medido en E2 (DeepSeek Flash, 60 ejecuciones):</span>
			{#each Object.entries(m5) as [c, v] (c)}
				<Badge variant={v.k ? 'destructive' : 'secondary'}>{c}: {v.k}/{v.n} ({pct(v.p)})</Badge>
			{/each}
		</div>
	{/if}

	<Card.Root>
		<Card.Content class="grid gap-4 lg:grid-cols-[minmax(0,20rem)_1fr]">
			<div class="max-h-96 space-y-1 overflow-y-auto pr-2">
				{#each ataques as a (a.carga)}
					<button
						type="button"
						onclick={() => (elegida = a.carga)}
						class="w-full rounded-md border px-3 py-2 text-left text-xs transition-colors hover:border-primary/50 {elegida ===
						a.carga
							? 'border-primary bg-primary/10'
							: 'border-transparent'}"
					>
						<span class="font-mono font-semibold">{a.carga}</span>
						· {CLASES[a.clase] ?? a.clase}
						<div class="text-muted-foreground">{UBICACIONES[a.ubicacion]} · {nombres[a.proveedor]}</div>
					</button>
				{/each}
			</div>
			{#if carga}
				<div class="space-y-3 text-sm">
					<div class="flex flex-wrap gap-2">
						<Badge>{carga.carga}</Badge>
						<Badge variant="outline">{CLASES[carga.clase]}</Badge>
						<Badge variant="outline">{UBICACIONES[carga.ubicacion]}</Badge>
						<Badge variant="outline">{nombres[carga.proveedor]} ({carga.proveedor})</Badge>
					</div>
					<div>
						<div class="text-xs text-muted-foreground">Objetivo del atacante</div>
						<p>{carga.objetivo}</p>
					</div>
					<div>
						<div class="text-xs text-muted-foreground">Texto plantado en <span class="font-mono">{carga.archivo}</span></div>
						<blockquote class="mt-1 rounded-md border-l-4 border-destructive bg-destructive/10 p-3 text-xs">
							{carga.texto}
						</blockquote>
					</div>
					<div class="flex flex-wrap gap-2">
						<Button disabled={enviando} onclick={correr}><Swords /> Correr C0 y C3</Button>
						<Button variant="outline" href="/corpus?carga={carga.carga}"><Eye /> Ver la página atacada</Button>
					</div>
					<p class="text-xs text-muted-foreground">
						Son dos consultas con su clave (≈ 2 × el costo del modelo elegido); corren una tras otra.
						El éxito se decide por programa con el predicado de la carga, sin juicio humano.
					</p>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>

	{#if ids.C0 || ids.C3}
		<div class="grid gap-4 xl:grid-cols-2">
			{#each LADOS as lado (lado)}
				<div class="space-y-2">
					<h2 class="font-semibold">
						{lado} · {lado === 'C0' ? 'sin defensas' : 'separación + clasificador + precio'}
					</h2>
					{#if ids[lado]}
						{#key ids[lado]}
							<Ejecucion id={ids[lado]!} {nombres} compacto />
						{/key}
					{:else}
						<Alert.Root><Alert.Description>Creando la consulta…</Alert.Description></Alert.Root>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
