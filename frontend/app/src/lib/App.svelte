<script lang="ts">
	import { onMount } from 'svelte';
	import { createApi, type Fetch } from './api/index.js';
	import { createAppStore } from './store/app.svelte.js';
	import type { Store } from './store/storage.js';

	let { fetch, store }: { fetch: Fetch; store: Store } = $props();
	const api = $derived(createApi(fetch));
	const appStore = createAppStore(store, api);

	onMount(() => {
		void appStore.init();
	});
</script>

<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>
