import { useState } from 'react';
import { View, Text, StyleSheet, Pressable, TextInput, ScrollView, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
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
        <Text style={styles.titleLabel}>Publier votre article</Text>
        <TextInput value={title} onChangeText={setTitle} placeholder="Le titre de votre article" placeholderTextColor="rgba(255,255,255,0.5)" style={styles.titleInput} />

        <View style={styles.chipRow}>
          {['Politique', 'Société', 'Sport', 'Économie'].map((item) => (
            <Pressable key={item} onPress={() => setCategory(item)}>
              <TagChip label={item} active={category === item} small />
            </Pressable>
          ))}
        </View>

        <GlassCard style={styles.mediaCard}>
          <View style={styles.mediaButton}><Text style={styles.mediaPlus}>+</Text></View>
          <View style={styles.mediaActions}><Text style={styles.mediaAction}>Photo</Text><Text style={styles.mediaAction}>Vidéo</Text></View>
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
  titleLabel: { color: '#fff', fontSize: 20, fontFamily: 'Montserrat_700Bold_Italic', marginBottom: 12 },
  titleInput: { borderBottomWidth: 1, borderBottomColor: palette.mint, color: '#fff', paddingBottom: 8, fontSize: 16, fontFamily: 'Montserrat_700Bold_Italic' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 16, marginBottom: 18 },
  mediaCard: { padding: 16, minHeight: 180, justifyContent: 'space-between' },
  mediaButton: { width: 76, height: 76, borderRadius: 38, backgroundColor: palette.mint, alignSelf: 'center', alignItems: 'center', justifyContent: 'center' },
  mediaPlus: { color: '#0b2b2b', fontSize: 36, fontWeight: '800' },
  mediaActions: { flexDirection: 'row', gap: 12 },
  mediaAction: { color: '#fff', fontFamily: 'Montserrat_600SemiBold_Italic', fontSize: 12 },
  bodyLabel: { color: '#fff', fontSize: 16, fontFamily: 'Montserrat_700Bold_Italic', marginTop: 18, marginBottom: 8 },
  bodyInput: { minHeight: 120, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 14, padding: 14, color: '#fff', textAlignVertical: 'top', fontSize: 13, fontFamily: 'Montserrat_600SemiBold_Italic' },
  publishButton: { marginTop: 20, backgroundColor: palette.mint, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  publishText: { color: '#0b2b2b', fontSize: 18, fontFamily: 'Montserrat_700Bold_Italic' },
});
