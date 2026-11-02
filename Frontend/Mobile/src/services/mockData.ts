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
  await new Promise((resolve) => setTimeout(resolve, 400));
  return latestNews;
}

export async function getNewsList(filter = 'Tous'): Promise<NewsItem[]> {
  await new Promise((resolve) => setTimeout(resolve, 350));
  if (filter === 'Tous') return newsList;
  return newsList.filter((item) => item.tags.includes(filter));
}

export async function login(email: string, password: string) {
  await new Promise((resolve) => setTimeout(resolve, 700));
  if (!email.includes('@') || password.length < 6) {
    throw new Error('Identifiants invalides');
  }
  return { ok: true };
}

export async function sendMessageToAI(message: string) {
  await new Promise((resolve) => setTimeout(resolve, 900));
  return {
    message: message || 'Message reçu',
    confidence: 72,
    summary: 'La vérification de cette information est partiellement confirmée : plusieurs éléments sont corroborés par des sources fiables, mais certains détails restent à confirmer.',
    sources: ['Source 1', 'Source 2'],
  };
}

export async function verifyContent(content: string) {
  await new Promise((resolve) => setTimeout(resolve, 650));
  return {
    credibility: 72,
    summary: 'Crédibilité moyenne : la déclaration est cohérente avec les éléments disponibles, mais elle demande un contrôle complémentaire.',
    explanation: 'Ce qui est confirmé : la déclaration correspond à des faits publics. Ce qui reste à vérifier : les sources secondaires et la date exacte.',
  };
}

export async function publishArticle(payload: { title: string; body: string; category: string }) {
  await new Promise((resolve) => setTimeout(resolve, 800));
  return { ok: true, id: 'article-1', ...payload };
}

export async function getProfile() {
  await new Promise((resolve) => setTimeout(resolve, 300));
  return {
    name: 'Nom de l’utilisateur',
    email: 'adresse@email.mg',
    publications: 0,
    verifications: 0,
    credibility: 0,
  };
}

export const demoMessage = 'Bonjour ! Envoyez-moi un texte, une photo ou une vidéo : je vérifie l’information.';
