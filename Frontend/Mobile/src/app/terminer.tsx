import { useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { File } from 'expo-file-system';
import { palette } from '@/theme/theme';
import { getVideoReport, setVideoReport } from '@/services/video-session';
import { getVideoAnalyses } from '@/services/vision';

export default function TerminerScreen() {
  const [report, setReport] = useState(() => getVideoReport());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const total = report?.clips.reduce((sum, clip) => sum + clip.durationSeconds, 0) ?? 0;
  const refresh = async () => {
    if (!report || loading) return;
    setLoading(true); setError('');
    try {
      const analyses = await getVideoAnalyses(report.captureId);
      const updated = { ...report, clips: report.clips.map((clip) => {
        const result = analyses.find((item) => item.result.sequence === clip.sequence);
        return result ? { ...clip, analysis: result,
          error: result.status === 'failed' ? result.result.error?.message : undefined } : clip;
      }) };
      setVideoReport(updated); setReport(updated);
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'Rapport indisponible.');
    } finally { setLoading(false); }
  };
  const preview = async (uri: string) => {
    try { await new File(uri).preview(); }
    catch { Alert.alert('Lecture indisponible', 'Le clip temporaire est absent ou aucun lecteur compatible n’est disponible.'); }
  };

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.heading}>Rapport vidéo privé</Text>
        {!report?.clips.length ? <>
          <Text style={styles.body}>Aucun clip enregistré dans cette session. Filmez un reportage pour recevoir des observations Gemini Vision.</Text>
          <Pressable style={styles.button} onPress={() => router.replace('/direct')}><Text style={styles.buttonText}>Ouvrir la caméra</Text></Pressable>
        </> : <>
          <Text style={styles.body}>{report.clips.length} clip(s) · {total.toFixed(1)} secondes enregistrées</Text>
          <Text style={styles.notice}>Les clips ne forment pas un enregistrement continu. Chaque clip a été analysé séparément. Les fichiers vidéo restent dans le cache privé du téléphone, susceptible d’être nettoyé par le système.</Text>
          {report.clips.map((clip) => {
            const analysis = clip.analysis?.result.analysis;
            return <View key={clip.sequence} style={styles.card}>
              <Text style={styles.clipTitle}>Clip {clip.sequence} · {clip.durationSeconds.toFixed(1)} s</Text>
              <Text style={styles.notice}>Capture : {new Date(clip.capturedAt).toLocaleTimeString('fr-FR')}</Text>
              <Pressable style={styles.outlineButton} onPress={() => { void preview(clip.uri); }}><Text style={styles.body}>Voir le clip enregistré</Text></Pressable>
              {analysis && clip.analysis?.status === 'completed' ? <>
                <Text style={styles.title}>{analysis.title}</Text><Text style={styles.body}>{analysis.summary}</Text>
                {analysis.observations.map((item, index) => <Text key={index} style={styles.body}>{item.time_seconds.toFixed(1)} s · {item.description}</Text>)}
                <Text style={styles.label}>LIMITES</Text>
                {analysis.limitations.map((item, index) => <Text key={index} style={styles.notice}>{item}</Text>)}
                <Text style={styles.label}>À VÉRIFIER</Text>
                {analysis.questions_to_verify.map((item, index) => <Text key={index} style={styles.body}>{item}</Text>)}
                <Text style={styles.notice}>Analyse privée enregistrée · référence {clip.analysis.id}</Text>
              </> : <Text style={styles.error}>{clip.error || clip.analysis?.result.error?.message || 'Résultat non reçu. Actualisez pour consulter l’état côté serveur.'}</Text>}
            </View>;
          })}
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <Pressable style={styles.button} disabled={loading} onPress={() => { void refresh(); }}>
            {loading ? <ActivityIndicator color={palette.ink} /> : <Text style={styles.buttonText}>Actualiser les analyses enregistrées</Text>}
          </Pressable>
          <Text style={styles.warning}>Pré-analyse IA uniquement. Aucun verdict de véracité et aucune publication automatique. La validation finale appartient à un éditeur autorisé.</Text>
          <Pressable style={styles.outlineButton} onPress={() => router.replace('/home')}><Text style={styles.body}>Retour à l’accueil</Text></Pressable>
        </>}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  content: { padding: 20, paddingBottom: 40, gap: 16 },
  heading: { color: '#fff', fontSize: 23, fontFamily: 'Montserrat_700Bold_Italic' },
  card: { padding: 16, borderRadius: 18, backgroundColor: 'rgba(255,255,255,0.07)', gap: 12 },
  clipTitle: { color: palette.mint, fontSize: 16, fontFamily: 'Montserrat_700Bold_Italic' },
  title: { color: '#fff', fontSize: 18, fontFamily: 'Montserrat_700Bold_Italic' },
  label: { color: palette.mint, fontSize: 12, fontFamily: 'Montserrat_700Bold_Italic' },
  body: { color: '#fff', fontSize: 13, lineHeight: 21 },
  notice: { color: '#b8cbcf', fontSize: 12, lineHeight: 19 },
  warning: { color: '#e7d899', fontSize: 13, lineHeight: 21 },
  error: { color: '#ffaaaa', fontSize: 13, lineHeight: 21 },
  button: { padding: 14, borderRadius: 12, backgroundColor: palette.mint, alignItems: 'center' },
  buttonText: { color: palette.ink, fontFamily: 'Montserrat_700Bold_Italic', textAlign: 'center' },
  outlineButton: { padding: 12, borderRadius: 12, borderColor: palette.mint, borderWidth: 1, alignItems: 'center' },
});
