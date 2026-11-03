import Constants from 'expo-constants';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { setVideoReport } from './video-session';

type TokenResponse = {
  access_token: string;
  refresh_token: string;
};

type ApiError = {
  detail?: string | { msg?: string }[];
};

const configuredUrl = process.env.EXPO_PUBLIC_API_URL || Constants.expoConfig?.extra?.apiUrl;
const backendUrl = new URL(configuredUrl || 'http://localhost:8000/api/v1');
const metroHost = Constants.expoConfig?.hostUri?.split(':')[0];
const isPrivateHost = (host: string) => ['localhost', '127.0.0.1'].includes(host)
  || /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(host);
if (__DEV__ && ['localhost', '127.0.0.1'].includes(backendUrl.hostname)) {
  const browserHost = typeof location !== 'undefined' ? location.hostname : undefined;
  const reachableHost = browserHost && isPrivateHost(browserHost) && !['localhost', '127.0.0.1'].includes(browserHost)
    ? browserHost
    : metroHost && isPrivateHost(metroHost) ? metroHost : undefined;
  if (reachableHost) backendUrl.hostname = reachableHost;
}
const API_URL = backendUrl.toString().replace(/\/$/, '');
export function newsImageUrl(url: string): string {
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'https:' && parsed.host === 'www.madagascar-tribune.com' && parsed.pathname.startsWith('/IMG/')) {
      return `${API_URL}/public/news-image?url=${encodeURIComponent(url)}`;
    }
  } catch { /* Keep the original URL for the image component to handle. */ }
  return url;
}
const TOKEN_STORAGE_KEY = 'fah-ai-marinana.auth-tokens';

let accessToken: string | null = null;
let refreshToken: string | null = null;
let refreshInFlight: Promise<boolean> | null = null;
let storageWrites = Promise.resolve();

export function setTokens(tokens: TokenResponse | null) {
  accessToken = tokens?.access_token ?? null;
  refreshToken = tokens?.refresh_token ?? null;
  storageWrites = storageWrites.catch(() => {}).then(() => persistTokens(tokens));
  void storageWrites.catch(() => {});
}

export function clearTokens() {
  setTokens(null);
  setVideoReport(null);
}

async function persistTokens(tokens: TokenResponse | null) {
  const value = tokens ? JSON.stringify(tokens) : null;
  if (Platform.OS !== 'web') {
    if (value) await SecureStore.setItemAsync(TOKEN_STORAGE_KEY, value);
    else await SecureStore.deleteItemAsync(TOKEN_STORAGE_KEY);
  } else if (typeof globalThis.localStorage !== 'undefined') {
    if (value) globalThis.localStorage.setItem(TOKEN_STORAGE_KEY, value);
    else globalThis.localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

export async function restoreTokens() {
  try {
    await storageWrites;
    const value = Platform.OS === 'web' ? globalThis.localStorage?.getItem(TOKEN_STORAGE_KEY)
      : await SecureStore.getItemAsync(TOKEN_STORAGE_KEY);
    if (!value) return;
    const tokens = JSON.parse(value) as Partial<TokenResponse>;
    if (typeof tokens.access_token === 'string' && typeof tokens.refresh_token === 'string') {
      accessToken = tokens.access_token;
      refreshToken = tokens.refresh_token;
    }
  } catch {
    await persistTokens(null);
  }
}

async function boundedFetch(url: string, init: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (init.signal?.aborted) controller.abort();
  init.signal?.addEventListener('abort', abort);
  const timer = setTimeout(abort, 60000);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (error) {
    if (controller.signal.aborted) throw new Error('Requête interrompue ou délai dépassé. Le serveur peut encore traiter le clip.');
    throw error;
  } finally {
    clearTimeout(timer);
    init.signal?.removeEventListener('abort', abort);
  }
}

function errorMessage(payload: ApiError) {
  if (typeof payload.detail === 'string') return payload.detail;
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((item) => item.msg).filter(Boolean).join(', ');
  }
  return 'La requête a échoué.';
}

async function requestResponse(path: string, init: RequestInit = {}, canRefresh = true): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  const sentToken = accessToken;
  if (sentToken) headers.set('Authorization', 'Bearer ' + sentToken);

  const response = await boundedFetch(`${API_URL}${path}`, { ...init, headers });
  if (response.status === 401 && canRefresh && refreshToken) {
    if (sentToken !== accessToken && accessToken) return requestResponse(path, init, false);
    if (!refreshInFlight) {
      const tokenToRefresh = refreshToken;
      refreshInFlight = (async () => {
        const refreshed = await boundedFetch(`${API_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: tokenToRefresh }),
        });
        if (refreshToken !== tokenToRefresh) return !!accessToken;
        if (refreshed.ok) {
          setTokens((await refreshed.json()) as TokenResponse);
          return true;
        }
        clearTokens();
        return false;
      })().finally(() => { refreshInFlight = null; });
    }
    if (await refreshInFlight) return requestResponse(path, init, false);
  }

  if (!response.ok) {
    if (response.status === 401 && !['/auth/login', '/auth/register'].includes(path)) {
      throw new Error('Session expirée ou absente. Reconnectez-vous pour lancer l’analyse.');
    }
    let payload: ApiError = {};
    try {
      payload = (await response.json()) as ApiError;
    } catch {
      // The status code is still reported by the generic message below.
    }
    throw new Error(errorMessage(payload));
  }

  return response;
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await requestResponse(path, init);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function editorialImageDataUrl(id: number, signal?: AbortSignal): Promise<string> {
  const response = await requestResponse(`/editorial/contributions/${id}/media`, { signal });
  const blob = await response.blob();
  if (!blob.type.startsWith('image/')) throw new Error('Ce média n’est pas une image.');
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => typeof reader.result === 'string' ? resolve(reader.result) : reject(new Error('Image illisible.'));
    reader.onerror = () => reject(new Error('Image illisible.'));
    reader.readAsDataURL(blob);
  });
}
