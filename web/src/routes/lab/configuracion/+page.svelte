<script lang="ts">
	import { config, visita, PRESETS, UMBRAL_INFORME } from '#lib/config.svelte.js';
	import { catalogo } from '#lib/datos.js';
	import { usd, pct } from '#lib/api.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Alert from '#lib/components/ui/alert/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Input } from '#lib/components/ui/input/index.js';
	import { Label } from '#lib/components/ui/label/index.js';
	import { Switch } from '#lib/components/ui/switch/index.js';
	import { Slider } from '#lib/components/ui/slider/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import FlaskConical from '@lucide/svelte/icons/flask-conical';

	const cat = catalogo();
	let mostrar = $state(false);

	const CAPAS = [
		[
			'separacion_planos',
			'Separación de planos',
			'El planificador no ve el texto de los proveedores; solo el extractor lo lee, con salida estructurada.'
		],
		[
			'clasificador',
			'Clasificador de inyección',
			'Un modelo local de Hugging Face marca y retira los fragmentos con instrucciones antes de extraer.'
		],
		[
			'precio',
			'Verificación de precio',
			'Excluye precios fuera de la banda del catálogo y lejos de la mediana del mercado.'
		]
	] as const;

	const DESCRIPCION_PRESET: Record<string, string> = {
		C0: 'Sin defensas',
		C1: 'Separación de planos',
		C2: 'C1 + clasificador (por defecto)',
		C3: 'C2 + verificación de precio'
	};
</script>

<div class="mx-auto max-w-4xl space-y-6">
	<div>
		<h1 class="text-2xl font-semibold">Configuración</h1>
		<p class="text-sm text-muted-foreground">
			Todo lo que controla el visitante. Se guarda solo en este navegador.
		</p>
	</div>

	<Card.Root>
		<Card.Header>
			<Card.Title>Clave de OpenRouter</Card.Title>
			<Card.Description>
				CotIA no trae créditos propios: cada consulta se paga con su clave. Viaja por HTTPS solo al
				crear la consulta; el servidor la usa en memoria y no la guarda ni la registra.
				{#await cat then c}
					{#if c.trazas}
						Para diagnóstico, cada paso de la consulta (sin la clave) se registra en LangSmith
						durante 14 días.
					{/if}
				{/await}
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-3">
			<div class="flex gap-2">
				<Input
					type={mostrar ? 'text' : 'password'}
					autocomplete="off"
					spellcheck={false}
					placeholder="sk-or-v1-…"
					bind:value={config.clave}
				/>
				<Button variant="outline" onclick={() => (mostrar = !mostrar)}>
					{mostrar ? 'Ocultar' : 'Mostrar'}
				</Button>
				<Button variant="destructive" disabled={!config.clave} onclick={() => config.olvidarClave()}>
					Olvidar
				</Button>
			</div>
			<div class="flex items-center gap-2">
				<Switch id="recordar" bind:checked={config.recordar} />
				<Label for="recordar" class="text-sm font-normal">
					Recordar en este navegador (si no, se borra al cerrar la pestaña)
				</Label>
			</div>
			<p class="text-xs text-muted-foreground">
				Recomendación: cree una clave exclusiva para CotIA con un límite de gasto bajo en su cuenta de
				OpenRouter. Gasto de esta visita: <strong>{visita.total}</strong> consultas,
				<strong>{usd(visita.gasto)}</strong>.
			</p>
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header>
			<Card.Title>Modelo</Card.Title>
			<Card.Description>
				Solo los que superaron la prueba de humo del agente completo y tienen desempeño con evidencia.
				El costo es el medido en esa prueba (una consulta del corpus B).
			</Card.Description>
		</Card.Header>
		<Card.Content>
			{#await cat}
				<p class="text-sm text-muted-foreground">Cargando…</p>
			{:then c}
				<div class="grid gap-3 sm:grid-cols-3">
					{#each c.modelos as m (m.nombre)}
						<button
							type="button"
							onclick={() => (config.modelo = m.nombre)}
							class="rounded-lg border p-3 text-left transition-colors hover:border-primary/50 {config.modelo ===
							m.nombre
								? 'border-primary bg-primary/10'
								: ''}"
						>
							<div class="font-medium">{m.etiqueta}</div>
							<div class="mt-1 font-mono text-xs text-muted-foreground">{m.id_modelo}</div>
							<div class="mt-2 space-y-0.5 text-xs">
								<div>≈ {usd(m.costo_usd, 3)} · {Math.round(m.segundos)} s por consulta</div>
								{#if m.m2_e3}
									<div class="text-muted-foreground">
										Acierto E3: {pct(m.m2_e3.m2_media)} [{pct(m.m2_e3.m2_bajo, 0)}; {pct(
											m.m2_e3.m2_alto,
											0
										)}]
									</div>
								{:else if m.acierto}
									<div class="text-muted-foreground">Acertó la tarea de la prueba de humo</div>
								{/if}
							</div>
						</button>
					{/each}
				</div>
			{/await}
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header>
			<Card.Title class="flex items-center gap-2">
				Defensas
				<Badge variant={config.configuracion === 'exploratorio' ? 'destructive' : 'secondary'}>
					{config.configuracion}
				</Badge>
			</Card.Title>
			<Card.Description>
				Active cada capa por separado o use un preset. C0–C3 son los puntos medidos en E2; cualquier
				otra combinación es exploratoria y no tiene cifras en el informe.
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-5">
			<div class="grid gap-2 sm:grid-cols-4">
				{#each Object.keys(PRESETS) as c (c)}
					<Button
						variant={config.configuracion === c ? 'default' : 'outline'}
						class="h-auto flex-col items-start py-2"
						onclick={() => config.aplicarPreset(c)}
					>
						<span class="font-semibold">{c}</span>
						<span class="text-xs font-normal whitespace-normal opacity-80">{DESCRIPCION_PRESET[c]}</span>
					</Button>
				{/each}
			</div>

			<div class="space-y-3">
				{#each CAPAS as [clave, nombre, texto] (clave)}
					<div class="flex items-start gap-3">
						<Switch id={clave} bind:checked={config.defensas[clave]} class="mt-0.5" />
						<div>
							<Label for={clave}>{nombre}</Label>
							<p class="text-xs text-muted-foreground">{texto}</p>
						</div>
					</div>
				{/each}
			</div>

			{#if config.defensas.clasificador}
				<div class="space-y-2 rounded-lg border p-4">
					<div class="flex items-center justify-between text-sm">
						<Label>Umbral del clasificador</Label>
						<span class="font-mono">{config.defensas.umbral.toFixed(2)}</span>
					</div>
					<Slider
						type="single"
						min={0.05}
						max={0.95}
						step={0.05}
						bind:value={config.defensas.umbral}
					/>
					<p class="text-xs text-muted-foreground">
						Más bajo detecta más cargas pero arriesga retirar texto comercial legítimo (falsos
						positivos); más alto deja pasar más. El informe se midió a {UMBRAL_INFORME}: con 0,5 el
						clasificador elegido tuvo 0 falsos positivos en 47 fragmentos limpios en español.
					</p>
					{#if config.defensas.umbral !== UMBRAL_INFORME}
						<Alert.Root>
							<FlaskConical />
							<Alert.Title>Modo exploratorio</Alert.Title>
							<Alert.Description>Este umbral no tiene cifras medidas en E2.</Alert.Description>
						</Alert.Root>
					{/if}

					<div class="pt-2">
						<Label>Clasificador</Label>
						{#await cat then c}
							<div class="mt-2 grid gap-3 sm:grid-cols-2">
								{#each Object.entries(c.clasificadores) as [id, k] (id)}
									<button
										type="button"
										onclick={() => (config.clasificador = id)}
										class="rounded-lg border p-3 text-left text-xs transition-colors hover:border-primary/50 {config.clasificador ===
										id
											? 'border-primary bg-primary/10'
											: ''}"
									>
										<div class="text-sm font-medium">{k.etiqueta}</div>
										<p class="mt-1 text-muted-foreground">{k.descripcion}</p>
										<div class="mt-2 flex flex-wrap gap-1">
											<Badge variant="outline">p50 {k.latencia_p50_ms} ms</Badge>
											<Badge variant="outline">{k.licencia}</Badge>
										</div>
									</button>
								{/each}
							</div>
						{/await}
					</div>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header>
			<Card.Title>Verificación por segunda ruta (N3)</Card.Title>
			<Card.Description>
				Relee el fragmento de cada oferta candidata por otra ruta: el programa cuando la fuente trae
				datos estructurados (MCP, schema.org) o Claude Haiku 5.5 por OpenRouter, con su clave. Cada
				oferta muestra si quedó verificada, con discrepancia o sin contraparte.
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-4">
			<div class="flex items-center gap-3">
				<Switch id="verificar" bind:checked={config.verificar} />
				<Label for="verificar">Verificar las ofertas candidatas</Label>
			</div>
			{#if config.verificar}
				<div class="grid gap-3 sm:grid-cols-2">
					{#each [['abstener', 'Abstenerse (por defecto)', 'Si la oferta recomendada no queda verificada, el agente no recomienda.'], ['excluir', 'Excluir', 'Descarta las ofertas no verificadas y elige la siguiente mejor.']] as [v, t, d] (v)}
						<button
							type="button"
							onclick={() => (config.politica_n3 = v as 'abstener' | 'excluir')}
							class="rounded-lg border p-3 text-left text-xs transition-colors hover:border-primary/50 {config.politica_n3 ===
							v
								? 'border-primary bg-primary/10'
								: ''}"
						>
							<div class="text-sm font-medium">{t}</div>
							<p class="mt-1 text-muted-foreground">{d}</p>
						</button>
					{/each}
				</div>
				<p class="text-xs text-muted-foreground">
					En E1 (corpus B), la extracción de las ofertas verificadas fue exacta campo a campo en el
					97,2 % de los casos, frente al 76,0 % de las no verificadas. Añade unos segundos y un costo
					pequeño por consulta.
				</p>
			{/if}
		</Card.Content>
	</Card.Root>
</div>
