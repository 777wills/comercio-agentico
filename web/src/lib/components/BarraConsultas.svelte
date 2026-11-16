<script lang="ts">
	// Barra lateral del modo Cliente (D140): nueva consulta, historial del visitante y, abajo, ajustes,
	// tema y laboratorio. En escritorio se colapsa; en móvil es un cajón.
	import { page } from '$app/state';
	import { onDestroy } from 'svelte';
	import * as Sidebar from '#lib/components/ui/sidebar/index.js';
	import { ajustes, config, visita } from '#lib/config.svelte.js';
	import { usd, type Resumen } from '#lib/api.js';
	import Tema from '#lib/components/Tema.svelte';
	import Plus from '@lucide/svelte/icons/plus';
	import Settings from '@lucide/svelte/icons/settings-2';
	import FlaskConical from '@lucide/svelte/icons/flask-conical';

	const sidebar = Sidebar.useSidebar();
	const cerrarEnMovil = () => {
		if (sidebar.isMobile) sidebar.setOpenMobile(false);
	};

	// Las ejecuciones del laboratorio de ataques no son consultas del cliente.
	const propias = $derived(visita.consultas.filter((c) => !c.carga));

	const GRUPOS = ['Hoy', 'Ayer', 'Últimos 7 días', 'Anteriores'] as const;
	function grupo(c: Resumen) {
		const hoy = new Date();
		hoy.setHours(0, 0, 0, 0);
		const dias = Math.floor((hoy.getTime() - new Date(c.creada).getTime()) / 86_400_000) + 1;
		return dias <= 0 ? GRUPOS[0] : dias === 1 ? GRUPOS[1] : dias <= 7 ? GRUPOS[2] : GRUPOS[3];
	}
	const agrupadas = $derived(
		GRUPOS.map((g) => [g, propias.filter((c) => grupo(c) === g)] as const).filter(([, l]) => l.length)
	);

	// Mientras alguna consulta siga en cola o en curso, la lista se refresca para mostrar su estado.
	const enCurso = $derived(propias.some((c) => c.estado === 'en_cola' || c.estado === 'en_curso'));
	let reloj: ReturnType<typeof setInterval> | undefined;
	$effect(() => {
		if (!enCurso) return;
		reloj = setInterval(() => visita.refrescar().catch(() => {}), 5000);
		return () => clearInterval(reloj);
	});
	onDestroy(() => clearInterval(reloj));

	const ESTADO: Record<string, string> = {
		en_cola: 'En cola',
		en_curso: 'En curso',
		terminada: 'Terminada',
		error: 'Con error',
		cancelada: 'Cancelada'
	};
</script>

<Sidebar.Root collapsible="offcanvas">
	<Sidebar.Header class="gap-3 px-3 pt-4">
		<a href="/" class="px-2 text-base font-semibold tracking-tight" onclick={cerrarEnMovil}
			>Cot<span class="text-primary">IA</span></a
		>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton class="border bg-background hover:bg-background/70">
					{#snippet child({ props })}
						<a href="/" {...props} onclick={cerrarEnMovil}><Plus /> <span>Nueva consulta</span></a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>

	<Sidebar.Content class="px-1">
		{#if agrupadas.length}
			{#each agrupadas as [nombre, lista] (nombre)}
				<Sidebar.Group>
					<Sidebar.GroupLabel>{nombre}</Sidebar.GroupLabel>
					<Sidebar.Menu>
						{#each lista as c (c.id)}
							<Sidebar.MenuItem>
								<Sidebar.MenuButton isActive={page.params.id === c.id} class="h-auto py-1.5">
									{#snippet child({ props })}
										<a href="/consulta/{c.id}" {...props} title={c.consulta} onclick={cerrarEnMovil}>
											<span
												class="size-1.5 shrink-0 rounded-full {c.estado === 'terminada'
													? 'bg-transparent'
													: c.estado === 'error'
														? 'bg-destructive'
														: c.estado === 'cancelada'
															? 'bg-muted-foreground/50'
															: 'animate-pulse bg-primary'}"
												aria-label={ESTADO[c.estado] ?? c.estado}
												role="img"
											></span>
											<span>{c.consulta}</span>
										</a>
									{/snippet}
								</Sidebar.MenuButton>
							</Sidebar.MenuItem>
						{/each}
					</Sidebar.Menu>
				</Sidebar.Group>
			{/each}
		{:else}
			<p class="px-4 py-3 text-xs leading-relaxed text-muted-foreground">
				Sus consultas aparecerán aquí. Se guardan solo en este navegador.
			</p>
		{/if}
	</Sidebar.Content>

	<Sidebar.Footer class="gap-1 border-t px-3 pb-4">
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton
					onclick={() => {
						cerrarEnMovil();
						ajustes.abierto = true;
					}}
				>
					<Settings />
					<span>Ajustes</span>
					<span
						class="ml-auto size-1.5 shrink-0 rounded-full {config.clave ? 'bg-primary' : 'bg-muted-foreground/50'}"
						aria-label={config.clave ? 'Clave configurada' : 'Sin clave'}
						role="img"
					></span>
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton>
					{#snippet child({ props })}
						<a href="/lab" {...props}><FlaskConical /> <span>Laboratorio del experimento</span></a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
		<div class="flex flex-wrap items-center justify-between gap-x-2 gap-y-2 px-2 pt-2 text-xs text-muted-foreground">
			<span class="cifra"
				>{visita.total} {visita.total === 1 ? 'consulta' : 'consultas'} · {usd(visita.gasto)}</span
			>
			<Tema />
		</div>
	</Sidebar.Footer>
	<Sidebar.Rail />
</Sidebar.Root>
