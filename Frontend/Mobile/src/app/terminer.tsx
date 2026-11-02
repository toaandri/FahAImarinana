import { useState } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { HeaderBar, BottomTabs } from '@/components/ui';
import { palette } from '@/theme/theme';

export default function TerminerScreen() {
  const [reading, setReading] = useState(false);

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar showBack />
      <View style={styles.readerCard}>
        <Text style={styles.status}>TERMINÉ</Text>
        <Text style={styles.duration}>02:12</Text>
        <Pressable style={styles.playButton} onPress={() => setReading((v) => !v)}>
          <Ionicons name={reading ? 'pause' : 'play'} size={28} color="#0B2B2B" />
        </Pressable>
        <View style={styles.progressBar}><View style={styles.progressFill} /></View>
      </View>

      <View style={styles.articleCard}>
        <Text style={styles.articleTag}>Article</Text>
        <Text style={styles.label}>TITRE :</Text>
        <Text style={styles.title}>Titre généré par l&apos;IA</Text>
        <Text style={styles.body}>Premier paragraphe de l&apos;article généré pendant le reportage.</Text>
        <Text style={styles.body}>Deuxième paragraphe de l&apos;article.</Text>
      </View>

      <View style={styles.summaryCard}>
        <View style={styles.summaryRow}><Text style={styles.summaryTitle}>Résumé de l&apos;article</Text><Text style={styles.percent}>78%</Text></View>
        <Text style={styles.summaryText}>Résumé en deux ou trois lignes généré par l&apos;IA à la fin de la vidéo.</Text>
        <View style={styles.actionRow}><Pressable style={styles.secondaryButton}><Text style={styles.secondaryText}>Modifier</Text></Pressable><Pressable style={styles.primaryButton}><Text style={styles.primaryText}>PUBLIER</Text></Pressable></View>
      </View>
      <BottomTabs active="home" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  readerCard: { margin: 16, backgroundColor: 'rgba(255,255,255,0.07)', borderRadius: 18, padding: 14 },
  status: { alignSelf: 'flex-start', backgroundColor: 'rgba(0,255,200,0.15)', borderRadius: 12, paddingHorizontal: 10, paddingVertical: 6, color: palette.mint, fontFamily: 'Montserrat_700Bold_Italic', fontSize: 10 },
  duration: { position: 'absolute', right: 14, top: 14, color: '#fff', fontFamily: 'Montserrat_700Bold_Italic', fontSize: 12 },
  playButton: { width: 64, height: 64, borderRadius: 32, backgroundColor: palette.mint, alignSelf: 'center', marginTop: 20, alignItems: 'center', justifyContent: 'center' },
  progressBar: { height: 10, borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.1)', overflow: 'hidden', marginTop: 18 },
  progressFill: { width: '62%', height: '100%', backgroundColor: palette.mint },
  articleCard: { marginHorizontal: 16, backgroundColor: 'rgba(255,255,255,0.07)', padding: 16, borderRadius: 18 },
  articleTag: { alignSelf: 'flex-start', backgroundColor: 'rgba(255,255,255,0.06)', borderRadius: 12, paddingHorizontal: 12, paddingVertical: 6, color: '#fff', fontFamily: 'Montserrat_600SemiBold_Italic', fontSize: 10 },
  label: { color: palette.mint, fontFamily: 'Montserrat_700Bold_Italic', marginTop: 10 },
  title: { color: '#fff', fontSize: 18, fontFamily: 'Montserrat_700Bold_Italic', marginTop: 4 },
  body: { color: '#fff', marginTop: 8, fontFamily: 'Montserrat_600SemiBold_Italic', fontSize: 11, lineHeight: 18 },
  summaryCard: { marginHorizontal: 16, marginTop: 18, backgroundColor: 'rgba(255,255,255,0.07)', borderRadius: 18, padding: 16 },
  summaryRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  summaryTitle: { color: palette.mint, fontFamily: 'Montserrat_700Bold_Italic', fontSize: 16 },
  percent: { color: '#fff', fontFamily: 'Montserrat_700Bold_Italic', fontSize: 12 },
  summaryText: { color: '#fff', marginTop: 12, fontFamily: 'Montserrat_600SemiBold_Italic', fontSize: 11, lineHeight: 18 },
  actionRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 18 },
  secondaryButton: { flex: 1, borderWidth: 1, borderColor: 'rgba(255,255,255,0.3)', borderRadius: 12, paddingVertical: 12, alignItems: 'center', marginRight: 8 },
  secondaryText: { color: '#fff', fontFamily: 'Montserrat_700Bold_Italic' },
  primaryButton: { flex: 1, backgroundColor: palette.mint, borderRadius: 12, paddingVertical: 12, alignItems: 'center', marginLeft: 8 },
  primaryText: { color: '#0B2B2B', fontFamily: 'Montserrat_700Bold_Italic' },
});
