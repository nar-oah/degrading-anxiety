<script lang="ts">
	import type { Arrange, Task } from '../api/index.js';

	let {
		onadd,
		disabled = false
	}: {
		onadd: (task: Task) => Promise<void>;
		disabled?: boolean;
	} = $props();

	let description = $state('');
	let duration = $state<number | undefined>(30);
	let arrange = $state<Arrange>('normal');
	let error = $state('');
	let saving = $state(false);
	let descriptionInput: HTMLInputElement;

	const getMessage = (value: unknown) =>
		value instanceof Error && value.message ? value.message : '任务保存失败，请重试';

	async function addTask(event: SubmitEvent) {
		event.preventDefault();
		const text = description.trim();
		const minutes = Number(duration);

		if (!text) {
			error = '请填写任务内容';
			descriptionInput?.focus();
			return;
		}
		if (!Number.isInteger(minutes) || minutes < 1) {
			error = '时长需要是大于 0 的整数';
			return;
		}

		saving = true;
		error = '';
		try {
			await onadd({ description: text, duration: minutes, arrange });
			description = '';
			duration = 30;
			arrange = 'normal';
			descriptionInput?.focus();
		} catch (value) {
			error = getMessage(value);
		} finally {
			saving = false;
		}
	}
</script>

<form class="rounded-2xl bg-stone-50 p-4 sm:p-5" onsubmit={addTask}>
	<div class="mb-4 flex items-center justify-between gap-3">
		<div>
			<h3 class="m-0 text-base font-700 text-stone-900">添加一项任务</h3>
			<p class="m-0 mt-1 text-xs text-stone-500">先记录要做什么，稍后交给系统安排时间</p>
		</div>
		<span class="h-2.5 w-2.5 shrink-0 rounded-full bg-emerald-400"></span>
	</div>

	<div class="grid gap-3 sm:grid-cols-2">
		<label class="grid min-w-0 gap-1.5 text-sm font-600 text-stone-700 sm:col-span-2">
			<span>任务内容</span>
			<input
				bind:this={descriptionInput}
				bind:value={description}
				class="h-11 w-full min-w-0 rounded-xl border border-stone-200 bg-white px-3.5 text-sm text-stone-900 outline-none transition focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
				placeholder="例如：完成项目周报"
				maxlength="120"
				disabled={disabled || saving}
				aria-invalid={Boolean(error && !description.trim())}
			/>
		</label>

		<label class="grid min-w-0 gap-1.5 text-sm font-600 text-stone-700">
			<span>时长（分钟）</span>
			<input
				bind:value={duration}
				class="h-11 w-full min-w-0 rounded-xl border border-stone-200 bg-white px-3.5 text-sm text-stone-900 outline-none transition focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
				type="number"
				min="1"
				step="1"
				inputmode="numeric"
				disabled={disabled || saving}
			/>
		</label>

		<label class="grid min-w-0 gap-1.5 text-sm font-600 text-stone-700">
			<span>安排偏好</span>
			<select
				bind:value={arrange}
				class="h-11 w-full min-w-0 rounded-xl border border-stone-200 bg-white px-3.5 text-sm text-stone-900 outline-none transition focus:border-emerald-500 focus:ring-3 focus:ring-emerald-100"
				disabled={disabled || saving}
			>
				<option value="normal">灵活安排</option>
				<option value="early">尽早安排</option>
				<option value="late">尽晚安排</option>
			</select>
		</label>

		<button
			type="submit"
			class="h-11 w-full rounded-xl bg-stone-900 px-5 text-sm font-700 text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-stone-300 sm:col-span-2"
			disabled={disabled || saving}
		>
			{saving ? '保存中…' : '添加任务'}
		</button>
	</div>

	{#if error}
		<p class="m-0 mt-3 text-sm text-red-600" role="alert">{error}</p>
	{/if}
</form>
