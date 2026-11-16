<script lang="ts">
	// Resultado del modo Cliente (D111): recomendación, tabla corta y fuente por oferta.
	import { cop, usd, type Propuesta } from '#lib/api.js';
	import { conNombres } from '#lib/datos.js';
	import BadgeCheck from '@lucide/svelte/icons/badge-check';
	import Info from '@lucide/svelte/icons/info';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import { enlaceOferta, etiquetaEnlace } from '#lib/enlaces.js';

	let {
		propuesta,
		nombres = {},
		segundos = null,
		estimado = false,
		carga = null
	}: {
		propuesta: Propuesta;
		nombres?: Record<string, string>;
		segundos?: number | null;
		estimado?: boolean;
		carga?: string | null;
	} = $props();

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
	// La procedencia técnica completa (URL y SHA-256) va en el informe de cotización (D142).
	const legible = (texto: string) => conNombres(texto, nombres);
	const justificacion = $derived(legible(propuesta.justificacion.replace(/\s*Procedencia:.*$/s, '')));
	const hayVerificadas = $derived(propuesta.ofertas.some((o) => o.verificacion === 'verificada'));
	const rec = $derived(propuesta.recomendada != null ? propuesta.ofertas[propuesta.recomendada] : null);
	// D145: cada oferta se abre en la página o el documento que la respalda.
	const enlaces = $derived(propuesta.ofertas.map((o) => enlaceOferta(o, carga)));
	const enlaceRec = $derived(propuesta.recomendada != null ? enlaces[propuesta.recomendada] : null);
</script>

{#if propuesta.abstencion || !rec}
	<div class="rounded-xl border bg-card p-5 sm:p-6">
		<p class="text-sm font-medium text-muted-foreground">Sin recomendación</p>
		<p class="mt-2 text-lg leading-snug">{legible(propuesta.motivo_abstencion ?? propuesta.justificacion)}</p>
	</div>
{:else}
	<!-- La recomendación se lee como una cotización: producto, total y sello de verificación (D139). -->
	<article class="overflow-hidden rounded-xl border bg-card">
		<div class="flex flex-col gap-5 p-5 sm:flex-row sm:items-end sm:justify-between sm:p-6">
			<div class="min-w-0">
				<p class="text-sm font-medium text-primary">Recomendación</p>
				<h2 class="mt-1.5 text-lg leading-snug font-medium sm:text-xl">{rec.titulo}</h2>
				<p class="mt-1 text-sm text-muted-foreground">
					{proveedor(rec)}{rec.plazo_entrega_dias != null ? ` · entrega en ${dias(rec.plazo_entrega_dias)}` : ''}{rec.disponibilidad !== 'desconocida' ? ` · ${DISPONIBILIDAD[rec.disponibilidad]}` : ''}
				</p>
				{#if enlaceRec}
					<a
						href={enlaceRec.href}
						target="_blank"
						rel="noopener noreferrer"
						class="mt-2 inline-flex items-center gap-1.5 text-sm text-primary underline-offset-2 hover:underline"
						>{etiquetaEnlace(rec, enlaceRec)}<ExternalLink class="size-3.5" /></a
					>
				{/if}
			</div>
			<div class="shrink-0 sm:text-right">
				<p class="cifra text-3xl font-semibold tracking-tight sm:text-4xl">{cop(total(rec))}</p>
				<p class="text-xs text-muted-foreground">total con envío</p>
			</div>
		</div>
		{#if rec.verificacion === 'verificada'}
			<p class="flex items-center gap-2 border-t border-dashed bg-accent px-5 py-2.5 text-xs text-accent-foreground sm:px-6">
				<BadgeCheck class="size-4 shrink-0" />
				Precio verificado: una segunda lectura independiente de la fuente confirmó el mismo valor.
			</p>
		{/if}
		<p class="border-t px-5 py-4 text-sm leading-relaxed text-muted-foreground sm:px-6">{justificacion}</p>
	</article>
{/if}

{#if alertas.length}
	<ul class="mt-6 space-y-1.5 text-sm text-muted-foreground">
		{#each alertas as a (a)}
			<li class="flex items-start gap-2"><Info class="mt-0.5 size-4 shrink-0 text-warning" />{a}</li>
		{/each}
	</ul>
{/if}

<!-- El fragmento parte en cualquier punto: una URL larga no ensancha la tabla ni esconde «Ocultar». -->
{#snippet fuente(o: Propuesta['ofertas'][number], e: ReturnType<typeof enlaceOferta>)}
	<p class="text-xs text-muted-foreground">
		Leído en {proveedor(o)} el
		{new Date(o.procedencia.marca_tiempo).toLocaleString('es-CO')} · precio
		{cop(o.precio)} + envío {cop(o.costo_envio)}. Este es el texto original de la fuente:
	</p>
	<pre
		class="mt-2 max-h-56 overflow-y-auto rounded-lg bg-muted p-3 text-xs whitespace-pre-wrap [overflow-wrap:anywhere] text-muted-foreground">{o
			.procedencia.fragmento_original}</pre>
	<div class="mt-1.5 flex items-center justify-between gap-3">
		{#if e}
			<a
				href={e.href}
				target="_blank"
				rel="noopener noreferrer"
				class="inline-flex items-center gap-1 text-xs text-primary underline-offset-2 hover:underline"
				>{etiquetaEnlace(o, e)}<ExternalLink class="size-3" /></a
			>
		{:else}
			<span class="text-xs text-muted-foreground"
				>{o.procedencia.tipo_fuente === 'mcp'
					? 'Catálogo consultado por API: no tiene una página que abrir.'
					: o.procedencia.consulta.startsWith('pdf://')
						? 'PDF que usted cargó: se conserva su texto, no el archivo.'
						: ''}</span
			>
		{/if}
		<button
			class="text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
			onclick={() => (abierta = null)}>Ocultar fuente</button
		>
	</div>
{/snippet}

{#if propuesta.ofertas.length}
	<div class="mt-12">
		<h2 class="text-sm text-muted-foreground">
			{propuesta.ofertas.length}
			{propuesta.ofertas.length === 1 ? 'oferta comparada' : 'ofertas comparadas'}
		</h2>

		<!-- Móvil: una oferta por bloque, con el total siempre a la vista. -->
		<ul class="mt-3 divide-y border-y sm:hidden">
			{#each propuesta.ofertas as o, i (i)}
				<li class="py-3.5 {i === propuesta.recomendada ? '' : 'text-foreground/85'}">
					<div class="flex items-start gap-3">
						<p class="line-clamp-2 min-w-0 flex-1 text-sm leading-snug">
							{#if i === propuesta.recomendada}<span
									class="mr-1.5 inline-block size-1.5 -translate-y-0.5 rounded-full bg-primary"
								></span>{/if}{o.titulo}
						</p>
						<p class="cifra shrink-0 text-sm font-medium">{cop(total(o))}</p>
					</div>
					<div class="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
						<span class="inline-flex items-center gap-1">
							{proveedor(o)}
							{#if o.verificacion === 'verificada'}<BadgeCheck class="size-3.5 text-primary" aria-label="Precio confirmado" />{/if}
						</span>
						{#each [o.plazo_entrega_dias != null ? dias(o.plazo_entrega_dias) : '', o.disponibilidad !== 'desconocida' ? DISPONIBILIDAD[o.disponibilidad] : ''].filter(Boolean) as d (d)}<span>· {d}</span>{/each}
						{#if enlaces[i]}
							<a
								href={enlaces[i]!.href}
								target="_blank"
								rel="noopener noreferrer"
								class="ml-auto -my-2 inline-flex items-center gap-1 px-1 py-2 hover:text-foreground"
								aria-label={etiquetaEnlace(o, enlaces[i]!)}
								title={etiquetaEnlace(o, enlaces[i]!)}>Abrir<ExternalLink class="size-3" /></a
							>
						{/if}
						<button
							class="{enlaces[i] ? '' : 'ml-auto '}-my-2 px-1 py-2 hover:text-foreground"
							aria-expanded={abierta === i}
							onclick={() => (abierta = abierta === i ? null : i)}>{abierta === i ? 'Ocultar' : 'Fuente'}</button
						>
					</div>
					{#if abierta === i}<div class="mt-3">{@render fuente(o, enlaces[i])}</div>{/if}
				</li>
			{/each}
		</ul>

		<div class="mt-3 hidden overflow-x-auto sm:block">
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
							<td class="py-3 pr-4 text-right whitespace-nowrap">{cop(total(o))}</td>
							<td class="py-3 pr-4 whitespace-nowrap">{dias(o.plazo_entrega_dias)}</td>
							<td class="py-3 pr-4 whitespace-nowrap">{DISPONIBILIDAD[o.disponibilidad]}</td>
							<td class="py-3 text-right whitespace-nowrap">
								{#if enlaces[i]}
									<a
										href={enlaces[i]!.href}
										target="_blank"
										rel="noopener noreferrer"
										class="mr-3 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
										aria-label={etiquetaEnlace(o, enlaces[i]!)}
										title={etiquetaEnlace(o, enlaces[i]!)}>Abrir<ExternalLink class="size-3" /></a
									>
								{/if}
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
								<td colspan={6} class="pt-3 pb-6">{@render fuente(o, enlaces[i])}</td>
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
	Esta consulta costó {estimado ? 'cerca de ' : ''}{usd(propuesta.costo_usd)}{segundos != null ? ` y tardó ${Math.round(segundos)} s` : ''}.
	{#if estimado}Es una estimación por tokens; el valor exacto está en su consola de Anthropic.{/if}
</p>
