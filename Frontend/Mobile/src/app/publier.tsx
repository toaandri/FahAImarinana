import { useState } from 'react';
import { View, Text, StyleSheet, Pressable, TextInput, ScrollView, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { HeaderBar, BottomTabs, GlassCard, TagChip } from '@/components/ui';
import { palette } from '@/theme/theme';
import { publishArticle } from '@/services/mockData';

export default function PublierScreen() {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [category, setCategory] = useState('Politique');

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
            <View style={styles.mediaButton}><Text style={styles.mediaPlus}>+</Text></View>
            <View style={styles.mediaActions}>
              <View style={styles.mediaAction}><Ionicons name="image-outline" size={11} color="#fff" /><Text style={styles.mediaActionText}>Photo</Text></View>
              <View style={styles.mediaAction}><Ionicons name="videocam-outline" size={11} color="#fff" /><Text style={styles.mediaActionText}>Vidéo</Text></View>
            </View>
          </View>
          <View style={styles.mediaDetails}>
            <Text style={styles.credibility}>—%</Text>
            <Text style={styles.credibilityLabel}>Crédibilité</Text>
            <Text style={styles.source}>Source</Text>
          </View>
        </GlassCard>

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
  mediaActions: { flexDirection: 'row', gap: 6 },
  mediaAction: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: 'rgba(14,24,31,0.48)', borderRadius: 14, paddingHorizontal: 8, paddingVertical: 5 },
  mediaActionText: { color: '#fff', fontFamily: 'Montserrat_600SemiBold_Italic', fontSize: 9 },
  mediaDetails: { width: 48, alignItems: 'center', justifyContent: 'space-between', paddingVertical: 6 },
  credibility: { width: 36, height: 36, borderRadius: 18, borderWidth: 3, borderColor: 'rgba(255,255,255,0.35)', color: '#fff', textAlign: 'center', textAlignVertical: 'center', fontSize: 10, fontFamily: 'Montserrat_700Bold_Italic' },
  credibilityLabel: { color: '#fff', fontSize: 7, fontFamily: 'Montserrat_600SemiBold_Italic' },
  source: { color: '#fff', backgroundColor: 'rgba(14,24,31,0.48)', paddingHorizontal: 6, paddingVertical: 4, borderRadius: 10, fontSize: 8, fontFamily: 'Montserrat_600SemiBold_Italic' },
  bodyLabel: { color: '#fff', fontSize: 13, fontFamily: 'Montserrat_700Bold_Italic', marginTop: 10, marginBottom: 6 },
  bodyInput: { minHeight: 150, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 14, borderWidth: 1, borderColor: 'rgba(255,255,255,0.18)', padding: 12, color: '#fff', textAlignVertical: 'top', fontSize: 12, fontFamily: 'Montserrat_600SemiBold_Italic' },
  publishButton: { marginTop: 20, backgroundColor: palette.mint, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  publishText: { color: '#0b2b2b', fontSize: 18, fontFamily: 'Montserrat_700Bold_Italic' },
});
