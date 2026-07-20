import type { Api, Task, TaskList } from '../api/index.js';
import type { Store } from './storage.js';

const TOKEN = 'token';
const TASKS = 'tasks';

export class AppStore {
	token = $state<string>();
	tasks = $state<TaskList>([]);
	loading = $state(false);
	initialized = $state(false);
	error = $state<unknown>();

	#initializing?: Promise<void>;
	#taskWriting = Promise.resolve();

	constructor(
		private readonly store: Store,
		private readonly api: Api
	) {}

	async init(): Promise<void> {
		if (this.initialized) return;
		this.#initializing ??= this.#load();
		await this.#initializing;
		this.#initializing = undefined;
	}

	async setToken(token: string): Promise<void> {
		const value = token.trim();
		if (!value) throw new Error('Token 不能为空');
		await this.store.set(TOKEN, value);
		this.token = value;
	}

	async setTasks(tasks: TaskList): Promise<void> {
		await this.#writeTasks(() => tasks);
	}

	async addTask(task: Task): Promise<void> {
		await this.#writeTasks((tasks) => [...tasks, task]);
	}

	async updateTask(index: number, task: Task): Promise<void> {
		const target = this.tasks[index];
		if (!target) throw new Error('未找到要修改的任务');
		await this.#writeTasks((tasks) => {
			const position = tasks.indexOf(target);
			if (position < 0) throw new Error('未找到要修改的任务');
			return tasks.map((current, index) => (index === position ? task : current));
		});
	}

	async removeTask(index: number): Promise<void> {
		const target = this.tasks[index];
		if (!target) throw new Error('未找到要删除的任务');
		await this.#writeTasks((tasks) => {
			const position = tasks.indexOf(target);
			if (position < 0) throw new Error('未找到要删除的任务');
			return tasks.filter((_, index) => index !== position);
		});
	}

	async moveTask(fromIndex: number, toIndex: number): Promise<void> {
		const source = this.tasks[fromIndex];
		const target = this.tasks[toIndex];
		if (!source || !target) throw new Error('未找到要移动的任务');
		if (source === target) return;
		await this.#writeTasks((tasks) => {
			const from = tasks.indexOf(source);
			const to = tasks.indexOf(target);
			if (from < 0 || to < 0) throw new Error('未找到要移动的任务');
			const reordered = [...tasks];
			reordered.splice(from, 1);
			reordered.splice(to, 0, source);
			return reordered;
		});
	}

	async arrangeToday(): Promise<string> {
		const token = this.#getToken();
		const requestId = await this.api.addAlloc(token, this.tasks);
		if (!requestId) throw new Error('安排请求提交失败，请稍后重试');
		return requestId;
	}

	async exportCalendar(date: string): Promise<Blob> {
		const token = this.#getToken();
		const calendar = await this.api.getExport(token, date);
		if (!calendar) throw new Error('日历导出失败，请稍后重试');
		return calendar;
	}

	async #load(): Promise<void> {
		this.loading = true;
		this.error = undefined;

		try {
			const [savedToken, savedTasks] = await Promise.all([
				this.store.get<string>(TOKEN),
				this.store.get<TaskList>(TASKS)
			]);
			const tasks = savedTasks ?? [];
			this.tasks = tasks;
			if (savedTasks === undefined) await this.store.set(TASKS, tasks);

			const storedToken = savedToken?.trim();
			const token = (storedToken || (await this.api.getToken()))?.trim();

			if (!token) throw new Error('Token 获取失败');

			if (storedToken !== token) await this.store.set(TOKEN, token);

			this.token = token;
			this.initialized = true;
		} catch (error) {
			this.error = error;
		} finally {
			this.loading = false;
		}
	}

	#getToken(): string {
		const token = this.token?.trim();
		if (!token) throw new Error('Token 尚未就绪');
		return token;
	}

	#writeTasks(update: (tasks: TaskList) => TaskList): Promise<void> {
		const writing = this.#taskWriting.then(async () => {
			const tasks = update(this.tasks);
			await this.store.set(TASKS, tasks);
			this.tasks = tasks;
		});
		this.#taskWriting = writing.catch(() => undefined);
		return writing;
	}
}

export const createAppStore = (store: Store, api: Api) => new AppStore(store, api);
