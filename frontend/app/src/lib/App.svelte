<script lang="ts">
	import { createApi, type Fetch } from './api/index.js';

	let { fetch }: { fetch: Fetch } = $props();
	const api = $derived(createApi(fetch));
</script>

<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>
