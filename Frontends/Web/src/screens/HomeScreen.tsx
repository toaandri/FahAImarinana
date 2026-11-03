import { Link, useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Image, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, Card, Icon, InteractivePressable, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';
import { articleAnalysisQuestion, getArticles, getGdeltNews } from '../services/api';
import { useI18n } from '../components/i18n';

type CarouselItem = { id: string; title: string; source: string; image?: string; excerpt?: string; url?: string; status: 'home.unverified' | 'home.certified' };

export default function HomeScreen() {
  const { width } = useWindowDimensions();
  const desktop = width >= 1000;
  const router = useRouter();
  const { t } = useI18n();
  const [items, setItems] = useState<CarouselItem[]>([]);
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<'home.unavailable' | 'home.empty' | ''>('');
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    Promise.allSettled([getGdeltNews(), getArticles()]).then(([external, certified]) => {
      if (!active) return;
      const fromFeed: CarouselItem[] = external.status === 'fulfilled' ? external.value.articles.slice(0, 10).map((item) => ({
        id: item.url, title: item.title, source: item.source, image: item.image || undefined,
        excerpt: item.excerpt, url: item.url,         status: 'home.unverified',
      })) : [];
      const fromCertified: CarouselItem[] = certified.status === 'fulfilled' ? certified.value.slice(0, 3).map((item) => ({
        id: `fanilo-${item.id}`, title: item.titre_final, source: 'FANILO', excerpt: item.corps_article, url: `article:${item.id}`, status: 'home.certified',
      })) : [];
      const all = [...fromFeed, ...fromCertified];
      setItems(all);
      setIndex(0);
      setError(all.length ? '' : external.status === 'rejected' && certified.status === 'rejected' ? 'home.unavailable' : 'home.empty');
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
    <AppShell active="/" fillHeight={desktop}>
      <PageTitle>{t('home.title')}</PageTitle>
      <View style={[styles.columns, desktop && styles.columnsDesktop]}>
        <Card style={[styles.columnCard, desktop && styles.newsCardDesktop]}>
          <View style={styles.cardHeading}>
            <View style={styles.cardTitleIcon}><Icon name="newspaper-variant-outline" color={colors.accent} size={21} /></View>
            <Text style={styles.cardTitle}>{t('home.latest')}</Text>
          </View>
          {activeItem ? <View style={styles.headline}>
            {activeItem.image ? <Image source={{ uri: activeItem.image }} accessibilityLabel={activeItem.title} style={styles.image} resizeMode="cover" /> : <View style={styles.imageFallback}><Icon name="newspaper-variant-outline" size={64} color={colors.accent} /></View>}
            <Text style={[styles.headlineText, width < 480 && styles.headlineTextMobile]}>{activeItem.title}</Text>
          </View> : <View style={styles.emptyState}>
            {loading ? <ActivityIndicator size="large" color={colors.accent} /> : <Icon name="newspaper-variant-outline" size={48} color={colors.muted} />}
            <Text style={styles.emptyText}>{loading ? t('home.loading') : error ? t(error) : ''}</Text>
          </View>}
          {activeItem ? <>
            <View style={styles.metaRow}>
              <Text style={styles.source}>{activeItem.source}</Text>
              <View style={styles.statusBadge}>
                <Icon name={activeItem.status === 'home.certified' ? 'check-decagram-outline' : 'information-outline'} size={16} color={colors.accent} />
                <Text style={styles.statusText}>{t(activeItem.status)}</Text>
              </View>
              <Text style={styles.counter}>{index + 1} / {items.length}</Text>
            </View>
            {items.length > 1 ? <View style={styles.carouselActions}>
              {items.length > 1 ? <>
                <InteractivePressable accessibilityRole="button" accessibilityLabel={t('home.previousLabel')} onPress={() => setIndex((current) => (current - 1 + items.length) % items.length)} style={styles.carouselButton}><Text style={styles.meta}>{t('home.previous')}</Text></InteractivePressable>
                <InteractivePressable accessibilityRole="button" accessibilityLabel={t('home.nextLabel')} onPress={() => setIndex((current) => (current + 1) % items.length)} style={styles.carouselButton}><Text style={styles.meta}>{t('home.next')}</Text></InteractivePressable>
              </> : null}
            </View> : null}
            <InteractivePressable accessibilityRole="button" onPress={() => router.push({ pathname: '/verifier', params: { analyze: '1', question: articleAnalysisQuestion(activeItem), ...(activeItem.url ? { article_url: activeItem.url } : {}) } })} style={styles.analyzeButton}><Icon name="shield-search" color={colors.deep} size={20} /><Text style={styles.analyzeText}>{t('home.analyze')}</Text></InteractivePressable>
          </> : !loading ? <InteractivePressable accessibilityRole="button" onPress={() => { setLoading(true); setReload((value) => value + 1); }} style={styles.carouselButton}><Text style={styles.meta}>{t('common.retry')}</Text></InteractivePressable> : null}
        </Card>

        <Card style={[styles.columnCard, styles.discussCard, desktop && styles.discussCardDesktop]}>
          <View style={styles.discussVisual} accessible={false}>
            <View style={styles.visualOrbit}>
              <View style={styles.visualIcon}><Icon name="message-processing-outline" color={colors.accent} size={56} /></View>
              <View style={styles.visualCheck}><Icon name="shield-check-outline" color={colors.deep} size={24} /></View>
            </View>
          </View>
          <Text accessibilityRole="header" style={styles.discussTitle}>{t('home.discuss')}</Text>
          <Text style={styles.description}>
            {t('home.description')}
          </Text>
          <Link href="/verifier" asChild>
            <InteractivePressable accessibilityRole="button" style={styles.cta}>
              <Text style={styles.ctaText}>{t('home.talk')}</Text>
              <Icon name="arrow-right" color={colors.deep} />
            </InteractivePressable>
          </Link>
        </Card>
      </View>
    </AppShell>
  );
}

const styles = StyleSheet.create({
  columns: { gap: spacing.xl, alignItems: 'stretch' },
  columnsDesktop: { flexDirection: 'row', alignItems: 'flex-start' },
  columnCard: { minWidth: 0, width: '100%', gap: 20, borderRadius: 24 },
  newsCardDesktop: { flex: 1.45, width: undefined },
  discussCardDesktop: { flex: 1, width: undefined },
  cardHeading: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  cardTitleIcon: { width: 44, height: 44, justifyContent: 'center', alignItems: 'center', borderRadius: 14, backgroundColor: colors.deep },
  cardTitle: { flex: 1, color: colors.white, fontSize: 20, lineHeight: 28, fontWeight: '700' },
  headline: { gap: 20 },
  headlineText: { color: colors.white, fontSize: 26, lineHeight: 36, fontWeight: '700' },
  headlineTextMobile: { fontSize: 22, lineHeight: 31 },
  image: { width: '100%', aspectRatio: 16 / 9, borderRadius: 16, backgroundColor: colors.deep },
  imageFallback: { width: '100%', aspectRatio: 16 / 9, borderRadius: 16, backgroundColor: colors.deep, justifyContent: 'center', alignItems: 'center' },
  emptyState: { minHeight: 240, padding: 24, borderRadius: 16, backgroundColor: colors.deep, alignItems: 'center', justifyContent: 'center', gap: 20 },
  emptyText: { color: colors.muted, fontSize: 16, lineHeight: 24, textAlign: 'center' },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, alignItems: 'center' },
  source: { flexShrink: 1, color: colors.muted, fontSize: 14, lineHeight: 22, fontWeight: '700' },
  statusBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, borderRadius: 20, backgroundColor: colors.deep, paddingHorizontal: 10, paddingVertical: 6 },
  statusText: { flexShrink: 1, color: colors.muted, fontSize: 12, lineHeight: 18, fontWeight: '600' },
  counter: { color: colors.muted, fontSize: 14, lineHeight: 22, marginLeft: 'auto', fontVariant: ['tabular-nums'] },
  carouselActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 20 },
  carouselButton: { flexGrow: 1, minHeight: 48, alignItems: 'center', justifyContent: 'center', borderColor: colors.border, borderWidth: 1, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 10 },
  meta: { color: colors.white, fontSize: 14, lineHeight: 22, fontWeight: '600' },
  analyzeButton: { minHeight: 52, flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center', gap: 10, borderRadius: 14, paddingHorizontal: 16, paddingVertical: 14, backgroundColor: colors.accent },
  analyzeText: { flexShrink: 1, color: colors.deep, fontSize: 16, lineHeight: 24, fontWeight: '800', textAlign: 'center' },
  discussCard: { backgroundColor: colors.deep, borderColor: colors.border },
  discussVisual: { minHeight: 180, justifyContent: 'center', alignItems: 'center', borderRadius: 16, backgroundColor: colors.background },
  visualOrbit: { width: 132, height: 132, borderRadius: 66, borderWidth: 1, borderColor: colors.border, justifyContent: 'center', alignItems: 'center' },
  visualIcon: { width: 100, height: 100, borderRadius: 50, backgroundColor: colors.deep, alignItems: 'center', justifyContent: 'center' },
  visualCheck: { position: 'absolute', bottom: 0, right: 0, width: 44, height: 44, borderRadius: 22, backgroundColor: colors.accent, alignItems: 'center', justifyContent: 'center', borderWidth: 4, borderColor: colors.background },
  discussTitle: { color: colors.white, fontSize: 26, lineHeight: 34, fontWeight: '700' },
  description: { color: colors.muted, fontSize: 17, lineHeight: 27 },
  cta: { minHeight: 52, borderRadius: 14, paddingHorizontal: 20, paddingVertical: 14, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12, backgroundColor: colors.accent },
  ctaText: { flexShrink: 1, color: colors.deep, fontSize: 16, lineHeight: 24, fontWeight: '800' },
});
