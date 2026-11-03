import Constants from 'expo-constants';

type TokenResponse = { access_token: string; refresh_token: string };
type ApiError = { detail?: string | Array<{ msg?: string }> };
export type ResponseLanguage = 'auto' | 'fr' | 'mg';
export type ResearchResult = { reponse: string; citations: { titre?: string; url?: string }[]; chronologie: unknown[] };

export async function getResponseLanguage() {
  const account = await request<{ response_language: ResponseLanguage }>('/auth/me');
  return account.response_language;
}

export function saveResponseLanguage(language: ResponseLanguage) {
  return request<{ language: ResponseLanguage }>('/auth/me/language', {
    method: 'PATCH', body: JSON.stringify({ language }),
  });
}

export function sendMessageToAI(question: string, language: ResponseLanguage) {
  return request<ResearchResult>('/copilot/research', { method: 'POST', body: JSON.stringify({ question, language }) });
}

export function translateAnswer(text: string, targetLanguage: 'fr' | 'mg') {
  return request<{ text: string; language: 'fr' | 'mg'; provider: string }>('/copilot/translate', {
    method: 'POST', body: JSON.stringify({ text, target_language: targetLanguage }),
  });
}

const configuredApiUrl = (Constants.expoConfig?.extra?.apiUrl as string | undefined) || 'http://localhost:18000/api/v1';
const apiUrl = new URL(configuredApiUrl);
const metroHost = Constants.expoConfig?.hostUri?.split(':')[0];
if (__DEV__ && ['localhost', '127.0.0.1'].includes(apiUrl.hostname) && metroHost) {
  apiUrl.hostname = metroHost;
}
const API_URL = apiUrl.toString().replace(/\/$/, '');
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

async function fetchApi(url: string, init: RequestInit) {
  try {
    return await fetch(url, init);
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`Impossible de joindre l’API (${API_URL}). Vérifiez que le backend est démarré et autorise l’origine web (CORS).`);
    }
    throw error;
  }
}

async function request<T>(path: string, init: RequestInit = {}, canRefresh = true): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  if (accessToken) headers.set('Authorization', 'Bearer ' + accessToken);
  const response = await fetchApi(`${API_URL}${path}`, { ...init, headers });

  if (response.status === 401 && canRefresh && refreshToken) {
    const refreshed = await fetchApi(`${API_URL}/auth/refresh`, {
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

export function register(email: string, password: string, invitationToken: string) {
  return request<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      email,
      mot_de_passe: password,
      invitation_token: invitationToken,
    }),
  }).then((tokens) => {
    accessToken = tokens.access_token;
    refreshToken = tokens.refresh_token;
  });
}

export function logout() {
  return request<void>('/auth/logout', { method: 'POST' }).finally(clearTokens);
}

export async function getProfile() {
  const profile = await request<{ email: string; role: string; response_language: ResponseLanguage }>('/auth/me');
  const photo = await request<{ photo: string | null }>('/auth/me/photo');
  return { ...profile, photo: photo.photo };
}

export function saveProfilePhoto(imageBase64: string) {
  return request<{ photo: string }>('/auth/me/photo', {
    method: 'PUT',
    body: JSON.stringify({ image_base64: imageBase64 }),
  });
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
