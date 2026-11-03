import * as ImagePicker from 'expo-image-picker';
import { useCallback, useState } from 'react';
import { useFocusEffect } from 'expo-router';
import { Image, StyleSheet, Text, TextInput, View } from 'react-native';
import { AppShell, Card, Icon, InteractivePressable, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';
import { LanguageSelector } from '../components/LanguageSelector';
import { getResponseLanguage, sendMessageToAI, translateAnswer, type ResearchResult, type ResponseLanguage } from '../services/api';

type Attachment = { uri: string; name: string; type: 'image' | 'video' };

export default function VerifyScreen() {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [status, setStatus] = useState('');
  const [language, setLanguage] = useState<ResponseLanguage>('auto');
  const [loadingLanguage, setLoadingLanguage] = useState(true);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [question, setQuestion] = useState('');
  const [translation, setTranslation] = useState<string | null>(null);

  useFocusEffect(useCallback(() => {
    let active = true;
    setLoadingLanguage(true);
    getResponseLanguage().then((value) => { if (active) setLanguage(value); })
      .catch((error) => { if (active) setStatus(error instanceof Error ? error.message : 'Préférence indisponible.'); })
      .finally(() => { if (active) setLoadingLanguage(false); });
    return () => { active = false; };
  }, []));

  const pickMedia = async (type: 'image' | 'video') => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        setStatus('Autorisez l’accès à votre photothèque pour joindre un média.');
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
        { uri: asset.uri, name: asset.fileName ?? (type === 'image' ? 'Photo' : 'Vidéo'), type },
      ]);
      setStatus('');
    } catch (error) {
      console.error('Échec de la sélection du média.', error);
      setStatus('Impossible d’ouvrir la photothèque. Réessayez.');
    }
  };

  const sendMessage = async () => {
    if (busy || loadingLanguage) return;
    if (attachments.length) {
      setStatus('Ce dialogue vérifie le texte. Retirez les pièces jointes et décrivez votre question.');
      return;
    }
    if (message.trim().length < 3) {
      setStatus('Écrivez une question d’au moins trois caractères.');
      return;
    }
    const submitted = message.trim();
    setBusy(true);
    setStatus('');
    try {
      const answer = await sendMessageToAI(submitted, language);
      setResult(answer);
      setQuestion(submitted);
      setTranslation(null);
      setMessage('');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Réponse indisponible.');
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
      setStatus('Traduction automatique à relire. / Dikanteny mandeha ho azy, mila averina vakina.');
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Traduction indisponible.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell active="/verifier">
      <View style={styles.content}>
        <PageTitle>Vérifier une information</PageTitle>
        <LanguageSelector value={language} onChange={setLanguage} disabled={busy || loadingLanguage} />
        <View style={styles.conversation}>
          <View style={styles.aiMessage}>
            <Text style={styles.messageText}>
              {language === 'mg' ? 'AI • Salama! Alefaso ny fanontanianao, hanampy anao hanamarina ny vaovao aho.' : 'AI • Bonjour ! Posez une question pour préparer votre vérification journalistique.'}
            </Text>
          </View>
          {question ? <View style={styles.userMessage}>
            <Text style={styles.userMessageText}>{question}</Text>
          </View> : null}
          <Card style={styles.resultCard}>
            <Text style={styles.resultTitle}>{language === 'mg' ? 'Valin’ny IA — mbola mila hamarinina' : 'Pré-analyse IA — à vérifier'}</Text>
            <Text selectable style={styles.resultText}>
              {translation ?? result?.reponse ?? 'Envoyez un message / Alefaso ny fanontanianao.'}
            </Text>
            <View style={styles.sources}>
              {result?.citations.map((source, index) => <Text selectable key={index} style={styles.source}>{[source.titre, source.url].filter(Boolean).join(' — ')}</Text>)}
              {result && !result.citations.length ? <Text style={styles.source}>Aucune source retournée / Tsy nisy loharano nomena.</Text> : null}
            </View>
            {result ? <View style={styles.translationActions}>
              <InteractivePressable accessibilityRole="button" disabled={busy} onPress={() => void translate('mg')} style={styles.translationButton}><Text style={styles.source}>Adika amin’ny teny malagasy</Text></InteractivePressable>
              <InteractivePressable accessibilityRole="button" disabled={busy} onPress={() => void translate('fr')} style={styles.translationButton}><Text style={styles.source}>Traduire en français</Text></InteractivePressable>
              {translation ? <InteractivePressable accessibilityRole="button" disabled={busy} onPress={() => { setTranslation(null); setStatus(''); }} style={styles.translationButton}><Text style={styles.source}>Voir l’original / Teny niandohana</Text></InteractivePressable> : null}
            </View> : null}
            <Text style={styles.disclaimer}>
              {busy ? 'En cours… / Eo am-pikarakarana…' : 'Une réponse IA doit être relue par un journaliste. / Mila hamarinina amin’ny mpanao gazety ny valin’ny IA.'}
            </Text>
          </Card>
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
                    accessibilityLabel={`Supprimer ${item.name}`}
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
              accessibilityLabel="Joindre une photo"
              onPress={() => void pickMedia('image')}
              style={styles.composerIcon}
            >
              <Icon name="image-outline" />
            </InteractivePressable>
            <InteractivePressable
              accessibilityRole="button"
              accessibilityLabel="Joindre une vidéo"
              onPress={() => void pickMedia('video')}
              style={styles.composerIcon}
            >
              <Icon name="video-outline" />
            </InteractivePressable>
            <TextInput
              accessibilityLabel="Écrire un message"
              value={message}
              editable={!busy}
              maxLength={2000}
              onChangeText={(value) => {
                setMessage(value);
                setStatus('');
              }}
              placeholder={language === 'mg' ? 'Soraty eto ny fanontanianao…' : 'Écrire un message…'}
              placeholderTextColor={colors.muted}
              style={styles.composerInput}
              returnKeyType="send"
              onSubmitEditing={sendMessage}
            />
            <InteractivePressable
              accessibilityRole="button"
              accessibilityLabel="Envoyer le message"
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
