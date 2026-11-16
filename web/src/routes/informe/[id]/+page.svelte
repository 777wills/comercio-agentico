<script lang="ts">
	// Informe de cotización (D142): la evidencia de todo lo que se investigó y del porqué de la
	// recomendación, armada solo con lo que la consulta dejó guardado (sin llamar a ningún modelo).
	// Se imprime o se guarda como PDF desde el navegador; el expediente JSON lleva la huella SHA-256.
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { cop, ErrorApi, obtener, usd, type Oferta, type OfertaFinal, type Propuesta } from '#lib/api.js';
	import { conNombres, nombresFuentes } from '#lib/datos.js';
	import { abrible, enlace, enlaceOferta, etiquetaEnlace } from '#lib/enlaces.js';

	type Lectura = { nombre: string; args: Record<string, unknown>; estado?: string };
	type Expediente = {
		version: number;
		generado: string;
		consulta: {
			id: string;
			texto: string;
			corpus: string;
			carga: string | null;
			modelo: string;
			opciones: Record<string, any>;
			estado: string;
			creada: string;
			costo_usd: number;
			segundos: number | null;
		};
		propuesta: Propuesta;
		detalle: Record<string, any> | null;
		eventos: { etapa: string; [k: string]: any }[];
		huella_sha256: string;
	};

	const id = page.params.id!;
	let exp = $state<Expediente | null>(null);
	let fallo = $state<string | null>(null);
	let nombres = $state<Record<string, string>>({});

	onMount(async () => {
		nombresFuentes().then((n) => (nombres = n)).catch(() => {});
		try {
			exp = await obtener<Expediente>(`/api/consultas/${id}/evidencia`);
		} catch (e) {
			fallo = e instanceof ErrorApi ? e.message : 'No se pudo cargar el informe.';
		}
	});

	const fecha = (iso: string) =>
		new Date(iso).toLocaleString('es-CO', { dateStyle: 'long', timeStyle: 'short' });
	const nombre = (codigo: string) => nombres[codigo] ?? codigo;
	const legible = (t: string) => conNombres(t, nombres);
	const total = (o: { precio: number; costo_envio: number | null }) => o.precio + (o.costo_envio ?? 0);
	const dias = (n: number | null) => (n == null ? '—' : `${n} ${n === 1 ? 'día' : 'días'}`);

	const CORPUS: Record<string, string> = {
		a: 'Tiendas colombianas (copias congeladas)',
		b: 'Proveedores de prueba',
		vivo: 'Tiendas en vivo y fuentes propias'
	};
	const DISPONIBILIDAD: Record<string, string> = {
		en_stock: 'En stock',
		bajo_pedido: 'Bajo pedido',
		agotado: 'Agotado',
		desconocida: 'Sin dato'
	};
	const N3: Record<string, string> = {
		verificada: 'Verificada',
		discrepancia: 'Discrepancia',
		sin_contraparte: 'Sin contraparte'
	};
	const TIPO_FUENTE: Record<string, string> = {
		mcp: 'Catálogo MCP',
		web_schema: 'Página web con datos estructurados',
		web_plana: 'Página web',
		pdf: 'Documento PDF',
		mensaje: 'Mensaje del proveedor',
		api: 'API'
	};
	const RUTA: Record<string, string> = {
		determinista: 'lectura directa de datos estructurados',
		llm: 'extracción con modelo de lenguaje',
		reextraccion: 'reextracción con modelo de lenguaje'
	};
	const ALERTA: Record<string, string> = {
		posible_inyeccion: 'Contenido sospechoso ignorado',
		precio_atipico: 'Precio atípico descartado',
		sin_verificar: 'Oferta sin confirmar',
		emparejamiento_dudoso: 'Emparejamiento dudoso',
		restriccion_incumplida: 'Restricción incumplida',
		fuente_no_disponible: 'Fuente no disponible',
		interpretacion_incompleta: 'Interpretación incompleta'
	};
	const HERRAMIENTA: Record<string, string> = {
		consultar_mcp: 'Catálogo del mayorista (MCP)',
		abrir_pagina: 'Página web',
		leer_documento: 'Documento del proveedor'
	};

	// Destino legible de una lectura: la URL completa (es evidencia) o la consulta al MCP.
	function destino(l: Lectura): string {
		const a = l.args ?? {};
		if (typeof a.url === 'string') return a.url;
		const partes = Object.entries(a)
			.filter(([, v]) => v !== '' && v != null)
			.map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`);
		return partes.join(' · ') || '—';
	}

	const p = $derived(exp?.propuesta ?? null);
	// D145: cada oferta, lectura y documento se enlaza con su fuente (también en el PDF impreso).
	const carga = $derived(exp?.consulta.carga ?? null);
	const enlaces = $derived((p?.ofertas ?? []).map((o) => enlaceOferta(o, carga)));
	const destinoUrl = (l: Lectura) => (typeof l.args?.url === 'string' ? abrible(l.args.url, carga) : null);
	const necesidad = $derived((exp?.detalle?.necesidad ?? null) as Record<string, any> | null);
	const rec = $derived(p && p.recomendada != null && !p.abstencion ? p.ofertas[p.recomendada] : null);
	const justificacion = $derived(p ? legible(p.justificacion.replace(/\s*Procedencia:.*$/s, '')) : '');

	// Bitácora: cada ronda de planificación con sus lecturas y lo que dejó cada una.
	const rondas = $derived.by(() => {
		const salida: { lecturas: Lectura[]; ofertas: number; porProveedor: Record<string, number> }[] = [];
		for (const e of exp?.eventos ?? []) {
			if (e.etapa === 'lecturas')
				salida.push({ lecturas: e.lecturas ?? [], ofertas: e.ofertas ?? 0, porProveedor: e.por_proveedor ?? {} });
		}
		return salida;
	});
	const lecturasTotales = $derived(rondas.reduce((n, r) => n + r.lecturas.length, 0));
	const lecturasFallidas = $derived(
		rondas.reduce((n, r) => n + r.lecturas.filter((l) => l.estado === 'error').length, 0)
	);
	const proveedoresConsultados = $derived(
		[...new Set(rondas.flatMap((r) => Object.keys(r.porProveedor)))]
	);

	// Ofertas que no llegaron al cuadro y por qué (mismo criterio que el laboratorio).
	const finales = $derived((exp?.detalle?.ofertas_finales ?? []) as OfertaFinal[]);
	const abierta = $derived(finales.some((o) => o.grupo != null));
	const claveP = (o: Oferta) => `${o.procedencia.fuente}|${o.titulo}|${o.precio}`;
	const claveF = (o: OfertaFinal) => `${o.proveedor}|${o.titulo}|${o.precio}`;
	const descartadas = $derived.by(() => {
		const en = new Set((p?.ofertas ?? []).map(claveP));
		return finales
			.filter((o) => !en.has(claveF(o)))
			.map((o) => ({
				...o,
				motivo:
					o.descarte ??
					(!abierta && !o.producto_catalogo
						? 'No corresponde a un producto identificable del catálogo.'
						: 'No cumple lo solicitado o la retiró un control de seguridad.')
			}))
			.sort((a, b) => a.precio - b.precio);
	});

	const ATRIBUTO: Record<string, string> = {
		tipo_producto: 'tipo de producto',
		frecuencia_refresco: 'frecuencia de refresco (Hz)',
		cancelacion_ruido: 'cancelación de ruido',
		inalambrico: 'inalámbrico',
		autonomia: 'autonomía (h)',
		tipo_almacenamiento: 'tipo de almacenamiento',
		velocidad_lectura: 'velocidad de lectura (MB/s)',
		tamano_pantalla: 'tamaño de pantalla (pulgadas)',
		resolucion: 'resolución',
		tipo_panel: 'tipo de panel',
		memoria_ram: 'memoria RAM (GB)',
		almacenamiento: 'almacenamiento (GB)',
		bateria: 'batería (mAh)',
		peso: 'peso (kg)',
		garantia: 'garantía (meses)',
		smart_tv: 'Smart TV'
	};
	function restricciones(n: Record<string, any>): string[] {
		const OP: Record<string, string> = { '>=': '≥', '<=': '≤', '==': '=' };
		return (n.restricciones ?? []).map(
			(r: any) => `${ATRIBUTO[r.atributo] ?? r.atributo.replaceAll('_', ' ')} ${OP[r.operador] ?? r.operador} ${r.valor}`
		);
	}
	// Impreso, el fragmento se recorta; completo queda en el expediente JSON, ligado por su SHA-256.
	const LIMITE_IMPRESO = 900;
	const recorte = (t: string) =>
		t.length <= LIMITE_IMPRESO
			? t
			: `${t.slice(0, LIMITE_IMPRESO)}…\n[Fragmento recortado: ${t.length.toLocaleString('es-CO')} caracteres en total; el texto completo está en el expediente JSON.]`;

	const defensas = $derived.by(() => {
		const o = exp?.consulta.opciones ?? {};
		const d = o.defensas ?? {};
		const partes: string[] = [];
		if (d.separacion_planos) partes.push('separación de instrucciones y datos');
		if (d.clasificador) partes.push('clasificador de inyección de instrucciones');
		if (d.precio) partes.push('control de precios atípicos');
		if (o.verificar) partes.push(`segunda lectura independiente de precios (si no coincide: ${o.politica_n3 === 'excluir' ? 'se excluye la oferta' : 'no se recomienda'})`);
		return partes;
	});

	let copiado = $state(false);
	async function copiarHuella() {
		if (!exp) return;
		try {
			await navigator.clipboard.writeText(exp.huella_sha256);
			copiado = true;
			setTimeout(() => (copiado = false), 1500);
		} catch {
			/* sin portapapeles: la huella sigue visible */
		}
	}
</script>

<svelte:head><title>CotIA · informe de cotización</title></svelte:head>

<div class="min-h-dvh bg-background print:bg-white">
	<nav class="no-imprimir sticky top-0 z-10 border-b bg-background/90 backdrop-blur">
		<div class="mx-auto flex max-w-4xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-6">
			<a href="/consulta/{id}" class="text-xs text-muted-foreground hover:text-foreground">← Volver a la consulta</a>
			<div class="ml-auto flex flex-wrap gap-2">
				<a
					href="/api/consultas/{id}/evidencia?descargar=true"
					class="rounded-full border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
					>Descargar evidencia (JSON)</a
				>
				<button
					type="button"
					class="rounded-full bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50"
					disabled={!exp}
					onclick={() => window.print()}>Imprimir o guardar como PDF</button
				>
			</div>
		</div>
	</nav>

	<main class="informe mx-auto max-w-4xl px-4 pt-10 pb-20 sm:px-6 print:max-w-none print:p-0">
		{#if fallo}
			<p class="text-destructive">{fallo}</p>
		{:else if !exp || !p}
			<p class="text-sm text-muted-foreground">Cargando el informe…</p>
		{:else}
			<header class="border-b pb-6">
				<p class="text-xs font-medium tracking-wide text-primary uppercase">CotIA · Informe de cotización</p>
				<h1 class="mt-2 text-2xl leading-snug font-medium tracking-tight">{exp.consulta.texto}</h1>
				<dl class="mt-5 grid grid-cols-1 gap-x-8 gap-y-1.5 text-xs sm:grid-cols-2">
					<div class="flex gap-2"><dt class="text-muted-foreground">Consulta realizada</dt><dd>{fecha(exp.consulta.creada)}</dd></div>
					<div class="flex gap-2"><dt class="text-muted-foreground">Informe generado</dt><dd>{fecha(exp.generado)}</dd></div>
					<div class="flex gap-2"><dt class="text-muted-foreground">Fuentes</dt><dd>{CORPUS[exp.consulta.corpus] ?? exp.consulta.corpus}</dd></div>
					<div class="flex gap-2"><dt class="text-muted-foreground">Identificador</dt><dd class="font-mono">{exp.consulta.id}</dd></div>
				</dl>
			</header>

			<!-- 1. Lo que pidió el comprador y cómo lo entendió el agente -->
			<section class="bloque">
				<h2>1. Solicitud y criterios aplicados</h2>
				<p class="texto">El agente convirtió la solicitud en criterios verificables; toda oferta se evaluó contra ellos.</p>
				{#if necesidad}
					<table class="tabla mt-4">
						<tbody>
							{#if necesidad.tipo_producto}<tr><th>Tipo de producto</th><td>{necesidad.tipo_producto}</td></tr>{/if}
							{#if necesidad.marca}<tr><th>Marca</th><td>{necesidad.marca}</td></tr>{/if}
							{#if necesidad.producto_mencionado}<tr><th>Producto mencionado</th><td>{necesidad.producto_mencionado}</td></tr>{/if}
							<tr><th>Presupuesto máximo</th><td>{necesidad.presupuesto_max ? `${cop(necesidad.presupuesto_max)} (precio + envío)` : 'No indicado'}</td></tr>
							<tr><th>Plazo máximo de entrega</th><td>{necesidad.plazo_max_dias ? dias(necesidad.plazo_max_dias) : 'No indicado'}</td></tr>
							<tr>
								<th>Especificaciones exigidas</th>
								<td>{restricciones(necesidad).join(' · ') || 'Ninguna'}</td>
							</tr>
						</tbody>
					</table>
				{:else}
					<p class="texto mt-3">La interpretación de la solicitud no quedó registrada.</p>
				{/if}
			</section>

			<!-- 2. La decisión -->
			<section class="bloque">
				<h2>2. Decisión</h2>
				{#if rec}
					<div class="mt-4 rounded-lg border p-4 sm:p-5">
						<div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
							<div class="min-w-0">
								<p class="text-xs font-medium text-primary">Opción recomendada</p>
								<p class="mt-1 font-medium leading-snug">{rec.titulo}</p>
								<p class="mt-1 text-xs text-muted-foreground">
									{nombre(rec.procedencia.fuente)} · entrega {dias(rec.plazo_entrega_dias)} · {DISPONIBILIDAD[rec.disponibilidad]}{rec.verificacion ? ` · precio ${N3[rec.verificacion].toLowerCase()}` : ''}
								</p>
							</div>
							<div class="shrink-0 sm:text-right">
								<p class="cifra text-2xl font-semibold">{cop(total(rec))}</p>
								<p class="text-xs text-muted-foreground">{cop(rec.precio)} + envío {cop(rec.costo_envio)}</p>
							</div>
						</div>
					</div>
					<h3>Justificación</h3>
					<p class="texto">{justificacion}</p>
				{:else}
					<p class="mt-3 font-medium">Sin recomendación de compra.</p>
					<h3>Motivo</h3>
					<p class="texto">{legible(p.motivo_abstencion ?? p.justificacion)}</p>
				{/if}
			</section>

			<!-- 3. Cuadro comparativo -->
			<section class="bloque">
				<h2>3. Cuadro comparativo</h2>
				<p class="texto">
					{p.ofertas.length}
					{p.ofertas.length === 1 ? 'oferta cumple' : 'ofertas cumplen'} los criterios y se comparan por costo total
					(precio más envío). La marca ● señala la recomendada; el título de cada producto (↗) abre la página o el
					documento de donde se tomó.
				</p>
				{#if p.ofertas.length}
					<div class="mt-4 overflow-x-auto print:overflow-visible">
						<table class="tabla">
							<thead>
								<tr>
									<th>#</th><th>Producto</th><th>Proveedor</th><th class="num">Precio</th><th class="num">Envío</th>
									<th class="num">Total</th><th>Entrega</th><th>Disponib.</th><th>Precio confirmado</th>
								</tr>
							</thead>
							<tbody>
								{#each p.ofertas as o, i (i)}
									<tr class={i === p.recomendada && !p.abstencion ? 'font-medium' : ''}>
										<td>{i === p.recomendada && !p.abstencion ? '●' : ''} {i + 1}</td>
										<td class="min-w-48">
											{#if enlaces[i]}<a href={enlaces[i]!.href} target="_blank" rel="noopener noreferrer" class="enlace" title={etiquetaEnlace(o, enlaces[i]!)}>{o.titulo} ↗</a>{:else}{o.titulo}{/if}
										</td>
										<td class="whitespace-nowrap">{nombre(o.procedencia.fuente)}</td>
										<td class="num">{cop(o.precio)}</td>
										<td class="num">{cop(o.costo_envio)}</td>
										<td class="num">{cop(total(o))}</td>
										<td>{dias(o.plazo_entrega_dias)}</td>
										<td>{DISPONIBILIDAD[o.disponibilidad]}</td>
										<td>{o.verificacion ? N3[o.verificacion] : 'No se verificó'}{o.campos_discrepancia?.length ? ` (${o.campos_discrepancia.join(', ').replaceAll('_', ' ')})` : ''}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</section>

			<!-- 4. Lo que se descartó -->
			<section class="bloque">
				<h2>4. Ofertas descartadas</h2>
				{#if descartadas.length}
					<p class="texto">
						{descartadas.length}
						{descartadas.length === 1 ? 'oferta encontrada quedó' : 'ofertas encontradas quedaron'} fuera del cuadro, cada una con su motivo.
					</p>
					<div class="mt-4 overflow-x-auto print:overflow-visible">
						<table class="tabla">
							<thead><tr><th>Producto</th><th>Proveedor</th><th class="num">Precio</th><th>Motivo del descarte</th></tr></thead>
							<tbody>
								{#each descartadas as o, i (i)}
									<tr>
										<td class="min-w-48">
											{#if enlace(o.url_fuente, o.url_detalle, carga)}<a href={enlace(o.url_fuente, o.url_detalle, carga)!.href} target="_blank" rel="noopener noreferrer" class="enlace">{o.titulo} ↗</a>{:else}{o.titulo}{/if}
										</td>
										<td class="whitespace-nowrap">{nombre(o.proveedor)}</td>
										<td class="num">{cop(o.precio)}</td>
										<td>{legible(o.motivo)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{:else}
					<p class="texto">No se descartaron ofertas después de la comparación.</p>
				{/if}
			</section>

			<!-- 5. Bitácora de la investigación -->
			<section class="bloque">
				<h2>5. Investigación realizada</h2>
				<p class="texto">
					El agente hizo {lecturasTotales} {lecturasTotales === 1 ? 'lectura' : 'lecturas'} en {rondas.length}
					{rondas.length === 1 ? 'ronda' : 'rondas'}{lecturasFallidas ? `, de las cuales ${lecturasFallidas} no obtuvieron respuesta` : ''},
					y reunió {exp.detalle?.ofertas_recolectadas ?? '—'} ofertas de
					{proveedoresConsultados.length} {proveedoresConsultados.length === 1 ? 'proveedor' : 'proveedores'}{proveedoresConsultados.length ? ` (${proveedoresConsultados.map(nombre).join(', ')})` : ''}.
				</p>
				{#each rondas as r, i (i)}
					<h3>Ronda {i + 1}</h3>
					<ol class="mt-2 space-y-1.5 text-sm">
						{#each r.lecturas as l, j (j)}
							<li class="flex gap-2">
								<span class="shrink-0 {l.estado === 'error' ? 'text-destructive' : 'text-primary'}">{l.estado === 'error' ? '✕' : '✓'}</span>
								<span class="min-w-0">
									<span class="text-muted-foreground">{HERRAMIENTA[l.nombre] ?? l.nombre}:</span>
									{#if destinoUrl(l)}<a href={destinoUrl(l)} target="_blank" rel="noopener noreferrer" class="enlace break-all">{destino(l)}</a
										>{:else}<span class="break-all">{destino(l)}</span>{/if}
									{#if l.estado === 'error'}<span class="text-destructive"> (sin respuesta)</span>{/if}
								</span>
							</li>
						{/each}
					</ol>
					<p class="mt-1.5 text-xs text-muted-foreground">
						{r.ofertas} {r.ofertas === 1 ? 'oferta extraída' : 'ofertas extraídas'}{Object.keys(r.porProveedor).length ? ': ' + Object.entries(r.porProveedor).map(([k, n]) => `${nombre(k)} ${n}`).join(' · ') : ''}.
					</p>
				{:else}
					<p class="texto mt-2">La bitácora de lecturas no quedó registrada para esta consulta.</p>
				{/each}
			</section>

			<!-- 6. Controles y alertas -->
			<section class="bloque">
				<h2>6. Controles de seguridad y alertas</h2>
				<p class="texto">
					Controles activos: {defensas.length ? defensas.join('; ') : 'ninguno'}. El contenido de las páginas se
					trata como dato y no como instrucción: un texto en una tienda no puede cambiar la tarea del agente.
				</p>
				{#if p.alertas.length}
					<ul class="mt-3 space-y-2 text-sm">
						{#each p.alertas as a, i (i)}
							<li><span class="font-medium">{ALERTA[a.tipo] ?? a.tipo}.</span> <span class="text-muted-foreground">{legible(a.mensaje)}</span></li>
						{/each}
					</ul>
				{:else}
					<p class="texto mt-2">No se registraron alertas.</p>
				{/if}
			</section>

			<!-- Anexo: procedencia de cada dato -->
			<section class="bloque anexo">
				<h2>Anexo. Procedencia de cada oferta comparada</h2>
				<p class="texto">
					Cada dato del cuadro proviene de un fragmento original de la fuente, leído en la fecha indicada. La suma
					SHA-256 identifica ese fragmento: si la fuente cambia, la suma cambia. Las direcciones enlazadas abren la
					página o el documento leído; el precio vigente puede diferir del registrado si la tienda lo cambió
					después.
				</p>
				{#each p.ofertas as o, i (i)}
					<article class="mt-5 border-t pt-4">
						<p class="text-sm font-medium break-after-avoid">{i + 1}. {o.titulo}</p>
						<dl class="mt-2 grid break-inside-avoid grid-cols-1 gap-y-1 text-xs sm:grid-cols-[11rem_1fr]">
							<dt class="text-muted-foreground">Proveedor</dt><dd>{nombre(o.procedencia.fuente)} · {TIPO_FUENTE[o.procedencia.tipo_fuente] ?? o.procedencia.tipo_fuente}</dd>
							{#if o.url_detalle}<dt class="text-muted-foreground">Página del producto</dt><dd class="break-all">{#if enlaces[i]?.ficha}<a href={enlaces[i]!.href} target="_blank" rel="noopener noreferrer" class="enlace">{o.url_detalle}</a>{:else}{o.url_detalle} <span class="text-muted-foreground">(no se enlaza: no pertenece al sitio leído)</span>{/if}</dd>{/if}
							<dt class="text-muted-foreground">Obtenido con</dt><dd class="break-all">{#if abrible(o.procedencia.consulta, carga)}<a href={abrible(o.procedencia.consulta, carga)} target="_blank" rel="noopener noreferrer" class="enlace">{o.procedencia.consulta}</a>{:else}{o.procedencia.consulta}{/if}</dd>
							<dt class="text-muted-foreground">Fecha de lectura</dt><dd>{fecha(o.procedencia.marca_tiempo)}</dd>
							<dt class="text-muted-foreground">Extracción</dt><dd>{RUTA[o.procedencia.ruta_extraccion] ?? o.procedencia.ruta_extraccion}{o.procedencia.modelo_extraccion ? ` (${o.procedencia.modelo_extraccion})` : ''}</dd>
							{#if o.gtin || o.marca || o.modelo}<dt class="text-muted-foreground">Identificación</dt><dd>{[o.marca, o.modelo, o.gtin ? `GTIN ${o.gtin}` : null].filter(Boolean).join(' · ')}</dd>{/if}
							<dt class="text-muted-foreground">SHA-256</dt><dd class="font-mono break-all">{o.procedencia.suma_verificacion || '—'}</dd>
						</dl>
						<pre class="mt-3 max-h-64 overflow-auto rounded-md bg-muted p-3 text-[11px] leading-relaxed whitespace-pre-wrap text-muted-foreground print:hidden">{o.procedencia.fragmento_original}</pre>
						<pre class="mt-3 hidden rounded-md bg-muted p-3 text-[10px] leading-relaxed break-all whitespace-pre-wrap text-muted-foreground print:block">{recorte(o.procedencia.fragmento_original)}</pre>
					</article>
				{/each}
			</section>

			<footer class="bloque border-t pt-6 text-xs text-muted-foreground">
				<p>
					Modelo {exp.consulta.modelo} · costo de la consulta {usd(exp.consulta.costo_usd)}{exp.consulta.segundos != null ? ` · ${Math.round(exp.consulta.segundos)} s` : ''}{exp.detalle?.llamadas_llm != null ? ` · ${exp.detalle.llamadas_llm} llamadas al modelo` : ''}.
					CotIA cotiza y recomienda; no ejecuta compras ni pagos. La decisión final es del comprador.
				</p>
				<p class="mt-3">
					Huella de integridad del expediente (SHA-256):
					<button type="button" class="font-mono break-all text-foreground hover:text-primary" title="Copiar" onclick={copiarHuella}>{exp.huella_sha256}</button>{copiado ? ' · copiada' : ''}
				</p>
				<p class="mt-1">
					El expediente JSON descargable contiene todos los datos de este informe; recalcular su huella permite comprobar
					que no se modificó después de generarlo.
				</p>
			</footer>
		{/if}
	</main>
</div>

<style>
	.enlace {
		color: var(--primary);
		text-underline-offset: 2px;
	}
	.enlace:hover {
		text-decoration: underline;
	}
	.informe :global(h2) {
		font-size: 1rem;
		font-weight: 500;
		letter-spacing: -0.01em;
	}
	.informe :global(h3) {
		margin-top: 1.25rem;
		font-size: 0.8125rem;
		font-weight: 500;
		color: var(--muted-foreground);
	}
	.bloque {
		margin-top: 2.5rem;
	}
	.texto {
		margin-top: 0.5rem;
		font-size: 0.875rem;
		line-height: 1.6;
		color: var(--muted-foreground);
	}
	.tabla {
		width: 100%;
		font-size: 0.8125rem;
		border-collapse: collapse;
		font-variant-numeric: tabular-nums;
	}
	.tabla :global(th),
	.tabla :global(td) {
		padding: 0.5rem 0.75rem 0.5rem 0;
		border-bottom: 1px solid var(--border);
		text-align: left;
		vertical-align: top;
	}
	.tabla :global(thead th) {
		font-size: 0.75rem;
		font-weight: 400;
		color: var(--muted-foreground);
		white-space: nowrap;
	}
	.tabla :global(tbody th) {
		width: 14rem;
		font-weight: 400;
		color: var(--muted-foreground);
	}
	.tabla :global(.num) {
		text-align: right;
		white-space: nowrap;
	}
	@media print {
		.no-imprimir {
			display: none;
		}
		.bloque {
			break-inside: auto;
		}
		.informe :global(h2),
		.informe :global(h3) {
			break-after: avoid;
		}
		.tabla :global(tr) {
			break-inside: avoid;
		}
		.anexo {
			break-before: page;
		}
	}
	@page {
		size: letter;
		margin: 18mm 16mm;
	}
</style>
