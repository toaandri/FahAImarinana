import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { HeaderBar, GlassCard, BottomTabs, StoryCard } from '@/components/ui';
import { articleAnalysisQuestion, getGdeltNews, getLatestNews } from '@/services/mockData';
import { palette } from '@/theme/theme';
import { useLanguage } from '@/i18n/LanguageProvider';

type CarouselItem = { id: string; title: string; source: string; image?: string; excerpt?: string; url?: string; status: string };

export default function HomeScreen() {
  const { t } = useLanguage();
  const [items, setItems] = useState<CarouselItem[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    Promise.allSettled([getGdeltNews(), getLatestNews()]).then(([external, certified]) => {
      if (!active) return;
      const fromFeed: CarouselItem[] = external.status === 'fulfilled' ? external.value.articles.slice(0, 10).map((item) => ({
        id: item.url, title: item.title, source: item.source, image: item.image || undefined,
        excerpt: item.excerpt, url: item.url, status: 'Non vérifié',
      })) : [];
      const fromCertified: CarouselItem[] = certified.status === 'fulfilled' ? certified.value.map((item) => ({
        id: `fanilo-${item.id}`, title: item.title, source: item.source, image: item.image,
        excerpt: item.summary, url: `article:${item.id}`, status: 'Article certifié',
      })) : [];
      const all = [...fromFeed, ...fromCertified];
      setItems(all);
      setActiveIndex(0);
      setError(all.length ? '' : external.status === 'rejected' && certified.status === 'rejected' ? 'Actualités indisponibles.' : 'Aucune actualité disponible.');
      setLoading(false);
    });
    return () => { active = false; };
  }, [reload]);

  useEffect(() => {
    if (items.length < 2) return undefined;

    const timer = setTimeout(() => {
      setActiveIndex((index) => (index + 1) % items.length);
    }, 8_000);

    return () => clearTimeout(timer);
  }, [activeIndex, items.length]);

  const activeItem = items[activeIndex];

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar />
      <ScrollView contentContainerStyle={styles.content}>
        {activeItem ? <StoryCard
          title={activeItem.title}
          source={activeItem.source}
          status={activeItem.status}
          image={activeItem.image}
          label={t('latestInformation')}
          onPress={() => router.push({ pathname: '/discussion', params: { analyze: '1', question: articleAnalysisQuestion(activeItem), ...(activeItem.url ? { article_url: activeItem.url } : {}) } })}
        /> : <GlassCard style={styles.emptyCard}>
          <Text style={styles.emptyText}>{loading ? 'Chargement des actualités…' : error}</Text>
          {!loading ? <Pressable accessibilityRole="button" onPress={() => { setLoading(true); setReload((value) => value + 1); }}><Text style={styles.emptyText}>Réessayer</Text></Pressable> : null}
        </GlassCard>}
        {items.length > 1 ? (
          <View style={styles.carouselControls}>
          <Pressable accessibilityRole="button" accessibilityLabel="Actualité précédente" onPress={() => setActiveIndex((index) => (index - 1 + items.length) % items.length)}><Text style={styles.carouselArrow}>‹</Text></Pressable>
          <View style={styles.carouselIndicators} accessibilityRole="tablist">
            {items.map((item, index) => (
              <Pressable
                key={item.id}
                accessibilityRole="tab"
                accessibilityLabel={t('informationIndex', { current: index + 1, total: items.length })}
                accessibilityState={{ selected: index === activeIndex }}
                onPress={() => setActiveIndex(index)}
                style={[styles.carouselDot, index === activeIndex && styles.carouselDotActive]}
              />
            ))}
          </View>
          <Pressable accessibilityRole="button" accessibilityLabel="Actualité suivante" onPress={() => setActiveIndex((index) => (index + 1) % items.length)}><Text style={styles.carouselArrow}>›</Text></Pressable>
          </View>
        ) : null}
        {activeItem ? <Pressable accessibilityRole="button" style={styles.analyzeButton} onPress={() => router.push({ pathname: '/discussion', params: { analyze: '1', question: articleAnalysisQuestion(activeItem), ...(activeItem.url ? { article_url: activeItem.url } : {}) } })}><Text style={styles.analyzeText}>Analyser avec l’IA</Text></Pressable> : null}

        <GlassCard style={styles.talkCard}>
          <View style={styles.talkRow}>
            <Text style={styles.bigText}>{t('homeTalk')}</Text>
            <View style={styles.logoMiniWrap}><Text style={styles.logoMini}>FAH</Text><Text style={styles.aiMini}>AI</Text><Text style={styles.logoMini}>MARINANA</Text></View>
          </View>
          <Pressable style={styles.parlerButton} onPress={() => router.push('/discussion' as any)}>
            <Text style={styles.parlerText}>{t('talk')}</Text>
          </Pressable>
        </GlassCard>

        <GlassCard style={styles.reportCard}>
          <Text style={styles.reportTitle}>{t('report')}</Text>
          <Pressable style={styles.cameraButton} onPress={() => router.push('/direct' as any)}>
            <Text style={styles.cameraIcon}>◉</Text>
          </Pressable>
        </GlassCard>
      </ScrollView>
      <BottomTabs active="home" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  content: { padding: 16, paddingBottom: 120 },
  emptyCard: { padding: 20 },
  emptyText: { color: '#fff', paddingVertical: 8 },
  carouselControls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 16 },
  carouselArrow: { color: '#fff', fontSize: 30, paddingHorizontal: 14 },
  analyzeButton: { marginTop: 10, padding: 12, borderRadius: 12, borderWidth: 1, borderColor: palette.mint, alignItems: 'center' },
  analyzeText: { color: '#fff', fontWeight: '700' },
  carouselIndicators: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8, marginTop: 10 },
  carouselDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: 'rgba(255,255,255,0.4)' },
  carouselDotActive: { width: 18, backgroundColor: palette.mint },
  talkCard: { padding: 16, marginTop: 16 },
  talkRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  bigText: { color: '#fff', fontSize: 22, fontFamily: 'Montserrat_700Bold_Italic', lineHeight: 28, flex: 1 },
  logoMiniWrap: { flexDirection: 'row', alignItems: 'center', marginLeft: 12 },
  logoMini: { color: '#fff', fontSize: 12, fontFamily: 'Montserrat_700Bold_Italic' },
  aiMini: { backgroundColor: palette.mint, color: '#0b2b2b', padding: 4, borderRadius: 6, fontSize: 10, fontFamily: 'Montserrat_700Bold_Italic', overflow: 'hidden', marginHorizontal: 2 },
  parlerButton: { backgroundColor: palette.mint, paddingVertical: 12, borderRadius: 14, marginTop: 18, alignItems: 'center' },
  parlerText: { color: '#0b2b2b', fontSize: 14, fontFamily: 'Montserrat_700Bold_Italic' },
  reportCard: { marginTop: 16, padding: 20 },
  reportTitle: { color: '#fff', fontSize: 22, fontFamily: 'Montserrat_700Bold_Italic' },
  cameraButton: { marginTop: 18, width: 68, height: 68, borderRadius: 34, backgroundColor: palette.mint, alignSelf: 'center', justifyContent: 'center', alignItems: 'center' },
  cameraIcon: { color: '#0b2b2b', fontSize: 24, fontWeight: '800' },
});
