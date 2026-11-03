import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Pressable, TextInput, ScrollView, Alert, Image, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import * as ImagePicker from 'expo-image-picker';
import { HeaderBar, BottomTabs, GlassCard, TagChip } from '@/components/ui';
import { palette } from '@/theme/theme';
import { publishArticle } from '@/services/mockData';
import { useLanguage } from '@/i18n/LanguageProvider';
import { analyzePublicationMedia, type PublicationAnalysis } from '@/services/vision';

export default function PublierScreen() {
  const { t } = useLanguage();
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [category, setCategory] = useState('Politique');
  const [media, setMedia] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [mediaError, setMediaError] = useState('');
  const [mediaLoading, setMediaLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [analysis, setAnalysis] = useState<PublicationAnalysis | null>(null);
  const [analysisError, setAnalysisError] = useState('');
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    setAnalysis(null);
    setAnalysisError('');
    if (!media) { setAnalyzing(false); return; }
    const controller = new AbortController();
    setAnalyzing(true);
    analyzePublicationMedia(media, controller.signal)
      .then((result) => { if (!controller.signal.aborted) setAnalysis(result); })
      .catch((error) => { if (!controller.signal.aborted) setAnalysisError(error instanceof Error ? error.message : 'Analyse indisponible.'); })
      .finally(() => { if (!controller.signal.aborted) setAnalyzing(false); });
    return () => controller.abort();
  }, [media]);

  async function pickMedia(mediaTypes: ImagePicker.MediaType[]) {
    setMediaError('');
    if (Platform.OS !== 'web') setMediaLoading(true);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes, quality: 0.9 });
      if (!result.canceled) setMedia(result.assets[0]);
    } catch (error) {
      setMediaError(error instanceof Error ? error.message : t('galleryError'));
    } finally {
      if (Platform.OS !== 'web') setMediaLoading(false);
    }
  }

  async function recordVideo() {
    setMediaError('');
    if (Platform.OS !== 'web') setMediaLoading(true);
    try {
      if (Platform.OS !== 'web') {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
          setMediaError(t('cameraPermission'));
          return;
        }
      }

      const result = await ImagePicker.launchCameraAsync({ mediaTypes: ['videos'] });
      if (!result.canceled) setMedia(result.assets[0]);
    } catch (error) {
      setMediaError(error instanceof Error ? error.message : t('cameraError'));
    } finally {
      if (Platform.OS !== 'web') setMediaLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar />
      <ScrollView contentContainerStyle={styles.content}>
        <GlassCard style={styles.titleCard}>
          <Text style={styles.titleLabel}>{t('publishArticle')}</Text>
          <Text style={styles.fieldLabel}>{t('titleLabel')}</Text>
          <TextInput value={title} onChangeText={setTitle} placeholder={t('articleTitle')} placeholderTextColor="rgba(255,255,255,0.5)" style={styles.titleInput} />

          <View style={styles.chipRow}>
            {([
              { value: 'Politique', key: 'politics' },
              { value: 'Société', key: 'society' },
              { value: 'Sport', key: 'sport' },
              { value: 'Économie', key: 'economy' },
            ] as const).map((item) => (
              <Pressable key={item.value} accessibilityRole="button" accessibilityState={{ selected: category === item.value }} onPress={() => setCategory(item.value)}>
                <TagChip label={t(item.key)} active={category === item.value} small />
              </Pressable>
            ))}
          </View>
        </GlassCard>

        <GlassCard style={styles.mediaCard}>
          <View style={styles.mediaPreview}>
            {media?.type === 'image' ? (
              <Image source={{ uri: media.uri }} style={styles.mediaImage} resizeMode="cover" />
            ) : media?.type === 'video' ? (
              <View style={styles.videoPreview}>
                <Ionicons name="videocam" size={28} color={palette.mint} />
                <Text numberOfLines={1} style={styles.videoName}>{media.fileName || t('selectedVideo')}</Text>
              </View>
            ) : null}
            {media ? <View pointerEvents="none" style={styles.mediaScrim} /> : null}
            <View pointerEvents="box-none" style={styles.mediaCenter}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={media ? t('replaceMedia') : t('addMedia')}
                disabled={mediaLoading}
                style={styles.mediaButton}
                onPress={() => pickMedia(['images', 'videos'])}
              >
                <Text style={styles.mediaPlus}>{mediaLoading ? '…' : '+'}</Text>
              </Pressable>
            </View>
            {media ? (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={t('removeMedia')}
                style={styles.removeMediaButton}
                onPress={() => setMedia(null)}
              >
                <Ionicons name="close" size={16} color="#fff" />
              </Pressable>
            ) : null}
            <View style={styles.mediaActions}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={t('choosePhoto')}
                disabled={mediaLoading}
                style={styles.mediaAction}
                onPress={() => pickMedia(['images'])}
              >
                <Ionicons name="image-outline" size={11} color="#fff" />
                <Text style={styles.mediaActionText}>{t('photo')}</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={t('recordVideo')}
                disabled={mediaLoading}
                style={styles.mediaAction}
                onPress={recordVideo}
              >
                <Ionicons name="videocam-outline" size={11} color="#fff" />
                <Text style={styles.mediaActionText}>{t('recordVideo')}</Text>
              </Pressable>
            </View>
          </View>
          <View style={styles.mediaDetails}>
            <Text style={styles.credibility}>—</Text>
            <Text style={styles.credibilityLabel}>Véracité non évaluée</Text>
            <Text style={styles.source}>{t('source')}</Text>
          </View>
        </GlassCard>
        {mediaError ? <Text accessibilityRole="alert" style={styles.mediaError}>{mediaError}</Text> : null}
        {media ? <GlassCard style={styles.analysisCard}>
          <Text style={styles.analysisTitle}>Analyse du média</Text>
          {analyzing ? <Text style={styles.analysisText} accessibilityLiveRegion="polite">Analyse en cours…</Text> : null}
          {analysisError ? <Text style={styles.mediaError} accessibilityRole="alert">{analysisError}</Text> : null}
          {analysis ? <>
            {analysis.summary ? <Text style={styles.analysisText}>{analysis.summary}</Text> : null}
            {analysis.labels.length ? <Text style={styles.analysisText}>Éléments détectés : {analysis.labels.join(' · ')}</Text> : null}
            {analysis.text ? <Text selectable style={styles.analysisText}>Texte détecté : {analysis.text}</Text> : null}
            {!analysis.labels.length && !analysis.text && !analysis.summary ? <Text style={styles.analysisText}>Aucun élément détecté.</Text> : null}
            <Text style={styles.analysisText}>{analysis.notice}</Text>
          </> : null}
        </GlassCard> : null}

        <Text style={styles.bodyLabel}>{t('articleBody')}</Text>
        <TextInput value={body} onChangeText={setBody} multiline placeholder={t('articlePlaceholder')} placeholderTextColor="rgba(255,255,255,0.5)" style={styles.bodyInput} />

        <Pressable
          style={styles.publishButton}
          disabled={submitting}
          accessibilityState={{ disabled: submitting, busy: submitting }}
          onPress={async () => {
            if (submitting) return;
            if (!title.trim() || !body.trim()) {
              Alert.alert(t('incompleteArticle'), t('completeArticleHint'));
              return;
            }
            setSubmitting(true);
            try {
              await publishArticle({ title: title.trim(), body: body.trim(), category, media });
              Alert.alert(t('articleSent'), t('articleSentMessage'));
              setTitle('');
              setBody('');
              setMedia(null);
            } catch (error) {
              Alert.alert(t('sendFailed'), error instanceof Error ? error.message : t('unexpectedError'));
            } finally {
              setSubmitting(false);
            }
          }}
        ><Text style={styles.publishText}>{submitting ? t('articleSending') : t('submitArticle')}</Text></Pressable>
      </ScrollView>
      <BottomTabs active="publier" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  content: { padding: 16, paddingBottom: 120 },
  titleCard: { padding: 12 },
  titleLabel: { color: '#fff', fontSize: 13, fontFamily: 'Montserrat_700Bold_Italic', marginBottom: 12 },
  fieldLabel: { color: palette.mint, fontSize: 10, fontFamily: 'Montserrat_700Bold_Italic' },
  titleInput: { borderBottomWidth: 1, borderBottomColor: palette.mint, color: '#fff', paddingBottom: 6, fontSize: 14, fontFamily: 'Montserrat_700Bold_Italic' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 10 },
  mediaCard: { padding: 8, minHeight: 200, flexDirection: 'row', alignItems: 'stretch', gap: 10, marginTop: 10 },
  mediaPreview: { flex: 1, minWidth: 0, borderRadius: 12, backgroundColor: 'rgba(14,24,31,0.32)', justifyContent: 'space-between', padding: 8 },
  mediaCenter: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, alignItems: 'center', justifyContent: 'center' },
  mediaButton: { width: 48, height: 48, borderRadius: 24, backgroundColor: palette.mint, alignItems: 'center', justifyContent: 'center' },
  mediaPlus: { color: '#0b2b2b', fontSize: 28, fontWeight: '800' },
  mediaImage: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, borderRadius: 12 },
  mediaScrim: { position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, borderRadius: 12, backgroundColor: 'rgba(14,24,31,0.28)' },
  videoPreview: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 6 },
  videoName: { maxWidth: '90%', color: '#fff', fontSize: 10, fontFamily: 'Montserrat_600SemiBold_Italic' },
  removeMediaButton: { position: 'absolute', top: 8, right: 8, width: 28, height: 28, borderRadius: 14, backgroundColor: 'rgba(14,24,31,0.7)', alignItems: 'center', justifyContent: 'center' },
  mediaActions: { flexDirection: 'row', gap: 6 },
  mediaAction: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: 'rgba(14,24,31,0.48)', borderRadius: 14, paddingHorizontal: 8, paddingVertical: 5 },
  mediaActionText: { color: '#fff', fontFamily: 'Montserrat_600SemiBold_Italic', fontSize: 9 },
  mediaError: { marginTop: 8, color: '#ffd0d0', fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic' },
  analysisCard: { marginTop: 10, padding: 12, gap: 6 },
  analysisTitle: { color: palette.mint, fontSize: 14, fontWeight: '700' },
  analysisText: { color: '#fff', fontSize: 12, lineHeight: 18 },
  mediaDetails: { width: 48, alignItems: 'center', justifyContent: 'space-between', paddingVertical: 6 },
  credibility: { width: 36, height: 36, borderRadius: 18, borderWidth: 3, borderColor: 'rgba(255,255,255,0.35)', color: '#fff', textAlign: 'center', textAlignVertical: 'center', fontSize: 10, fontFamily: 'Montserrat_700Bold_Italic' },
  credibilityLabel: { color: '#fff', fontSize: 7, fontFamily: 'Montserrat_600SemiBold_Italic' },
  source: { color: '#fff', backgroundColor: 'rgba(14,24,31,0.48)', paddingHorizontal: 6, paddingVertical: 4, borderRadius: 10, fontSize: 8, fontFamily: 'Montserrat_600SemiBold_Italic' },
  bodyLabel: { color: '#fff', fontSize: 13, fontFamily: 'Montserrat_700Bold_Italic', marginTop: 10, marginBottom: 6 },
  bodyInput: { minHeight: 150, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 14, borderWidth: 1, borderColor: 'rgba(255,255,255,0.18)', padding: 12, color: '#fff', textAlignVertical: 'top', fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic' },
  publishButton: { minHeight: 58, marginTop: 20, backgroundColor: palette.mint, borderRadius: 14, paddingHorizontal: 16, paddingVertical: 12, alignItems: 'center', justifyContent: 'center' },
  publishText: { width: '100%', color: '#0b2b2b', fontSize: 18, textAlign: 'center', flexShrink: 1, fontFamily: 'Montserrat_700Bold_Italic' },
});
