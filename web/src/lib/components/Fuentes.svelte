<script lang="ts">
	// Lista blanca del visitante (D113): ver, activar, agregar y eliminar fuentes.
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { ErrorApi, type Grupo } from '#lib/api.js';
	import { config, fuentes } from '#lib/config.svelte.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import { Switch } from '#lib/components/ui/switch/index.js';
	import { Input } from '#lib/components/ui/input/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import Trash from '@lucide/svelte/icons/trash-2';
	import FileUp from '@lucide/svelte/icons/file-up';
	import Plus from '@lucide/svelte/icons/plus';

	let url = $state('');
	let selector = $state<HTMLInputElement>();

	const TIPO: Record<string, string> = {
		mcp: 'Catálogo MCP',
		web_schema: 'Tienda web',
		web_plana: 'Tienda web',
		pdf: 'PDF',
		mensaje: 'Chat'
	};
	const AYUDA: Record<Grupo, string> = {
		vivo: 'Tiendas reales en internet, leídas en el momento. Puede agregar las suyas y sus listas de precios en PDF.',
		a: 'Réplicas de tiendas colombianas con datos leídos el 9-nov-2026. Siempre dan el mismo resultado.',
		b: 'Cinco proveedores ficticios en formatos distintos: catálogo MCP, dos webs, PDF y chat.'
	};

	onMount(() => {
		if (!fuentes.lista) fuentes.cargar().catch(() => {});
	});

	async function intentar(accion: () => Promise<void>, exito?: string) {
		try {
			await accion();
			if (exito) toast.success(exito);
		} catch (e) {
			toast.error(e instanceof ErrorApi ? e.message : 'No se pudo completar la acción.');
		}
	}

	const grupo = $derived(fuentes.grupo(config.corpus));
	const propias = $derived(grupo?.fuentes.filter((f) => f.eliminable) ?? []);
	const urlsPropias = $derived(propias.filter((f) => f.tipo_fuente !== 'pdf').length);
	const pdfsPropios = $derived(propias.filter((f) => f.tipo_fuente === 'pdf').length);
</script>

<Dialog.Root bind:open={fuentes.panel}>
	<Dialog.Content class="max-h-[85vh] gap-5 overflow-y-auto p-6 sm:max-w-xl">
		<Dialog.Header>
			<Dialog.Title class="text-base">Fuentes</Dialog.Title>
			<Dialog.Description>
				Cada consulta usa un solo grupo: el de la pestaña seleccionada al cerrar este panel, con sus
				fuentes activas. Así no se mezclan tiendas reales con proveedores de prueba. Sus cambios valen
				solo en este navegador.
			</Dialog.Description>
		</Dialog.Header>

		<div class="flex gap-1 rounded-lg bg-muted/40 p-1 text-sm">
			{#each fuentes.lista?.grupos ?? [] as g (g.id)}
				<button
					class="flex-1 rounded-md px-2 py-1.5 transition-colors {config.corpus === g.id
						? 'bg-background text-foreground'
						: 'text-muted-foreground hover:text-foreground'}"
					onclick={() => (config.corpus = g.id)}>{g.nombre}</button
				>
			{/each}
		</div>
		<p class="-mt-2 text-xs text-muted-foreground">{AYUDA[config.corpus]}</p>

		{#if grupo}
			<ul class="divide-y rounded-lg border">
				{#each grupo.fuentes as f (f.id)}
					<li class="flex items-center gap-3 px-3 py-2.5">
						<Switch
							checked={f.activa}
							disabled={fuentes.ocupado}
							onCheckedChange={(v) => intentar(() => fuentes.activar(f.id, v))}
							aria-label="Activar {f.nombre}"
						/>
						<div class="min-w-0 flex-1">
							<div class="truncate text-sm {f.activa ? '' : 'text-muted-foreground'}">{f.nombre}</div>
							<div class="truncate text-xs text-muted-foreground" title={f.url}>
								{TIPO[f.tipo_fuente] ?? f.tipo_fuente}{f.origen === 'usuario' ? ' · agregada por usted' : ''}
								· {f.url}
							</div>
						</div>
						{#if f.eliminable}
							<Button
								variant="ghost"
								size="icon-sm"
								aria-label="Eliminar {f.nombre}"
								disabled={fuentes.ocupado}
								onclick={() => intentar(() => fuentes.eliminar(f.id), 'Fuente eliminada.')}
							>
								<Trash class="size-4" />
							</Button>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}

		{#if config.corpus === 'vivo' && fuentes.lista}
			{@const lim = fuentes.lista.limites}
			<div class="space-y-3">
				<form
					class="flex gap-2"
					onsubmit={(e) => {
						e.preventDefault();
						intentar(async () => {
							await fuentes.agregarUrl(url);
							url = '';
						}, 'Tienda agregada.');
					}}
				>
					<Input
						bind:value={url}
						type="url"
						placeholder="https://www.mitienda.com/"
						disabled={urlsPropias >= lim.urls || fuentes.ocupado}
					/>
					<Button type="submit" variant="secondary" disabled={url.length < 8 || urlsPropias >= lim.urls || fuentes.ocupado}>
						<Plus /> Tienda
					</Button>
				</form>
				<input
					bind:this={selector}
					type="file"
					accept="application/pdf"
					class="hidden"
					onchange={(e) => {
						const archivo = (e.currentTarget as HTMLInputElement).files?.[0];
						if (archivo) intentar(() => fuentes.agregarPdf(archivo), 'PDF agregado.');
						(e.currentTarget as HTMLInputElement).value = '';
					}}
				/>
				<Button
					variant="secondary"
					class="w-full"
					disabled={pdfsPropios >= lim.pdfs || fuentes.ocupado}
					onclick={() => selector?.click()}
				>
					<FileUp /> Subir lista de precios (PDF)
				</Button>
				<p class="text-xs text-muted-foreground">
					Hasta {lim.urls} tiendas y {lim.pdfs} PDF de {lim.mb_pdf} MB. CotIA solo abre direcciones
					públicas y respeta el robots.txt de cada sitio. Del PDF se guarda el texto y su huella
					SHA-256, no el archivo.
				</p>
			</div>
		{/if}

		<button
			class="justify-self-start text-xs text-muted-foreground hover:text-foreground"
			disabled={fuentes.ocupado}
			onclick={() =>
				intentar(() => fuentes.restablecer(), 'Lista restablecida: todas activas y sin fuentes propias.')}
			>Restablecer la lista por defecto</button
		>
	</Dialog.Content>
</Dialog.Root>
