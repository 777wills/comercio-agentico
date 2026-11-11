<script lang="ts">
	// Resultado del modo Cliente (D111): recomendación, tabla corta y fuente por oferta.
	import { cop, usd, type Propuesta } from '#lib/api.js';
	import BadgeCheck from '@lucide/svelte/icons/badge-check';
	import Info from '@lucide/svelte/icons/info';

	let {
		propuesta,
		nombres = {},
		segundos = null
	}: { propuesta: Propuesta; nombres?: Record<string, string>; segundos?: number | null } =
		$props();

	let abierta = $state<number | null>(null);

	const total = (o: Propuesta['ofertas'][number]) => o.precio + (o.costo_envio ?? 0);
	const proveedor = (o: Propuesta['ofertas'][number]) =>
		nombres[o.procedencia.fuente] ?? o.procedencia.fuente;
	const DISPONIBILIDAD: Record<string, string> = {
		en_stock: 'En stock',
		bajo_pedido: 'Bajo pedido',
		agotado: 'Agotado',
		desconocida: '—'
	};
	// Solo las alertas que le sirven a quien compra, en su idioma.
	const ALERTAS: Record<string, string> = {
		posible_inyeccion: 'Se ignoró contenido sospechoso en una de las fuentes.',
		precio_atipico: 'Se descartó un precio fuera de lo normal.',
		sin_verificar: 'Una oferta no se pudo confirmar en una segunda lectura.',
		emparejamiento_dudoso: 'Una oferta podría no corresponder exactamente al producto.',
		restriccion_incumplida: 'Alguna oferta no cumple todo lo que pidió.',
		fuente_no_disponible: 'Un proveedor no respondió.',
		interpretacion_incompleta: 'La solicitud se interpretó de forma parcial.'
	};
	const alertas = $derived([...new Set(propuesta.alertas.map((a) => ALERTAS[a.tipo]).filter(Boolean))]);
	const dias = (n: number | null) => (n == null ? '—' : `${n} ${n === 1 ? 'día' : 'días'}`);
	// La procedencia técnica (URL y SHA-256) queda para el laboratorio; aquí va en «Fuente».
	const justificacion = $derived(propuesta.justificacion.replace(/\s*Procedencia:.*$/s, ''));
	const hayVerificadas = $derived(propuesta.ofertas.some((o) => o.verificacion === 'verificada'));
	const rec = $derived(propuesta.recomendada != null ? propuesta.ofertas[propuesta.recomendada] : null);
</script>

{#if propuesta.abstencion || !rec}
	<div class="border-l-2 border-muted-foreground/40 py-1 pl-5">
		<p class="text-xs tracking-wide text-muted-foreground uppercase">Sin recomendación</p>
		<p class="mt-2 text-lg">{propuesta.motivo_abstencion ?? propuesta.justificacion}</p>
	</div>
{:else}
	<div class="border-l-2 border-primary py-1 pl-5">
		<p class="text-xs tracking-wide text-primary uppercase">Recomendación</p>
		<p class="mt-2 text-xl font-medium">{rec.titulo}</p>
		<p class="mt-1 text-muted-foreground">
			{proveedor(rec)} · <span class="text-foreground">{cop(total(rec))}</span> con envío{rec.plazo_entrega_dias != null ? ` · ${dias(rec.plazo_entrega_dias)}` : ''}
		</p>
		<p class="mt-4 max-w-2xl text-sm leading-relaxed text-muted-foreground">{justificacion}</p>
	</div>
{/if}

{#if alertas.length}
	<ul class="mt-8 space-y-1.5 text-sm text-muted-foreground">
		{#each alertas as a (a)}
			<li class="flex items-start gap-2"><Info class="mt-0.5 size-4 shrink-0 text-amber-400" />{a}</li>
		{/each}
	</ul>
{/if}

{#if propuesta.ofertas.length}
	<div class="mt-12">
		<h2 class="text-sm text-muted-foreground">
			{propuesta.ofertas.length}
			{propuesta.ofertas.length === 1 ? 'oferta comparada' : 'ofertas comparadas'}
		</h2>
		<div class="mt-3 overflow-x-auto">
			<table class="w-full text-sm">
				<thead class="text-left text-xs text-muted-foreground">
					<tr class="border-b">
						<th class="py-2 pr-4 font-normal">Producto</th>
						<th class="py-2 pr-4 font-normal">Proveedor</th>
						<th class="py-2 pr-4 text-right font-normal">Total con envío</th>
						<th class="py-2 pr-4 font-normal">Entrega</th>
						<th class="py-2 pr-4 font-normal">Disponibilidad</th>
						<th class="py-2 font-normal"></th>
					</tr>
				</thead>
				<tbody>
					{#each propuesta.ofertas as o, i (i)}
						<tr class="border-b border-border/60 {i === propuesta.recomendada ? 'text-foreground' : 'text-foreground/80'}">
							<td class="max-w-72 py-3 pr-4">
								<div class="flex items-center gap-2">
									{#if i === propuesta.recomendada}<span class="size-1.5 shrink-0 rounded-full bg-primary"></span>{/if}
									<span class="truncate" title={o.titulo}>{o.titulo}</span>
								</div>
							</td>
							<td class="py-3 pr-4 whitespace-nowrap">
								<span class="inline-flex items-center gap-1">
									{proveedor(o)}
									{#if o.verificacion === 'verificada'}
										<BadgeCheck class="size-3.5 text-primary" aria-label="Precio confirmado" />
									{/if}
								</span>
							</td>
							<td class="py-3 pr-4 text-right whitespace-nowrap tabular-nums">{cop(total(o))}</td>
							<td class="py-3 pr-4 whitespace-nowrap">
								{dias(o.plazo_entrega_dias)}
							</td>
							<td class="py-3 pr-4 whitespace-nowrap">{DISPONIBILIDAD[o.disponibilidad]}</td>
							<td class="py-3 text-right">
								<button
									class="text-xs whitespace-nowrap text-muted-foreground hover:text-foreground"
									aria-expanded={abierta === i}
									onclick={() => (abierta = abierta === i ? null : i)}
									>{abierta === i ? 'Ocultar' : 'Fuente'}</button
								>
							</td>
						</tr>
						{#if abierta === i}
							<tr>
								<td colspan={6} class="pt-3 pb-6">
									<p class="text-xs text-muted-foreground">
										Leído en {proveedor(o)} el
										{new Date(o.procedencia.marca_tiempo).toLocaleString('es-CO')} · precio
										{cop(o.precio)} + envío {cop(o.costo_envio)}. Este es el texto original de la fuente:
									</p>
									<pre
										class="mt-2 max-h-56 overflow-auto rounded-lg bg-muted/40 p-3 text-xs whitespace-pre-wrap text-muted-foreground">{o
											.procedencia.fragmento_original}</pre>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
		{#if hayVerificadas}
			<p class="mt-4 flex items-center gap-1 text-xs text-muted-foreground">
				<BadgeCheck class="size-3.5 text-primary" /> precio confirmado en una segunda lectura de la fuente.
			</p>
		{/if}
	</div>
{/if}

<p class="mt-10 text-xs text-muted-foreground">
	Esta consulta costó {usd(propuesta.costo_usd)}{segundos != null ? ` y tardó ${Math.round(segundos)} s` : ''}.
</p>
