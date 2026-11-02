import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { HeaderBar, GlassCard, BottomTabs, StoryCard } from '@/components/ui';
import { getLatestNews } from '@/services/mockData';
import { palette } from '@/theme/theme';

export default function HomeScreen() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    getLatestNews().then(setItems);
  }, []);

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar />
      <ScrollView contentContainerStyle={styles.content}>
        <StoryCard
          title={items[0]?.title ?? 'Jeux Olympiques de la Jeunesse 2026'}
          source={items[0]?.source ?? '2424.mg'}
          credibility={items[0]?.credibility ?? 85}
          image={items[0]?.image}
          onPress={() => router.push('/discussion' as any)}
        />

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
