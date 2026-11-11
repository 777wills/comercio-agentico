<script lang="ts">
	import { onMount } from 'svelte';
	import { usd } from '#lib/api.js';
	import { visita } from '#lib/config.svelte.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Table from '#lib/components/ui/table/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';

	onMount(() => {
		visita.refrescar().catch(() => {});
	});
	const ESTADOS: Record<string, 'secondary' | 'destructive' | 'outline'> = {
		terminada: 'secondary',
		error: 'destructive'
	};
</script>

<div class="space-y-4">
	<div>
		<h1 class="text-2xl font-semibold">Historial de esta visita</h1>
		<p class="text-sm text-muted-foreground">
			{visita.total} {visita.total === 1 ? 'consulta' : 'consultas'} · {usd(visita.gasto)} con su clave. El historial se asocia a un
			identificador anónimo guardado en este navegador.
		</p>
	</div>
	<Card.Root>
		<Card.Content>
			{#if visita.consultas.length}
				<div class="overflow-x-auto">
					<Table.Root>
						<Table.Header>
							<Table.Row>
								<Table.Head>Fecha</Table.Head>
								<Table.Head>Consulta</Table.Head>
								<Table.Head>Corpus</Table.Head>
								<Table.Head>Modelo</Table.Head>
								<Table.Head>Defensas</Table.Head>
								<Table.Head>Estado</Table.Head>
								<Table.Head class="text-right">Costo</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each visita.consultas as c (c.id)}
								<Table.Row>
									<Table.Cell class="text-xs whitespace-nowrap">
										{new Date(c.creada).toLocaleString('es-CO')}
									</Table.Cell>
									<Table.Cell class="max-w-80">
										<a href="/consultas/{c.id}" class="block truncate hover:text-primary" title={c.consulta}>
											{#if c.carga}<Badge variant="destructive" class="mr-1">{c.carga}</Badge>{/if}
											{c.consulta}
										</a>
									</Table.Cell>
									<Table.Cell>{c.corpus.toUpperCase()}</Table.Cell>
									<Table.Cell class="text-xs">{c.modelo}</Table.Cell>
									<Table.Cell>{c.opciones.configuracion}</Table.Cell>
									<Table.Cell><Badge variant={ESTADOS[c.estado] ?? 'outline'}>{c.estado}</Badge></Table.Cell>
									<Table.Cell class="text-right font-mono">{usd(c.costo_usd)}</Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>
			{:else}
				<p class="text-sm text-muted-foreground">
					Aún no hay consultas en esta visita. <a href="/" class="underline">Haga la primera</a>.
				</p>
			{/if}
		</Card.Content>
	</Card.Root>
</div>
