import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Image, Linking } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { HeaderBar, BottomTabs, TagChip } from '@/components/ui';
import { articleAnalysisQuestion, getNewsList, getGdeltNews, type GdeltArticle } from '@/services/mockData';
import { palette } from '@/theme/theme';
import { useLanguage } from '@/i18n/LanguageProvider';

export default function ActualitesScreen() {
  const { t } = useLanguage();
  const [filter, setFilter] = useState('Tous');
  const [items, setItems] = useState<any[]>([]);
  const [unavailable, setUnavailable] = useState(false);
  const [gdelt, setGdelt] = useState<GdeltArticle[]>([]);
  const [gdeltError, setGdeltError] = useState('');
  const [feedProvider, setFeedProvider] = useState<'gdelt' | 'rss' | null>(null);
  const [feedStale, setFeedStale] = useState(false);
  const [feedLoading, setFeedLoading] = useState(true);
  const filters = [
    { value: 'Tous', key: 'all' },
    { value: 'Vérifiés', key: 'verified' },
    { value: 'Politique', key: 'politics' },
    { value: 'Sport', key: 'sport' },
    { value: 'Société', key: 'society' },
    { value: 'Économie', key: 'economy' },
  ] as const;

  useEffect(() => {
    let active = true;
    getNewsList(filter).then((news) => {
      if (active) { setItems(news); setUnavailable(false); }
    }).catch(() => {
      if (active) { setItems([]); setUnavailable(true); }
    });
    return () => { active = false; };
  }, [filter]);

  const visibleExternal = filter === 'Tous' ? gdelt : gdelt.filter((item) => (item.categories || []).includes(filter));

  function loadFeed() {
    setFeedLoading(true);
    setGdeltError('');
    getGdeltNews().then((result) => { setGdelt(result.articles); setFeedProvider(result.provider); setFeedStale(!!result.stale); })
      .catch(() => setGdeltError('Actualités momentanément indisponibles.'))
      .finally(() => setFeedLoading(false));
  }
  useEffect(() => {
    getGdeltNews().then((result) => { setGdelt(result.articles); setFeedProvider(result.provider); setFeedStale(!!result.stale); })
      .catch(() => setGdeltError('Actualités momentanément indisponibles.'))
      .finally(() => setFeedLoading(false));
  }, []);

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar />
      <View style={styles.filtersWrap}>
        {filters.map((item) => (
          <Pressable key={item.value} accessibilityRole="button" accessibilityState={{ selected: filter === item.value }} onPress={() => {
            setUnavailable(false);
            setFilter(item.value);
          }}>
            <TagChip label={t(item.key)} active={filter === item.value} small />
          </Pressable>
        ))}
      </View>

      <ScrollView contentContainerStyle={styles.listWrap}>
        {filter !== 'Vérifiés' ? <View style={styles.externalSection}>
          <Text style={styles.externalHeading}>Actualités Madagascar · {feedProvider === 'rss' ? 'presse' : 'GDELT'}</Text>
          <Text style={styles.externalNote}>{feedProvider === 'rss' ? 'GDELT indisponible : affichage du flux de presse. Articles non vérifiés ; dates de publication.' : 'Articles externes non vérifiés. La date indique leur détection par GDELT.'}</Text>
          <Text style={styles.externalNote}>Thèmes attribués automatiquement à partir du contenu disponible.</Text>
          {feedStale ? <Text style={styles.externalNote}>Derniers articles disponibles ; actualisation momentanément indisponible.</Text> : null}
          {feedLoading ? <Text style={styles.externalNote}>Chargement des actualités…</Text> : null}
          {gdeltError ? <Text style={styles.externalNote}>{gdeltError}</Text> : null}
          {gdeltError ? <Pressable accessibilityRole="button" onPress={loadFeed}><Text style={styles.externalNote}>Réessayer</Text></Pressable> : null}
          {!feedLoading && !gdeltError && visibleExternal.length === 0 ? <Text style={styles.externalNote}>Aucun article externe dans ce thème pour le moment.</Text> : null}
          {visibleExternal.map((item) => <View key={item.url} style={styles.externalCard}>
            {item.image ? <Image source={{ uri: item.image }} style={styles.externalImage} resizeMode="cover" /> : null}
            <Text style={styles.externalSource}>{item.source}{item.seen_at ? ` · ${new Date(item.seen_at).toLocaleString('fr-FR')}` : ''}</Text>
            <Text style={styles.externalTitle}>{item.title}</Text>
            {item.categories?.length ? <Text style={styles.externalSource}>{item.categories.join(' · ')}</Text> : null}
            <View style={styles.externalActions}>
              <Pressable accessibilityRole="button" onPress={() => void Linking.openURL(item.url).catch(() => setGdeltError('Impossible d’ouvrir la source.'))}><Text style={styles.externalLink}>Lire la source</Text></Pressable>
              <Pressable accessibilityRole="button" onPress={() => router.push({ pathname: '/discussion', params: { analyze: '1', question: articleAnalysisQuestion(item) } })}><Text style={styles.externalLink}>Analyser avec l’IA</Text></Pressable>
            </View>
          </View>)}
        </View> : null}
        <View style={styles.newsPanel}>
          {unavailable ? <Text style={styles.emptyState}>{t('newsUnavailable')}</Text> : null}
          {!unavailable && items.length === 0 ? <Text style={styles.emptyState}>{t('noNews')}</Text> : null}
          {items.map((item, index) => (
            <Pressable
              key={item.id}
              accessibilityRole="button"
              onPress={() => router.push('/discussion' as any)}
              style={[styles.itemRow, index === items.length - 1 && styles.itemRowLast]}
            >
              <View style={styles.itemTextWrap}>
                <Text style={styles.source}>{item.source} <Text style={styles.time}>[1 {t('hour')}]</Text></Text>
                <Text style={styles.title}>{item.title}</Text>
              </View>
              {item.image ? <Image source={{ uri: item.image }} style={styles.thumb} /> : <View style={styles.thumbPlaceholder} />}
            </Pressable>
          ))}
        </View>
      </ScrollView>
      <BottomTabs active="actus" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  externalSection: { gap: 8, marginBottom: 20 },
  externalHeading: { color: '#fff', fontSize: 16, fontWeight: '700' },
  externalNote: { color: '#fff', fontSize: 12, lineHeight: 18 },
  externalCard: { backgroundColor: palette.headerTint, padding: 12, borderRadius: 12, gap: 6 },
  externalImage: { width: '100%', height: 170, borderRadius: 8 },
  externalSource: { color: palette.ink, fontSize: 11 },
  externalTitle: { color: palette.ink, fontSize: 14, fontWeight: '700' },
  externalActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 18, marginTop: 8 },
  externalLink: { color: palette.ink, textDecorationLine: 'underline', fontWeight: '700', paddingVertical: 8 },
  screen: { flex: 1, backgroundColor: palette.background },
  filtersWrap: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 16, paddingVertical: 16, gap: 8 },
  listWrap: { paddingHorizontal: 16, paddingBottom: 120 },
  newsPanel: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 18, backgroundColor: palette.headerTint },
  itemRow: { minHeight: 70, flexDirection: 'row', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: 'rgba(31,54,62,0.12)' },
  itemRowLast: { borderBottomWidth: 0 },
  itemTextWrap: { flex: 1, marginRight: 10 },
  source: { color: palette.ink, fontSize: 10, lineHeight: 14, fontFamily: 'Montserrat_700Bold_Italic', marginBottom: 3 },
  time: { color: palette.ink, fontSize: 9, fontFamily: 'Montserrat_600SemiBold_Italic', fontWeight: '400' },
  title: { color: palette.ink, fontSize: 11, fontFamily: 'Montserrat_700Bold_Italic', lineHeight: 14 },
  thumb: { width: 68, height: 52, borderRadius: 8 },
  thumbPlaceholder: { width: 68, height: 52, borderRadius: 8, backgroundColor: palette.backgroundDeep },
  emptyState: { color: '#fff', padding: 18, textAlign: 'center', fontFamily: 'Montserrat_600SemiBold_Italic' },
});
