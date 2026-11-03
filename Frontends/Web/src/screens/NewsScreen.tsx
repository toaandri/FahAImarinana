import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Image, Linking, StyleSheet, Text, TextInput, View, useWindowDimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { AppShell, Icon, InteractivePressable, PageTitle } from '../components/ui';
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

const normalize = (value: string) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();

function formatDate(value: string | null, locale: string) {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' });
}

type CertifiedStory = { source: string; title: string; excerpt: string; category: string };

export default function NewsScreen() {
  const { width } = useWindowDimensions();
  const router = useRouter();
  const { language, t } = useI18n();
  const mobile = width < 768;
  const locale = language === 'mg' ? 'mg-MG' : language === 'en' ? 'en-US' : 'fr-FR';
  const [filter, setFilter] = useState('Tous');
  const [search, setSearch] = useState('');
  const [stories, setStories] = useState<CertifiedStory[]>([]);
  const [error, setError] = useState('');
  const [articlesLoading, setArticlesLoading] = useState(true);
  const [external, setExternal] = useState<GdeltArticle[]>([]);
  const [externalError, setExternalError] = useState('');
  const [feedProvider, setFeedProvider] = useState<'gdelt' | 'rss' | 'google_news' | 'mixed' | null>(null);
  const [feedStale, setFeedStale] = useState(false);
  const [feedLoading, setFeedLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getArticles()
      .then((articles) => {
        if (active) setStories(articles.map((article) => ({
          source: 'FANILO', title: article.titre_final, excerpt: article.corps_article,
          category: article.categorie,
        })));
      })
      .catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : 'news.unavailable'); })
      .finally(() => { if (active) setArticlesLoading(false); });
    return () => { active = false; };
  }, []);

  const loadFeed = useCallback(() => {
    setFeedLoading(true);
    setExternalError('');
    getGdeltNews()
      .then((result) => {
        setExternal(result.articles);
        setFeedProvider(result.provider);
        setFeedStale(!!result.stale);
      })
      .catch(() => setExternalError('news.unavailable'))
      .finally(() => setFeedLoading(false));
  }, []);

  useEffect(() => { void Promise.resolve().then(loadFeed); }, [loadFeed]);

  const visibleStories = useMemo(() => stories.filter((story) => {
    const categoryMatches = filter === 'Tous' || filter === 'Vérifiés'
      || normalize(story.category) === normalize(filter);
    const textMatches = !normalize(search)
      || normalize(`${story.title} ${story.excerpt} ${story.category}`).includes(normalize(search));
    return categoryMatches && textMatches;
  }), [filter, search, stories]);

  const visibleExternal = useMemo(() => external.filter((item) => {
    const categoryMatches = filter === 'Tous'
      || (item.categories || []).some((category) => normalize(category) === normalize(filter));
    const textMatches = !normalize(search)
      || normalize(`${item.title} ${item.excerpt} ${item.source} ${(item.categories || []).join(' ')}`).includes(normalize(search));
    return categoryMatches && textMatches;
  }), [external, filter, search]);

  const providerLabel = feedProvider === 'mixed' ? t('news.mixedProvider')
    : feedProvider === 'google_news' ? t('news.googleProvider')
      : feedProvider === 'rss' ? t('news.pressProvider') : t('news.gdeltProvider');

  return (
    <AppShell active="/actualites">
      <View style={styles.pageIntro}>
        <View style={styles.titleRow}>
          <View style={styles.titleCopy}>
            <PageTitle>{t('news.title')}</PageTitle>
            <Text style={styles.introText}>{t('news.description')}</Text>
          </View>
          <View style={styles.totalBadge}>
            <Text style={styles.totalNumber}>{external.length + stories.length}</Text>
            <Text style={styles.totalLabel}>{t('news.available')}</Text>
          </View>
        </View>

        <View style={styles.searchBox}>
          <Icon name="magnify" color={colors.muted} size={21} />
          <TextInput
            accessibilityLabel={t('news.search')}
            value={search}
            onChangeText={setSearch}
            placeholder={t('news.searchPlaceholder')}
            placeholderTextColor={colors.muted}
            returnKeyType="search"
            style={styles.searchInput}
          />
          {search ? <InteractivePressable accessibilityRole="button" accessibilityLabel={t('news.clearSearch')} onPress={() => setSearch('')} style={styles.clearSearch}>
            <Icon name="close-circle" color={colors.muted} size={20} />
          </InteractivePressable> : null}
        </View>

        <View style={styles.filters} accessibilityRole="radiogroup">
          {filters.map((item) => {
            const selected = filter === item.value;
            return <InteractivePressable
              key={item.value}
              accessibilityRole="radio"
              accessibilityLabel={t('news.filter', { filter: t(item.key) })}
              accessibilityState={{ checked: selected }}
              aria-checked={selected}
              onPress={() => setFilter(item.value)}
              style={[styles.filterButton, selected && styles.filterSelected]}
            >
              <Text style={[styles.filterText, selected && styles.filterTextSelected]}>{t(item.key)}</Text>
            </InteractivePressable>;
          })}
        </View>
      </View>

      {filter !== 'Vérifiés' ? <View style={styles.section}>
        <View style={styles.sectionHeading}>
          <View style={styles.sectionHeadingCopy}>
            <Text style={styles.sectionTitle}>{t('news.madagascar')}</Text>
            <Text style={styles.sectionDescription}>{t('news.externalDisclaimer')}</Text>
          </View>
          <View style={styles.providerBadge}>
            <View style={styles.providerDot} />
            <Text style={styles.providerText}>{providerLabel}</Text>
          </View>
        </View>
        {feedStale ? <View style={styles.notice}><Icon name="clock-alert-outline" color={colors.muted} size={18} /><Text style={styles.noticeText}>{t('news.stale')}</Text></View> : null}
        <Text style={styles.themeNote}>{t('news.autoThemes')}</Text>
        {feedLoading ? <View style={styles.loadingState}><ActivityIndicator color={colors.accent} /><Text style={styles.stateText}>{t('news.loading')}</Text></View> : null}
        {externalError ? <View style={styles.errorState}>
          <Icon name="cloud-alert-outline" color={colors.muted} size={22} />
          <Text style={styles.stateText}>{externalError === 'news.unavailable' ? t('news.unavailable') : externalError === 'news.openFailed' ? t('news.openFailed') : externalError}</Text>
          <InteractivePressable accessibilityRole="button" onPress={loadFeed} style={styles.retryButton}><Text style={styles.retryText}>{t('common.retry')}</Text></InteractivePressable>
        </View> : null}
        {!feedLoading && !externalError && visibleExternal.length === 0 ? <View style={styles.emptyState}>
          <Icon name="newspaper-variant-outline" color={colors.muted} size={26} />
          <Text style={styles.stateText}>{search ? t('news.noSearchResults') : t('news.noExternal')}</Text>
        </View> : null}
        <View style={[styles.storyGrid, mobile && styles.storyGridMobile]}>
          {visibleExternal.map((item) => <View key={item.url} style={[styles.storyCard, styles.externalCard, mobile && styles.storyCardMobile]}>
            {item.image ? <Image source={{ uri: item.image }} accessibilityLabel={item.title} style={styles.externalImage} resizeMode="cover" /> : (
              <View style={styles.imagePlaceholder}><Icon name="image-outline" color={colors.muted} size={30} /><Text style={styles.placeholderText}>{t('common.image')}</Text></View>
            )}
            <View style={styles.storyContent}>
              <View style={styles.metaRow}>
                <Text style={styles.source} numberOfLines={1}>{item.source}</Text>
                {item.seen_at ? <Text style={styles.date}>{formatDate(item.seen_at, locale)}</Text> : null}
              </View>
              <Text style={styles.title}>{item.title}</Text>
              {item.excerpt ? <Text style={styles.excerpt} numberOfLines={4}>{item.excerpt}</Text> : null}
              {item.categories?.length ? <View style={styles.categoryList}>{item.categories.slice(0, 3).map((category) => (
                <View key={category} style={styles.categoryTag}><Text style={styles.categoryText}>{category}</Text></View>
              ))}</View> : null}
              <View style={styles.externalActions}>
                <InteractivePressable accessibilityRole="link" onPress={() => void Linking.openURL(item.url).catch(() => setExternalError('news.openFailed'))} style={styles.primaryAction}>
                  <Text style={styles.primaryActionText}>{t('news.readSource')}</Text><Icon name="arrow-top-right" color={colors.deep} size={17} />
                </InteractivePressable>
                <InteractivePressable accessibilityRole="button" onPress={() => router.push({ pathname: '/verifier', params: { analyze: '1', question: articleAnalysisQuestion(item), article_url: item.url } })} style={styles.secondaryAction}>
                  <Icon name="creation-outline" color={colors.background} size={17} /><Text style={styles.secondaryActionText}>{t('news.analyze')}</Text>
                </InteractivePressable>
              </View>
            </View>
          </View>)}
        </View>
      </View> : null}

      <View style={styles.section}>
        <View style={styles.sectionHeading}>
          <View style={styles.sectionHeadingCopy}>
            <Text style={styles.sectionTitle}>{t('news.certified')}</Text>
            <Text style={styles.sectionDescription}>{t('news.verifiedDescription')}</Text>
          </View>
          <View style={styles.verifiedBadge}><Icon name="check-decagram-outline" color={colors.deep} size={18} /><Text style={styles.verifiedText}>{t('news.verified')}</Text></View>
        </View>
        {articlesLoading ? <View style={styles.loadingState}><ActivityIndicator color={colors.accent} /><Text style={styles.stateText}>{t('news.loading')}</Text></View> : null}
        {error ? <Text style={styles.stateText}>{error === 'news.unavailable' ? t('news.unavailable') : error}</Text> : null}
        {!articlesLoading && !error && visibleStories.length === 0 ? <View style={styles.emptyState}>
          <Icon name="check-decagram-outline" color={colors.muted} size={26} />
          <Text style={styles.stateText}>{search ? t('news.noSearchResults') : t('news.noCertified')}</Text>
        </View> : null}
        <View style={[styles.storyGrid, mobile && styles.storyGridMobile]}>
          {visibleStories.map((story, index) => <View key={`${story.source}-${index}`} style={[styles.storyCard, styles.certifiedCard, mobile && styles.storyCardMobile]}>
            <View style={styles.certifiedMark}><Icon name="check-decagram" color={colors.accent} size={22} /><Text style={styles.certifiedMarkText}>{t('news.verified')}</Text></View>
            <Text style={styles.title}>{story.title}</Text>
            {story.excerpt ? <Text style={styles.certifiedExcerpt} numberOfLines={4}>{story.excerpt}</Text> : null}
            <Text style={styles.certifiedSource}>{story.source}{story.category ? ` · ${story.category}` : ''}</Text>
          </View>)}
        </View>
      </View>
    </AppShell>
  );
}

const styles = StyleSheet.create({
  pageIntro: { gap: spacing.lg, marginBottom: spacing.xxl },
  titleRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: spacing.lg },
  titleCopy: { flex: 1, minWidth: 0 },
  introText: { color: colors.muted, fontSize: 16, lineHeight: 24, maxWidth: 720, marginTop: -spacing.md },
  totalBadge: { minWidth: 92, minHeight: 72, paddingHorizontal: spacing.md, borderRadius: 16, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  totalNumber: { color: colors.white, fontSize: 22, lineHeight: 28, fontWeight: '800' },
  totalLabel: { color: colors.muted, fontSize: 11, lineHeight: 16, fontWeight: '700', textAlign: 'center' },
  searchBox: { minHeight: 52, maxWidth: 720, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 14, borderWidth: 1, borderColor: colors.border, borderRadius: 14, backgroundColor: colors.surface },
  searchInput: { flex: 1, minWidth: 0, minHeight: 50, color: colors.white, fontSize: 15, paddingVertical: 10, outlineStyle: 'none' } as object,
  clearSearch: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center' },
  filters: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  filterButton: { minHeight: 42, justifyContent: 'center', paddingHorizontal: 16, borderRadius: 24, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  filterSelected: { backgroundColor: colors.accent, borderColor: colors.accent },
  filterText: { color: colors.white, fontSize: 14, fontWeight: '700' },
  filterTextSelected: { color: colors.deep },
  section: { gap: spacing.lg, marginBottom: spacing.section },
  sectionHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: spacing.md },
  sectionHeadingCopy: { flex: 1, minWidth: 0, gap: 4 },
  sectionTitle: { color: colors.white, fontSize: 23, lineHeight: 30, fontWeight: '800' },
  sectionDescription: { color: colors.muted, fontSize: 13, lineHeight: 19, maxWidth: 760 },
  providerBadge: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  providerDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.accent },
  providerText: { color: colors.white, fontSize: 12, lineHeight: 16, fontWeight: '700' },
  notice: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12, paddingVertical: 10, borderRadius: 12, backgroundColor: colors.surface },
  noticeText: { flex: 1, color: colors.muted, fontSize: 13, lineHeight: 19 },
  themeNote: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  loadingState: { minHeight: 108, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 12, borderWidth: 1, borderColor: colors.border, borderRadius: 16, backgroundColor: colors.surface },
  errorState: { minHeight: 116, alignItems: 'center', justifyContent: 'center', gap: 10, padding: spacing.lg, borderWidth: 1, borderColor: colors.border, borderRadius: 16, backgroundColor: colors.surface },
  stateText: { color: colors.muted, fontSize: 14, lineHeight: 21, textAlign: 'center' },
  retryButton: { minHeight: 40, justifyContent: 'center', paddingHorizontal: 18, borderWidth: 1, borderColor: colors.border, borderRadius: 20 },
  retryText: { color: colors.white, fontSize: 13, fontWeight: '700' },
  emptyState: { minHeight: 128, alignItems: 'center', justifyContent: 'center', gap: 10, padding: spacing.lg, borderWidth: 1, borderColor: colors.border, borderStyle: 'dashed', borderRadius: 16, backgroundColor: colors.surface },
  storyGrid: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'stretch', gap: spacing.lg },
  storyGridMobile: { flexDirection: 'column' },
  storyCard: { flexBasis: '47%', flexGrow: 1, minWidth: 280, maxWidth: 640, overflow: 'hidden', borderWidth: 1, borderColor: colors.border, borderRadius: 18, backgroundColor: colors.white },
  storyCardMobile: { minWidth: 0, width: '100%', maxWidth: undefined, flexBasis: 'auto' },
  externalCard: { alignSelf: 'stretch' },
  externalImage: { width: '100%', aspectRatio: 16 / 9, backgroundColor: colors.surface },
  imagePlaceholder: { width: '100%', aspectRatio: 16 / 9, alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: colors.surface },
  placeholderText: { color: colors.muted, fontSize: 13, fontWeight: '600' },
  storyContent: { flex: 1, padding: spacing.lg, gap: 10 },
  metaRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  source: { flex: 1, minWidth: 0, color: colors.background, fontSize: 12, lineHeight: 18, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.35 },
  date: { color: colors.background, opacity: 0.72, fontSize: 12, lineHeight: 18 },
  title: { color: colors.background, fontSize: 18, lineHeight: 26, fontWeight: '800' },
  excerpt: { color: colors.background, opacity: 0.82, fontSize: 14, lineHeight: 21 },
  categoryList: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 2 },
  categoryTag: { paddingHorizontal: 9, paddingVertical: 5, borderRadius: 14, backgroundColor: colors.surface },
  categoryText: { color: colors.white, fontSize: 11, lineHeight: 15, fontWeight: '700' },
  externalActions: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 8, marginTop: 'auto', paddingTop: 8 },
  primaryAction: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingHorizontal: 12, borderRadius: 12, backgroundColor: colors.accent },
  primaryActionText: { color: colors.deep, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  secondaryAction: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingHorizontal: 12, borderWidth: 1, borderColor: colors.border, borderRadius: 12, backgroundColor: colors.white },
  secondaryActionText: { color: colors.background, fontSize: 13, lineHeight: 18, fontWeight: '700' },
  verifiedBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 18, backgroundColor: colors.accent },
  verifiedText: { color: colors.deep, fontSize: 12, lineHeight: 16, fontWeight: '800' },
  certifiedCard: { gap: 12, padding: spacing.lg, backgroundColor: colors.surface },
  certifiedMark: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  certifiedMarkText: { color: colors.white, fontSize: 12, lineHeight: 18, fontWeight: '700' },
  certifiedExcerpt: { color: colors.white, opacity: 0.82, fontSize: 14, lineHeight: 21 },
  certifiedSource: { color: colors.muted, fontSize: 12, lineHeight: 18, fontWeight: '700', marginTop: 'auto', paddingTop: 4 },
});
