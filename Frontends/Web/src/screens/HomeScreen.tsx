import { Link, useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Image, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, Card, Icon, InteractivePressable, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';
import { articleAnalysisQuestion, getArticles, getGdeltNews } from '../services/api';
import { useI18n } from '../components/i18n';

type CarouselItem = { id: string; title: string; source: string; image?: string; excerpt?: string; url?: string; status: 'home.unverified' | 'home.certified' };

export default function HomeScreen() {
  const { width } = useWindowDimensions();
  const desktop = width >= 1200;
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
        <Card style={styles.columnCard}>
          <View style={styles.cardHeading}>
            <View style={styles.cardTitleIcon}><Icon name="newspaper-variant-outline" color={colors.accent} size={21} /></View>
            <Text style={styles.cardTitle}>{t('home.latest')}</Text>
          </View>
          {activeItem ? <View style={[styles.headline, desktop && styles.headlineDesktop]}>
            {activeItem.image ? <Image source={{ uri: activeItem.image }} accessibilityLabel={activeItem.title} style={styles.image} resizeMode="cover" /> : null}
            <Text style={styles.headlineText}>{activeItem.title}</Text>
          </View> : <Text style={styles.meta}>{loading ? t('home.loading') : error ? t(error) : ''}</Text>}
          {activeItem ? <>
            <View style={styles.metaRow}>
              <Text style={styles.meta}>{activeItem.source} · {t(activeItem.status)}</Text>
              <Text style={styles.meta}>{index + 1} / {items.length}</Text>
            </View>
            <View style={styles.carouselActions}>
              {items.length > 1 ? <>
                <InteractivePressable accessibilityRole="button" accessibilityLabel={t('home.previousLabel')} onPress={() => setIndex((current) => (current - 1 + items.length) % items.length)} style={styles.carouselButton}><Text style={styles.meta}>{t('home.previous')}</Text></InteractivePressable>
                <InteractivePressable accessibilityRole="button" accessibilityLabel={t('home.nextLabel')} onPress={() => setIndex((current) => (current + 1) % items.length)} style={styles.carouselButton}><Text style={styles.meta}>{t('home.next')}</Text></InteractivePressable>
              </> : null}
              <InteractivePressable accessibilityRole="button" onPress={() => router.push({ pathname: '/verifier', params: { analyze: '1', question: articleAnalysisQuestion(activeItem), ...(activeItem.url ? { article_url: activeItem.url } : {}) } })} style={styles.carouselButton}><Text style={styles.meta}>{t('home.analyze')}</Text></InteractivePressable>
            </View>
          </> : !loading ? <InteractivePressable accessibilityRole="button" onPress={() => { setLoading(true); setReload((value) => value + 1); }} style={styles.carouselButton}><Text style={styles.meta}>{t('common.retry')}</Text></InteractivePressable> : null}
        </Card>

        <Card style={styles.columnCard}>
          <View style={styles.cardHeading}>
            <View style={styles.cardTitleIcon}><Icon name="message-processing-outline" color={colors.accent} size={21} /></View>
            <Text style={styles.cardTitle}>{t('home.discuss')}</Text>
          </View>
          <Text style={styles.description}>
            {t('home.description')}
          </Text>
          <Link href="/verifier" asChild>
            <InteractivePressable accessibilityRole="button" style={styles.cta}>
              <Icon name="arrow-right" color={colors.deep} />
              <Text style={styles.ctaText}>{t('home.talk')}</Text>
            </InteractivePressable>
          </Link>
        </Card>
      </View>
    </AppShell>
  );
}

const styles = StyleSheet.create({
  columns: { gap: spacing.xl },
  columnsDesktop: { flexDirection: 'row', alignItems: 'flex-start' },
  columnCard: { flex: 1, minWidth: 0, gap: 8 },
  cardHeading: { minHeight: 40, flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 20 },
  cardTitleIcon: { width: 56, height: 56, justifyContent: 'center', alignItems: 'center', borderRadius: 12, backgroundColor: colors.deep },
  cardTitle: { flex: 1, color: colors.white, fontSize: 22, lineHeight: 30, fontWeight: '700' },
  headline: {
    minHeight: 140,
    backgroundColor: colors.deep,
    flexDirection: 'column',
    alignItems: 'stretch',
    gap: 20,
    padding: 16,
    marginBottom: 20,
    borderRadius: 12,
  },
  headlineDesktop: { minHeight: 180 },
  headlineAccent: { width: 4, alignSelf: 'stretch', backgroundColor: colors.accent, marginRight: 12 },
  headlineText: { color: colors.white, fontSize: 21, lineHeight: 30, fontWeight: '700' },
  image: { width: '100%', aspectRatio: 16 / 9, borderRadius: 12 },
  carouselActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 12 },
  carouselButton: { minHeight: 44, justifyContent: 'center', borderColor: colors.accent, borderWidth: 1, borderRadius: 10, paddingHorizontal: 12 },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 16, alignItems: 'center', marginTop: 12 },
  meta: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  description: { color: colors.white, fontSize: 17, lineHeight: 25, marginTop: 4, marginBottom: 24 },
  cta: { minHeight: 48, borderRadius: 12, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: colors.accent },
  ctaText: { flexShrink: 1, color: colors.deep, fontSize: 15, lineHeight: 20, fontWeight: '700' },
});
