import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { View, Text, StyleSheet, ScrollView, Pressable, TextInput, Alert } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { HeaderBar } from '@/components/ui';
import { palette } from '@/theme/theme';
<<<<<<< Updated upstream
import { sendMessageToAI } from '@/services/mockData';
import { useLanguage } from '@/i18n/LanguageProvider';
=======
import { getResponseLanguage, sendMessageToAI, translateAnswer, type ResponseLanguage } from '@/services/mockData';
import { LanguageSelector } from '@/components/LanguageSelector';
>>>>>>> Stashed changes

export default function DiscussionScreen() {
  const { t } = useLanguage();
  const { bottom } = useSafeAreaInsets();
  const [text, setText] = useState('');
  const [answer, setAnswer] = useState('');
  const [original, setOriginal] = useState('');
  const [question, setQuestion] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [language, setLanguage] = useState<ResponseLanguage>('auto');
  const [loadingLanguage, setLoadingLanguage] = useState(true);
  const [busy, setBusy] = useState(false);
  const [translated, setTranslated] = useState(false);
  const [status, setStatus] = useState('');

  useFocusEffect(useCallback(() => {
    let active = true;
    setLoadingLanguage(true);
    getResponseLanguage().then((value) => { if (active) setLanguage(value); })
      .catch((error) => { if (active) setStatus(error instanceof Error ? error.message : 'Préférence indisponible.'); })
      .finally(() => { if (active) setLoadingLanguage(false); });
    return () => { active = false; };
  }, []));

  async function send() {
    if (busy || loadingLanguage || text.trim().length < 3) return;
    const submitted = text.trim();
    setBusy(true);
    setStatus('');
    try {
      const result = await sendMessageToAI(submitted, language);
      setAnswer(result.summary);
      setOriginal(result.summary);
      setSources(result.sources);
      setQuestion(submitted);
      setTranslated(false);
      setText('');
    } catch (error) {
      Alert.alert('Vérification impossible', error instanceof Error ? error.message : 'Une erreur est survenue.');
    } finally {
      setBusy(false);
    }
  }

  async function translate(target: 'fr' | 'mg') {
    if (busy || !original) return;
    setBusy(true);
    setStatus('');
    try {
      const result = await translateAnswer(original, target);
      setAnswer(result.text);
      setTranslated(true);
      setStatus('Traduction automatique à relire. / Dikanteny mandeha ho azy, mila averina vakina.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Traduction indisponible.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar showBack />
      <ScrollView contentContainerStyle={styles.content}>
        <LanguageSelector value={language} onChange={setLanguage} disabled={busy || loadingLanguage} />
        <View style={styles.messageRow}>
          <Text style={styles.avatar}>AI</Text>
<<<<<<< Updated upstream
          <View style={styles.aiBubble}><Text style={styles.bubbleText}>{t('helloAI')}</Text></View>
        </View>

        <View style={styles.mediaRow}>
          <View style={styles.mediaThumb}><Ionicons name="image-outline" size={24} color="#fff" /></View>
          <View style={styles.mediaThumb}><Ionicons name="play" size={20} color="#fff" /><Text style={styles.time}>0:24</Text></View>
        </View>

        <View style={styles.userRow}><View style={styles.userBubble}><Text style={styles.userText}>{t('userMessage')}</Text></View></View>
=======
          <View style={styles.aiBubble}><Text style={styles.bubbleText}>{language === 'mg' ? 'Salama! Alefaso ny fanontanianao, hanampy anao hanamarina ny vaovao aho.' : 'Bonjour ! Posez une question pour préparer votre vérification journalistique.'}</Text></View>
        </View>

        {question ? <View style={styles.userRow}><View style={styles.userBubble}><Text style={styles.userText}>{question}</Text></View></View> : null}
>>>>>>> Stashed changes

        <View style={styles.resultCard}>
          <View style={styles.resultTop}>
            <View style={styles.resultTextWrap}>
<<<<<<< Updated upstream
              <Text style={styles.resultTitle}>{t('averageCredibility')}</Text>
              <Text style={styles.resultSummary}>{answer || t('sendMessageToVerify')}</Text>
=======
              <Text style={styles.resultTitle}>{language === 'mg' ? 'Valin’ny IA — mbola mila hamarinina' : 'Pré-analyse IA — à vérifier'}</Text>
              <Text selectable style={styles.resultSummary}>{answer || 'Envoyez un message / Alefaso ny fanontanianao.'}</Text>
>>>>>>> Stashed changes
            </View>
          </View>
          {sources.map((source, index) => <Text selectable key={`${index}-${source}`} style={styles.source}>{source}</Text>)}
          {answer && !sources.length ? <Text style={styles.source}>Aucune source retournée / Tsy nisy loharano nomena.</Text> : null}
          {original ? <View style={styles.translationActions}>
            <Pressable accessibilityRole="button" disabled={busy} onPress={() => void translate('mg')} style={styles.translationButton}><Text style={styles.bubbleText}>Adika amin’ny teny malagasy</Text></Pressable>
            <Pressable accessibilityRole="button" disabled={busy} onPress={() => void translate('fr')} style={styles.translationButton}><Text style={styles.bubbleText}>Traduire en français</Text></Pressable>
            {translated ? <Pressable accessibilityRole="button" disabled={busy} onPress={() => { setAnswer(original); setTranslated(false); setStatus(''); }} style={styles.translationButton}><Text style={styles.bubbleText}>Voir l’original / Teny niandohana</Text></Pressable> : null}
          </View> : null}
          {busy ? <Text accessibilityLiveRegion="polite" style={styles.source}>En cours… / Eo am-pikarakarana…</Text> : null}
          {status ? <Text accessibilityLiveRegion="polite" style={styles.source}>{status}</Text> : null}
        </View>
      </ScrollView>

      <View style={[styles.inputBar, { bottom: Math.max(bottom, 12) + 8 }]}>
<<<<<<< Updated upstream
        <View style={styles.inputActions}><Ionicons name="image-outline" size={18} color="#fff" /><Ionicons name="videocam-outline" size={18} color="#fff" /></View>
        <TextInput value={text} onChangeText={setText} placeholder={t('writeMessage')} placeholderTextColor="rgba(255,255,255,0.55)" style={styles.input} />
        <Pressable
          style={styles.sendButton}
          onPress={async () => {
            if (!text.trim()) return;
            try {
              const result = await sendMessageToAI(text.trim());
              setAnswer(result.summary);
              setText('');
            } catch (error) {
              Alert.alert(t('verificationFailed'), error instanceof Error ? error.message : t('unexpectedError'));
            }
          }}
=======
        <TextInput value={text} onChangeText={setText} maxLength={2000} editable={!busy} placeholder={language === 'mg' ? 'Soraty eto ny fanontanianao…' : 'Écrire un message…'} placeholderTextColor="rgba(255,255,255,0.55)" style={styles.input} />
        <Pressable
          style={styles.sendButton}
          accessibilityRole="button" accessibilityLabel="Envoyer / Alefa"
          disabled={busy || loadingLanguage || text.trim().length < 3}
          onPress={() => void send()}
>>>>>>> Stashed changes
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
  source: { color: palette.mint, fontSize: 12, lineHeight: 18, marginTop: 10 },
  translationActions: { gap: 8, marginTop: 12 },
  translationButton: { minHeight: 44, borderWidth: 1, borderColor: palette.mint, borderRadius: 10, justifyContent: 'center', padding: 10 },
  tagRow: { flexDirection: 'row', marginTop: 12 },
  tag: { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 12, paddingHorizontal: 10, paddingVertical: 6, color: '#fff', marginRight: 8, fontSize: 10, fontFamily: 'Montserrat_600SemiBold_Italic' },
  inputBar: { position: 'absolute', left: 16, right: 16, backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: 18, paddingHorizontal: 12, paddingVertical: 10, flexDirection: 'row', alignItems: 'center' },
  inputActions: { flexDirection: 'row', gap: 10, marginRight: 8 },
  input: { flex: 1, color: '#fff', fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic' },
  sendButton: { width: 34, height: 34, borderRadius: 17, backgroundColor: palette.mint, alignItems: 'center', justifyContent: 'center', marginLeft: 8 },
});
