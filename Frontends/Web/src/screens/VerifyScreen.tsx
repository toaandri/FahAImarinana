import * as ImagePicker from 'expo-image-picker';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useFocusEffect, useLocalSearchParams } from 'expo-router';
import { Image, StyleSheet, Text, TextInput, View } from 'react-native';
import { AppShell, Card, Icon, InteractivePressable, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';
import { LanguageSelector } from '../components/LanguageSelector';
import { CredibilityForm } from '../components/CredibilityForm';
import { getResponseLanguage, sendMessageToAI, translateAnswer, type ResearchResult, startPrecompute, type ResponseLanguage, type Corroboration } from '../services/api';
import { useI18n } from '../components/i18n';

type Attachment = { uri: string; name: string; type: 'image' | 'video' };

export default function VerifyScreen() {
  const params = useLocalSearchParams<{ question?: string; analyze?: string; article_url?: string }>();
  const { t } = useI18n();
  const [message, setMessage] = useState(typeof params.question === 'string' ? params.question.slice(0, 2000) : '');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [status, setStatus] = useState('');
  const [language, setLanguage] = useState<ResponseLanguage>('auto');
  const [loadingLanguage, setLoadingLanguage] = useState(true);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [question, setQuestion] = useState('');
  const [translation, setTranslation] = useState<string | null>(null);
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
      .catch((error) => { if (active) setStatus(error instanceof Error ? error.message : t('verify.aiLanguageUnavailable')); })
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
        const answer = await sendMessageToAI(submitted, language);
        if (!active) return;
        setResult(answer);
        setStatistics(null);
        setAnalysisVersion((value) => value + 1);
        setQuestion(submitted);
        setTranslation(null);
        setMessage('');
      } catch (error) {
        if (active) setStatus(error instanceof Error ? error.message : t('verify.analysisUnavailable'));
      } finally {
        if (active) setBusy(false);
      }
    });
    return () => { active = false; };
  }, [params.question, params.analyze, loadingLanguage, language, t]);

  const pickMedia = async (type: 'image' | 'video') => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        setStatus(t('verify.permission'));
        return;
      }
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: type === 'image' ? ['images'] : ['videos'],
        allowsEditing: false,
        quality: 1,
      });
      if (result.canceled) return;
      const asset = result.assets[0];
      setAttachments((current) => [
        ...current,
        { uri: asset.uri, name: asset.fileName ?? t(type === 'image' ? 'common.photo' : 'common.video'), type },
      ]);
      setStatus('');
    } catch (error) {
      console.error('Échec de la sélection du média.', error);
      setStatus(t('verify.pickError'));
    }
  };

  const sendMessage = async () => {
    if (busy || loadingLanguage) return;
    if (attachments.length) {
      setStatus(t('verify.attachmentsUnsupported'));
      return;
    }
    if (message.trim().length < 3) {
      setStatus(t('verify.questionRequired'));
      return;
    }
    const submitted = message.trim();
    setBusy(true);
    setStatus('');
    try {
      const answer = await sendMessageToAI(submitted, language);
      setResult(answer);
      setStatistics(null);
      setAnalysisVersion((value) => value + 1);
      setQuestion(submitted);
      setTranslation(null);
      setMessage('');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : t('verify.answerUnavailable'));
    } finally {
      setBusy(false);
    }
  };

  async function translate(target: 'fr' | 'mg') {
    if (!result || busy) return;
    setBusy(true);
    setStatus('');
    try {
      const translated = await translateAnswer(result.reponse, target);
      setTranslation(translated.text);
      setStatus(t('verify.translationNotice'));
    } catch (error) {
      setStatus(error instanceof Error ? error.message : t('verify.translationUnavailable'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell active="/verifier">
      <View style={styles.content}>
        <PageTitle>{t('verify.title')}</PageTitle>
        <LanguageSelector value={language} onChange={setLanguage} disabled={busy || loadingLanguage} />
        <View style={styles.conversation}>
          <View style={styles.aiMessage}>
            <Text style={styles.messageText}>
              {t('verify.greeting')}
            </Text>
          </View>
          {question ? <View style={styles.userMessage}>
            <Text style={styles.userMessageText}>{question}</Text>
          </View> : null}
          <Card style={styles.resultCard}>
            <Text style={styles.resultTitle}>{t('verify.preAnalysis')}</Text>
            {result ? <View accessibilityLiveRegion="polite" style={styles.statistics}>
              <Text style={styles.resultTitle}>{t(statisticsProvisional ? 'verify.provisional' : 'verify.corroboration')}</Text>
              <Text style={styles.resultText}>{statistics?.corroboration_percent == null
                ? t('verify.insufficient')
                : `${statistics.corroboration_percent}${t('verify.confirmPercent')}`}</Text>
              {statistics ? <Text style={styles.resultText}>{t('verify.evidenceCounts', {
                supports: statistics.supports,
                contradicts: statistics.contradicts,
                inconclusive: statistics.inconclusive,
              })}</Text> : null}
            </View> : null}
            <Text selectable style={styles.resultText}>
              {translation ?? result?.reponse ?? t('verify.sendPrompt')}
            </Text>
            <View style={styles.sources}>
              {result?.citations.map((source, index) => <Text selectable key={index} style={styles.source}>{[source.titre, source.url].filter(Boolean).join(' — ')}</Text>)}
              {result && !result.citations.length ? <Text style={styles.source}>{t('verify.noSources')}</Text> : null}
            </View>
            {result ? <View style={styles.translationActions}>
              <InteractivePressable accessibilityRole="button" disabled={busy} onPress={() => void translate('mg')} style={styles.translationButton}><Text style={styles.source}>{t('verify.translateMg')}</Text></InteractivePressable>
              <InteractivePressable accessibilityRole="button" disabled={busy} onPress={() => void translate('fr')} style={styles.translationButton}><Text style={styles.source}>{t('verify.translateFr')}</Text></InteractivePressable>
              {translation ? <InteractivePressable accessibilityRole="button" disabled={busy} onPress={() => { setTranslation(null); setStatus(''); }} style={styles.translationButton}><Text style={styles.source}>{t('verify.original')}</Text></InteractivePressable> : null}
            </View> : null}
            <Text style={styles.disclaimer}>
              {busy ? t('verify.working') : t('verify.disclaimer')}
            </Text>
          </Card>
          {result ? <CredibilityForm key={`${analysisVersion}-${question}`} articleUrl={params.analyze === '1' && question === params.question ? params.article_url : undefined} onResultChange={(value, provisional) => { setStatistics(value); setStatisticsProvisional(!!provisional); }} /> : null}
        </View>

        <View style={styles.composerArea}>
          {attachments.length ? (
            <View style={styles.attachments}>
              {attachments.map((item, index) => (
                <View style={styles.attachment} key={`${item.uri}-${index}`}>
                  {item.type === 'image' ? (
                    <Image source={{ uri: item.uri }} style={styles.attachmentImage} />
                  ) : (
                    <Icon name="video-outline" color={colors.accent} />
                  )}
                  <Text style={styles.attachmentName} numberOfLines={1}>{item.name}</Text>
                  <InteractivePressable
                    accessibilityRole="button"
                    accessibilityLabel={t('verify.removeAttachment', { name: item.name })}
                    onPress={() => {
                      setAttachments((current) => current.filter((_, i) => i !== index));
                      setStatus('');
                    }}
                    style={styles.removeAttachment}
                  >
                    <Icon name="close" size={18} />
                  </InteractivePressable>
                </View>
              ))}
            </View>
          ) : null}
          <View style={styles.composer}>
            <InteractivePressable
              accessibilityRole="button"
              accessibilityLabel={t('verify.attachPhoto')}
              onPress={() => void pickMedia('image')}
              style={styles.composerIcon}
            >
              <Icon name="image-outline" />
            </InteractivePressable>
            <InteractivePressable
              accessibilityRole="button"
              accessibilityLabel={t('verify.attachVideo')}
              onPress={() => void pickMedia('video')}
              style={styles.composerIcon}
            >
              <Icon name="video-outline" />
            </InteractivePressable>
            <TextInput
              accessibilityLabel={t('verify.writeMessage')}
              value={message}
              editable={!busy}
              maxLength={2000}
              onChangeText={(value) => {
                setMessage(value);
                setStatus('');
              }}
              placeholder={t('verify.placeholder')}
              placeholderTextColor={colors.muted}
              style={styles.composerInput}
              returnKeyType="send"
              onSubmitEditing={sendMessage}
            />
            <InteractivePressable
              accessibilityRole="button"
              accessibilityLabel={t('verify.sendMessage')}
              onPress={sendMessage}
              disabled={busy || loadingLanguage}
              style={({ pressed }) => [styles.sendButton, pressed && styles.pressed]}
            >
              <Icon name="send" color={colors.deep} />
            </InteractivePressable>
          </View>
          {status ? <Text style={styles.status} accessibilityRole="alert" accessibilityLiveRegion="polite">{status}</Text> : null}
        </View>
      </View>
    </AppShell>
  );
}

const styles = StyleSheet.create({
  content: { width: '100%', maxWidth: 880, alignSelf: 'center', flex: 1 },
  conversation: { gap: 20 },
  aiMessage: {
    minHeight: 100,
    padding: 20,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
  },
  messageText: { color: colors.white, fontSize: 16, lineHeight: 24 },
  sampleMedia: {
    alignSelf: 'flex-end',
    width: 300,
    maxWidth: '100%',
    minHeight: 88,
    backgroundColor: colors.deep,
    justifyContent: 'center',
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: colors.accent,
    borderTopRightRadius: 12,
    borderBottomRightRadius: 12,
  },
  sampleText: { color: colors.muted, fontWeight: '700' },
  userMessage: { alignSelf: 'flex-end', width: '96%', minHeight: 60, justifyContent: 'center', padding: 16, backgroundColor: colors.accent, borderRadius: 12 },
  userMessageText: { color: colors.deep, fontSize: 16, lineHeight: 24 },
  resultCard: { gap: 18 },
  resultTitle: { color: colors.white, fontSize: 17, lineHeight: 24, fontWeight: '700' },
  resultText: { color: colors.white, fontSize: 16, lineHeight: 24 },
  statistics: { padding: 12, borderWidth: 1, borderColor: colors.accent, borderRadius: 10, gap: 6 },
  sources: { gap: 12, marginTop: 16 },
  translationActions: { gap: 8 },
  translationButton: { minHeight: 44, borderRadius: 12, borderWidth: 1, borderColor: colors.accent, padding: 12, justifyContent: 'center' },
  source: { color: colors.accent, fontSize: 14, fontWeight: '700' },
  disclaimer: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  composerArea: { marginTop: 32, paddingBottom: spacing.md },
  attachments: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  attachment: { maxWidth: '100%', minHeight: 48, paddingLeft: 8, paddingRight: 4, flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: colors.deep },
  attachmentImage: { width: 34, height: 34 },
  attachmentName: { maxWidth: 180, color: colors.muted, fontSize: 14 },
  removeAttachment: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  composer: { minHeight: 60, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8, backgroundColor: colors.deep, borderRadius: 16, borderWidth: 1, borderColor: colors.border },
  composerIcon: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  composerInput: { flex: 1, minWidth: 40, minHeight: 48, color: colors.white, fontSize: 15, paddingHorizontal: 8 },
  sendButton: { width: 48, height: 48, borderRadius: 24, backgroundColor: colors.accent, alignItems: 'center', justifyContent: 'center' },
  pressed: { opacity: 0.75 },
  status: { color: colors.muted, fontSize: 14, lineHeight: 20, marginTop: 8 },
});
