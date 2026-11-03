import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { HeaderBar, BottomTabs, TagChip } from '@/components/ui';
import { getNewsList } from '@/services/mockData';
import { palette } from '@/theme/theme';
import { useLanguage } from '@/i18n/LanguageProvider';

export default function ActualitesScreen() {
  const { t } = useLanguage();
  const [filter, setFilter] = useState('Tous');
  const [items, setItems] = useState<any[]>([]);
  const [unavailable, setUnavailable] = useState(false);
  const filters = [
    { value: 'Tous', key: 'all' },
    { value: 'Vérifiés', key: 'verified' },
    { value: 'Politique', key: 'politics' },
    { value: 'Sport', key: 'sport' },
  ] as const;

  useEffect(() => {
    getNewsList(filter).then(setItems).catch(() => {
      setItems([]);
      setUnavailable(true);
    });
  }, [filter]);

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
  screen: { flex: 1, backgroundColor: palette.background },
  filtersWrap: { flexDirection: 'row', paddingHorizontal: 16, paddingVertical: 16, gap: 8 },
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
