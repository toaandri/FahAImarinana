import { useCallback, useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Image, Linking, Alert, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useFocusEffect } from 'expo-router';
import { HeaderBar, BottomTabs, TagChip } from '@/components/ui';
import { articleAnalysisQuestion, getNewsList, getGdeltNews, getEditorialContributions, getCurrentUserId, deleteContribution, parseContribution, interleaveNewsWithImages, type GdeltArticle, type EditorialContribution } from '@/services/mockData';
import Ionicons from '@expo/vector-icons/Ionicons';
import { palette } from '@/theme/theme';
import { useLanguage } from '@/i18n/LanguageProvider';
import { editorialImageDataUrl } from '@/services/api';

function ContributionImage({ id }: { id: number }) {
  const [uri, setUri] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    editorialImageDataUrl(id, controller.signal)
      .then((value) => { if (!controller.signal.aborted) setUri(value); })
      .catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => controller.abort();
  }, [id]);
  if (failed) return <View style={styles.externalImagePlaceholder}><Text style={styles.externalImagePlaceholderText}>Image indisponible</Text></View>;
  if (!uri) return <View style={styles.externalImagePlaceholder}><Text style={styles.externalImagePlaceholderText}>Chargement de l’image…</Text></View>;
  return <Image source={{ uri }} style={styles.externalImage} resizeMode="cover" onError={() => setFailed(true)} />;
}

function NewsImage({ uri }: { uri: string | null }) {
  const [failed, setFailed] = useState(false);
  if (!uri || failed) return <View style={styles.externalImagePlaceholder}><Text style={styles.externalImagePlaceholderText}>Image indisponible</Text></View>;
  return <Image source={{ uri }} style={styles.externalImage} resizeMode="cover" onError={() => setFailed(true)} />;
}

export default function ActualitesScreen() {
  const { t } = useLanguage();
  const [filter, setFilter] = useState('Tous');
  const [items, setItems] = useState<any[]>([]);
  const [unavailable, setUnavailable] = useState(false);
  const [gdelt, setGdelt] = useState<GdeltArticle[]>([]);
  const [gdeltError, setGdeltError] = useState('');
  const [feedProvider, setFeedProvider] = useState<'gdelt' | 'rss' | 'google_news' | 'mixed' | null>(null);
  const [feedStale, setFeedStale] = useState(false);
  const [feedLoading, setFeedLoading] = useState(true);
  const [contributions, setContributions] = useState<EditorialContribution[]>([]);
  const [userId, setUserId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deleteError, setDeleteError] = useState('');
  const filters = [
    { value: 'Tous', key: 'all' },
    { value: 'Vérifiés', key: 'verified' },
    { value: 'Politique', key: 'politics' },
    { value: 'Sport', key: 'sport' },
    { value: 'Société', key: 'society' },
    { value: 'Économie', key: 'economy' },
    { value: 'Finance', key: 'finance' },
    { value: 'Culture', key: 'culture' },
    { value: 'Environnement', key: 'environment' },
    { value: 'Technologie', key: 'technology' },
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

  useFocusEffect(useCallback(() => {
    let active = true;
    getEditorialContributions().then((result) => { if (active) setContributions(result.filter((item) => item.kind === 'signal' && item.status === 'submitted')); })
      .catch(() => { if (active) setContributions([]); });
    getCurrentUserId().then((user) => { if (active) setUserId(user.id); }).catch(() => { if (active) setUserId(null); });
    return () => { active = false; };
  }, []));

  const visibleExternal = interleaveNewsWithImages(filter === 'Tous' ? gdelt : gdelt.filter((item) => (item.categories || []).includes(filter)));
  const visibleContributions = contributions.map((item) => ({ ...item, parsed: parseContribution(item.content) }))
    .filter((item) => filter !== 'Vérifiés' && (filter === 'Tous' || item.parsed.category === filter));

  function confirmDelete(id: number) {
    if (deletingId !== null) return;
    const remove = async () => {
      setDeleteError('');
      setDeletingId(id);
      try {
        await deleteContribution(id);
        setContributions((current) => current.filter((item) => item.id !== id));
      } catch (error) {
        setDeleteError(error instanceof Error ? error.message : 'Suppression impossible.');
      } finally { setDeletingId(null); }
    };
    if (Platform.OS === 'web') {
      if (globalThis.confirm('Supprimer cette contribution et son média ?')) void remove();
    } else {
      Alert.alert('Supprimer la contribution ?', 'Le texte et le média joint seront supprimés.', [
        { text: 'Annuler', style: 'cancel' },
        { text: 'Supprimer', style: 'destructive', onPress: () => void remove() },
      ]);
    }
  }

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
        {visibleContributions.length ? <View style={styles.externalSection}>
          <Text style={styles.externalHeading}>Contributions de la rédaction</Text>
          <Text style={styles.externalNote}>Visibles par la rédaction · non vérifiées et non publiées.</Text>
          {deleteError ? <Text accessibilityRole="alert" style={styles.externalNote}>{deleteError}</Text> : null}
          {visibleContributions.map((item) => <View key={`contribution-${item.id}`} style={styles.externalCard}>
            {item.has_media && item.media_content_type?.startsWith('image/') ? <ContributionImage id={item.id} /> : null}
            <Text style={styles.externalSource}>{item.parsed.category || 'Contribution'} · {new Date(item.created_at).toLocaleString('fr-FR')}</Text>
            <Text style={styles.externalTitle}>{item.parsed.title}</Text>
            <Text style={styles.externalSource}>{item.parsed.body}</Text>
            <Text style={styles.externalSource}>{item.has_media ? 'Média joint · ' : ''}Non vérifié · en attente de traitement</Text>
            {item.submitted_by_id === userId ? <Pressable accessibilityRole="button" accessibilityLabel={`Supprimer ${item.parsed.title}`}
              disabled={deletingId !== null} onPress={() => confirmDelete(item.id)} style={styles.deleteButton}>
              <Ionicons name="trash-outline" size={16} color="#9a2637" />
              <Text style={styles.deleteText}>{deletingId === item.id ? 'Suppression…' : 'Supprimer'}</Text>
            </Pressable> : null}
          </View>)}
        </View> : null}
        {filter !== 'Vérifiés' ? <View style={styles.externalSection}>
          <Text style={styles.externalHeading}>Actualités Madagascar · {feedProvider === 'mixed' ? 'sources multiples' : feedProvider === 'google_news' ? 'Google Actualités' : feedProvider === 'rss' ? 'presse' : 'GDELT'}</Text>
          <Text style={styles.externalNote}>Articles externes non vérifiés. La date correspond à leur publication ou à leur détection selon la source.</Text>
          <Text style={styles.externalNote}>Thèmes attribués automatiquement à partir du contenu disponible.</Text>
          {feedStale ? <Text style={styles.externalNote}>Derniers articles disponibles ; actualisation momentanément indisponible.</Text> : null}
          {feedLoading ? <Text style={styles.externalNote}>Chargement des actualités…</Text> : null}
          {gdeltError ? <Text style={styles.externalNote}>{gdeltError}</Text> : null}
          {gdeltError ? <Pressable accessibilityRole="button" onPress={loadFeed}><Text style={styles.externalNote}>Réessayer</Text></Pressable> : null}
          {!feedLoading && !gdeltError && visibleExternal.length === 0 ? <Text style={styles.externalNote}>Aucun article externe dans ce thème pour le moment.</Text> : null}
          {visibleExternal.map((item) => <View key={item.url} style={styles.externalCard}>
            <NewsImage uri={item.image} />
            <Text style={styles.externalSource}>{item.source}{item.seen_at ? ` · ${new Date(item.seen_at).toLocaleString('fr-FR')}` : ''}</Text>
            <Text style={styles.externalTitle}>{item.title}</Text>
            {item.categories?.length ? <Text style={styles.externalSource}>{item.categories.join(' · ')}</Text> : null}
            <View style={styles.externalActions}>
              <Pressable accessibilityRole="button" onPress={() => void Linking.openURL(item.url).catch(() => setGdeltError('Impossible d’ouvrir la source.'))}><Text style={styles.externalLink}>Lire la source</Text></Pressable>
              <Pressable accessibilityRole="button" onPress={() => router.push({ pathname: '/discussion', params: { analyze: '1', question: articleAnalysisQuestion(item), article_url: item.url } })}><Text style={styles.externalLink}>Analyser avec l’IA</Text></Pressable>
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
  externalImagePlaceholder: { width: '100%', height: 100, borderRadius: 8, backgroundColor: '#d9e4df', justifyContent: 'center', alignItems: 'center' },
  externalImagePlaceholderText: { color: palette.ink, fontSize: 12 },
  externalSource: { color: palette.ink, fontSize: 11 },
  externalTitle: { color: palette.ink, fontSize: 14, fontWeight: '700' },
  externalActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 18, marginTop: 8 },
  externalLink: { color: palette.ink, textDecorationLine: 'underline', fontWeight: '700', paddingVertical: 8 },
  deleteButton: { flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-end', gap: 5, padding: 8 },
  deleteText: { color: '#9a2637', fontSize: 12, fontWeight: '700' },
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
