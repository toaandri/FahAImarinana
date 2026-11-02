import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Camera } from 'expo-camera';
import { router } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { HeaderBar, BottomTabs } from '@/components/ui';
import { palette } from '@/theme/theme';

export default function DirectScreen() {
  const [permission, setPermission] = useState<boolean | null>(null);

  useEffect(() => {
    Camera.requestCameraPermissionsAsync().then(({ status }) => setPermission(status === 'granted'));
  }, []);

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar showBack />
      <View style={styles.videoCard}>
        <View style={styles.liveBadge}>● DIRECT</View>
        <Text style={styles.timer}>00:42</Text>
        {permission ? <View style={styles.cameraFrame}><Text style={styles.frameText}>Caméra</Text></View> : <View style={styles.cameraFrame}><Text style={styles.frameText}>Accès caméra</Text></View>}
        <View style={styles.controlsRow}>
          <Pressable style={styles.smallButton}><Ionicons name="mic-outline" size={22} color="#fff" /></Pressable>
          <Pressable style={styles.stopButton} onPress={() => router.push('/terminer' as any)}><View style={styles.stopInner} /></Pressable>
          <Pressable style={styles.smallButton}><Ionicons name="camera-reverse-outline" size={22} color="#fff" /></Pressable>
        </View>
      </View>

      <View style={styles.articleCard}>
        <View style={styles.articleHeader}><Text style={styles.articleTag}>Article en direct</Text><Text style={styles.aiText}><Text style={styles.dot} /> L'IA analyse...</Text></View>
        <Text style={styles.label}>TITRE :</Text>
        <Text style={styles.title}>Titre généré par l'IA</Text>
        <Text style={styles.line}>00:08 · Phrase générée à partir de la vidéo</Text>
        <Text style={styles.line}>00:15 · Phrase générée à partir de la vidéo</Text>
        <Text style={styles.line}>00:18 · Phrase en cours d'écriture</Text>
      </View>

      <View style={styles.lockCard}><Ionicons name="lock-closed-outline" size={18} color="#fff" /><Text style={styles.lockText}>Résumé de l'article disponible à la fin du reportage</Text></View>
      <BottomTabs active="home" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  videoCard: { margin: 16, backgroundColor: 'rgba(255,255,255,0.07)', borderRadius: 20, padding: 14, minHeight: 260 },
  liveBadge: { position: 'absolute', left: 14, top: 14, backgroundColor: '#0d2a32', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12, color: palette.mint, fontFamily: 'Montserrat_700Bold_Italic', fontSize: 10 },
  timer: { position: 'absolute', right: 14, top: 14, color: '#fff', fontFamily: 'Montserrat_700Bold_Italic', fontSize: 12 },
  cameraFrame: { marginTop: 46, height: 150, borderRadius: 18, borderWidth: 2, borderColor: palette.mint, justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.18)' },
  frameText: { color: '#fff', fontFamily: 'Montserrat_600SemiBold_Italic' },
  controlsRow: { marginTop: 18, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  smallButton: { width: 46, height: 46, borderRadius: 23, backgroundColor: 'rgba(255,255,255,0.08)', alignItems: 'center', justifyContent: 'center' },
  stopButton: { width: 64, height: 64, borderRadius: 32, backgroundColor: '#1A2C32', borderWidth: 2, borderColor: palette.mint, alignItems: 'center', justifyContent: 'center' },
  stopInner: { width: 20, height: 20, backgroundColor: palette.mint, borderRadius: 4 },
  articleCard: { marginHorizontal: 16, backgroundColor: 'rgba(255,255,255,0.07)', borderRadius: 18, padding: 14 },
  articleHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  articleTag: { backgroundColor: 'rgba(255,255,255,0.07)', borderRadius: 12, paddingHorizontal: 8, paddingVertical: 6, fontFamily: 'Montserrat_600SemiBold_Italic', color: '#fff', fontSize: 10 },
  aiText: { color: '#fff', fontSize: 10, fontFamily: 'Montserrat_600SemiBold_Italic' },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: palette.mint },
  label: { color: palette.mint, fontFamily: 'Montserrat_700Bold_Italic', marginTop: 10 },
  title: { color: '#fff', fontSize: 18, fontFamily: 'Montserrat_700Bold_Italic', marginTop: 4 },
  line: { color: '#fff', fontSize: 11, marginTop: 6, fontFamily: 'Montserrat_600SemiBold_Italic' },
  lockCard: { marginHorizontal: 16, marginTop: 18, flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 14, padding: 12 },
  lockText: { color: '#fff', marginLeft: 10, fontFamily: 'Montserrat_600SemiBold_Italic', fontSize: 11 },
});
