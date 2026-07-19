import type { components, operations } from './schema.js';

export const API_BASE_URL = 'https://aws.naroah.top/degrading-anxiety';

export type Arrange = components['schemas']['Arrange'];
export type REvent = components['schemas']['REvent'];
export type Task = components['schemas']['Task'];
export type TaskList = components['schemas']['TaskList'];

type GetTokenResponse = operations['get_token_token_get']['responses'][200]['content']['application/json'];
type AddEventResponse = operations['add_event_add_post']['responses'][202]['content']['application/json'];
type AddEventQuery = operations['add_event_add_post']['parameters']['query'];
type ModScheduleResponse = operations['mod_schedule_delay_post']['responses'][202]['content']['application/json'];
type ModScheduleQuery = operations['mod_schedule_delay_post']['parameters']['query'];
type AddAllocResponse = operations['add_alloc_alloc_post']['responses'][202]['content']['application/json'];
type AddAllocQuery = operations['add_alloc_alloc_post']['parameters']['query'];
type GetExportQuery = operations['get_export_export_get']['parameters']['query'];

export interface ApiOptions {
	baseUrl?: string;
	fetch?: typeof globalThis.fetch;
}

export class ApiError extends Error {
	readonly status: number;
	readonly body: unknown;

	constructor(status: number, body: unknown, message: string) {
		super(message);
		this.name = 'ApiError';
		this.status = status;
		this.body = body;
	}
}

const makeUrl = (baseUrl: string, path: string, query?: Record<string, string | number>) => {
	const search = query ? `?${new URLSearchParams(Object.entries(query).map(([key, value]) => [key, String(value)]))}` : '';
	return `${baseUrl.replace(/\/+$/, '')}${path}${search}`;
};

const getMessage = (body: unknown, fallback: string) => {
	if (typeof body === 'string' && body) return body;
	if (!body || typeof body !== 'object') return fallback;

	const detail = 'detail' in body ? body.detail : body;
	if (typeof detail === 'string') return detail;
	if (Array.isArray(detail)) {
		const messages = detail
			.map((item) => item && typeof item === 'object' && 'msg' in item ? item.msg : undefined)
			.filter((message): message is string => typeof message === 'string');
		if (messages.length) return messages.join('; ');
	}

	return fallback;
};

const getResponse = async (fetcher: typeof globalThis.fetch, url: string, init?: RequestInit) => {
	const response = await fetcher(url, init);
	if (response.ok) return response;

	const contentType = response.headers.get('content-type') ?? '';
	const body: unknown = contentType.includes('application/json')
		? await response.json()
		: await response.text();
	throw new ApiError(
		response.status,
		body,
		getMessage(body, `${response.status} ${response.statusText}`.trim())
	);
};

const getJson = async <T>(fetcher: typeof globalThis.fetch, url: string, init?: RequestInit) =>
	(await getResponse(fetcher, url, init)).json() as Promise<T>;

const postJson = <T>(fetcher: typeof globalThis.fetch, url: string, body: unknown) =>
	getJson<T>(fetcher, url, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(body)
	});

export const createApi = ({ baseUrl = API_BASE_URL, fetch: fetcher = globalThis.fetch }: ApiOptions = {}) => ({
	getToken: () => getJson<GetTokenResponse>(fetcher, makeUrl(baseUrl, '/token')),

	addEvent: (token: AddEventQuery['token'], event: REvent) =>
		postJson<AddEventResponse>(fetcher, makeUrl(baseUrl, '/add', { token }), event),

	modSchedule: (token: ModScheduleQuery['token'], minute: ModScheduleQuery['minute']) =>
		getJson<ModScheduleResponse>(fetcher, makeUrl(baseUrl, '/delay', { token, minute }), {
			method: 'POST',
			headers: { Accept: 'application/json' }
		}),

	addAlloc: (token: AddAllocQuery['token'], tasks: TaskList) =>
		postJson<AddAllocResponse>(fetcher, makeUrl(baseUrl, '/alloc', { token }), tasks),

	getExport: async (token: GetExportQuery['token'], date: GetExportQuery['date']) =>
		(await getResponse(fetcher, makeUrl(baseUrl, '/export', { token, date }), {
			headers: { Accept: 'text/calendar' }
		})).blob()
});

export type Api = ReturnType<typeof createApi>;

export const api = createApi();
export const { getToken, addEvent, modSchedule, addAlloc, getExport } = api;
