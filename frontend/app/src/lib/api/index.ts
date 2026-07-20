import createClient from 'openapi-fetch';
import type { components, paths } from './schema.js';

export type Fetch = typeof globalThis.fetch;
export type Arrange = components['schemas']['Arrange'];
export type REvent = components['schemas']['REvent'];
export type Task = components['schemas']['Task'];
export type TaskList = components['schemas']['TaskList'];

export function createApi(fetch: Fetch) {
	const api = createClient<paths>({
		baseUrl: 'https://aws.naroah.top/degrading-anxiety/',
		fetch
	});

	return {
		async getToken(): Promise<string | undefined> {
			const { data, error } = await api.GET('/token', {});
			if (!error) return data;
		},

		async addEvent(token: string, event: REvent): Promise<string | undefined> {
			const { data, error } = await api.POST('/add', {
				params: { query: { token } },
				body: event
			});
			if (!error) return data;
		},

		async modSchedule(token: string, minute: number): Promise<string | undefined> {
			const { data, error } = await api.POST('/delay', {
				params: { query: { token, minute } }
			});
			if (!error) return data;
		},

		async addAlloc(token: string, tasks: TaskList): Promise<string | undefined> {
			const { data, error } = await api.POST('/alloc', {
				params: { query: { token } },
				body: tasks
			});
			if (!error) return data;
		},

		async getExport(token: string, date: string): Promise<Blob | undefined> {
			const { data, error } = await api.GET('/export', {
				params: { query: { token, date } },
				parseAs: 'blob'
			});
			if (!error) return data;
		}
	};
}

export type Api = ReturnType<typeof createApi>;
