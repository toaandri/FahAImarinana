import { useEffect, useMemo, useState } from 'react';
import { Image, Linking, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { AppShell, InteractivePressable, MediaPreview, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';
import { articleAnalysisQuestion, getArticles, getGdeltNews, type GdeltArticle } from '../services/api';
import { useI18n } from '../components/i18n';

const filters = [
  { value: 'Tous', key: 'news.all' },
  { value: 'Vérifiés', key: 'news.verified' },
  { value: 'Politique', key: 'news.politics' },
  { value: 'Sport', key: 'news.sport' },
  { value: 'Société', key: 'news.society' },
  { value: 'Économie', key: 'news.economy' },
] as const;
const normalizeCategory = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
export default function NewsScreen() {
  const { width } = useWindowDimensions();
  const router = useRouter();
  const { language, t } = useI18n();
  const mobile = width < 768;
  const [filter, setFilter] = useState('Tous');
  const [stories, setStories] = useState<{ source: string; title: string; category: string }[]>([]);
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
    })))).catch((reason) => setError(reason instanceof Error ? reason.message : 'news.unavailable'));
  }, []);
  function loadFeed() {
    setFeedLoading(true);
    setExternalError('');
    getGdeltNews().then((result) => { setExternal(result.articles); setFeedProvider(result.provider); setFeedStale(!!result.stale); })
      .catch(() => setExternalError('news.unavailable'))
      .finally(() => setFeedLoading(false));
  }
  useEffect(() => {
    getGdeltNews().then((result) => { setExternal(result.articles); setFeedProvider(result.provider); setFeedStale(!!result.stale); })
      .catch(() => setExternalError('news.unavailable'))
      .finally(() => setFeedLoading(false));
  }, []);
  const visibleStories = useMemo(
    () => (filter === 'Tous' || filter === 'Vérifiés' ? stories : stories.filter((story) => normalizeCategory(story.category) === normalizeCategory(filter))),
    [filter, stories],
  );
  const visibleExternal = filter === 'Tous' ? external : external.filter((item) => (item.categories || []).includes(filter));

  return (
    <AppShell active="/actualites">
      <PageTitle>{t('news.title')}</PageTitle>
      <View style={styles.filters} accessibilityRole="radiogroup">
        {filters.map((item) => {
          const selected = filter === item.value;
          return (
            <InteractivePressable
              key={item.value}
              accessibilityRole="radio"
              accessibilityLabel={t('news.filter', { filter: t(item.key) })}
              accessibilityState={{ checked: selected }}
              aria-checked={selected}
              onPress={() => setFilter(item.value)}
              style={[styles.filterButton, selected && styles.filterSelected]}
            >
              <Text style={[styles.filterText, selected && styles.filterTextSelected]}>{t(item.key)}</Text>
            </InteractivePressable>
          );
        })}
      </View>
      {filter !== 'Vérifiés' ? <View style={styles.list}>
        <Text style={styles.externalHeading}>{t('news.madagascar')} · {feedProvider === 'mixed' ? t('news.mixedProvider') : feedProvider === 'google_news' ? t('news.googleProvider') : feedProvider === 'rss' ? t('news.pressProvider') : t('news.gdeltProvider')}</Text>
        <Text style={styles.empty}>{t('news.externalDisclaimer')}</Text>
        <Text style={styles.empty}>{t('news.autoThemes')}</Text>
        {feedStale ? <Text style={styles.empty}>{t('news.stale')}</Text> : null}
        {feedLoading ? <Text style={styles.empty}>{t('news.loading')}</Text> : null}
        {externalError ? <Text style={styles.empty}>
          {externalError === 'news.unavailable' ? t('news.unavailable') : externalError === 'news.openFailed' ? t('news.openFailed') : externalError}
        </Text> : null}
        {externalError ? <InteractivePressable accessibilityRole="button" onPress={loadFeed}><Text style={styles.empty}>{t('common.retry')}</Text></InteractivePressable> : null}
        {!feedLoading && !externalError && visibleExternal.length === 0 ? <Text style={styles.empty}>{t('news.noExternal')}</Text> : null}
        {visibleExternal.map((item) => <View key={item.url} style={styles.story}>
          {item.image ? <Image source={{ uri: item.image }} accessibilityLabel={item.title} style={styles.externalImage} resizeMode="cover" /> : null}
          <View style={styles.storyText}>
            <Text style={styles.source}>{item.source}{item.seen_at ? ` · ${new Date(item.seen_at).toLocaleString(language === 'mg' ? 'mg-MG' : language === 'en' ? 'en-US' : 'fr-FR')}` : ''}</Text>
            <Text style={styles.title}>{item.title}</Text>
            {item.excerpt ? <Text style={styles.excerpt}>{item.excerpt}</Text> : null}
            {item.categories?.length ? <Text style={styles.source}>{item.categories.join(' · ')}</Text> : null}
            <View style={styles.externalActions}>
              <InteractivePressable accessibilityRole="button" onPress={() => void Linking.openURL(item.url).catch(() => setExternalError('news.openFailed'))}><Text style={styles.externalLink}>{t('news.readSource')}</Text></InteractivePressable>
              <InteractivePressable accessibilityRole="button" onPress={() => router.push({ pathname: '/verifier', params: { analyze: '1', question: articleAnalysisQuestion(item), article_url: item.url } })}><Text style={styles.externalLink}>{t('news.analyze')}</Text></InteractivePressable>
            </View>
          </View>
        </View>)}
        <Text style={styles.externalHeading}>{t('news.certified')}</Text>
      </View> : null}
      <View style={styles.list}>
        {error ? <Text style={styles.empty}>{error === 'news.unavailable' ? t('news.unavailable') : error}</Text> : null}
        {visibleStories.length === 0 ? (
          <Text style={styles.empty}>{t('news.noCertified')}</Text>
        ) : visibleStories.map((story, index) => (
          <View key={`${story.source}-${index}`} style={styles.story}>
            <MediaPreview title={mobile ? t('common.image') : t('common.media')} compact />
            <View style={styles.storyText}>
              <Text style={styles.source}>{story.source}</Text>
              <Text style={[styles.title, mobile && styles.titleMobile]}>{story.title}</Text>
            </View>
          </View>
        ))}
      </View>
    </AppShell>
  );
}

const styles = StyleSheet.create({
  externalHeading: { color: colors.white, fontSize: 18, fontWeight: '700', marginVertical: 12 },
  externalActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 20, marginTop: 12 },
  externalImage: { width: '100%', aspectRatio: 16 / 9, maxHeight: 440, borderRadius: 12 },
  externalLink: { color: colors.background, textDecorationLine: 'underline', fontWeight: '700', fontSize: 16, lineHeight: 24, paddingVertical: 12, minHeight: 48 },
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
  list: { gap: 20, marginBottom: 24 },
  story: {
    minHeight: 120,
    padding: 16,
    backgroundColor: colors.white,
    flexDirection: 'column',
    alignItems: 'stretch',
    justifyContent: 'space-between',
    gap: 16,
    borderRadius: 16,
  },
  storyText: { minWidth: 0 },
  source: { color: colors.background, fontSize: 14, lineHeight: 20, fontWeight: '700', marginBottom: 8 },
  title: { color: colors.background, fontSize: 18, lineHeight: 26, fontWeight: '700' },
  titleMobile: { fontSize: 18, lineHeight: 27 },
  excerpt: { color: colors.background, fontSize: 15, lineHeight: 22, marginTop: 8 },
  empty: { color: colors.muted, fontSize: 16, lineHeight: 24 },
});
