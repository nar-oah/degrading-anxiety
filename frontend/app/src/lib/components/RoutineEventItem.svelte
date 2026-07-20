<script lang="ts">
	import type { REvent } from '../api/index.js';

	let {
		routine,
		index,
		onupdate,
		onremove
	}: {
		routine: REvent;
		index: number;
		onupdate: (index: number, event: REvent) => Promise<void>;
		onremove: (index: number) => Promise<void>;
	} = $props();

	let editing = $state(false);
	let confirming = $state(false);
	let busy = $state(false);
	let summary = $state('');
	let dtstart = $state('');
	let dtend = $state('');
	let error = $state('');

	const toInputValue = (value: string) => value.slice(0, 16);
	const formatDateTime = (value: string) => {
		const date = new Date(value);
		return Number.isNaN(date.getTime())
			? value
			: new Intl.DateTimeFormat('zh-CN', {
					month: 'numeric',
					day: 'numeric',
					hour: '2-digit',
					minute: '2-digit',
					hour12: false
				}).format(date);
	};

	function startEditing() {
		summary = routine.summary;
		dtstart = toInputValue(routine.dtstart);
		dtend = toInputValue(routine.dtend);
		confirming = false;
		error = '';
		editing = true;
	}

	function cancelEditing() {
		editing = false;
		error = '';
	}

	async function saveEvent(submit: SubmitEvent) {
		submit.preventDefault();
		const text = summary.trim();
		const start = new Date(dtstart);
		const end = new Date(dtend);
		if (!text) {
			error = '日程内容不能为空';
			return;
		}
		if (!dtstart || !dtend || Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
			error = '请选择有效的开始和结束时间';
			return;
		}
		if (end <= start) {
			error = '结束时间需要晚于开始时间';
			return;
		}

		busy = true;
		error = '';
		try {
			await onupdate(index, {
				...routine,
				summary: text,
				dtstart,
				dtend,
				description: routine.description || text
			});
			editing = false;
		} catch (value) {
			error = value instanceof Error && value.message ? value.message : '日常任务保存失败，请重试';
		} finally {
			busy = false;
		}
	}

	async function removeEvent() {
		busy = true;
		error = '';
		try {
			await onremove(index);
		} catch (value) {
			error = value instanceof Error && value.message ? value.message : '删除失败，请重试';
			confirming = false;
			busy = false;
		}
	}
</script>

<li class="rounded-2xl border border-stone-200 bg-white p-4 transition hover:border-stone-300 sm:p-5">
	{#if editing}
		<form class="grid gap-3" onsubmit={saveEvent}>
			<label class="grid gap-1.5 text-sm font-600 text-stone-700">
				<span>日程内容</span>
				<input bind:value={summary} class="h-11 rounded-xl border border-stone-200 px-3.5 text-sm text-stone-900 outline-none focus:border-sky-500 focus:ring-3 focus:ring-sky-100" maxlength="120" disabled={busy} />
			</label>

			<div class="grid gap-3 sm:grid-cols-2">
				<label class="grid gap-1.5 text-sm font-600 text-stone-700">
					<span>开始时间</span>
					<input bind:value={dtstart} class="h-11 min-w-0 rounded-xl border border-stone-200 bg-white px-3 text-sm text-stone-900 outline-none focus:border-sky-500 focus:ring-3 focus:ring-sky-100" type="datetime-local" step="60" disabled={busy} />
				</label>
				<label class="grid gap-1.5 text-sm font-600 text-stone-700">
					<span>结束时间</span>
					<input bind:value={dtend} class="h-11 min-w-0 rounded-xl border border-stone-200 bg-white px-3 text-sm text-stone-900 outline-none focus:border-sky-500 focus:ring-3 focus:ring-sky-100" type="datetime-local" step="60" disabled={busy} />
				</label>
			</div>

			{#if error}<p class="m-0 text-sm text-red-600" role="alert">{error}</p>{/if}

			<div class="flex justify-end gap-2">
				<button type="button" class="h-10 rounded-xl px-4 text-sm font-600 text-stone-600 hover:bg-stone-100" disabled={busy} onclick={cancelEditing}>取消</button>
				<button type="submit" class="h-10 rounded-xl bg-stone-900 px-4 text-sm font-700 text-white hover:bg-sky-700 disabled:bg-stone-300" disabled={busy}>{busy ? '保存中…' : '保存修改'}</button>
			</div>
		</form>
	{:else}
		<div class="flex items-start gap-3">
			<div class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-sky-50 text-lg text-sky-700" aria-hidden="true">◷</div>
			<div class="min-w-0 flex-1">
				<p class="m-0 break-words text-[15px] font-650 leading-6 text-stone-900">{routine.summary}</p>
				<p class="m-0 mt-1.5 text-xs font-600 text-stone-500">{formatDateTime(routine.dtstart)} — {formatDateTime(routine.dtend)}</p>
				{#if error}<p class="m-0 mt-2 text-sm text-red-600" role="alert">{error}</p>{/if}
			</div>

			<div class="flex shrink-0 items-center gap-1">
				{#if confirming}
					<button type="button" class="h-9 rounded-lg px-2.5 text-xs font-700 text-stone-500 hover:bg-stone-100" disabled={busy} onclick={() => (confirming = false)}>取消</button>
					<button type="button" class="h-9 rounded-lg bg-red-50 px-2.5 text-xs font-700 text-red-600 hover:bg-red-100 disabled:opacity-50" disabled={busy} onclick={removeEvent}>{busy ? '删除中…' : '确认'}</button>
				{:else}
					<button type="button" class="h-9 rounded-lg px-2.5 text-xs font-700 text-stone-500 hover:bg-stone-100 hover:text-stone-900" onclick={startEditing}>编辑</button>
					<button type="button" class="h-9 rounded-lg px-2.5 text-xs font-700 text-stone-400 hover:bg-red-50 hover:text-red-600" onclick={() => (confirming = true)}>删除</button>
				{/if}
			</div>
		</div>
	{/if}
</li>
