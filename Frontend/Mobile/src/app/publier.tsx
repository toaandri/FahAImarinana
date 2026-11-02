import { useState } from 'react';
import { View, Text, StyleSheet, Pressable, TextInput, ScrollView, Alert, Image, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import * as ImagePicker from 'expo-image-picker';
import { HeaderBar, BottomTabs, GlassCard, TagChip } from '@/components/ui';
import { palette } from '@/theme/theme';
import { publishArticle } from '@/services/mockData';

export default function PublierScreen() {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [category, setCategory] = useState('Politique');
  const [media, setMedia] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [mediaError, setMediaError] = useState('');
  const [mediaLoading, setMediaLoading] = useState(false);

  async function pickMedia(mediaTypes: ImagePicker.MediaType[]) {
    setMediaError('');
    if (Platform.OS !== 'web') setMediaLoading(true);
    try {
      const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes, quality: 0.9 });
      if (!result.canceled) setMedia(result.assets[0]);
    } catch (error) {
      setMediaError(error instanceof Error ? error.message : 'Impossible d’ouvrir la galerie.');
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
          setMediaError('Autorisez l’accès à la caméra pour filmer une vidéo.');
          return;
        }
      }

      const result = await ImagePicker.launchCameraAsync({ mediaTypes: ['videos'] });
      if (!result.canceled) setMedia(result.assets[0]);
    } catch (error) {
      setMediaError(error instanceof Error ? error.message : 'Impossible d’ouvrir la caméra.');
    } finally {
      if (Platform.OS !== 'web') setMediaLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <HeaderBar />
      <ScrollView contentContainerStyle={styles.content}>
        <GlassCard style={styles.titleCard}>
          <Text style={styles.titleLabel}>Publier votre article</Text>
          <Text style={styles.fieldLabel}>TITRE :</Text>
          <TextInput value={title} onChangeText={setTitle} placeholder="Le titre de votre article" placeholderTextColor="rgba(255,255,255,0.5)" style={styles.titleInput} />

          <View style={styles.chipRow}>
            {['Politique', 'Société', 'Sport', 'Économie'].map((item) => (
              <Pressable key={item} onPress={() => setCategory(item)}>
                <TagChip label={item} active={category === item} small />
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
                <Text numberOfLines={1} style={styles.videoName}>{media.fileName || 'Vidéo sélectionnée'}</Text>
              </View>
            ) : null}
            {media ? <View pointerEvents="none" style={styles.mediaScrim} /> : null}
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={media ? 'Remplacer le média' : 'Ajouter une photo ou une vidéo'}
              disabled={mediaLoading}
              style={styles.mediaButton}
              onPress={() => pickMedia(['images', 'videos'])}
            >
              <Text style={styles.mediaPlus}>{mediaLoading ? '…' : '+'}</Text>
            </Pressable>
            {media ? (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Supprimer le média sélectionné"
                style={styles.removeMediaButton}
                onPress={() => setMedia(null)}
              >
                <Ionicons name="close" size={16} color="#fff" />
              </Pressable>
            ) : null}
            <View style={styles.mediaActions}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Choisir une photo"
                disabled={mediaLoading}
                style={styles.mediaAction}
                onPress={() => pickMedia(['images'])}
              >
                <Ionicons name="image-outline" size={11} color="#fff" />
                <Text style={styles.mediaActionText}>Photo</Text>
              </Pressable>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Filmer une vidéo"
                disabled={mediaLoading}
                style={styles.mediaAction}
                onPress={recordVideo}
              >
                <Ionicons name="videocam-outline" size={11} color="#fff" />
                <Text style={styles.mediaActionText}>Filmer une vidéo</Text>
              </Pressable>
            </View>
          </View>
          <View style={styles.mediaDetails}>
            <Text style={styles.credibility}>—%</Text>
            <Text style={styles.credibilityLabel}>Crédibilité</Text>
            <Text style={styles.source}>Source</Text>
          </View>
        </GlassCard>
        {mediaError ? <Text accessibilityRole="alert" style={styles.mediaError}>{mediaError}</Text> : null}

        <Text style={styles.bodyLabel}>Votre article</Text>
        <TextInput value={body} onChangeText={setBody} multiline placeholder="Écrivez ou collez votre article..." placeholderTextColor="rgba(255,255,255,0.5)" style={styles.bodyInput} />

        <Pressable
          style={styles.publishButton}
          onPress={async () => {
            if (!title.trim() || !body.trim()) {
              Alert.alert('Article incomplet', 'Ajoutez un titre et un contenu.');
              return;
            }
            try {
              await publishArticle({ title: title.trim(), body: body.trim(), category });
              Alert.alert('Article envoyé', 'Votre contribution a été transmise pour traitement éditorial.');
              setTitle('');
              setBody('');
            } catch (error) {
              Alert.alert('Envoi impossible', error instanceof Error ? error.message : 'Une erreur est survenue.');
            }
          }}
        ><Text style={styles.publishText}>PUBLIER</Text></Pressable>
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
  mediaCard: { padding: 8, minHeight: 132, flexDirection: 'row', alignItems: 'stretch', gap: 10, marginTop: 10 },
  mediaPreview: { flex: 1, minWidth: 0, borderRadius: 12, backgroundColor: 'rgba(14,24,31,0.32)', justifyContent: 'space-between', padding: 8 },
  mediaButton: { width: 48, height: 48, borderRadius: 24, backgroundColor: palette.mint, alignSelf: 'center', alignItems: 'center', justifyContent: 'center', marginTop: 10 },
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
  mediaDetails: { width: 48, alignItems: 'center', justifyContent: 'space-between', paddingVertical: 6 },
  credibility: { width: 36, height: 36, borderRadius: 18, borderWidth: 3, borderColor: 'rgba(255,255,255,0.35)', color: '#fff', textAlign: 'center', textAlignVertical: 'center', fontSize: 10, fontFamily: 'Montserrat_700Bold_Italic' },
  credibilityLabel: { color: '#fff', fontSize: 7, fontFamily: 'Montserrat_600SemiBold_Italic' },
  source: { color: '#fff', backgroundColor: 'rgba(14,24,31,0.48)', paddingHorizontal: 6, paddingVertical: 4, borderRadius: 10, fontSize: 8, fontFamily: 'Montserrat_600SemiBold_Italic' },
  bodyLabel: { color: '#fff', fontSize: 13, fontFamily: 'Montserrat_700Bold_Italic', marginTop: 10, marginBottom: 6 },
  bodyInput: { minHeight: 150, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 14, borderWidth: 1, borderColor: 'rgba(255,255,255,0.18)', padding: 12, color: '#fff', textAlignVertical: 'top', fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic' },
  publishButton: { marginTop: 20, backgroundColor: palette.mint, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  publishText: { color: '#0b2b2b', fontSize: 18, fontFamily: 'Montserrat_700Bold_Italic' },
});
