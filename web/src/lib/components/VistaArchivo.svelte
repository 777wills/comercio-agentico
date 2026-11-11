<script lang="ts">
	let { url, alto = 'h-[32rem]', marca = null }: { url: string; alto?: string; marca?: string | null } =
		$props();

	const tipo = $derived(url.split('.').pop());
	let vista = $state<'vista' | 'fuente'>('vista');
	let texto = $state<string | null>(null);

	$effect(() => {
		texto = null;
		if (tipo !== 'pdf') fetch(url).then(async (r) => (texto = r.ok ? await r.text() : 'No disponible.'));
	});

	/** Parte el texto alrededor de la carga plantada (por sus primeros caracteres). */
	const partes = $derived.by(() => {
		if (!texto || !marca) return null;
		for (const n of [60, 30]) {
			const inicio = texto.indexOf(marca.slice(0, n));
			if (inicio >= 0) {
				const corte = inicio + marca.length;
				return [texto.slice(0, inicio), texto.slice(inicio, corte), texto.slice(corte)];
			}
		}
		return null;
	});

	let pre = $state<HTMLElement | null>(null);
	$effect(() => {
		if (partes && pre) pre.querySelector('mark')?.scrollIntoView({ block: 'center' });
	});
</script>

{#if tipo === 'html'}
	<div class="mb-2 flex gap-1 text-xs">
		{#each [['vista', 'Vista'], ['fuente', 'Código fuente']] as [v, t] (v)}
			<button
				type="button"
				class="rounded px-2 py-1 {vista === v ? 'bg-muted' : 'text-muted-foreground'}"
				onclick={() => (vista = v as 'vista' | 'fuente')}>{t}</button
			>
		{/each}
	</div>
{/if}

{#if tipo === 'pdf'}
	<iframe title="PDF" src={url} class="w-full rounded-md border bg-white {alto}"></iframe>
{:else if tipo === 'html' && vista === 'vista'}
	<!-- sandbox vacío: sin scripts, sin formularios y en un origen opaco -->
	<iframe title="Página" src={url} sandbox="" class="w-full rounded-md border bg-white {alto}"></iframe>
{:else}
	<pre
		bind:this={pre}
		class="overflow-auto rounded-md border bg-background p-3 text-xs whitespace-pre-wrap {alto}">{#if partes}{partes[0]}<mark
				class="rounded bg-destructive/30 px-0.5 text-foreground">{partes[1]}</mark
			>{partes[2]}{:else}{texto ?? 'Cargando…'}{/if}</pre>
{/if}
