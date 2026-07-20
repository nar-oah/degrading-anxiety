import type { Store } from '@degrading-anxiety/app';
import { LazyStore } from '@tauri-apps/plugin-store';

export const store: Store = new LazyStore('store.json');
