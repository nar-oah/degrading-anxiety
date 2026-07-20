<script lang="ts">
	import { App } from '@degrading-anxiety/app';
	import { store } from '$lib/store.js';
</script>

<App fetch={globalThis.fetch} {store} apiBaseUrl="/api/" />
