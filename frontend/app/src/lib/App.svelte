<script lang="ts">
	import { onMount } from 'svelte';
	import { createApi, type Fetch, type Task } from './api/index.js';
	import CredentialRow from './components/CredentialRow.svelte';
	import TaskForm from './components/TaskForm.svelte';
	import TaskItem from './components/TaskItem.svelte';
	import { createAppStore } from './store/app.svelte.js';
	import type { Store } from './store/storage.js';

	let { fetch, store }: { fetch: Fetch; store: Store } = $props();
	const appStore = $derived(createAppStore(store, createApi(fetch)));

	type Notice = { tone: 'success' | 'error'; text: string };

	let dateLabel = $state('今天');
	let arranging = $state(false);
	let exporting = $state(false);
	let notice = $state<Notice>();
	let draggedTask = $state<Task>();
	let dragTarget = $state<Task>();

	const totalMinutes = $derived(appStore.tasks.reduce((total, task) => total + task.duration, 0));
	const caldavUrl = $derived(
		appStore.token
			? `aws.naroah.top/degrading-anxiety/radicale/${encodeURIComponent(appStore.token)}`
			: undefined
	);

	const getMessage = (value: unknown, fallback: string) => {
		const message = value instanceof Error ? value.message : '';
		return /[\u3400-\u9fff]/.test(message) ? message : fallback;
	};

	const pad = (value: number) => String(value).padStart(2, '0');
	const getLocalDate = () => {
		const today = new Date();
		return `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
	};

	onMount(() => {
		dateLabel = new Intl.DateTimeFormat('zh-CN', {
			month: 'long',
			day: 'numeric',
			weekday: 'long'
		}).format(new Date());
		void appStore.init();
	});

	const addTask = (task: Task) => appStore.addTask(task);
	const updateTask = (index: number, task: Task) => appStore.updateTask(index, task);
	const removeTask = (index: number) => appStore.removeTask(index);
	const moveTask = async (fromIndex: number, toIndex: number) => {
		if (fromIndex === toIndex || toIndex < 0 || toIndex >= appStore.tasks.length) return;
		try {
			await appStore.moveTask(fromIndex, toIndex);
		} catch (value) {
			notice = { tone: 'error', text: getMessage(value, '任务顺序保存失败，请重试') };
		}
	};

	function startTaskDrag(index: number, event: DragEvent) {
		const task = appStore.tasks[index];
		if (!task) return;
		draggedTask = task;
		dragTarget = task;
		if (!event.dataTransfer) return;
		event.dataTransfer.effectAllowed = 'move';
		event.dataTransfer.setData('text/plain', String(index));
	}

	function overTaskDrag(index: number, event: DragEvent) {
		if (!draggedTask) return;
		event.preventDefault();
		dragTarget = appStore.tasks[index];
		if (event.dataTransfer) event.dataTransfer.dropEffect = 'move';
	}

	function dropTask(index: number, event: DragEvent) {
		event.preventDefault();
		const fromIndex = draggedTask ? appStore.tasks.indexOf(draggedTask) : -1;
		draggedTask = undefined;
		dragTarget = undefined;
		if (fromIndex >= 0) void moveTask(fromIndex, index);
	}

	function endTaskDrag() {
		draggedTask = undefined;
		dragTarget = undefined;
	}

	async function arrangeToday() {
		if (!appStore.token || appStore.tasks.length === 0) return;
		arranging = true;
		notice = undefined;
		try {
			await appStore.arrangeToday();
			notice = {
				tone: 'success',
				text: '今日任务的安排请求已提交，可稍后在 CalDAV 日历中查看。'
			};
		} catch (value) {
			notice = { tone: 'error', text: getMessage(value, '安排请求提交失败，请稍后重试') };
		} finally {
			arranging = false;
		}
	}

	async function exportToday() {
		if (!appStore.token) return;
		exporting = true;
		notice = undefined;
		const date = getLocalDate();
		try {
			const calendar = await appStore.exportCalendar(date);
			const url = URL.createObjectURL(calendar);
			const anchor = document.createElement('a');
			anchor.href = url;
			anchor.download = `schedule-${date}.ics`;
			document.body.append(anchor);
			anchor.click();
			anchor.remove();
			setTimeout(() => URL.revokeObjectURL(url), 0);
			notice = { tone: 'success', text: '今天的 ICS 日历文件已开始下载。' };
		} catch (value) {
			notice = {
				tone: 'error',
				text: getMessage(value, '日历导出失败；如果等待时间较长，请稍后重试')
			};
		} finally {
			exporting = false;
		}
	}
</script>

<svelte:head>
	<title>今日任务 · Degrading Anxiety</title>
	<meta
		name="description"
		content="记录、安排并导出今天的任务，让日程更清晰。"
	/>
</svelte:head>

<div class="min-h-screen bg-[#f5f4ef] text-stone-900">
	<div class="mx-auto max-w-6xl px-4 py-5 sm:px-6 sm:py-8 lg:px-8">
		<header class="mb-7 flex items-center justify-between gap-4">
			<div class="flex items-center gap-3">
				<div class="grid h-10 w-10 place-items-center rounded-2xl bg-emerald-700 text-lg font-800 text-white shadow-sm">
					安
				</div>
				<div>
					<p class="m-0 text-sm font-800 tracking-tight text-stone-900">Degrading Anxiety</p>
					<p class="m-0 mt-0.5 text-xs text-stone-500">把今天，安排得刚刚好</p>
				</div>
			</div>
			<div class="flex items-center gap-2 rounded-full border border-stone-200 bg-white px-3 py-1.5 text-xs font-600 text-stone-600 shadow-sm">
				<span
					class={`h-2 w-2 rounded-full ${appStore.token ? 'bg-emerald-500' : appStore.loading ? 'animate-pulse bg-amber-400' : 'bg-stone-300'}`}
				></span>
				{appStore.token ? '账户已就绪' : appStore.loading ? '正在初始化' : '账户未就绪'}
			</div>
		</header>

		<main>
			<section class="mb-5 overflow-hidden rounded-3xl bg-stone-900 px-5 py-6 text-white shadow-lg shadow-stone-900/8 sm:px-7 sm:py-8">
				<div class="flex flex-col justify-between gap-6 sm:flex-row sm:items-end">
					<div>
						<p class="m-0 mb-3 text-xs font-700 uppercase tracking-[0.18em] text-emerald-300">{dateLabel}</p>
						<h1 class="m-0 max-w-xl text-3xl font-800 tracking-tight sm:text-4xl">今天想完成什么？</h1>
						<p class="m-0 mt-3 max-w-xl text-sm leading-6 text-stone-300">
							写下任务和所需时间，系统会结合日历空档帮你安排今天。
						</p>
					</div>
					<div class="flex shrink-0 gap-2">
						<div class="min-w-24 rounded-2xl bg-white/8 px-4 py-3 backdrop-blur-sm">
							<p class="m-0 text-2xl font-800">{appStore.tasks.length}</p>
							<p class="m-0 mt-0.5 text-xs text-stone-400">项任务</p>
						</div>
						<div class="min-w-24 rounded-2xl bg-white/8 px-4 py-3 backdrop-blur-sm">
							<p class="m-0 text-2xl font-800">{totalMinutes}</p>
							<p class="m-0 mt-0.5 text-xs text-stone-400">分钟</p>
						</div>
					</div>
				</div>
			</section>

			{#if appStore.loading && !appStore.initialized}
				<div class="mb-5 flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3.5 text-sm text-amber-900" role="status">
					<span class="h-4 w-4 animate-spin rounded-full border-2 border-amber-600 border-r-transparent"></span>
					正在读取本地任务并准备你的账户…
				</div>
			{:else if appStore.error && !appStore.token}
				<div class="mb-5 flex flex-col justify-between gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3.5 text-sm text-red-800 sm:flex-row sm:items-center" role="alert">
					<div>
						<p class="m-0 font-700">账户初始化失败</p>
						<p class="m-0 mt-1 text-xs text-red-700">请检查网络后重试；已有任务仍可继续编辑。</p>
					</div>
					<button
						type="button"
						class="h-10 rounded-xl bg-white px-4 text-sm font-700 text-red-700 shadow-sm transition hover:bg-red-100"
						onclick={() => void appStore.init()}
					>重新获取 Token</button
					>
				</div>
			{/if}

			{#if notice}
				<div
					class={`mb-5 flex items-start justify-between gap-3 rounded-2xl border px-4 py-3.5 text-sm ${
						notice.tone === 'success'
							? 'border-emerald-200 bg-emerald-50 text-emerald-800'
							: 'border-red-200 bg-red-50 text-red-800'
					}`}
					role={notice.tone === 'error' ? 'alert' : 'status'}
					aria-live="polite"
				>
					<span>{notice.text}</span>
					<button
						type="button"
						class="shrink-0 rounded-lg px-2 text-lg leading-6 opacity-60 transition hover:bg-black/5 hover:opacity-100"
						aria-label="关闭提示"
						onclick={() => (notice = undefined)}
					>×</button
					>
				</div>
			{/if}

			<div class="grid items-start gap-5 lg:grid-cols-[minmax(0,1.75fr)_minmax(18rem,1fr)]">
				<section class="rounded-3xl border border-stone-200 bg-white p-4 shadow-sm sm:p-6" aria-labelledby="tasks-title">
					<div class="mb-5 flex items-end justify-between gap-4">
						<div>
							<p class="m-0 mb-1 text-xs font-700 uppercase tracking-wider text-emerald-700">Task list</p>
							<h2 id="tasks-title" class="m-0 text-xl font-800 tracking-tight text-stone-900">今日任务</h2>
						</div>
						<p class="m-0 text-right text-xs text-stone-500">{appStore.tasks.length} 项 · {totalMinutes} 分钟</p>
					</div>

					<TaskForm onadd={addTask} disabled={appStore.loading} />

					{#if appStore.tasks.length === 0}
						<div class="mt-5 rounded-2xl border border-dashed border-stone-300 px-5 py-12 text-center">
							<div class="mx-auto mb-3 grid h-11 w-11 place-items-center rounded-2xl bg-stone-100 text-xl text-stone-400">✓</div>
							<p class="m-0 text-sm font-700 text-stone-700">还没有今日任务</p>
							<p class="m-0 mt-1.5 text-xs text-stone-500">从上方添加一项，给今天一个轻松的开始。</p>
						</div>
					{:else}
						<ul class="m-0 mt-5 grid list-none gap-3 p-0">
							{#each appStore.tasks as task, index (task)}
								<TaskItem
									{task}
									{index}
									onupdate={updateTask}
									onremove={removeTask}
									onmove={moveTask}
									ondragstart={startTaskDrag}
									ondragover={overTaskDrag}
									ondrop={dropTask}
									ondragend={endTaskDrag}
									dragging={draggedTask === task}
									dropTarget={dragTarget === task && draggedTask !== task}
								/>
							{/each}
						</ul>
					{/if}
				</section>

				<aside class="grid gap-5 lg:sticky lg:top-5">
					<section class="rounded-3xl border border-stone-200 bg-white p-5 shadow-sm" aria-labelledby="caldav-title">
						<div class="mb-4 flex items-start justify-between gap-3">
							<div>
								<p class="m-0 mb-1 text-xs font-700 uppercase tracking-wider text-emerald-700">Calendar</p>
								<h2 id="caldav-title" class="m-0 text-lg font-800 text-stone-900">CalDAV 账户</h2>
							</div>
							<span class="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-700 text-emerald-700">可同步</span>
						</div>

						<CredentialRow label="服务器地址" value={caldavUrl} />
						<CredentialRow label="用户名 & 密码" value={appStore.token} />

						<p class="m-0 mt-4 rounded-xl bg-stone-50 px-3 py-2.5 text-xs leading-5 text-stone-500">
							首次提交安排后会自动创建日历，此后即可在系统日历中添加该账户。
						</p>
					</section>

					<section class="rounded-3xl bg-emerald-700 p-5 text-white shadow-lg shadow-emerald-900/10" aria-labelledby="actions-title">
						<h2 id="actions-title" class="m-0 text-lg font-800">准备好了？</h2>
						<p class="m-0 mt-1.5 text-xs leading-5 text-emerald-100">提交后，任务会被安排到今天的日历空档中。</p>

						<button
							type="button"
							class="mt-4 h-12 w-full rounded-xl bg-white px-4 text-sm font-800 text-emerald-800 shadow-sm transition hover:bg-emerald-50 disabled:cursor-not-allowed disabled:bg-white/35 disabled:text-white/70"
							disabled={!appStore.token || appStore.tasks.length === 0 || arranging}
							onclick={arrangeToday}
						>{arranging ? '正在提交…' : '安排今日任务'}</button
						>

						<button
							type="button"
							class="mt-2.5 h-11 w-full rounded-xl border border-white/25 bg-transparent px-4 text-sm font-700 text-white transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-45"
							disabled={!appStore.token || exporting}
							onclick={exportToday}
						>{exporting ? '正在导出…' : '导出今天的 ICS'}</button
						>

						{#if !appStore.token}
							<p class="m-0 mt-3 text-center text-xs text-emerald-100">获取或填写 Token 后即可操作</p>
						{:else if appStore.tasks.length === 0}
							<p class="m-0 mt-3 text-center text-xs text-emerald-100">至少添加一项任务后即可安排</p>
						{/if}
					</section>
				</aside>
			</div>
		</main>

		<footer class="py-7 text-center text-xs text-stone-400">任务草稿保存在当前设备，账户凭据由系统自动生成。</footer>
	</div>
</div>
