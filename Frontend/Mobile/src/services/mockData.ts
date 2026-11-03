import { apiRequest, clearTokens, setTokens, newsImageUrl } from './api';

export type ResponseLanguage = 'auto' | 'fr' | 'mg';
export type SourceAssessment = { url: string; assessment: 'supports' | 'contradicts' | 'inconclusive' };
export type Corroboration = { claim: string; corroboration_percent: number | null; supports: number; contradicts: number; inconclusive: number; source_groups: number; excluded_duplicates: number; limitation: string };
export function calculateCorroboration(claim: string, sources: SourceAssessment[]) {
  return apiRequest<Corroboration>('/copilot/credibility', { method: 'POST', body: JSON.stringify({ claim, sources }) });
}

export type PrecomputeSource = SourceAssessment & { title: string; excerpt: string; quote: string; date: string | null; origin: string; duplicate: boolean };
export type PrecomputeResult = { claim: string | null; sources: PrecomputeSource[]; calculation: Corroboration | null; checked_at: string; warnings: string[]; notice: string };
export type PrecomputeJob = { job_id: string; status: 'queued' | 'running' | 'completed' | 'failed'; result?: PrecomputeResult | null };
export function startPrecompute(articleUrl: string) {
  return apiRequest<PrecomputeJob>('/copilot/precompute', { method: 'POST', body: JSON.stringify({ article_url: articleUrl }) });
}
export function getPrecompute(jobId: string) {
  return apiRequest<PrecomputeJob>(`/copilot/precompute/${jobId}`);
}
export type GdeltArticle = { title: string; url: string; source: string; seen_at: string | null; image: string | null; excerpt: string; categories: string[] };
export function interleaveNewsWithImages(articles: GdeltArticle[]): GdeltArticle[] {
  const illustrated = articles.filter((article) => !!article.image);
  const other = articles.filter((article) => !article.image);
  const result: GdeltArticle[] = [];
  for (let index = 0; index < Math.max(illustrated.length, other.length); index++) {
    if (illustrated[index]) result.push(illustrated[index]);
    if (other[index]) result.push(other[index]);
  }
  return result;
}
export function articleAnalysisQuestion(item: { title: string; excerpt?: string; url?: string }) {
  return `Analyse journalistique de ce contenu. Distingue les affirmations, les preuves disponibles, les éléments à vérifier et les limites ; ne conclus pas à sa fiabilité sans sources indépendantes. Tu ne disposes que du titre${item.excerpt ? ' et de l’extrait fourni' : ''}, ne prétends pas avoir lu un lien.\nTitre : ${item.title.slice(0, 350)}\n${item.excerpt ? `Extrait : ${item.excerpt.slice(0, 850)}\n` : ''}${item.url ? `Source : ${item.url.slice(0, 400)}` : ''}`;
}
export async function getGdeltNews() {
  const feed = await apiRequest<{ articles: GdeltArticle[]; fetched_at: string; provider: 'gdelt' | 'rss' | 'google_news' | 'mixed'; stale?: boolean }>('/public/gdelt?themes=1');
  return { ...feed, articles: feed.articles.map((item) => ({ ...item, image: item.image ? newsImageUrl(item.image) : null })) };
}

export async function getResponseLanguage() {
  const account = await apiRequest<{ response_language: ResponseLanguage }>('/auth/me');
  return account.response_language;
}

export function saveResponseLanguage(language: ResponseLanguage) {
  return apiRequest<{ language: ResponseLanguage }>('/auth/me/language', {
    method: 'PATCH', body: JSON.stringify({ language }),
  });
}

export function translateAnswer(text: string, targetLanguage: 'fr' | 'mg') {
  return apiRequest<{ text: string; language: 'fr' | 'mg'; provider: string }>('/copilot/translate', {
    method: 'POST', body: JSON.stringify({ text, target_language: targetLanguage }),
  });
}

export type NewsItem = {
  id: string;
  source: string;
  time: string;
  title: string;
  image?: string;
  credibility: number | null;
  summary: string;
  tags: string[];
};

export const latestNews: NewsItem[] = [
  {
    id: '1',
    source: '2424.mg',
    time: 'Heure',
    title: 'Jeux Olympiques de la Jeunesse 2026 : la compétition historique de Dakar lancée ce 31 octobre',
    credibility: 85,
    summary: 'Le lancement a été annoncé avec une forte mobilisation autour du programme sportif national et international.',
    tags: ['Sport'],
    image: 'https://images.unsplash.com/photo-1547347298-4074fc3086f0?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: '2',
    source: 'France24.com',
    time: 'Aujourd’hui',
    title: 'Les relations vers des partenaires africains ont changé, affirme Bruno Fuchs',
    credibility: 72,
    summary: 'L’analyse souligne un changement notable de la dynamique diplomatique régionale.',
    tags: ['Politique'],
    image: 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: '3',
    source: 'TVM.mg',
    time: 'Il y a 2h',
    title: 'Coopération russo-malgache : la TVM lance « Russomada TV »',
    credibility: 67,
    summary: 'La chaîne a présenté le lancement du programme de diffusion avec un nouveau format d’émissions.',
    tags: ['Société'],
    image: 'https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=800&q=80',
  },
];

export const newsList: NewsItem[] = [
  ...latestNews,
  {
    id: '4',
    source: '24h.madagascar',
    time: 'Il y a 4h',
    title: 'Maromanga : violentes chutes de grêle dans la commune',
    credibility: 58,
    summary: 'Les pluies orageuses ont provoqué des dégâts et des interruptions de services publics.',
    tags: ['Société'],
    image: 'https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=800&q=80',
  },
  {
    id: '5',
    source: 'Source',
    time: 'Il y a 1h',
    title: 'Le dernier article sur les réformes de la capitale et les mesures de sécurité',
    credibility: 77,
    summary: 'Les autorités ont détaillé le plan de mise à niveau des infrastructures et des services publics.',
    tags: ['Politique'],
  },
];

export async function getLatestNews(): Promise<NewsItem[]> {
  const items = await getNewsList('Tous');
  return items.slice(0, 3);
}

export async function getNewsList(filter = 'Tous'): Promise<NewsItem[]> {
  const articles = await apiRequest<{
    id: number;
    titre_final: string;
    corps_article: string;
    categorie: string;
    statut_verification: string;
    horodatage_validation: string;
  }[]>('/public/articles');

  const items = articles.map((article) => ({
    id: String(article.id),
    source: 'FANILO',
    time: new Date(article.horodatage_validation).toLocaleDateString('fr-FR'),
    title: article.titre_final,
    credibility: null,
    summary: article.corps_article,
    tags: [article.categorie],
  }));
  if (filter === 'Tous' || filter === 'Vérifiés') return items;
  const normalize = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  return items.filter((item) => item.tags.some((tag) => normalize(tag) === normalize(filter)));
}

export async function login(email: string, password: string) {
  const tokens = await apiRequest<{ access_token: string; refresh_token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, mot_de_passe: password }),
  });
  setTokens(tokens);
  return { ok: true };
}

export async function register(email: string, password: string) {
  const tokens = await apiRequest<{ access_token: string; refresh_token: string }>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, mot_de_passe: password }),
  });
  setTokens(tokens);
  return { ok: true };
}

export async function sendMessageToAI(message: string, language?: ResponseLanguage) {
  const answer = await apiRequest<{
    reponse: string;
    citations: { titre?: string; url?: string }[];
  }>('/copilot/research', {
    method: 'POST',
    body: JSON.stringify({ question: message, language }),
  });
  return {
    message: message || 'Message reçu',
    confidence: null,
    summary: answer.reponse,
    sources: answer.citations.map((citation) => [citation.titre, citation.url].filter(Boolean).join(' — ') || 'Source'),
  };
}

export async function verifyContent(content: string) {
  const answer = await sendMessageToAI(content);
  return {
    credibility: answer.confidence,
    summary: answer.summary,
    explanation: answer.sources.join(', ') || 'Aucune source n’a été retournée.',
  };
}

export async function publishArticle(payload: { title: string; body: string; category: string; media?: any }) {
  let media_base64: string | undefined;
  if (payload.media?.uri) {
    const response = await fetch(payload.media.uri);
    const blob = await response.blob();
    media_base64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(String(reader.result).split(',')[1] || '');
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }
  const contribution = await apiRequest<{ id: number; status: string }>('/contributions/signals', {
    method: 'POST',
    body: JSON.stringify({
      content: `[${payload.category}] ${payload.title}\n\n${payload.body}`,
      media_base64,
    }),
  });
  return { ok: true, id: String(contribution.id), status: contribution.status, ...payload };
}

export async function getProfile() {
  const [account, stats] = await Promise.all([apiRequest<{
    id: number;
    name: string;
    email: string;
    role: string;
    response_language: ResponseLanguage;
  }>('/auth/me'), apiRequest<{ publications: number; verifications: number; credibility: number | null }>('/auth/me/stats')]);
  const photo = await apiRequest<{ photo: string | null }>('/auth/me/photo');
  return {
    name: account.name || account.role,
    email: account.email,
    ...stats,
    photo: photo.photo,
    language: account.response_language,
  };
}

export function updateProfile(name: string, email: string) {
  return apiRequest<{ name: string; email: string; role: string }>('/auth/me', {
    method: 'PATCH', body: JSON.stringify({ name, email }),
  });
}

export function getNotifications() {
  return apiRequest<{ id: string; title: string; message: string; created_at: string; read: boolean }[]>('/auth/notifications');
}

export function requestPasswordReset(email: string) {
  return apiRequest<{ message: string; reset_token?: string }>('/auth/password/forgot', {
    method: 'POST', body: JSON.stringify({ email }),
  });
}

export function resetPassword(resetToken: string, newPassword: string) {
  return apiRequest<{ message: string }>('/auth/password/reset', {
    method: 'POST', body: JSON.stringify({ reset_token: resetToken, new_password: newPassword }),
  });
}

export function saveProfilePhoto(imageBase64: string) {
  return apiRequest<{ photo: string }>('/auth/me/photo', {
    method: 'PUT',
    body: JSON.stringify({ image_base64: imageBase64 }),
  });
}

export async function logout() {
  try {
    await apiRequest<void>('/auth/logout', { method: 'POST' });
  } finally {
    clearTokens();
  }
}

export const demoMessage = 'Bonjour ! Envoyez-moi un texte, une photo ou une vidéo : je vérifie l’information.';
