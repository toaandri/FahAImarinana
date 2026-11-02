import * as ImagePicker from 'expo-image-picker';
import { useState } from 'react';
import { Image, StyleSheet, Text, TextInput, View } from 'react-native';
import { AppShell, Card, CredibilityBadge, Icon, InteractivePressable, PageTitle } from '../components/ui';
import { colors, spacing } from '../theme';

type Attachment = { uri: string; name: string; type: 'image' | 'video' };

export default function VerifyScreen() {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [status, setStatus] = useState('');

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

  const sendMessage = () => {
    if (!message.trim() && attachments.length === 0) {
      setStatus('Ajoutez un message ou une photo/vidéo avant l’envoi.');
      return;
    }
    setStatus('Votre demande n’a pas été envoyée : le service de vérification n’est pas encore connecté.');
  };

  return (
    <AppShell active="/verifier">
      <View style={styles.content}>
        <PageTitle>Vérifier une information</PageTitle>
        <View style={styles.conversation}>
          <View style={styles.aiMessage}>
            <Text style={styles.messageText}>
              AI • Bonjour ! Envoyez-moi un texte, une photo ou une vidéo : je vérifie l’information.
            </Text>
          </View>
          <View style={styles.sampleMedia}>
            <Text style={styles.sampleText}>Exemple de média</Text>
          </View>
          <View style={styles.userMessage}>
            <Text style={styles.userMessageText}>[Message de l’utilisateur]</Text>
          </View>
          <Card style={styles.resultCard}>
            <CredibilityBadge value="72 %" caption="Crédibilité moyenne · exemple de maquette" />
            <Text style={styles.resultTitle}>[Résumé de la vérification]</Text>
            <Text style={styles.resultText}>
              [Explication de l’IA : ce qui est confirmé, ce qui reste à vérifier]
            </Text>
            <View style={styles.sources}>
              <Text style={styles.source}>[Source 1]</Text>
              <Text style={styles.source}>[Source 2]</Text>
            </View>
            <Text style={styles.disclaimer}>
              Exemple visuel uniquement — aucun résultat d’analyse réel.
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
              onChangeText={(value) => {
                setMessage(value);
                setStatus('');
              }}
              placeholder="Écrire un message..."
              placeholderTextColor={colors.muted}
              style={styles.composerInput}
              returnKeyType="send"
              onSubmitEditing={sendMessage}
            />
            <InteractivePressable
              accessibilityRole="button"
              accessibilityLabel="Envoyer le message"
              onPress={sendMessage}
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
  sources: { flexDirection: 'row', gap: 16, marginTop: 16 },
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
