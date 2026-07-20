<script lang="ts">
	import App from '$lib/App.svelte';
	import type { Store } from '$lib/store/storage.js';

	const store: Store = {
		async get<T>(key: string): Promise<T | undefined> {
			const value = globalThis.localStorage.getItem(key);
			return value === null ? undefined : (JSON.parse(value) as T);
		},
		async set(key: string, value: unknown): Promise<void> {
			globalThis.localStorage.setItem(key, JSON.stringify(value));
		}
	};
</script>

<App fetch={globalThis.fetch} {store} />
