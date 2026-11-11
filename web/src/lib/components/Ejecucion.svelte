<script lang="ts">
	import { onDestroy } from 'svelte';
	import { obtener, seguirEventos, usd, cop, type Detalle, type Evento } from '#lib/api.js';
	import { visita } from '#lib/config.svelte.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import { Skeleton } from '#lib/components/ui/skeleton/index.js';
	import Propuesta from './Propuesta.svelte';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import CircleX from '@lucide/svelte/icons/circle-x';

	let {
		id,
		nombres = {},
		compacto = false,
		alTerminar
	}: {
		id: string;
		nombres?: Record<string, string>;
		compacto?: boolean;
		alTerminar?: (d: Detalle) => void;
	} = $props();

	let eventos = $state<Evento[]>([]);
	let detalle = $state<Detalle | null>(null);
	let fallo = $state<string | null>(null);
	const fin = $derived(eventos.find((e) => e.etapa === 'fin'));
	let inicio = Date.now();
	let ahora = $state(Date.now());
	const reloj = setInterval(() => (ahora = Date.now()), 1000);

	// El padre monta este componente dentro de {#key id}: el id no cambia durante su vida.
	// svelte-ignore state_referenced_locally
	const cerrar = seguirEventos(
		id,
		async (e) => {
			eventos.push(e);
			if (e.etapa === 'fin') {
				clearInterval(reloj);
				detalle = await obtener<Detalle>(`/api/consultas/${id}`);
				visita.refrescar().catch(() => {});
				alTerminar?.(detalle);
			}
		},
		(m) => (fallo = m)
	);
	onDestroy(() => {
		cerrar();
		clearInterval(reloj);
	});

	const TITULOS: Record<string, string> = {
		en_cola: 'En cola',
		inicio: 'Inicio',
		interpretacion: 'Interpretación de la necesidad',
		plan: 'El planificador decide qué fuentes leer',
		lecturas: 'Lectura y extracción',
		emparejamiento: 'Emparejamiento con el catálogo',
		propuesta: 'Propuesta',
		fin: 'Fin'
	};

	function explicarError(m: string): string {
		if (/Unauthorized|401/.test(m)) return 'OpenRouter rechazó la clave. Revísela en Configuración.';
		if (/PaymentRequired|402|credits/i.test(m)) return 'La cuenta de OpenRouter no tiene saldo suficiente.';
		if (/TooManyRequests|429/.test(m)) return 'El proveedor del modelo limitó la tasa; intente en unos minutos.';
		return m;
	}

	function resumen(e: Evento): string {
		switch (e.etapa) {
			case 'en_cola':
				return 'Hay otra consulta en curso; esta espera su turno.';
			case 'inicio':
				return `Modelo ${e.modelo} · defensas ${e.configuracion}`;
			case 'interpretacion': {
				const n = e.necesidad ?? {};
				const partes = [
					n.tipo_producto,
					n.producto_mencionado,
					n.presupuesto_max ? `presupuesto ${cop(n.presupuesto_max)}` : null,
					n.plazo_max_dias ? `plazo ≤ ${n.plazo_max_dias} días` : null,
					...(n.restricciones ?? []).map(
						(r: any) => `${r.atributo} ${r.operador} ${r.valor}${r.unidad ? ' ' + r.unidad : ''}`
					)
				].filter(Boolean);
				return partes.join(' · ') || 'Sin campos interpretados';
			}
			case 'plan':
				return e.herramientas.length
					? e.herramientas
							.map(
								(h: any) =>
									`${h.nombre}(${Object.values(h.args ?? {})
										.filter((v) => v !== '' && v != null)
										.join(', ')})`
							)
							.join(' · ')
					: 'Termina de leer y pasa a comparar.';
			case 'lecturas': {
				const por = Object.entries(e.por_proveedor ?? {})
					.map(([p, n]) => `${nombres[p] ?? p}: ${n}`)
					.join(', ');
				return `${e.lecturas.length} lectura(s) · ${e.ofertas} oferta(s) acumuladas${por ? ` (${por})` : ''}`;
			}
			case 'emparejamiento':
				return `${e.emparejadas} de ${e.ofertas} ofertas emparejadas con el catálogo`;
			case 'propuesta':
				return e.abstencion
					? 'El agente se abstiene de recomendar.'
					: `Recomienda la oferta ${Number(e.recomendada) + 1} de ${e.ofertas}`;
			case 'fin':
				return e.estado === 'error'
					? explicarError(e.error)
					: `${usd(e.costo_usd)} · ${e.segundos} s`;
		}
		return '';
	}
</script>

<div class="grid gap-4 {compacto ? '' : 'lg:grid-cols-[minmax(0,22rem)_1fr]'}">
	<Card.Root class="h-fit">
		<Card.Header>
			<Card.Title class="flex items-center gap-2 text-base">
				{#if !fin && !fallo}
					<LoaderCircle class="size-4 animate-spin text-primary" /> Progreso en vivo
				{:else if fin?.estado === 'error' || fallo}
					<CircleX class="size-4 text-destructive" /> Terminó con error
				{:else}
					<CircleCheck class="size-4 text-primary" /> Terminada
				{/if}
				<span class="ml-auto font-mono text-xs text-muted-foreground">
					{fin?.segundos ?? Math.round((ahora - inicio) / 1000)} s
				</span>
			</Card.Title>
		</Card.Header>
		<Card.Content>
			<ol class="relative space-y-3 border-l pl-4">
				{#each eventos as e, i (i)}
					<li class="text-sm">
						<span
							class="absolute -left-[5px] mt-1.5 size-2.5 rounded-full {e.etapa === 'fin' &&
							e.estado === 'error'
								? 'bg-destructive'
								: 'bg-primary'}"
						></span>
						<div class="font-medium">{TITULOS[e.etapa]}</div>
						<div class="break-words text-xs text-muted-foreground">{resumen(e)}</div>
						{#if e.etapa === 'lecturas' && e.alertas?.length}
							{#each e.alertas as a, j (j)}
								<Badge variant="destructive" class="mt-1">{a.tipo}</Badge>
							{/each}
						{/if}
						{#if e.etapa === 'fin' && e.exito_ataque != null}
							<Badge class="mt-1" variant={e.exito_ataque ? 'destructive' : 'secondary'}>
								{e.exito_ataque ? 'El ataque tuvo éxito' : 'Ataque frenado'}
							</Badge>
						{/if}
					</li>
				{/each}
				{#if !fin && !fallo}
					<li><Skeleton class="h-8 w-full" /></li>
				{/if}
			</ol>
			{#if fallo}<p class="mt-3 text-sm text-destructive">{fallo}</p>{/if}
		</Card.Content>
	</Card.Root>

	<div class="min-w-0">
		{#if detalle?.propuesta}
			<Propuesta propuesta={detalle.propuesta} {nombres} segundos={detalle.segundos} />
		{:else if detalle?.error}
			<Card.Root><Card.Content class="space-y-1 text-sm">
				<p class="text-destructive">{explicarError(detalle.error)}</p>
				<p class="font-mono text-xs text-muted-foreground">{detalle.error}</p>
			</Card.Content></Card.Root>
		{:else if !compacto}
			<Card.Root>
				<Card.Content class="space-y-3">
					<Skeleton class="h-6 w-1/3" />
					<Skeleton class="h-32 w-full" />
					<p class="text-xs text-muted-foreground">
						Una consulta tarda entre 1 y 3 minutos: el agente lee cada fuente, extrae ofertas con
						salida estructurada y las empareja con el catálogo antes de comparar.
					</p>
				</Card.Content>
			</Card.Root>
		{/if}
	</div>
</div>
