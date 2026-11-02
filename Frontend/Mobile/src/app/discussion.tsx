import { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, TextInput, Alert } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { HeaderBar, CredibilityRing } from '@/components/ui';
import { palette } from '@/theme/theme';
import { sendMessageToAI } from '@/services/mockData';

export default function DiscussionScreen() {
  const { bottom } = useSafeAreaInsets();
  const [text, setText] = useState('');
  const [answer, setAnswer] = useState('');

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar showBack />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.messageRow}>
          <Text style={styles.avatar}>AI</Text>
          <View style={styles.aiBubble}><Text style={styles.bubbleText}>Bonjour ! Envoyez-moi un texte, une photo ou une vidéo : je vérifie l’information.</Text></View>
        </View>

        <View style={styles.mediaRow}>
          <View style={styles.mediaThumb}><Ionicons name="image-outline" size={24} color="#fff" /></View>
          <View style={styles.mediaThumb}><Ionicons name="play" size={20} color="#fff" /><Text style={styles.time}>0:24</Text></View>
        </View>

        <View style={styles.userRow}><View style={styles.userBubble}><Text style={styles.userText}>Message de l’utilisateur</Text></View></View>

        <View style={styles.resultCard}>
          <View style={styles.resultTop}>
            <CredibilityRing value={72} size={62} />
            <View style={styles.resultTextWrap}>
              <Text style={styles.resultTitle}>Crédibilité moyenne</Text>
              <Text style={styles.resultSummary}>{answer || 'Envoyez un message pour lancer la vérification.'}</Text>
            </View>
          </View>
          <View style={styles.tagRow}><Text style={styles.tag}>Source 1</Text><Text style={styles.tag}>Source 2</Text></View>
        </View>
      </ScrollView>

      <View style={[styles.inputBar, { bottom: Math.max(bottom, 12) + 8 }]}>
        <View style={styles.inputActions}><Ionicons name="image-outline" size={18} color="#fff" /><Ionicons name="videocam-outline" size={18} color="#fff" /></View>
        <TextInput value={text} onChangeText={setText} placeholder="Écrire un message..." placeholderTextColor="rgba(255,255,255,0.55)" style={styles.input} />
        <Pressable
          style={styles.sendButton}
          onPress={async () => {
            if (!text.trim()) return;
            try {
              const result = await sendMessageToAI(text.trim());
              setAnswer(result.summary);
              setText('');
            } catch (error) {
              Alert.alert('Vérification impossible', error instanceof Error ? error.message : 'Une erreur est survenue.');
            }
          }}
        ><Ionicons name="send" size={16} color="#0B2B2B" /></Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  content: { padding: 16, paddingBottom: 108 },
  messageRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 14 },
  avatar: { width: 32, height: 32, borderRadius: 16, backgroundColor: palette.mint, color: '#0b2b2b', textAlign: 'center', textAlignVertical: 'center', fontWeight: '800', fontFamily: 'Montserrat_700Bold_Italic', marginRight: 8 },
  aiBubble: { backgroundColor: 'rgba(255,255,255,0.06)', borderRadius: 14, padding: 12, maxWidth: '78%' },
  bubbleText: { color: '#fff', fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic', lineHeight: 18 },
  mediaRow: { flexDirection: 'row', justifyContent: 'flex-end', marginBottom: 10 },
  mediaThumb: { width: 98, height: 86, borderRadius: 12, backgroundColor: 'rgba(255,255,255,0.08)', marginLeft: 10, alignItems: 'center', justifyContent: 'center' },
  time: { position: 'absolute', right: 8, bottom: 8, color: '#fff', fontSize: 10 },
  userRow: { alignItems: 'flex-end', marginBottom: 16 },
  userBubble: { backgroundColor: palette.mint, borderRadius: 14, padding: 12, maxWidth: '80%' },
  userText: { color: '#0B2B2B', fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic' },
  resultCard: { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 18, padding: 14 },
  resultTop: { flexDirection: 'row', alignItems: 'center' },
  resultTextWrap: { flex: 1, marginLeft: 14 },
  resultTitle: { color: palette.mint, fontSize: 16, fontFamily: 'Montserrat_700Bold_Italic' },
  resultSummary: { color: '#fff', fontSize: 11, marginTop: 8, fontFamily: 'Montserrat_600SemiBold_Italic', lineHeight: 18 },
  tagRow: { flexDirection: 'row', marginTop: 12 },
  tag: { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 12, paddingHorizontal: 10, paddingVertical: 6, color: '#fff', marginRight: 8, fontSize: 10, fontFamily: 'Montserrat_600SemiBold_Italic' },
  inputBar: { position: 'absolute', left: 16, right: 16, backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: 18, paddingHorizontal: 12, paddingVertical: 10, flexDirection: 'row', alignItems: 'center' },
  inputActions: { flexDirection: 'row', gap: 10, marginRight: 8 },
  input: { flex: 1, color: '#fff', fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic' },
  sendButton: { width: 34, height: 34, borderRadius: 17, backgroundColor: palette.mint, alignItems: 'center', justifyContent: 'center', marginLeft: 8 },
});
