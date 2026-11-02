import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { HeaderBar, BottomTabs, TagChip, GlassCard } from '@/components/ui';
import { getNewsList } from '@/services/mockData';
import { palette } from '@/theme/theme';

export default function ActualitesScreen() {
  const [filter, setFilter] = useState('Tous');
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    getNewsList(filter).then(setItems);
  }, [filter]);

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar />
      <View style={styles.filtersWrap}>
        {['Tous', 'Vérifiés', 'Politique', 'Sport'].map((item) => (
          <Pressable key={item} onPress={() => setFilter(item)}>
            <TagChip label={item} active={filter === item} small />
          </Pressable>
        ))}
      </View>

      <ScrollView contentContainerStyle={styles.listWrap}>
        {items.map((item) => (
          <Pressable key={item.id} onPress={() => router.push('/discussion' as any)} style={styles.itemRow}>
            <View style={styles.itemTextWrap}>
              <Text style={styles.source}>{item.source}</Text>
              <Text style={styles.title}>{item.title}</Text>
            </View>
            {item.image ? <Image source={{ uri: item.image }} style={styles.thumb} /> : <View style={styles.thumbPlaceholder} />}
          </Pressable>
        ))}
      </ScrollView>
      <BottomTabs active="actus" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  filtersWrap: { flexDirection: 'row', paddingHorizontal: 16, paddingVertical: 16, gap: 8 },
  listWrap: { paddingHorizontal: 16, paddingBottom: 120 },
  itemRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.12)' },
  itemTextWrap: { flex: 1, marginRight: 10 },
  source: { color: '#fff', fontSize: 11, fontFamily: 'Montserrat_600SemiBold_Italic', marginBottom: 6 },
  title: { color: '#fff', fontSize: 13, fontFamily: 'Montserrat_700Bold_Italic', lineHeight: 18 },
  thumb: { width: 80, height: 80, borderRadius: 12 },
  thumbPlaceholder: { width: 80, height: 80, borderRadius: 12, backgroundColor: 'rgba(255,255,255,0.1)' },
});
