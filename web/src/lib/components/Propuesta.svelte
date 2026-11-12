<script lang="ts">
	import { cop, usd, type Propuesta } from '#lib/api.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Table from '#lib/components/ui/table/index.js';
	import * as Alert from '#lib/components/ui/alert/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import Award from '@lucide/svelte/icons/award';
	import TriangleAlert from '@lucide/svelte/icons/triangle-alert';
	import CircleSlash from '@lucide/svelte/icons/circle-slash';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';

	let {
		propuesta,
		nombres = {},
		segundos = null,
		estimado = false
	}: {
		propuesta: Propuesta;
		nombres?: Record<string, string>;
		segundos?: number | null;
		estimado?: boolean;
	} = $props();

	let abierta = $state<number | null>(null);

	const DISPONIBILIDAD: Record<string, string> = {
		en_stock: 'En stock',
		bajo_pedido: 'Bajo pedido',
		agotado: 'Agotado',
		desconocida: '—'
	};
	const N3: Record<string, { texto: string; clase: string }> = {
		verificada: { texto: 'Verificada', clase: 'border-primary/40 text-primary' },
		discrepancia: { texto: 'Discrepancia', clase: 'border-destructive/50 text-destructive' },
		sin_contraparte: { texto: 'Sin contraparte', clase: 'border-amber-500/50 text-amber-400' }
	};
	const ALERTAS: Record<string, string> = {
		posible_inyeccion: 'Posible inyección retirada',
		precio_atipico: 'Precio atípico excluido',
		sin_verificar: 'Oferta no verificada',
		emparejamiento_dudoso: 'Emparejamiento dudoso',
		restriccion_incumplida: 'Restricción incumplida',
		fuente_no_disponible: 'Fuente no disponible',
		interpretacion_incompleta: 'Interpretación incompleta'
	};

	const total = (o: Propuesta['ofertas'][number]) => o.precio + (o.costo_envio ?? 0);
	const TIPO: Record<string, string> = {
		mcp: 'MCP',
		web_schema: 'Web',
		web_plana: 'Web',
		pdf: 'PDF',
		mensaje: 'Chat',
		api: 'API'
	};
</script>

<Card.Root>
	<Card.Header>
		<Card.Title class="text-base">Propuesta de compra</Card.Title>
		<Card.Description>
			{propuesta.ofertas.length} ofertas comparables · perfil «{propuesta.perfil}» · modelo {propuesta.modelo}
			· {estimado ? '≈ ' : ''}{usd(propuesta.costo_usd)}{estimado ? ' (estimado)' : ''}{segundos != null ? ` · ${Math.round(segundos)} s` : ''}
		</Card.Description>
	</Card.Header>
	<Card.Content class="space-y-4">
		{#if propuesta.abstencion}
			<Alert.Root>
				<CircleSlash />
				<Alert.Title>El agente se abstiene</Alert.Title>
				<Alert.Description>{propuesta.motivo_abstencion ?? propuesta.justificacion}</Alert.Description>
			</Alert.Root>
		{:else if propuesta.recomendada != null}
			<Alert.Root class="border-primary/40">
				<Award class="text-primary" />
				<Alert.Title>
					Recomendación: {propuesta.ofertas[propuesta.recomendada].titulo}
				</Alert.Title>
				<Alert.Description>{propuesta.justificacion}</Alert.Description>
			</Alert.Root>
		{/if}

		{#if propuesta.alertas.length}
			<div class="flex flex-wrap gap-2">
				{#each propuesta.alertas as a, i (i)}
					<Badge variant="destructive" title={a.mensaje}>
						<TriangleAlert class="size-3" />
						{ALERTAS[a.tipo] ?? a.tipo}{a.oferta != null ? ` · oferta ${a.oferta + 1}` : ''}
					</Badge>
				{/each}
			</div>
		{/if}

		<div class="overflow-x-auto">
			<Table.Root>
				<Table.Header>
					<Table.Row>
						<Table.Head>#</Table.Head>
						<Table.Head>Producto</Table.Head>
						<Table.Head>Proveedor</Table.Head>
						<Table.Head class="text-right">Precio</Table.Head>
						<Table.Head class="text-right">Envío</Table.Head>
						<Table.Head class="text-right">Costo total</Table.Head>
						<Table.Head>Plazo</Table.Head>
						<Table.Head>Disp.</Table.Head>
						<Table.Head>Fuente</Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each propuesta.ofertas as o, i (i)}
						<Table.Row class={i === propuesta.recomendada ? 'bg-primary/10' : ''}>
							<Table.Cell class="font-mono text-xs">{i + 1}</Table.Cell>
							<Table.Cell class="max-w-60">
								<div class="truncate" title={o.titulo}>{o.titulo}</div>
								<div class="flex flex-wrap gap-1 pt-1">
									{#if i === propuesta.recomendada}<Badge>Recomendada</Badge>{/if}
									{#if o.verificacion}
										<Badge variant="outline" class={N3[o.verificacion].clase}>
											N3: {N3[o.verificacion].texto}
										</Badge>
									{/if}
									{#if !o.producto_catalogo}
										<Badge variant="outline" class="text-muted-foreground">Sin emparejar</Badge>
									{/if}
								</div>
							</Table.Cell>
							<Table.Cell>{nombres[o.procedencia.fuente] ?? o.procedencia.fuente}</Table.Cell>
							<Table.Cell class="text-right font-mono">{cop(o.precio)}</Table.Cell>
							<Table.Cell class="text-right font-mono">{cop(o.costo_envio)}</Table.Cell>
							<Table.Cell class="text-right font-mono font-medium">{cop(total(o))}</Table.Cell>
							<Table.Cell>{o.plazo_entrega_dias != null ? `${o.plazo_entrega_dias} d` : '—'}</Table.Cell>
							<Table.Cell>{DISPONIBILIDAD[o.disponibilidad]}</Table.Cell>
							<Table.Cell>
								<Button
									variant="ghost"
									size="sm"
									aria-expanded={abierta === i}
									onclick={() => (abierta = abierta === i ? null : i)}
								>
									{TIPO[o.procedencia.tipo_fuente] ?? o.procedencia.tipo_fuente}
									<ChevronDown class="transition-transform {abierta === i ? 'rotate-180' : ''}" />
								</Button>
							</Table.Cell>
						</Table.Row>
						{#if abierta === i}
							<Table.Row class="hover:bg-transparent">
								<Table.Cell colspan={9} class="bg-muted/30 whitespace-normal">
									<dl class="grid gap-x-6 gap-y-1 text-xs sm:grid-cols-[auto_1fr]">
										<dt class="text-muted-foreground">Fuente</dt>
										<dd>{nombres[o.procedencia.fuente] ?? ''} ({o.procedencia.fuente}) · {o.procedencia.tipo_fuente}</dd>
										<dt class="text-muted-foreground">Consulta</dt>
										<dd class="break-all font-mono">{o.procedencia.consulta}</dd>
										<dt class="text-muted-foreground">Extracción</dt>
										<dd>
											{o.procedencia.ruta_extraccion}{o.procedencia.modelo_extraccion
												? ` · ${o.procedencia.modelo_extraccion}`
												: ''} · {new Date(o.procedencia.marca_tiempo).toLocaleString('es-CO')}
										</dd>
										<dt class="text-muted-foreground">SHA-256</dt>
										<dd class="break-all font-mono">{o.procedencia.suma_verificacion}</dd>
										{#if o.gtin}<dt class="text-muted-foreground">GTIN</dt><dd class="font-mono">{o.gtin}</dd>{/if}
									</dl>
									<div class="mt-2 text-xs text-muted-foreground">Fragmento original</div>
									<pre
										class="mt-1 max-h-64 overflow-auto rounded-md border bg-background p-3 text-xs whitespace-pre-wrap">{o
											.procedencia.fragmento_original}</pre>
								</Table.Cell>
							</Table.Row>
						{/if}
					{/each}
				</Table.Body>
			</Table.Root>
		</div>
		<p class="text-xs text-muted-foreground">
			Cada cifra lleva su procedencia: el fragmento que leyó el agente, con su suma SHA-256 para
			auditarlo. CotIA no ejecuta pagos ni compras.
		</p>
	</Card.Content>
</Card.Root>
