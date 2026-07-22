<script lang="ts">
	import { onMount } from 'svelte';
	import type { REvent } from '../api/index.js';
	import { toMinutes, toTodayDateTime } from '../routine.js';

	let {
		onadd,
		disabled = false
	}: {
		onadd: (event: REvent) => Promise<void>;
		disabled?: boolean;
	} = $props();

	let summary = $state('');
	let startTime = $state('');
	let endTime = $state('');
	let error = $state('');
	let saving = $state(false);
	let summaryInput: HTMLInputElement;

	const pad = (value: number) => String(value).padStart(2, '0');
	const toInputValue = (date: Date) => `${pad(date.getHours())}:${pad(date.getMinutes())}`;

	function resetTime() {
		const start = new Date();
		start.setSeconds(0, 0);
		start.setMinutes(Math.ceil((start.getMinutes() + 1) / 30) * 30);
		const end = new Date(start.getTime() + 30 * 60 * 1000);
		startTime = toInputValue(start);
		endTime = toInputValue(end);
	}

	onMount(resetTime);

	async function addEvent(submit: SubmitEvent) {
		submit.preventDefault();
		const text = summary.trim();

		if (!text) {
			error = '请填写日常任务内容';
			summaryInput?.focus();
			return;
		}
		if (!startTime || !endTime) {
			error = '请选择有效的开始和结束时间';
			return;
		}
		if (toMinutes(endTime) <= toMinutes(startTime)) {
			error = '结束时间需要晚于开始时间';
			return;
		}

		saving = true;
		error = '';
		try {
			await onadd({
				summary: text,
				dtstart: toTodayDateTime(startTime),
				dtend: toTodayDateTime(endTime),
				location: '',
				description: text,
				alarms: [15],
				repeat: null
			});
			summary = '';
			resetTime();
			summaryInput?.focus();
		} catch (value) {
			error = value instanceof Error && value.message ? value.message : '日常任务保存失败，请重试';
		} finally {
			saving = false;
		}
	}
</script>

<form class="rounded-2xl bg-stone-50 p-4 sm:p-5" onsubmit={addEvent}>
	<div class="mb-4 flex items-center justify-between gap-3">
		<div>
			<h3 class="m-0 text-base font-700 text-stone-900">添加固定日程</h3>
			<p class="m-0 mt-1 text-xs text-stone-500">指定占用时间，安排其他任务时会避开这段日程</p>
		</div>
		<span class="h-2.5 w-2.5 shrink-0 rounded-full bg-sky-400"></span>
	</div>

	<div class="grid gap-3 sm:grid-cols-2">
		<label class="grid min-w-0 gap-1.5 text-sm font-600 text-stone-700 sm:col-span-2">
			<span>日程内容</span>
			<input
				bind:this={summaryInput}
				bind:value={summary}
				class="box-border h-11 w-full min-w-0 rounded-xl border border-stone-200 bg-white px-3.5 text-sm text-stone-900 outline-none transition focus:border-sky-500 focus:ring-3 focus:ring-sky-100"
				placeholder="例如：午餐和散步"
				maxlength="120"
				disabled={disabled || saving}
			/>
		</label>

		<label class="grid min-w-0 gap-1.5 text-sm font-600 text-stone-700">
			<span>开始时间</span>
			<input bind:value={startTime} class="box-border h-11 min-w-0 rounded-xl border border-stone-200 bg-white px-3 text-sm text-stone-900 outline-none focus:border-sky-500 focus:ring-3 focus:ring-sky-100" type="time" step="60" disabled={disabled || saving} />
		</label>

		<label class="grid min-w-0 gap-1.5 text-sm font-600 text-stone-700">
			<span>结束时间</span>
			<input bind:value={endTime} class="box-border h-11 min-w-0 rounded-xl border border-stone-200 bg-white px-3 text-sm text-stone-900 outline-none focus:border-sky-500 focus:ring-3 focus:ring-sky-100" type="time" step="60" disabled={disabled || saving} />
		</label>

		<button type="submit" class="box-border h-11 w-full rounded-xl bg-stone-900 px-5 text-sm font-700 text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-stone-300 sm:col-span-2" disabled={disabled || saving}>
			{saving ? '保存中…' : '添加日常任务'}
		</button>
	</div>

	{#if error}
		<p class="m-0 mt-3 text-sm text-red-600" role="alert">{error}</p>
	{/if}
</form>
