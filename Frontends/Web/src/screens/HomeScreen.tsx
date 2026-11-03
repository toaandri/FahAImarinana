import { Link, useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Image, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, Card, Icon, InteractivePressable, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';
import { articleAnalysisQuestion, getArticles, getGdeltNews } from '../services/api';

type CarouselItem = { id: string; title: string; source: string; image?: string; excerpt?: string; url?: string; status: string };

export default function HomeScreen() {
  const { width } = useWindowDimensions();
  const desktop = width >= 1200;
  const router = useRouter();
  const [items, setItems] = useState<CarouselItem[]>([]);
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    Promise.allSettled([getGdeltNews(), getArticles()]).then(([external, certified]) => {
      if (!active) return;
      const fromFeed: CarouselItem[] = external.status === 'fulfilled' ? external.value.articles.slice(0, 10).map((item) => ({
        id: item.url, title: item.title, source: item.source, image: item.image || undefined,
        excerpt: item.excerpt, url: item.url, status: 'Non vérifié',
      })) : [];
      const fromCertified: CarouselItem[] = certified.status === 'fulfilled' ? certified.value.slice(0, 3).map((item) => ({
        id: `fanilo-${item.id}`, title: item.titre_final, source: 'FANILO', excerpt: item.corps_article, url: `article:${item.id}`, status: 'Article certifié',
      })) : [];
      const all = [...fromFeed, ...fromCertified];
      setItems(all);
      setIndex(0);
      setError(all.length ? '' : external.status === 'rejected' && certified.status === 'rejected' ? 'Actualités indisponibles.' : 'Aucune actualité disponible.');
      setLoading(false);
    });
    return () => { active = false; };
  }, [reload]);

  useEffect(() => {
    if (items.length < 2) return undefined;
    const timer = setTimeout(() => setIndex((current) => (current + 1) % items.length), 8000);
    return () => clearTimeout(timer);
  }, [index, items.length]);
  const activeItem = items[index];

  return (
    <AppShell active="/">
      <PageTitle>Accueil</PageTitle>
      <View style={[styles.columns, desktop && styles.columnsDesktop]}>
        <Card style={styles.columnCard}>
          <Text style={styles.cardTitle}>Dernière information</Text>
          {activeItem ? <View style={styles.headline}>
            <View style={styles.headlineAccent} />
            <Text style={styles.headlineText}>{activeItem.title}</Text>
            {activeItem.image ? <Image source={{ uri: activeItem.image }} style={styles.image} resizeMode="cover" /> : null}
          </View> : <Text style={styles.meta}>{loading ? 'Chargement des actualités…' : error}</Text>}
          {activeItem ? <>
            <View style={styles.metaRow}>
              <Text style={styles.meta}>{activeItem.source} · {activeItem.status}</Text>
              <Text style={styles.meta}>{index + 1} / {items.length}</Text>
            </View>
            <View style={styles.carouselActions}>
              {items.length > 1 ? <>
                <InteractivePressable accessibilityRole="button" accessibilityLabel="Actualité précédente" onPress={() => setIndex((current) => (current - 1 + items.length) % items.length)} style={styles.carouselButton}><Text style={styles.meta}>← Précédente</Text></InteractivePressable>
                <InteractivePressable accessibilityRole="button" accessibilityLabel="Actualité suivante" onPress={() => setIndex((current) => (current + 1) % items.length)} style={styles.carouselButton}><Text style={styles.meta}>Suivante →</Text></InteractivePressable>
              </> : null}
              <InteractivePressable accessibilityRole="button" onPress={() => router.push({ pathname: '/verifier', params: { analyze: '1', question: articleAnalysisQuestion(activeItem), ...(activeItem.url ? { article_url: activeItem.url } : {}) } })} style={styles.carouselButton}><Text style={styles.meta}>Analyser avec l’IA</Text></InteractivePressable>
            </View>
          </> : !loading ? <InteractivePressable accessibilityRole="button" onPress={() => { setLoading(true); setReload((value) => value + 1); }} style={styles.carouselButton}><Text style={styles.meta}>Réessayer</Text></InteractivePressable> : null}
        </Card>

        <Card style={styles.columnCard}>
          <Text style={styles.cardTitle}>Discuter et vérifier</Text>
          <Text style={styles.description}>
            Envoyez un texte, une photo ou une vidéo à FahAIMarinana.
          </Text>
          <Link href="/verifier" asChild>
            <InteractivePressable accessibilityRole="button" style={styles.cta}>
              <Icon name="arrow-right" color={colors.deep} />
              <Text style={styles.ctaText}>Parler</Text>
            </InteractivePressable>
          </Link>
        </Card>
      </View>
    </AppShell>
  );
}

const styles = StyleSheet.create({
  columns: { gap: spacing.xl },
  columnsDesktop: { flexDirection: 'row', alignItems: 'stretch' },
  columnCard: { flex: 1, minHeight: 320 },
  cardTitle: { color: colors.white, fontSize: 22, lineHeight: 30, fontWeight: '700', marginBottom: 20 },
  headline: {
    minHeight: 140,
    backgroundColor: colors.deep,
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    marginBottom: 20,
    borderRadius: 12,
  },
  headlineAccent: { width: 4, alignSelf: 'stretch', backgroundColor: colors.accent, marginRight: 12 },
  headlineText: { flex: 1, color: colors.muted, fontSize: 17, lineHeight: 24, fontWeight: '700' },
  image: { width: 90, height: 90, borderRadius: 8, marginLeft: 8 },
  carouselActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 12 },
  carouselButton: { minHeight: 44, justifyContent: 'center', borderColor: colors.accent, borderWidth: 1, borderRadius: 10, paddingHorizontal: 12 },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 16, alignItems: 'center', marginTop: 12 },
  meta: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  example: { color: colors.muted, fontSize: 14, lineHeight: 20, marginLeft: 'auto' },
  description: { color: colors.white, fontSize: 17, lineHeight: 25, marginTop: 20, marginBottom: 'auto' },
  cta: { minHeight: 48, borderRadius: 12, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: colors.accent },
  ctaText: { color: colors.deep, fontSize: 15, lineHeight: 20, fontWeight: '700' },
});
