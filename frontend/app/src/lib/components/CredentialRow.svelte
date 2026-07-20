<script lang="ts">
	import { onDestroy } from 'svelte';

	let {
		label,
		value
	}: {
		label: string;
		value?: string;
	} = $props();

	let copied = $state(false);
	let copyError = $state(false);
	let resetTimer: ReturnType<typeof setTimeout> | undefined;

	async function copyValue() {
		if (!value) return;
		try {
			await navigator.clipboard.writeText(value);
			copied = true;
			copyError = false;
			clearTimeout(resetTimer);
			resetTimer = setTimeout(() => (copied = false), 1600);
		} catch {
			copyError = true;
		}
	}

	onDestroy(() => clearTimeout(resetTimer));
</script>

<div class="border-t border-stone-100 py-3 first:border-t-0 first:pt-0 last:pb-0">
	<div class="mb-1.5 flex items-center justify-between gap-3">
		<span class="text-xs font-700 uppercase tracking-wider text-stone-400">{label}</span>
		<div class="flex items-center gap-1">
			<button
				type="button"
				class="rounded-lg px-2 py-1 text-xs font-700 text-emerald-700 transition hover:bg-emerald-50 disabled:cursor-not-allowed disabled:text-stone-300"
				disabled={!value}
				onclick={copyValue}
			>{copied ? '已复制' : copyError ? '复制失败' : '复制'}</button
			>
		</div>
	</div>
	<p class="m-0 break-all font-mono text-xs leading-5 text-stone-700">
		{value || '正在获取 Token…'}
	</p>
</div>
