<script lang="ts">
	import { obtener, pct, usd } from '#lib/api.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Table from '#lib/components/ui/table/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';

	type Intervalo = { k: number; n: number; p: number; bajo: number; alto: number };
	const res = obtener<Record<'e1' | 'e2' | 'e3', { datos: any; figuras: string[] }>>(
		'/api/resultados'
	);
	const ic = (x: Intervalo | undefined) =>
		x ? `${pct(x.p)} [${pct(x.bajo, 1)}; ${pct(x.alto, 1)}]` : '—';
	const POLITICAS: Record<string, string> = {
		sin_n3: 'Sin N3',
		abstener: 'N3 · abstener',
		excluir: 'N3 · excluir'
	};
</script>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-semibold">Resultados de los experimentos</h1>
		<p class="max-w-3xl text-sm text-muted-foreground">
			Las cifras del informe, leídas de la evidencia versionada en el repositorio. Los corchetes son
			intervalos de Wilson al 95 %.
		</p>
	</div>

	{#await res}
		<p class="text-sm text-muted-foreground">Cargando…</p>
	{:then r}
		{#if r.e3.datos}
			<Card.Root>
				<Card.Header>
					<Card.Title>E3 · Modelo base: acierto frente a costo</Card.Title>
					<Card.Description>
						Subconjunto de 30 tareas del corpus B × 3 repeticiones por modelo. Frontera de Pareto:
						{r.e3.datos.pareto.join(', ')}.
					</Card.Description>
				</Card.Header>
				<Card.Content class="space-y-4">
					<div class="overflow-x-auto">
						<Table.Root>
							<Table.Header>
								<Table.Row>
									<Table.Head>Modelo</Table.Head>
									<Table.Head>M2 (acierto)</Table.Head>
									<Table.Head>Acuerdo entre repeticiones</Table.Head>
									<Table.Head class="text-right">Costo por tarea</Table.Head>
									<Table.Head class="text-right">Latencia p50</Table.Head>
								</Table.Row>
							</Table.Header>
							<Table.Body>
								{#each r.e3.datos.pasos as p (p.modelo)}
									<Table.Row>
										<Table.Cell class="font-medium">
											{p.modelo}
											{#if r.e3.datos.pareto.includes(p.modelo)}<Badge class="ml-1">Pareto</Badge>{/if}
										</Table.Cell>
										<Table.Cell>
											{pct(p.m2_media)} [{pct(p.m2_bajo)}; {pct(p.m2_alto)}]
										</Table.Cell>
										<Table.Cell>{pct(p.acuerdo_total)}</Table.Cell>
										<Table.Cell class="text-right font-mono">{usd(p.costo_medio)}</Table.Cell>
										<Table.Cell class="text-right font-mono">{Math.round(p.latencia_p50)} s</Table.Cell>
									</Table.Row>
								{/each}
							</Table.Body>
						</Table.Root>
					</div>
					{#each r.e3.figuras as f (f)}
						<img src={f} alt="Figura de E3" class="mx-auto max-h-96 rounded-md bg-white p-2" />
					{/each}
				</Card.Content>
			</Card.Root>
		{/if}

		{#if r.e2.datos}
			<Card.Root>
				<Card.Header>
					<Card.Title>E2 · Curva seguridad-utilidad de las defensas</Card.Title>
					<Card.Description>
						20 cargas × 3 repeticiones por configuración (M5 = tasa de éxito del ataque) y utilidad
						sobre 30 tareas benignas. Codo: {r.e2.datos.codo}.
					</Card.Description>
				</Card.Header>
				<Card.Content class="space-y-4">
					<div class="overflow-x-auto">
						<Table.Root>
							<Table.Header>
								<Table.Row>
									<Table.Head>Configuración</Table.Head>
									<Table.Head>M5 (éxito del ataque)</Table.Head>
									<Table.Head>Utilidad (M2 benigno)</Table.Head>
									<Table.Head>Acierto bajo ataque</Table.Head>
								</Table.Row>
							</Table.Header>
							<Table.Body>
								{#each r.e2.datos.puntos as p (p.configuracion)}
									<Table.Row>
										<Table.Cell class="font-medium">
											{p.configuracion}
											{#if p.configuracion === r.e2.datos.codo}<Badge class="ml-1">Codo</Badge>{/if}
										</Table.Cell>
										<Table.Cell>{p.m5.k}/{p.m5.n} · {ic(p.m5)}</Table.Cell>
										<Table.Cell>{p.utilidad.k}/{p.utilidad.n} · {ic(p.utilidad)}</Table.Cell>
										<Table.Cell>{ic(p.acierto_bajo_ataque)}</Table.Cell>
									</Table.Row>
								{/each}
							</Table.Body>
						</Table.Root>
					</div>
					<div class="grid gap-4 lg:grid-cols-2">
						{#each r.e2.figuras as f (f)}
							<img src={f} alt="Figura de E2" class="max-h-96 w-full rounded-md bg-white object-contain p-2" />
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		{/if}

		{#if r.e1.datos}
			<Card.Root>
				<Card.Header>
					<Card.Title>E1 · Verificación por segunda ruta (N3)</Card.Title>
					<Card.Description>
						Reproducción pareada sobre corridas registradas: M2 con y sin N3, por política.
					</Card.Description>
				</Card.Header>
				<Card.Content class="space-y-4">
					<div class="overflow-x-auto">
						<Table.Root>
							<Table.Header>
								<Table.Row>
									<Table.Head>Corpus</Table.Head>
									<Table.Head>Ejecuciones</Table.Head>
									{#each Object.keys(POLITICAS) as p (p)}<Table.Head>{POLITICAS[p]}</Table.Head>{/each}
								</Table.Row>
							</Table.Header>
							<Table.Body>
								{#each r.e1.datos as d (d.corpus)}
									<Table.Row>
										<Table.Cell class="font-medium">{d.corpus.toUpperCase()}</Table.Cell>
										<Table.Cell>{d.ejecuciones}</Table.Cell>
										{#each Object.keys(POLITICAS) as p (p)}
											<Table.Cell>{ic(d.politicas[p]?.m2)}</Table.Cell>
										{/each}
									</Table.Row>
								{/each}
							</Table.Body>
						</Table.Root>
					</div>
					{#each r.e1.figuras as f (f)}
						<img src={f} alt="Figura de E1" class="mx-auto max-h-96 rounded-md bg-white p-2" />
					{/each}
				</Card.Content>
			</Card.Root>
		{/if}
	{:catch}
		<p class="text-sm text-destructive">No se pudieron cargar los resultados.</p>
	{/await}
</div>
