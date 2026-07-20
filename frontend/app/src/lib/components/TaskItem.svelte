<script lang="ts">
	import type { Arrange, Task } from '../api/index.js';

	let {
		task,
		index,
		onupdate,
		onremove
	}: {
		task: Task;
		index: number;
		onupdate: (index: number, task: Task) => Promise<void>;
		onremove: (index: number) => Promise<void>;
	} = $props();

	const arrangeLabels: Record<Arrange, string> = {
		early: '尽早',
		normal: '灵活',
		late: '尽晚'
	};

	let editing = $state(false);
	let confirming = $state(false);
	let busy = $state(false);
	let description = $state('');
	let duration = $state<number | undefined>(30);
	let arrange = $state<Arrange>('normal');
	let error = $state('');

	const getMessage = (value: unknown) =>
		value instanceof Error && value.message ? value.message : '操作失败，请重试';

	function startEditing() {
		description = task.description;
		duration = task.duration;
		arrange = task.arrange;
		confirming = false;
		error = '';
		editing = true;
	}

	function cancelEditing() {
		editing = false;
		error = '';
	}

	async function saveTask(event: SubmitEvent) {
		event.preventDefault();
		const text = description.trim();
		const minutes = Number(duration);
		if (!text) {
			error = '任务内容不能为空';
			return;
		}
		if (!Number.isInteger(minutes) || minutes < 1) {
			error = '时长需要是大于 0 的整数';
			return;
		}

		busy = true;
		error = '';
		try {
			await onupdate(index, { description: text, duration: minutes, arrange });
			editing = false;
		} catch (value) {
			error = getMessage(value);
		} finally {
			busy = false;
		}
	}

	async function removeTask() {
		busy = true;
		error = '';
		try {
			await onremove(index);
		} catch (value) {
			error = getMessage(value);
			confirming = false;
			busy = false;
		}
	}
</script>

<li class="rounded-2xl border border-stone-200 bg-white p-4 transition hover:border-stone-300 sm:p-5">
	{#if editing}
		<form class="grid gap-3" onsubmit={saveTask}>
			<label class="grid gap-1.5 text-sm font-600 text-stone-700">
				<span>任务内容</span>
				<input
					bind:value={description}
					class="h-11 rounded-xl border border-stone-200 px-3.5 text-sm text-stone-900 outline-none focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
					maxlength="120"
					disabled={busy}
				/>
			</label>

			<div class="grid gap-3 sm:grid-cols-2">
				<label class="grid gap-1.5 text-sm font-600 text-stone-700">
					<span>时长（分钟）</span>
					<input
						bind:value={duration}
						class="h-11 rounded-xl border border-stone-200 px-3.5 text-sm text-stone-900 outline-none focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
						type="number"
						min="1"
						step="5"
						disabled={busy}
					/>
				</label>

				<label class="grid gap-1.5 text-sm font-600 text-stone-700">
					<span>安排偏好</span>
					<select
						bind:value={arrange}
						class="h-11 rounded-xl border border-stone-200 bg-white px-3.5 text-sm text-stone-900 outline-none focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
						disabled={busy}
					>
						<option value="normal">灵活安排</option>
						<option value="early">尽早安排</option>
						<option value="late">尽晚安排</option>
					</select>
				</label>
			</div>

			{#if error}
				<p class="m-0 text-sm text-red-600" role="alert">{error}</p>
			{/if}

			<div class="flex flex-wrap justify-end gap-2">
				<button
					type="button"
					class="h-10 rounded-xl px-4 text-sm font-600 text-stone-600 transition hover:bg-stone-100 disabled:opacity-50"
					disabled={busy}
					onclick={cancelEditing}
				>取消</button
				>
				<button
					type="submit"
					class="h-10 rounded-xl bg-stone-900 px-4 text-sm font-700 text-white transition hover:bg-emerald-700 disabled:bg-stone-300"
					disabled={busy}
				>{busy ? '保存中…' : '保存修改'}</button
				>
			</div>
		</form>
	{:else}
		<div class="flex items-start gap-3 sm:gap-4">
			<div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-sm font-800 text-emerald-700">
				{index + 1}
			</div>
			<div class="min-w-0 flex-1">
				<p class="m-0 break-words text-[15px] font-650 leading-6 text-stone-900">{task.description}</p>
				<div class="mt-2 flex flex-wrap items-center gap-2 text-xs font-600">
					<span class="rounded-full bg-stone-100 px-2.5 py-1 text-stone-600">{task.duration} 分钟</span>
					<span class="rounded-full bg-emerald-50 px-2.5 py-1 text-emerald-700"
						>{arrangeLabels[task.arrange]}</span
					>
				</div>
				{#if error}
					<p class="m-0 mt-2 text-sm text-red-600" role="alert">{error}</p>
				{/if}
			</div>

			<div class="flex shrink-0 items-center gap-1">
				{#if confirming}
					<span class="mr-1 hidden text-xs text-stone-500 sm:inline">确认删除？</span>
					<button
						type="button"
						class="h-9 rounded-lg px-2.5 text-xs font-700 text-stone-500 hover:bg-stone-100"
						disabled={busy}
						onclick={() => (confirming = false)}
					>取消</button
					>
					<button
						type="button"
						class="h-9 rounded-lg bg-red-50 px-2.5 text-xs font-700 text-red-600 hover:bg-red-100 disabled:opacity-50"
						disabled={busy}
						onclick={removeTask}
					>{busy ? '删除中…' : '确认'}</button
					>
				{:else}
					<button
						type="button"
						class="h-9 rounded-lg px-2.5 text-xs font-700 text-stone-500 transition hover:bg-stone-100 hover:text-stone-900"
						onclick={startEditing}
					>编辑</button
					>
					<button
						type="button"
						class="h-9 rounded-lg px-2.5 text-xs font-700 text-stone-400 transition hover:bg-red-50 hover:text-red-600"
						onclick={() => (confirming = true)}
					>删除</button
					>
				{/if}
			</div>
		</div>
	{/if}
</li>
