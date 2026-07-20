import type { RequestHandler } from './$types';

const API_URL = 'https://aws.naroah.top/degrading-anxiety/';
const methods: Record<string, string> = {
	token: 'GET',
	alloc: 'POST',
	export: 'GET'
};

const proxy: RequestHandler = async ({ fetch, params, request, url }) => {
	const method = methods[params.endpoint];
	if (!method) return new Response('Not found', { status: 404 });
	if (request.method !== method) {
		return new Response('Method not allowed', {
			status: 405,
			headers: { Allow: method }
		});
	}

	const target = new URL(params.endpoint, API_URL);
	target.search = url.search;
	const headers = new Headers();
	for (const name of ['accept', 'content-type']) {
		const value = request.headers.get(name);
		if (value) headers.set(name, value);
	}

	return fetch(target, {
		method,
		headers,
		body: method === 'GET' ? undefined : await request.arrayBuffer()
	});
};

export const GET = proxy;
export const POST = proxy;
