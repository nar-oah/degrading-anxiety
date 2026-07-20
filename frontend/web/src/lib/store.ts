import type { Store } from '@degrading-anxiety/app';

export const store: Store = {
	async get<T>(key: string): Promise<T | undefined> {
		const value = globalThis.localStorage.getItem(key);
		return value === null ? undefined : (JSON.parse(value) as T);
	},

	async set(key: string, value: unknown): Promise<void> {
		globalThis.localStorage.setItem(key, JSON.stringify(value));
	}
};
