import * as ImagePicker from 'expo-image-picker';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Image, Platform, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, Field, Icon, InteractivePressable, PageTitle, PrimaryButton } from '../components/ui';
import { colors, spacing } from '../theme';
import { analyzePublicationMedia, ContributionMediaTooLargeError, MAX_CONTRIBUTION_MEDIA_BYTES, submitContribution, type PublicationMediaAnalysis } from '../services/api';
import { useI18n } from '../components/i18n';

const categories = [
  { value: 'Politique', key: 'news.politics' },
  { value: 'Société', key: 'news.society' },
  { value: 'Sport', key: 'news.sport' },
  { value: 'Économie', key: 'news.economy' },
] as const;

type PublishMedia = ImagePicker.ImagePickerAsset & { type: 'image' | 'video' };

export default function PublishScreen() {
  const { width } = useWindowDimensions();
  const desktop = width >= 1000;
  const { t } = useI18n();
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Politique');
  const [source, setSource] = useState('');
  const [article, setArticle] = useState('');
  const [media, setMedia] = useState<PublishMedia | null>(null);
  const [analysis, setAnalysis] = useState<PublicationMediaAnalysis | null>(null);
  const [analysisError, setAnalysisError] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<{ title?: string; article?: string; status?: string }>({});

  function selectMedia(value: PublishMedia | null) {
    setAnalysis(null);
    setAnalysisError('');
    setAnalyzing(!!value);
    setMedia(value);
  }

  useEffect(() => {
    if (!media) return;
    const controller = new AbortController();
    void Promise.resolve().then(async () => {
      try {
        const result = await analyzePublicationMedia(media, controller.signal);
        if (!controller.signal.aborted) setAnalysis(result);
      } catch (reason) {
        if (!controller.signal.aborted) {
          setAnalysisError(reason instanceof ContributionMediaTooLargeError
            ? t('publish.analysisMediaTooLarge')
            : reason instanceof Error ? reason.message : t('publish.analysisFailed'));
        }
      } finally {
        if (!controller.signal.aborted) setAnalyzing(false);
      }
    });
    return () => controller.abort();
  }, [media, t]);

  const pickMedia = async (type: 'image' | 'video') => {
    try {
      if (Platform.OS !== 'web') {
        const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
          setErrors((current) => ({ ...current, status: t('publish.mediaPermission') }));
          return;
        }
      }
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: type === 'image' ? ['images'] : ['videos'],
        allowsEditing: false,
        quality: 1,
      });
      if (!result.canceled) {
        const selected = result.assets[0];
        if (selected.fileSize !== undefined && selected.fileSize > MAX_CONTRIBUTION_MEDIA_BYTES) {
          setErrors((current) => ({ ...current, status: t('publish.mediaTooLarge') }));
          return;
        }
        selectMedia({ ...selected, type });
        setErrors((current) => ({ ...current, status: undefined }));
      }
    } catch (error) {
      console.error('Échec de la sélection du média.', error);
      setErrors((current) => ({ ...current, status: t('publish.mediaPickError') }));
    }
  };

  const publish = async () => {
    if (submitting) return;
    const nextErrors = {
      title: title.trim() ? undefined : t('publish.titleRequired'),
      article: article.trim() ? undefined : t('publish.articleRequired'),
    };
    if (nextErrors.title || nextErrors.article) {
      setErrors(nextErrors);
      return;
    }
    setSubmitting(true);
    try {
      await submitContribution({ title: title.trim(), body: article.trim(), category, source: source.trim(), media });
      setErrors({ status: t('publish.sent') });
      setTitle('');
      setArticle('');
      setSource('');
      selectMedia(null);
    } catch (error) {
      setErrors({
        status: error instanceof ContributionMediaTooLargeError
          ? t('publish.mediaTooLarge')
          : error instanceof Error ? error.message : t('publish.failed'),
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppShell active="/publier">
      <PageTitle>{t('publish.title')}</PageTitle>
      <View style={[styles.columns, desktop && styles.columnsDesktop]}>
        <View style={[styles.formColumn, desktop && styles.formColumnDesktop]}>
          <Field
            label={t('publish.articleTitle')}
            value={title}
            onChangeText={(value) => {
              setTitle(value);
              setErrors((current) => ({ ...current, title: undefined, status: undefined }));
            }}
            placeholder={t('publish.titlePlaceholder')}
            error={errors.title}
          />
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>{t('publish.category')}</Text>
            <View style={styles.categories} accessibilityRole="radiogroup">
              {categories.map((item) => {
                const selected = category === item.value;
                return (
                  <InteractivePressable
                    key={item.value}
                    accessibilityRole="radio"
                    accessibilityLabel={`${t('publish.category')} : ${t(item.key)}`}
                    accessibilityState={{ checked: selected }}
                    aria-checked={selected}
                    onPress={() => {
                      setCategory(item.value);
                      setErrors((current) => ({ ...current, status: undefined }));
                    }}
                    style={[styles.category, width < 480 && styles.categorySmall, selected && styles.categorySelected]}
                  >
                    <Text style={[styles.categoryText, selected && styles.categoryTextSelected]}>{t(item.key)}</Text>
                  </InteractivePressable>
                );
              })}
            </View>
          </View>
          <Field
            label={t('publish.sourceOptional')}
            value={source}
            onChangeText={(value) => {
              setSource(value);
              setErrors((current) => ({ ...current, status: undefined }));
            }}
            placeholder={t('publish.sourcePlaceholder')}
          />
          <Field
            label={t('publish.article')}
            value={article}
            onChangeText={(value) => {
              setArticle(value);
              setErrors((current) => ({ ...current, article: undefined, status: undefined }));
            }}
            placeholder={t('publish.articlePlaceholder')}
            error={errors.article}
            multiline
            numberOfLines={7}
          />
          <PrimaryButton label={t('publish.submit')} icon="send" onPress={publish} loading={submitting} />
          {errors.status ? <Text style={styles.status} accessibilityRole="alert" accessibilityLiveRegion="polite">{errors.status}</Text> : null}
        </View>
        <View style={[styles.mediaColumn, desktop && styles.mediaColumnDesktop]}>
          {(['image', 'video'] as const).map((type) => (
            <MediaCard
              key={type}
              type={type}
              media={media?.type === type ? media : null}
              onPick={pickMedia}
              onRemove={() => {
                selectMedia(null);
                setErrors((current) => ({ ...current, status: undefined }));
              }}
            />
          ))}
          {media ? <View style={styles.analysisCard}>
            <View style={styles.analysisHeading}>
              <Icon name="creation-outline" color={colors.accent} size={20} />
              <Text style={styles.analysisTitle}>{t('publish.analysisTitle')}</Text>
            </View>
            {analyzing ? <View style={styles.analysisLoading}><ActivityIndicator color={colors.accent} /><Text style={styles.analysisText}>{t('publish.analysisLoading')}</Text></View> : null}
            {analysisError ? <Text style={styles.analysisError} accessibilityRole="alert">{analysisError}</Text> : null}
            {analysis ? <>
              {analysis.summary ? <Text style={styles.analysisText}>{analysis.summary}</Text> : null}
              {analysis.labels.length ? <Text style={styles.analysisText}>{t('publish.analysisLabels', { labels: analysis.labels.join(' · ') })}</Text> : null}
              {analysis.text ? <Text selectable style={styles.analysisText}>{t('publish.analysisText', { text: analysis.text })}</Text> : null}
              <Text style={styles.analysisNotice}>{analysis.notice}</Text>
            </> : null}
            <Text style={styles.analysisLimit}>{t('publish.analysisLimit')}</Text>
          </View> : null}
        </View>
      </View>
    </AppShell>
  );
}

function MediaCard({
  type,
  media,
  onPick,
  onRemove,
}: {
  type: 'image' | 'video';
  media: ImagePicker.ImagePickerAsset | null;
  onPick: (type: 'image' | 'video') => void;
  onRemove: () => void;
}) {
  const { t } = useI18n();
  return (
    <View style={styles.mediaCard}>
      <View style={styles.mediaHeading}>
        <Icon name={type === 'image' ? 'image-outline' : 'video-outline'} color={colors.accent} size={22} />
        <Text accessibilityRole="header" style={styles.mediaTitle}>{t(type === 'image' ? 'common.photo' : 'common.video')}</Text>
      </View>
      <View style={styles.mediaPlaceholder}>
        {media?.type === 'image' ? (
          <Image source={{ uri: media.uri }} accessibilityLabel={media.fileName ?? t('publish.attachPhoto')} style={styles.mediaImage} resizeMode="contain" />
        ) : null}
        {media?.type !== 'image' ? <View style={styles.mediaIcon}><Icon name={type === 'image' ? 'image-plus-outline' : 'video-plus-outline'} color={colors.accent} size={36} /></View> : null}
        <Text style={styles.mediaPrompt}>
          {media ? media.fileName ?? t(type === 'video' ? 'publish.attachVideo' : 'publish.attachPhoto') : t(type === 'image' ? 'common.addPhoto' : 'common.addVideo')}
        </Text>
        {media ? (
          <InteractivePressable accessibilityRole="button" accessibilityLabel={t('publish.removeMedia')} onPress={onRemove} style={styles.removeButton}>
            <Icon name="close" />
          </InteractivePressable>
        ) : null}
      </View>
      <InteractivePressable accessibilityRole="button" accessibilityLabel={t(type === 'image' ? 'common.addPhoto' : 'common.addVideo')} onPress={() => onPick(type)} style={styles.mediaAction}>
        <Icon name="plus" color={colors.accent} size={19} />
        <Text style={styles.mediaActionText}>{t(type === 'image' ? 'common.addPhoto' : 'common.addVideo')}</Text>
      </InteractivePressable>
      <Text style={styles.mediaLimit}>{t('publish.mediaLimit')}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  columns: { gap: spacing.xl },
  columnsDesktop: { flexDirection: 'row', alignItems: 'flex-start' },
  formColumn: { flex: 1, minWidth: 0, padding: 20, borderRadius: 20, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  formColumnDesktop: { flex: 2, padding: 28 },
  mediaColumn: { gap: spacing.xl, minWidth: 0 },
  mediaColumnDesktop: { flex: 1, minWidth: 240, maxWidth: 340 },
  fieldGroup: { marginBottom: 20 },
  label: { color: colors.white, fontSize: 14, lineHeight: 20, fontWeight: '700', marginBottom: 8 },
  categories: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  category: { flexBasis: '23%', flexGrow: 1, minHeight: 48, justifyContent: 'center', paddingHorizontal: 10, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: 10 },
  categorySmall: { flexBasis: '45%' },
  categorySelected: { backgroundColor: colors.accent, borderColor: colors.accent },
  categoryText: { color: colors.white, fontSize: 14, fontWeight: '700' },
  categoryTextSelected: { color: colors.deep },
  mediaCard: { minWidth: 0, borderRadius: 20, borderWidth: 1, borderColor: colors.border, padding: 16, gap: 16, backgroundColor: colors.surface },
  mediaHeading: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  mediaTitle: { flex: 1, color: colors.white, fontSize: 17, lineHeight: 24, fontWeight: '700' },
  mediaPlaceholder: { minHeight: 164, padding: 16, backgroundColor: colors.deep, alignItems: 'center', justifyContent: 'center', gap: 12, borderRadius: 12 },
  mediaIcon: { width: 64, height: 64, borderRadius: 20, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center' },
  mediaPrompt: { color: colors.muted, fontSize: 14, lineHeight: 22, textAlign: 'center', flexShrink: 1 },
  mediaImage: { width: '100%', aspectRatio: 16 / 9, borderRadius: 12 },
  removeButton: { minWidth: 44, minHeight: 44, justifyContent: 'center', alignItems: 'center' },
  mediaAction: { minHeight: 48, borderWidth: 1, borderColor: colors.accent, borderRadius: 12, paddingHorizontal: 12, paddingVertical: 10, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  mediaActionText: { color: colors.accent, fontSize: 15, fontWeight: '700' },
  mediaLimit: { color: colors.muted, fontSize: 13, lineHeight: 18, textAlign: 'center' },
  analysisCard: { minWidth: 0, padding: 16, gap: 10, borderRadius: 18, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  analysisHeading: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  analysisTitle: { color: colors.white, fontSize: 16, lineHeight: 22, fontWeight: '800' },
  analysisLoading: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  analysisText: { color: colors.white, fontSize: 13, lineHeight: 20 },
  analysisNotice: { color: colors.muted, fontSize: 12, lineHeight: 18 },
  analysisLimit: { color: colors.muted, fontSize: 11, lineHeight: 16 },
  analysisError: { color: colors.white, fontSize: 13, lineHeight: 20 },
  status: { color: colors.muted, fontSize: 14, lineHeight: 20, marginTop: 12, padding: 12, borderWidth: 1, borderColor: colors.border, borderRadius: 12 },
});
