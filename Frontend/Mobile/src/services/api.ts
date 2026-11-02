import Constants from 'expo-constants';

type TokenResponse = {
  access_token: string;
  refresh_token: string;
};

type ApiError = {
  detail?: string | Array<{ msg?: string }>;
};

const configuredUrl = Constants.expoConfig?.extra?.apiUrl;
const API_URL = (configuredUrl || 'http://localhost:8000/api/v1').replace(/\/$/, '');

let accessToken: string | null = null;
let refreshToken: string | null = null;

export function setTokens(tokens: TokenResponse | null) {
  accessToken = tokens?.access_token ?? null;
  refreshToken = tokens?.refresh_token ?? null;
}

export function clearTokens() {
  setTokens(null);
}

function errorMessage(payload: ApiError) {
  if (typeof payload.detail === 'string') return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((item) => item.msg).filter(Boolean).join(', ');
  }
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
      setTokens((await refreshed.json()) as TokenResponse);
      return request<T>(path, init, false);
    }
    clearTokens();
  }

  if (!response.ok) {
    let payload: ApiError = {};
    try {
      payload = (await response.json()) as ApiError;
    } catch {
      // The status code is still reported by the generic message below.
    }
    throw new Error(errorMessage(payload));
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function apiRequest<T>(path: string, init?: RequestInit) {
  return request<T>(path, init);
}
