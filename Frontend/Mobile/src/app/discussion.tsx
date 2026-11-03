import { useCallback, useEffect, useRef, useState } from 'react';
import { useFocusEffect, useLocalSearchParams } from 'expo-router';
import { View, Text, StyleSheet, ScrollView, Pressable, TextInput, Alert } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { HeaderBar } from '@/components/ui';
import { palette } from '@/theme/theme';
import { useLanguage } from '@/i18n/LanguageProvider';
import { getResponseLanguage, sendMessageToAI, translateAnswer, startPrecompute, type ResponseLanguage, type Corroboration } from '@/services/mockData';
import { LanguageSelector } from '@/components/LanguageSelector';
import { CredibilityForm } from '@/components/CredibilityForm';

export default function DiscussionScreen() {
  const { t } = useLanguage();
  const params = useLocalSearchParams<{ question?: string; analyze?: string; article_url?: string }>();
  const { bottom } = useSafeAreaInsets();
  const [text, setText] = useState(typeof params.question === 'string' ? params.question.slice(0, 2000) : '');
  const [answer, setAnswer] = useState('');
  const [original, setOriginal] = useState('');
  const [question, setQuestion] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [language, setLanguage] = useState<ResponseLanguage>('auto');
  const [loadingLanguage, setLoadingLanguage] = useState(true);
  const [busy, setBusy] = useState(false);
  const [translated, setTranslated] = useState(false);
  const [status, setStatus] = useState('');
  const [statistics, setStatistics] = useState<Corroboration | null>(null);
  const [analysisVersion, setAnalysisVersion] = useState(0);
  const analyzedQuestion = useRef('');
  const [statisticsProvisional, setStatisticsProvisional] = useState(false);
  useEffect(() => {
    if (params.analyze === '1' && typeof params.article_url === 'string') {
      void startPrecompute(params.article_url).catch(() => {});
    }
  }, [params.analyze, params.article_url]);

  useFocusEffect(useCallback(() => {
    let active = true;
    setLoadingLanguage(true);
    getResponseLanguage().then((value) => { if (active) setLanguage(value); })
      .catch((error) => { if (active) setStatus(error instanceof Error ? error.message : t('aiLanguageUnavailable')); })
      .finally(() => { if (active) setLoadingLanguage(false); });
    return () => { active = false; };
  }, [t]));

  useEffect(() => {
    const submitted = typeof params.question === 'string' ? params.question.slice(0, 2000) : '';
    if (loadingLanguage || params.analyze !== '1' || !submitted || analyzedQuestion.current === submitted) return;
    let active = true;
    Promise.resolve().then(async () => {
      if (!active) return;
      analyzedQuestion.current = submitted;
      setBusy(true);
      setStatus('');
      try {
        const result = await sendMessageToAI(submitted, language);
        if (!active) return;
        setAnswer(result.summary);
        setStatistics(null);
        setAnalysisVersion((value) => value + 1);
        setOriginal(result.summary);
        setSources(result.sources);
        setQuestion(submitted);
        setTranslated(false);
        setText('');
      } catch (error) {
        if (active) setStatus(error instanceof Error ? error.message : t('verificationFailed'));
      } finally {
        if (active) setBusy(false);
      }
    });
    return () => { active = false; };
  }, [params.question, params.analyze, loadingLanguage, language, t]);

  async function send() {
    if (busy || loadingLanguage || text.trim().length < 3) return;
    const submitted = text.trim();
    setBusy(true);
    setStatus('');
    try {
      const result = await sendMessageToAI(submitted, language);
      setAnswer(result.summary);
      setStatistics(null);
      setAnalysisVersion((value) => value + 1);
      setOriginal(result.summary);
      setSources(result.sources);
      setQuestion(submitted);
      setTranslated(false);
      setText('');
    } catch (error) {
      Alert.alert(t('verificationFailed'), error instanceof Error ? error.message : t('unexpectedError'));
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
      setStatus(t('aiTranslationNotice'));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : t('aiTranslationUnavailable'));
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
          <View style={styles.aiBubble}><Text style={styles.bubbleText}>{t('aiGreeting')}</Text></View>
        </View>

        {question ? <View style={styles.userRow}><View style={styles.userBubble}><Text style={styles.userText}>{question}</Text></View></View> : null}

        <View style={styles.resultCard}>
          <View style={styles.resultTop}>
            <View style={styles.resultTextWrap}>
              <Text style={styles.resultTitle}>{t('aiPreAnalysis')}</Text>
              {answer ? <View accessibilityLiveRegion="polite" style={styles.statistics}>
                <Text style={styles.resultTitle}>{statisticsProvisional ? 'Statistique IA provisoire' : 'Statistique de corroboration'}</Text>
                <Text style={styles.resultSummary}>{statistics?.corroboration_percent == null
                  ? 'Preuves insuffisantes — renseignez les sources ci-dessous.'
                  : `${statistics.corroboration_percent} % des groupes conclusifs confirment l’affirmation.`}</Text>
                {statistics ? <Text style={styles.source}>{statistics.supports} confirme(nt) · {statistics.contradicts} contredit(sent) · {statistics.inconclusive} non concluant(s)</Text> : null}
              </View> : null}
              <Text selectable style={styles.resultSummary}>{answer || t('sendMessageToVerify')}</Text>
            </View>
          </View>
          {sources.map((source, index) => <Text selectable key={`${index}-${source}`} style={styles.source}>{source}</Text>)}
          {answer && !sources.length ? <Text style={styles.source}>{t('aiNoSources')}</Text> : null}
          {original ? <View style={styles.translationActions}>
            <Pressable accessibilityRole="button" disabled={busy} onPress={() => void translate('mg')} style={styles.translationButton}><Text style={styles.bubbleText}>Adika amin’ny teny malagasy</Text></Pressable>
            <Pressable accessibilityRole="button" disabled={busy} onPress={() => void translate('fr')} style={styles.translationButton}><Text style={styles.bubbleText}>{t('aiTranslateFrench')}</Text></Pressable>
            {translated ? <Pressable accessibilityRole="button" disabled={busy} onPress={() => { setAnswer(original); setTranslated(false); setStatus(''); }} style={styles.translationButton}><Text style={styles.bubbleText}>{t('aiViewOriginal')}</Text></Pressable> : null}
          </View> : null}
          {busy ? <Text accessibilityLiveRegion="polite" style={styles.source}>{t('aiWorking')}</Text> : null}
          {status ? <Text accessibilityLiveRegion="polite" style={styles.source}>{status}</Text> : null}
        </View>
        {answer ? <CredibilityForm key={`${analysisVersion}-${question}`} articleUrl={params.analyze === '1' && question === params.question ? params.article_url : undefined} onResultChange={(value, provisional) => { setStatistics(value); setStatisticsProvisional(!!provisional); }} /> : null}
      </ScrollView>

      <View style={[styles.inputBar, { bottom: Math.max(bottom, 12) + 8 }]}>
        <TextInput value={text} onChangeText={setText} maxLength={2000} editable={!busy} placeholder={t('writeMessage')} placeholderTextColor="rgba(255,255,255,0.55)" style={styles.input} />
        <Pressable
          style={styles.sendButton}
          accessibilityRole="button" accessibilityLabel={t('aiSend')}
          disabled={busy || loadingLanguage || text.trim().length < 3}
          onPress={() => void send()}
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
  statistics: { marginTop: 14, padding: 10, borderWidth: 1, borderColor: palette.mint, borderRadius: 10 },
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
