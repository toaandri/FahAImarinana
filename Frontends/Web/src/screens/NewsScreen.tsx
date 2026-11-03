import { useEffect, useMemo, useState } from 'react';
import { Image, Linking, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { AppShell, InteractivePressable, MediaPreview, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';
import { articleAnalysisQuestion, getArticles, getGdeltNews, type GdeltArticle } from '../services/api';

const filters = ['Tous', 'Vérifiés', 'Politique', 'Sport', 'Société', 'Économie'];
const normalizeCategory = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
export default function NewsScreen() {
  const { width } = useWindowDimensions();
  const router = useRouter();
  const mobile = width < 768;
  const [filter, setFilter] = useState('Tous');
  const [stories, setStories] = useState<Array<{ source: string; title: string; category: string }>>([]);
  const [error, setError] = useState('');
  const [external, setExternal] = useState<GdeltArticle[]>([]);
  const [externalError, setExternalError] = useState('');
  const [feedProvider, setFeedProvider] = useState<'gdelt' | 'rss' | 'google_news' | 'mixed' | null>(null);
  const [feedStale, setFeedStale] = useState(false);
  const [feedLoading, setFeedLoading] = useState(true);
  useEffect(() => {
    getArticles().then((articles) => setStories(articles.map((article) => ({
      source: 'FANILO',
      title: article.titre_final,
      category: article.categorie,
    })))).catch((reason) => setError(reason instanceof Error ? reason.message : 'Actualités indisponibles.'));
  }, []);
  function loadFeed() {
    setFeedLoading(true);
    setExternalError('');
    getGdeltNews().then((result) => { setExternal(result.articles); setFeedProvider(result.provider); setFeedStale(!!result.stale); })
      .catch(() => setExternalError('Actualités momentanément indisponibles.'))
      .finally(() => setFeedLoading(false));
  }
  useEffect(() => {
    getGdeltNews().then((result) => { setExternal(result.articles); setFeedProvider(result.provider); setFeedStale(!!result.stale); })
      .catch(() => setExternalError('Actualités momentanément indisponibles.'))
      .finally(() => setFeedLoading(false));
  }, []);
  const visibleStories = useMemo(
    () => (filter === 'Tous' || filter === 'Vérifiés' ? stories : stories.filter((story) => normalizeCategory(story.category) === normalizeCategory(filter))),
    [filter, stories],
  );
  const visibleExternal = filter === 'Tous' ? external : external.filter((item) => (item.categories || []).includes(filter));

  return (
    <AppShell active="/actualites">
      <PageTitle>Actualités</PageTitle>
      <View style={styles.filters} accessibilityRole="radiogroup">
        {filters.map((item) => {
          const selected = filter === item;
          return (
            <InteractivePressable
              key={item}
              accessibilityRole="radio"
              accessibilityLabel={`Filtrer les actualités : ${item}`}
              accessibilityState={{ checked: selected }}
              aria-checked={selected}
              onPress={() => setFilter(item)}
              style={[styles.filterButton, selected && styles.filterSelected]}
            >
              <Text style={[styles.filterText, selected && styles.filterTextSelected]}>{item}</Text>
            </InteractivePressable>
          );
        })}
      </View>
      {filter !== 'Vérifiés' ? <View style={styles.list}>
        <Text style={styles.externalHeading}>Actualités Madagascar · {feedProvider === 'mixed' ? 'GDELT et Google Actualités' : feedProvider === 'google_news' ? 'Google Actualités' : feedProvider === 'rss' ? 'presse' : 'GDELT'}</Text>
        <Text style={styles.empty}>Articles externes non vérifiés. La date correspond à leur publication ou à leur détection selon la source.</Text>
        <Text style={styles.empty}>Thèmes attribués automatiquement à partir du contenu disponible.</Text>
        {feedStale ? <Text style={styles.empty}>Derniers articles disponibles ; actualisation momentanément indisponible.</Text> : null}
        {feedLoading ? <Text style={styles.empty}>Chargement des actualités…</Text> : null}
        {externalError ? <Text style={styles.empty}>{externalError}</Text> : null}
        {externalError ? <InteractivePressable accessibilityRole="button" onPress={loadFeed}><Text style={styles.empty}>Réessayer</Text></InteractivePressable> : null}
        {!feedLoading && !externalError && visibleExternal.length === 0 ? <Text style={styles.empty}>Aucun article externe dans ce thème pour le moment.</Text> : null}
        {visibleExternal.map((item) => <View key={item.url} style={styles.story}>
          <View style={styles.storyText}>
            <Text style={styles.source}>{item.source}{item.seen_at ? ` · ${new Date(item.seen_at).toLocaleString('fr-FR')}` : ''}</Text>
            <Text style={styles.title}>{item.title}</Text>
            {item.categories?.length ? <Text style={styles.source}>{item.categories.join(' · ')}</Text> : null}
            <View style={styles.externalActions}>
              <InteractivePressable accessibilityRole="button" onPress={() => void Linking.openURL(item.url).catch(() => setExternalError('Impossible d’ouvrir la source.'))}><Text style={styles.externalLink}>Lire la source</Text></InteractivePressable>
              <InteractivePressable accessibilityRole="button" onPress={() => router.push({ pathname: '/verifier', params: { analyze: '1', question: articleAnalysisQuestion(item), article_url: item.url } })}><Text style={styles.externalLink}>Analyser avec l’IA</Text></InteractivePressable>
            </View>
          </View>
          {item.image ? <Image source={{ uri: item.image }} style={styles.externalImage} resizeMode="cover" /> : null}
        </View>)}
        <Text style={styles.externalHeading}>Articles certifiés FANILO</Text>
      </View> : null}
      <View style={styles.list}>
        {error ? <Text style={styles.empty}>{error}</Text> : null}
        {visibleStories.length === 0 ? (
          <Text style={styles.empty}>Aucun article certifié ne correspond à ce filtre.</Text>
        ) : visibleStories.map((story, index) => (
          <View key={`${story.source}-${index}`} style={styles.story}>
            <View style={styles.storyText}>
              <Text style={styles.source}>{story.source}</Text>
              <Text style={[styles.title, mobile && styles.titleMobile]}>{story.title}</Text>
            </View>
            <MediaPreview title={mobile ? 'Visuel' : 'Média'} compact />
          </View>
        ))}
      </View>
    </AppShell>
  );
}

const styles = StyleSheet.create({
  externalHeading: { color: colors.white, fontSize: 18, fontWeight: '700', marginVertical: 12 },
  externalActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 20, marginTop: 12 },
  externalImage: { width: 100, height: 80, borderRadius: 8 },
  externalLink: { color: colors.background, textDecorationLine: 'underline', fontWeight: '700', paddingVertical: 8 },
  filters: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: spacing.xl },
  filterButton: {
    minHeight: 44,
    minWidth: 72,
    justifyContent: 'center',
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  filterSelected: { backgroundColor: colors.accent, borderColor: colors.accent },
  filterText: { color: colors.white, fontSize: 14, fontWeight: '700' },
  filterTextSelected: { color: colors.deep },
  list: { gap: 8 },
  story: {
    minHeight: 120,
    padding: 16,
    backgroundColor: colors.white,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 16,
    borderRadius: 16,
  },
  storyText: { flex: 1, minWidth: 0 },
  source: { color: colors.background, fontSize: 14, lineHeight: 20, fontWeight: '700', marginBottom: 8 },
  title: { color: colors.background, fontSize: 18, lineHeight: 26, fontWeight: '700' },
  titleMobile: { fontSize: 16, lineHeight: 24 },
  empty: { color: colors.muted, fontSize: 16, lineHeight: 24 },
});
