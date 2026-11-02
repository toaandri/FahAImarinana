import * as ImagePicker from 'expo-image-picker';
import { useState } from 'react';
import { Image, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { AppShell, Field, Icon, InteractivePressable, PageTitle, PrimaryButton } from '../components/ui';
import { colors, spacing } from '../theme';
import { submitContribution } from '../services/api';

const categories = ['Politique', 'Société', 'Sport', 'Économie'];

export default function PublishScreen() {
  const { width } = useWindowDimensions();
  const desktop = width >= 1200;
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Politique');
  const [source, setSource] = useState('');
  const [article, setArticle] = useState('');
  const [media, setMedia] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [errors, setErrors] = useState<{ title?: string; article?: string; status?: string }>({});

  const pickMedia = async (type: 'image' | 'video') => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        setErrors((current) => ({ ...current, status: 'Autorisez l’accès à votre photothèque pour joindre un média.' }));
        return;
      }
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: type === 'image' ? ['images'] : ['videos'],
        allowsEditing: false,
        quality: 1,
      });
      if (!result.canceled) {
        setMedia(result.assets[0]);
        setErrors((current) => ({ ...current, status: undefined }));
      }
    } catch (error) {
      console.error('Échec de la sélection du média.', error);
      setErrors((current) => ({ ...current, status: 'Impossible d’ouvrir la photothèque. Réessayez.' }));
    }
  };

  const publish = async () => {
    const nextErrors = {
      title: title.trim() ? undefined : 'Le titre est obligatoire.',
      article: article.trim() ? undefined : 'Le texte de votre article est obligatoire.',
    };
    if (nextErrors.title || nextErrors.article) {
      setErrors(nextErrors);
      return;
    }
    try {
      await submitContribution({ title: title.trim(), body: article.trim(), category, source: source.trim() });
      setErrors({ status: 'Votre contribution a été envoyée pour traitement éditorial.' });
      setTitle('');
      setArticle('');
      setSource('');
    } catch (error) {
      setErrors({ status: error instanceof Error ? error.message : 'Envoi impossible.' });
    }
  };

  return (
    <AppShell active="/publier">
      <PageTitle>Publier un article</PageTitle>
      <View style={[styles.columns, desktop && styles.columnsDesktop]}>
        <View style={styles.formColumn}>
          <Field
            label="Titre"
            value={title}
            onChangeText={(value) => {
              setTitle(value);
              setErrors((current) => ({ ...current, title: undefined, status: undefined }));
            }}
            placeholder="Le titre de votre article"
            error={errors.title}
          />
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Catégorie</Text>
            <View style={styles.categories} accessibilityRole="radiogroup">
              {categories.map((item) => {
                const selected = category === item;
                return (
                  <InteractivePressable
                    key={item}
                    accessibilityRole="radio"
                    accessibilityLabel={`Catégorie : ${item}`}
                    accessibilityState={{ checked: selected }}
                    aria-checked={selected}
                    onPress={() => {
                      setCategory(item);
                      setErrors((current) => ({ ...current, status: undefined }));
                    }}
                    style={[styles.category, width < 480 && styles.categorySmall, selected && styles.categorySelected]}
                  >
                    <Text style={[styles.categoryText, selected && styles.categoryTextSelected]}>{item}</Text>
                  </InteractivePressable>
                );
              })}
            </View>
          </View>
          {!desktop ? (
            <MediaCard
              media={media}
              onPick={pickMedia}
              onRemove={() => {
                setMedia(null);
                setErrors((current) => ({ ...current, status: undefined }));
              }}
            />
          ) : null}
          <Field
            label="Source (facultatif)"
            value={source}
            onChangeText={(value) => {
              setSource(value);
              setErrors((current) => ({ ...current, status: undefined }));
            }}
            placeholder="Adresse ou nom de la source"
          />
          <Field
            label="Votre article"
            value={article}
            onChangeText={(value) => {
              setArticle(value);
              setErrors((current) => ({ ...current, article: undefined, status: undefined }));
            }}
            placeholder="Écrivez ou collez votre article..."
            error={errors.article}
            multiline
            numberOfLines={7}
          />
          <PrimaryButton label="PUBLIER" icon="send" onPress={publish} />
          {errors.status ? <Text style={styles.status} accessibilityRole="alert" accessibilityLiveRegion="polite">{errors.status}</Text> : null}
        </View>
        {desktop ? (
          <MediaCard
            media={media}
            onPick={pickMedia}
            onRemove={() => {
              setMedia(null);
              setErrors((current) => ({ ...current, status: undefined }));
            }}
          />
        ) : null}
      </View>
    </AppShell>
  );
}

function MediaCard({
  media,
  onPick,
  onRemove,
}: {
  media: ImagePicker.ImagePickerAsset | null;
  onPick: (type: 'image' | 'video') => void;
  onRemove: () => void;
}) {
  return (
    <View style={styles.mediaCard}>
      <View style={styles.mediaPlaceholder}>
        {media?.type === 'image' ? (
          <Image source={{ uri: media.uri }} style={styles.mediaImage} resizeMode="cover" />
        ) : null}
        <View style={styles.mediaAccent} />
        <Text style={styles.mediaPrompt}>
          {media ? media.fileName ?? (media.type === 'video' ? 'Vidéo jointe' : 'Photo jointe') : '+ Ajouter un média'}
        </Text>
        {media ? (
          <InteractivePressable accessibilityRole="button" accessibilityLabel="Supprimer le média" onPress={onRemove} style={styles.removeButton}>
            <Icon name="close" />
          </InteractivePressable>
        ) : null}
      </View>
      <View style={styles.mediaActions}>
        <InteractivePressable accessibilityRole="button" accessibilityLabel="Ajouter une photo" onPress={() => onPick('image')} style={styles.mediaAction}>
          <Icon name="image-outline" color={colors.accent} size={19} />
          <Text style={styles.mediaActionText}>Photo</Text>
        </InteractivePressable>
        <Text style={styles.slash}>/</Text>
        <InteractivePressable accessibilityRole="button" accessibilityLabel="Ajouter une vidéo" onPress={() => onPick('video')} style={styles.mediaAction}>
          <Icon name="video-outline" color={colors.accent} size={19} />
          <Text style={styles.mediaActionText}>Vidéo</Text>
        </InteractivePressable>
      </View>
      <Text style={styles.credibility}>— % Crédibilité</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  columns: { gap: spacing.xl },
  columnsDesktop: { flexDirection: 'row', alignItems: 'flex-start' },
  formColumn: { flex: 1, minWidth: 0 },
  fieldGroup: { marginBottom: 20 },
  label: { color: colors.white, fontSize: 14, lineHeight: 20, fontWeight: '700', marginBottom: 8 },
  categories: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  category: { flexBasis: '23%', flexGrow: 1, minHeight: 48, justifyContent: 'center', paddingHorizontal: 10, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: 10 },
  categorySmall: { flexBasis: '45%' },
  categorySelected: { backgroundColor: colors.accent, borderColor: colors.accent },
  categoryText: { color: colors.white, fontSize: 14, fontWeight: '700' },
  categoryTextSelected: { color: colors.deep },
  mediaCard: { flex: 1, minWidth: 0, borderRadius: 16, borderWidth: 1, borderColor: colors.border, padding: 16, backgroundColor: colors.surface, marginBottom: 20 },
  mediaPlaceholder: { minHeight: 240, padding: 20, backgroundColor: colors.deep, flexDirection: 'row', alignItems: 'center', gap: 16, borderRadius: 12 },
  mediaAccent: { width: 4, alignSelf: 'stretch', backgroundColor: colors.accent },
  mediaPrompt: { flex: 1, color: colors.muted, fontSize: 15, lineHeight: 22, fontWeight: '700' },
  mediaImage: { width: 96, height: 96, borderRadius: 10 },
  removeButton: { minWidth: 44, minHeight: 44, justifyContent: 'center', alignItems: 'center' },
  mediaActions: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 12 },
  mediaAction: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 6 },
  mediaActionText: { color: colors.accent, fontSize: 15, fontWeight: '700' },
  slash: { color: colors.accent, fontWeight: '700' },
  credibility: { color: colors.white, fontSize: 15, marginTop: 4 },
  status: { color: colors.muted, fontSize: 14, lineHeight: 20, marginTop: 12, padding: 12, borderWidth: 1, borderColor: colors.border, borderRadius: 12 },
});
