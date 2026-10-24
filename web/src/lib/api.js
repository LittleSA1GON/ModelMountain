// Thin client for the Model Mountain control API (/api/v1). Never invents data:
// every call resolves to { ok, data } or { ok:false, error:{code,message}, status }.
const BASE = '/api/v1';

export async function request(path, { method = 'GET', body, signal } = {}) {
  let res;
  try {
    res = await fetch(BASE + path, {
      method, signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    if (err?.name === 'AbortError') throw err;
    return { ok: false, status: 0, error: { code: 'offline', message: 'The control API is unreachable.' } };
  }
  let data = null;
  try { data = await res.json(); } catch { /* non-JSON */ }
  if (!res.ok || data == null) {
    const e = data?.error || { code: `http_${res.status}`, message: `The API returned HTTP ${res.status}.` };
    return { ok: false, status: res.status, error: e };
  }
  return { ok: true, status: res.status, data, fetchedAt: new Date() };
}

export const api = {
  health: (o) => request('/health', o),
  models: (o) => request('/models', o),
  vectors: (o) => request('/vectors', o),
  reports: (o) => request('/reports', o),
  orchestration: (o) => request('/orchestration', o),
  jobs: (o) => request('/jobs', o),
  experiments: (o) => request('/experiments', o),
  defenses: (o) => request('/defenses', o),
  defenseLab: (o) => request('/defenses/lab', o),
  defenseCheck: (body) => request('/defenses/check', { method: 'POST', body }),
  steering: (o) => request('/steering', o),
  captureSmoke: (o) => request('/capture-smoke', o),
  steeringProfile: (body) => request('/steering/profile', { method: 'POST', body }),
  infer: (question, condition, model_id) =>
    request('/inference', { method: 'POST', body: { model_id, question, mode: 'simulation', condition, max_output_tokens: 160 } }),
};
