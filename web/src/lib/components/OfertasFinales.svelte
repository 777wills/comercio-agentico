<script lang="ts">
	import { cop, type OfertaFinal, type Propuesta } from '#lib/api.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Table from '#lib/components/ui/table/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';

	let {
		ofertas,
		propuesta = null,
		nombres = {}
	}: { ofertas: OfertaFinal[]; propuesta?: Propuesta | null; nombres?: Record<string, string> } =
		$props();

	const N3: Record<string, { texto: string; clase: string }> = {
		verificada: { texto: 'Verificada', clase: 'border-primary/40 text-primary' },
		discrepancia: { texto: 'Discrepancia', clase: 'border-destructive/50 text-destructive' },
		sin_contraparte: { texto: 'Sin contraparte', clase: 'border-amber-500/50 text-amber-400' }
	};

	// La comparación abierta escribe `grupo`; el corpus congelado, `producto_catalogo`.
	const abierta = $derived(ofertas.some((o) => o.grupo != null));
	const enPropuesta = $derived(
		new Set((propuesta?.ofertas ?? []).map((o) => `${o.procedencia.fuente}|${o.titulo}|${o.precio}`))
	);
	const clave = (o: OfertaFinal) => `${o.proveedor}|${o.titulo}|${o.precio}`;
	const propuesta_ = (o: OfertaFinal) => enPropuesta.has(clave(o));
	function motivo(o: OfertaFinal): string | null {
		if (o.descarte) return o.descarte;
		if (!abierta && !o.producto_catalogo) return 'sin producto del catálogo';
		if (!abierta) return 'no cumple la necesidad o el perfil, o la retiró una defensa';
		return null;
	}
	const ordenadas = $derived(
		[...ofertas].sort(
			(a, b) => Number(propuesta_(b)) - Number(propuesta_(a)) || a.precio - b.precio
		)
	);
	const incluidas = $derived(ofertas.filter(propuesta_).length);
</script>

<Card.Root>
	<Card.Header>
		<Card.Title class="text-base">Ofertas finales</Card.Title>
		<Card.Description>
			{ofertas.length} ofertas tras {abierta ? 'la comparación abierta' : 'el emparejamiento con el catálogo'}
			· {incluidas} en la propuesta. Para cada una, con qué {abierta ? 'grupo' : 'producto'} quedó y, si
			quedó fuera, el motivo.
		</Card.Description>
	</Card.Header>
	<Card.Content class="overflow-x-auto">
		<Table.Root>
			<Table.Header>
				<Table.Row>
					<Table.Head>Proveedor</Table.Head>
					<Table.Head>Producto</Table.Head>
					<Table.Head class="text-right">Precio</Table.Head>
					<Table.Head class="text-right">Envío</Table.Head>
					<Table.Head>{abierta ? 'Grupo' : 'Catálogo'}</Table.Head>
					<Table.Head>Resultado</Table.Head>
					<Table.Head>N3</Table.Head>
				</Table.Row>
			</Table.Header>
			<Table.Body>
				{#each ordenadas as o, i (i)}
					<Table.Row class={propuesta_(o) ? '' : 'text-muted-foreground'}>
						<Table.Cell>{nombres[o.proveedor] ?? o.proveedor}</Table.Cell>
						<Table.Cell class="max-w-72">
							<div class="truncate" title={o.titulo}>{o.titulo}</div>
						</Table.Cell>
						<Table.Cell class="text-right font-mono">{cop(o.precio)}</Table.Cell>
						<Table.Cell class="text-right font-mono">{cop(o.costo_envio)}</Table.Cell>
						<Table.Cell class="font-mono text-xs">
							{abierta ? (o.grupo ?? '—') : (o.producto_catalogo ?? '—')}
						</Table.Cell>
						<Table.Cell class="max-w-64 whitespace-normal text-xs">
							{#if propuesta_(o)}
								<Badge>En la propuesta</Badge>
							{:else if motivo(o)}
								Fuera: {motivo(o)}
							{:else}
								<Badge variant="outline">Cumple</Badge>
							{/if}
						</Table.Cell>
						<Table.Cell>
							{#if o.verificacion}
								<Badge variant="outline" class={N3[o.verificacion].clase}>
									{N3[o.verificacion].texto}
								</Badge>
							{:else}
								<span class="text-xs">—</span>
							{/if}
						</Table.Cell>
					</Table.Row>
				{/each}
			</Table.Body>
		</Table.Root>
	</Card.Content>
</Card.Root>
