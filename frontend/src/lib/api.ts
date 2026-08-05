import type { ChatRequest, ChatResponse, HealthResponse } from '@/types';

const BASE_URL = 'http://localhost:8000';

async function parseResponse<T>(res: Response): Promise<T> {
  const text = await res.text();
  let data: unknown;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { response: text };
  }
  return data as T;
}

export async function postChat(payload: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  });
  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(`Chat request failed (${res.status}): ${errText || res.statusText}`);
  }
  return parseResponse<ChatResponse>(res);
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/api/health`, { signal });
  if (!res.ok) {
    throw new Error(`Health check failed (${res.status})`);
  }
  return parseResponse<HealthResponse>(res);
}

export async function getSession(sessionId: string, signal?: AbortSignal): Promise<unknown> {
  const res = await fetch(`${BASE_URL}/api/session/${encodeURIComponent(sessionId)}`, { signal });
  if (!res.ok) {
    throw new Error(`Session fetch failed (${res.status})`);
  }
  return parseResponse<unknown>(res);
}

export async function deleteSession(sessionId: string, signal?: AbortSignal): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/session/${encodeURIComponent(sessionId)}`, {
    method: 'DELETE',
    signal,
  });
  if (!res.ok) {
    throw new Error(`Session clear failed (${res.status})`);
  }
}
