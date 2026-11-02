import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { HeaderBar, GlassCard, BottomTabs, StoryCard } from '@/components/ui';
import { getLatestNews, type NewsItem } from '@/services/mockData';
import { palette } from '@/theme/theme';

export default function HomeScreen() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    getLatestNews().then((news) => {
      setItems(news);
      setActiveIndex(0);
    });
  }, []);

  useEffect(() => {
    if (items.length < 2) return undefined;

    const timer = setTimeout(() => {
      setActiveIndex((index) => (index + 1) % items.length);
    }, 20_000);

    return () => clearTimeout(timer);
  }, [activeIndex, items.length]);

  const activeItem = items[activeIndex];

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar />
      <ScrollView contentContainerStyle={styles.content}>
        <StoryCard
          title={activeItem?.title ?? 'Jeux Olympiques de la Jeunesse 2026'}
          source={activeItem?.source ?? '2424.mg'}
          credibility={activeItem?.credibility ?? 85}
          image={activeItem?.image}
          onPress={() => router.push('/discussion' as any)}
        />
        {items.length > 1 ? (
          <View style={styles.carouselIndicators} accessibilityRole="tablist">
            {items.map((item, index) => (
              <Pressable
                key={item.id}
                accessibilityRole="tab"
                accessibilityLabel={`Information ${index + 1} sur ${items.length}`}
                accessibilityState={{ selected: index === activeIndex }}
                onPress={() => setActiveIndex(index)}
                style={[styles.carouselDot, index === activeIndex && styles.carouselDotActive]}
              />
            ))}
          </View>
        ) : null}

        <GlassCard style={styles.talkCard}>
          <View style={styles.talkRow}>
            <Text style={styles.bigText}>Discuter{"\n"}et vérifier vos informations</Text>
            <View style={styles.logoMiniWrap}><Text style={styles.logoMini}>FAH</Text><Text style={styles.aiMini}>AI</Text><Text style={styles.logoMini}>MARINANA</Text></View>
          </View>
          <Pressable style={styles.parlerButton} onPress={() => router.push('/discussion' as any)}>
            <Text style={styles.parlerText}>Parler</Text>
          </Pressable>
        </GlassCard>

        <GlassCard style={styles.reportCard}>
          <Text style={styles.reportTitle}>Reportage</Text>
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
