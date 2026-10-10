<script lang="ts">
	import '../app.css';
	import 'maplibre-gl/dist/maplibre-gl.css';
	import 'svelte-maplibre-gl/vite'; // registers the MapLibre web worker under Vite
	import favicon from '#lib/assets/favicon.svg';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Property Acquisition Analyser</title>
	<meta
		name="description"
		content="Is this house fairly priced? UK sold prices per square metre, mapped."
	/>
</svelte:head>

{@render children()}
