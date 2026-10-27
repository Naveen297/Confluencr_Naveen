export class ApiError extends Error {
  constructor(status, { code = 'UNKNOWN', message = 'Request failed', details } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request(path, { method = 'GET', body, query, signal } = {}) {
  let url = `/api${path}`;
  if (query) {
    const params = new URLSearchParams();
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') params.set(key, value);
    });
    const qs = params.toString();
    if (qs) url += `?${qs}`;
  }

  let res;
  try {
    res = await fetch(url, {
      method,
      signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    throw new ApiError(0, {
      code: 'NETWORK',
      message: 'Could not reach the server. Check that it is running.',
    });
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, data?.error);
  return data;
}

export const api = {
  listAccounts: (search, opts) => request('/accounts', { query: { search }, ...opts }),
  createAccount: (name) => request('/accounts', { method: 'POST', body: { name } }),
  getAccount: (id, opts) => request(`/accounts/${encodeURIComponent(id)}`, opts),
  getBalance: (id) => request(`/accounts/${encodeURIComponent(id)}/balance`),
  listTransactions: (id, { type, page, limit }, opts) =>
    request(`/accounts/${encodeURIComponent(id)}/transactions`, {
      query: { type, page, limit },
      ...opts,
    }),
  createTransaction: (id, payload) =>
    request(`/accounts/${encodeURIComponent(id)}/transactions`, {
      method: 'POST',
      body: payload,
    }),
};
