<script lang="ts">
	import { App } from '@degrading-anxiety/app';
	import { fetch } from '@tauri-apps/plugin-http';
	import { store } from '$lib/store.js';
</script>

<App {fetch} {store} />
