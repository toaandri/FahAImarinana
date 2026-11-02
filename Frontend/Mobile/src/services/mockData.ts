import { apiRequest, clearTokens, setTokens } from './api';

export type NewsItem = {
  id: string;
  source: string;
  time: string;
  title: string;
  image?: string;
  credibility: number;
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
  const articles = await apiRequest<Array<{
    id: number;
    titre_final: string;
    corps_article: string;
    categorie: string;
    statut_verification: string;
    horodatage_validation: string;
  }>>('/public/articles');

  const items = articles.map((article) => ({
    id: String(article.id),
    source: 'FANILO',
    time: new Date(article.horodatage_validation).toLocaleDateString('fr-FR'),
    title: article.titre_final,
    credibility: article.statut_verification === 'Vrai' ? 100 : article.statut_verification === 'Trompeur' ? 50 : 0,
    summary: article.corps_article,
    tags: [article.categorie],
  }));
  if (filter === 'Tous' || filter === 'Vérifiés') return items;
  return items.filter((item) => item.tags.includes(filter));
}

export async function login(email: string, password: string) {
  const tokens = await apiRequest<{ access_token: string; refresh_token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, mot_de_passe: password }),
  });
  setTokens(tokens);
  return { ok: true };
}

export async function sendMessageToAI(message: string) {
  const answer = await apiRequest<{
    reponse: string;
    citations: Array<{ titre?: string; url?: string }>;
  }>('/copilot/research', {
    method: 'POST',
    body: JSON.stringify({ question: message }),
  });
  return {
    message: message || 'Message reçu',
    confidence: answer.citations.length ? 72 : 0,
    summary: answer.reponse,
    sources: answer.citations.map((citation) => citation.titre || citation.url || 'Source'),
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

export async function publishArticle(payload: { title: string; body: string; category: string }) {
  const contribution = await apiRequest<{ id: number; status: string }>('/contributions/signals', {
    method: 'POST',
    body: JSON.stringify({
      content: `[${payload.category}] ${payload.title}\n\n${payload.body}`,
    }),
  });
  return { ok: true, id: String(contribution.id), status: contribution.status, ...payload };
}

export async function getProfile() {
  const account = await apiRequest<{
    id: number;
    email: string;
    role: string;
  }>('/auth/me');
  return {
    name: account.role,
    email: account.email,
    publications: 0,
    verifications: 0,
    credibility: 0,
  };
}

export async function logout() {
  try {
    await apiRequest<void>('/auth/logout', { method: 'POST' });
  } finally {
    clearTokens();
  }
}

export const demoMessage = 'Bonjour ! Envoyez-moi un texte, une photo ou une vidéo : je vérifie l’information.';
