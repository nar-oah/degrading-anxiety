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
		if (!value) throw new Error('Token cannot be empty');
		await this.store.set(TOKEN, value);
		this.token = value;
	}

	async setTasks(tasks: TaskList): Promise<void> {
		await this.store.set(TASKS, tasks);
		this.tasks = tasks;
	}

	async addTask(task: Task): Promise<void> {
		await this.setTasks([...this.tasks, task]);
	}

	async updateTask(index: number, task: Task): Promise<void> {
		if (index < 0 || index >= this.tasks.length) throw new Error('Task not found');
		await this.setTasks(this.tasks.map((current, position) => (position === index ? task : current)));
	}

	async removeTask(index: number): Promise<void> {
		if (index < 0 || index >= this.tasks.length) throw new Error('Task not found');
		await this.setTasks(this.tasks.filter((_, position) => position !== index));
	}

	async arrangeToday(): Promise<string> {
		const token = this.#getToken();
		const requestId = await this.api.addAlloc(token, this.tasks);
		if (!requestId) throw new Error('Failed to arrange tasks');
		return requestId;
	}

	async exportCalendar(date: string): Promise<Blob> {
		const token = this.#getToken();
		const calendar = await this.api.getExport(token, date);
		if (!calendar) throw new Error('Failed to export calendar');
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
			const storedToken = savedToken?.trim();
			const token = storedToken || (await this.api.getToken());

			if (token === undefined) throw new Error('Failed to get token');

			const tasks = savedTasks ?? [];
			await Promise.all([
				storedToken !== token ? this.store.set(TOKEN, token) : Promise.resolve(),
				savedTasks === undefined ? this.store.set(TASKS, tasks) : Promise.resolve()
			]);

			this.token = token;
			this.tasks = tasks;
			this.initialized = true;
		} catch (error) {
			this.error = error;
		} finally {
			this.loading = false;
		}
	}

	#getToken(): string {
		const token = this.token?.trim();
		if (!token) throw new Error('Token is not ready');
		return token;
	}
}

export const createAppStore = (store: Store, api: Api) => new AppStore(store, api);
