import type { Api, REvent, TaskList } from '../api/index.js';
import type { Store } from './storage.js';

const TOKEN = 'token';
const TASKS = 'tasks';
const EVENTS = 'events';

export class AppStore {
	token = $state<string>();
	tasks = $state<TaskList>([]);
	events = $state<REvent[]>([]);
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

	async setTasks(tasks: TaskList): Promise<void> {
		await this.store.set(TASKS, tasks);
		this.tasks = tasks;
	}

	async setEvents(events: REvent[]): Promise<void> {
		await this.store.set(EVENTS, events);
		this.events = events;
	}

	async #load(): Promise<void> {
		this.loading = true;
		this.error = undefined;

		try {
			const [savedToken, savedTasks, savedEvents] = await Promise.all([
				this.store.get<string>(TOKEN),
				this.store.get<TaskList>(TASKS),
				this.store.get<REvent[]>(EVENTS)
			]);
			const token = savedToken ?? (await this.api.getToken());

			if (token === undefined) throw new Error('Failed to get token');

			const tasks = savedTasks ?? [];
			const events = savedEvents ?? [];
			await Promise.all([
				savedToken === undefined ? this.store.set(TOKEN, token) : Promise.resolve(),
				savedTasks === undefined ? this.store.set(TASKS, tasks) : Promise.resolve(),
				savedEvents === undefined ? this.store.set(EVENTS, events) : Promise.resolve()
			]);

			this.token = token;
			this.tasks = tasks;
			this.events = events;
			this.initialized = true;
		} catch (error) {
			this.error = error;
		} finally {
			this.loading = false;
		}
	}
}

export const createAppStore = (store: Store, api: Api) => new AppStore(store, api);
