import Constants from 'expo-constants';

type TokenResponse = { access_token: string; refresh_token: string };
type ApiError = { detail?: string | Array<{ msg?: string }> };

const API_URL = ((Constants.expoConfig?.extra?.apiUrl as string | undefined) || 'http://localhost:18000/api/v1').replace(/\/$/, '');
let accessToken: string | null = null;
let refreshToken: string | null = null;

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
}

function message(payload: ApiError) {
  if (typeof payload.detail === 'string') return payload.detail;
  if (Array.isArray(payload.detail)) return payload.detail.map((item) => item.msg).filter(Boolean).join(', ');
  return 'La requête a échoué.';
}

async function request<T>(path: string, init: RequestInit = {}, canRefresh = true): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  if (accessToken) headers.set('Authorization', 'Bearer ' + accessToken);
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });

  if (response.status === 401 && canRefresh && refreshToken) {
    const refreshed = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (refreshed.ok) {
      const tokens = (await refreshed.json()) as TokenResponse;
      accessToken = tokens.access_token;
      refreshToken = tokens.refresh_token;
      return request<T>(path, init, false);
    }
    clearTokens();
  }

  if (!response.ok) {
    let payload: ApiError = {};
    try { payload = (await response.json()) as ApiError; } catch { /* status message below */ }
    throw new Error(message(payload));
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function login(email: string, password: string) {
  return request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, mot_de_passe: password }),
  }).then((tokens) => {
    accessToken = tokens.access_token;
    refreshToken = tokens.refresh_token;
  });
}

export function logout() {
  return request<void>('/auth/logout', { method: 'POST' }).finally(clearTokens);
}

export function getProfile() {
  return request<{ email: string; role: string }>('/auth/me');
}

export function getArticles() {
  return request<Array<{
    id: number;
    titre_final: string;
    categorie: string;
    horodatage_validation: string;
  }>>('/public/articles');
}

export function submitContribution(payload: { title: string; body: string; category: string; source?: string }) {
  return request<{ id: number }>('/contributions/signals', {
    method: 'POST',
    body: JSON.stringify({
      content: `[${payload.category}] ${payload.title}\n\n${payload.body}${payload.source ? `\n\nSource : ${payload.source}` : ''}`,
    }),
  });
}
