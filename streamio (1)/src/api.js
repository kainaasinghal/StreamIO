const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error(`Cannot reach the API at ${API_BASE}. Start the FastAPI server and check the API URL.`);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const fieldErrors = Array.isArray(detail)
      ? Object.fromEntries(detail.map(item => [item.loc?.at(-1), item.msg]).filter(([field]) => field && field !== 'body'))
      : {};
    const message = Array.isArray(detail)
      ? detail.map(item => item.msg).join(' ')
      : detail || `Request failed (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    error.fieldErrors = fieldErrors;
    throw error;
  }
  if (response.status === 204) return null;
  return response.json();
}

export function getApiBase() {
  return API_BASE;
}

export function getCollection(resource, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) query.set(key, value);
  });
  return request(`/${resource}${query.size ? `?${query}` : ''}`);
}

export function getDashboard() {
  return request('/dashboard');
}

export function getApiHealth() {
  return request('/health');
}

export function getOptions() {
  return request('/meta/options');
}

export function createRecord(resource, payload) {
  return request(`/${resource}`, { method: 'POST', body: JSON.stringify(payload) });
}

export function updateRecord(resource, id, payload) {
  return request(`/${resource}/${id}`, { method: 'PUT', body: JSON.stringify(payload) });
}

export function deleteRecord(resource, id) {
  return request(`/${resource}/${id}`, { method: 'DELETE' });
}