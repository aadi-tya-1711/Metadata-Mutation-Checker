/**
 * Thin API client for the FastAPI backend.
 * In dev, vite proxies /analyze to http://127.0.0.1:8000.
 * In prod, set VITE_API_BASE_URL to point to the deployed backend.
 */

const BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function analyzeFile(file) {
  const form = new FormData();
  form.append('file', file);

  const res = await fetch(`${BASE}/analyze`, {
    method: 'POST',
    body: form,
  });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.detail) detail = body.detail;
    } catch (_) {
      /* ignore */
    }
    throw new Error(detail);
  }

  return res.json();
}

export async function compareFiles(fileA, fileB) {
  const form = new FormData();
  form.append('file_a', fileA);
  form.append('file_b', fileB);

  const res = await fetch(`${BASE}/compare`, {
    method: 'POST',
    body: form,
  });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.detail) detail = body.detail;
    } catch (_) {
      /* ignore */
    }
    throw new Error(detail);
  }

  return res.json();
}
