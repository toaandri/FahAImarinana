import Constants from 'expo-constants';

type TokenResponse = { access_token: string; refresh_token: string };
type ApiError = { detail?: string | Array<{ msg?: string }> };
export type ResponseLanguage = 'auto' | 'fr' | 'mg';
export type SourceAssessment = { url: string; assessment: 'supports' | 'contradicts' | 'inconclusive' };
export type Corroboration = { claim: string; corroboration_percent: number | null; supports: number; contradicts: number; inconclusive: number; source_groups: number; excluded_duplicates: number; limitation: string };
export function calculateCorroboration(claim: string, sources: SourceAssessment[]) {
  return request<Corroboration>('/copilot/credibility', { method: 'POST', body: JSON.stringify({ claim, sources }) });
}
export type PrecomputeSource = SourceAssessment & { title: string; excerpt: string; quote: string; date: string | null; origin: string; duplicate: boolean };
export type PrecomputeResult = { claim: string | null; sources: PrecomputeSource[]; calculation: Corroboration | null; checked_at: string; warnings: string[]; notice: string };
export type PrecomputeJob = { job_id: string; status: 'queued' | 'running' | 'completed' | 'failed'; result?: PrecomputeResult | null };
export function startPrecompute(articleUrl: string) {
  return request<PrecomputeJob>('/copilot/precompute', { method: 'POST', body: JSON.stringify({ article_url: articleUrl }) });
}
export function getPrecompute(jobId: string) {
  return request<PrecomputeJob>(`/copilot/precompute/${jobId}`);
}
export type GdeltArticle = { title: string; url: string; source: string; seen_at: string | null; image: string | null; excerpt: string; categories: string[] };
export function articleAnalysisQuestion(item: { title: string; excerpt?: string; url?: string }) {
  return `Analyse journalistique de ce contenu. Distingue les affirmations, les preuves disponibles, les éléments à vérifier et les limites ; ne conclus pas à sa fiabilité sans sources indépendantes. Tu ne disposes que du titre${item.excerpt ? ' et de l’extrait fourni' : ''}, ne prétends pas avoir lu un lien.\nTitre : ${item.title.slice(0, 350)}\n${item.excerpt ? `Extrait : ${item.excerpt.slice(0, 850)}\n` : ''}${item.url ? `Source : ${item.url.slice(0, 400)}` : ''}`;
}
export function getGdeltNews() {
  return request<{ articles: GdeltArticle[]; fetched_at: string; provider: 'gdelt' | 'rss' | 'google_news' | 'mixed'; stale?: boolean }>('/public/gdelt?themes=1');
}
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

const configuredUrl = (
  (typeof process !== 'undefined' ? process.env.EXPO_PUBLIC_API_URL : undefined)
  || (Constants.expoConfig?.extra?.apiUrl as string | undefined)
);
const backendUrl = new URL(configuredUrl || 'http://127.0.0.1:18000/api/v1');
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
const TOKEN_STORAGE_KEY = 'fah-ai-marinana.auth-tokens';
let accessToken: string | null = null;
let refreshToken: string | null = null;

export const MAX_CONTRIBUTION_MEDIA_BYTES = 100 * 1024 * 1024;

export class ContributionMediaTooLargeError extends Error {}

function persistTokens(tokens: TokenResponse | null) {
  if (typeof globalThis.localStorage === 'undefined') return;
  if (tokens) globalThis.localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens));
  else globalThis.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

function restoreTokens() {
  if (typeof globalThis.localStorage === 'undefined') return;
  try {
    const stored = globalThis.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!stored) return;
    const tokens = JSON.parse(stored) as Partial<TokenResponse>;
    if (typeof tokens.access_token === 'string' && typeof tokens.refresh_token === 'string') {
      accessToken = tokens.access_token;
      refreshToken = tokens.refresh_token;
    }
  } catch {
    globalThis.localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

restoreTokens();

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  persistTokens(null);
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
      persistTokens(tokens);
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
    persistTokens(tokens);
  });
}

export function register(email: string, password: string) {
  return request<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, mot_de_passe: password }),
  }).then((tokens) => {
    accessToken = tokens.access_token;
    refreshToken = tokens.refresh_token;
    persistTokens(tokens);
  });
}

export function logout() {
  return request<void>('/auth/logout', { method: 'POST' }).finally(clearTokens);
}

export function updateProfile(name: string, email: string) {
  return request<{ name: string; email: string; role: string }>('/auth/me', {
    method: 'PATCH', body: JSON.stringify({ name, email }),
  });
}

export function getProfileStats() {
  return request<{ publications: number; verifications: number; credibility: number | null }>('/auth/me/stats');
}

export function getNotifications() {
  return request<{ id: string; title: string; message: string; created_at: string; read: boolean }[]>('/auth/notifications');
}

export function requestPasswordReset(email: string) {
  return request<{ message: string; reset_token?: string }>('/auth/password/forgot', {
    method: 'POST', body: JSON.stringify({ email }),
  });
}

export function resetPassword(resetToken: string, newPassword: string) {
  return request<{ message: string }>('/auth/password/reset', {
    method: 'POST', body: JSON.stringify({ reset_token: resetToken, new_password: newPassword }),
  });
}

export async function getProfile() {
  const [profile, stats] = await Promise.all([
    request<{ name: string; email: string; role: string; response_language: ResponseLanguage }>('/auth/me'),
    getProfileStats(),
  ]);
  const photo = await request<{ photo: string | null }>('/auth/me/photo');
  return { ...profile, ...stats, photo: photo.photo };
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
    corps_article: string;
    categorie: string;
    horodatage_validation: string;
  }>>('/public/articles');
}

async function encodeContributionMedia(media: {
  uri: string;
  mimeType?: string | null;
  fileSize?: number | null;
  type: 'image' | 'video';
}) {
  if (media.fileSize !== undefined && media.fileSize !== null && media.fileSize > MAX_CONTRIBUTION_MEDIA_BYTES) {
    throw new ContributionMediaTooLargeError();
  }
  const response = await fetch(media.uri);
  if (!response.ok) throw new Error('Impossible de lire le média sélectionné.');
  const blob = await response.blob();
  if (blob.size > MAX_CONTRIBUTION_MEDIA_BYTES) {
    throw new ContributionMediaTooLargeError();
  }
  const mediaBase64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result;
      if (typeof result !== 'string') {
        reject(new Error('Impossible de lire le média sélectionné.'));
        return;
      }
      resolve(result.slice(result.indexOf(',') + 1));
    };
    reader.onerror = () => reject(reader.error ?? new Error('Impossible de lire le média sélectionné.'));
    reader.readAsDataURL(blob);
  });
  return {
    media_base64: mediaBase64,
    media_content_type: media.mimeType || blob.type || (media.type === 'image' ? 'image/jpeg' : 'video/mp4'),
  };
}

export async function submitContribution(payload: {
  title: string;
  body: string;
  category: string;
  source?: string;
  media?: { uri: string; mimeType?: string | null; fileSize?: number | null; type: 'image' | 'video' } | null;
}) {
  const media = payload.media ? await encodeContributionMedia(payload.media) : {};
  return request<{ id: number }>('/contributions/signals', {
    method: 'POST',
    body: JSON.stringify({
      content: `[${payload.category}] ${payload.title}\n\n${payload.body}${payload.source ? `\n\nSource : ${payload.source}` : ''}`,
      ...media,
    }),
  });
}
