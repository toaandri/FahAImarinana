import { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, AppState, Linking, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions, useMicrophonePermissions } from 'expo-camera';
import { router, useFocusEffect } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { palette } from '@/theme/theme';
import { analyzeVideoClip, getVisionCapabilities, type VideoAnalysis } from '@/services/vision';
import { getVideoReport, setVideoReport, type RecordedClip, type VideoReport } from '@/services/video-session';

const MAX_CLIPS = 10;
const secondsLabel = (value: number) => `${Math.floor(value / 60).toString().padStart(2, '0')}:${Math.floor(value % 60).toString().padStart(2, '0')}`;
type Phase = 'idle' | 'preparing' | 'recording' | 'analysing' | 'stopping';

export default function DirectScreen() {
  const camera = useRef<CameraView | null>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [microphone, requestMicrophone] = useMicrophonePermissions();
  const [facing, setFacing] = useState<'back' | 'front'>('back');
  const [audio, setAudio] = useState(false);
  const [ready, setReady] = useState(false);
  const [visible, setVisible] = useState(true);
  const [phase, setPhase] = useState<Phase>('idle');
  const [error, setError] = useState('');
  const [duration, setDuration] = useState(0);
  const [clipCount, setClipCount] = useState(0);
  const [latest, setLatest] = useState<VideoAnalysis | null>(null);
  const active = useRef(false);
  const runningLoop = useRef(false);
  const recordingClip = useRef(false);
  const mounted = useRef(true);
  const finishRequested = useRef(false);
  const controller = useRef<AbortController | null>(null);
  const recordedDuration = useRef(0);
  const currentReport = useRef<VideoReport | null>(null);
  const busy = phase !== 'idle';

  const interrupt = useCallback(() => {
    const wasActive = active.current || runningLoop.current;
    active.current = false;
    finishRequested.current = false;
    controller.current?.abort();
    if (recordingClip.current) {
      try { camera.current?.stopRecording(); } catch { /* Camera may already be stopped. */ }
    }
    recordingClip.current = false;
    if (wasActive && currentReport.current) currentReport.current.endedAt = new Date().toISOString();
  }, []);

  useFocusEffect(useCallback(() => {
    mounted.current = true;
    setVisible(true);
    setPhase('idle');
    setReady(false);
    const previous = getVideoReport();
    currentReport.current = previous;
    setClipCount(previous?.clips.length ?? 0);
    setDuration(previous?.clips.reduce((sum, clip) => sum + clip.durationSeconds, 0) ?? 0);
    setLatest(previous?.clips.filter((clip) => clip.analysis?.status === 'completed').at(-1)?.analysis ?? null);
    return () => {
      mounted.current = false;
      interrupt();
      setVisible(false);
    };
  }, [interrupt]));

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (state) => {
      if (state !== 'active') {
        const wasRecording = runningLoop.current;
        interrupt();
        if (mounted.current) {
          setVisible(false); setReady(false);
          if (wasRecording) setError('Capture interrompue en arrière-plan. Consultez le rapport pour les résultats déjà reçus.');
        }
      } else if (mounted.current) {
        setVisible(true);
      }
    });
    return () => subscription.remove();
  }, [interrupt]);

  const toggleAudio = async () => {
    if (busy) return;
    if (audio) { setAudio(false); return; }
    try {
      const result = microphone?.granted ? microphone : await requestMicrophone();
      if (!result.granted) { setError('Accès microphone refusé. Vous pouvez filmer sans audio.'); return; }
      setError(''); setAudio(true);
    } catch {
      setError('Microphone indisponible. Vous pouvez filmer sans audio.');
    }
  };

  const start = async () => {
    if (runningLoop.current || active.current || busy || !ready || !camera.current) return;
    runningLoop.current = true;
    active.current = true;
    finishRequested.current = false;
    setError(''); setPhase('preparing');
    const abort = new AbortController(); controller.current = abort;
    let report: VideoReport | null = null;
    let failed = false;
    try {
      const capabilities = await getVisionCapabilities(abort.signal);
      if (!capabilities.configured) throw new Error('Gemini Vision est indisponible : configurez la clé sur le backend.');
      if (!active.current || !mounted.current) return;
      report = { captureId: capabilities.capture_id, startedAt: new Date().toISOString(), clips: [] };
      setLatest(null); setDuration(0); setClipCount(0);
      currentReport.current = report; setVideoReport(report);
      let total = 0;
      for (let sequence = 1; active.current && sequence <= MAX_CLIPS; sequence++) {
        if (!camera.current) break;
        const started = Date.now(); recordedDuration.current = 0;
        setPhase('recording');
        recordingClip.current = true;
        const video = await camera.current.recordAsync({
          maxDuration: capabilities.clip_seconds,
          maxFileSize: capabilities.max_video_bytes - 65536,
          ...(Platform.OS === 'ios' ? { codec: 'avc1' as const } : {}),
        });
        recordingClip.current = false;
        if (!video?.uri) {
          if (!active.current) break;
          throw new Error('La caméra n’a enregistré aucun clip.');
        }
        const clip: RecordedClip = {
          sequence, uri: video.uri, capturedAt: new Date(started).toISOString(),
          durationSeconds: Math.max(0.1, recordedDuration.current,
            Math.min(capabilities.clip_seconds, (Date.now() - started) / 1000)),
        };
        report.clips.push(clip); total += clip.durationSeconds;
        if (!mounted.current || abort.signal.aborted) {
          clip.error = 'Analyse non envoyée : capture interrompue.'; break;
        }
        setDuration(total); setClipCount(sequence); setPhase('analysing');
        try {
          const result = await analyzeVideoClip(report.captureId, clip, capabilities.max_video_bytes, abort.signal);
          clip.analysis = result;
          if (mounted.current) setLatest(result);
        } catch (problem) {
          clip.error = problem instanceof Error ? problem.message : 'Analyse indisponible.';
          throw problem;
        }
      }
    } catch (problem) {
      failed = true;
      if (mounted.current) setError(problem instanceof Error ? problem.message : 'La capture vidéo a échoué.');
    } finally {
      runningLoop.current = false;
      recordingClip.current = false;
      active.current = false;
      if (report) report.endedAt = new Date().toISOString();
      if (mounted.current) {
        setPhase('idle');
        if (report?.clips.length && (!failed || finishRequested.current)) router.push('/terminer');
      }
    }
  };

  const stop = () => {
    if (!active.current) return;
    active.current = false; finishRequested.current = true;
    if (recordingClip.current) {
      try { camera.current?.stopRecording(); } catch { /* The native recorder may have just completed. */ }
    }
    recordingClip.current = false;
    setPhase('stopping');
  };
  const observed = latest?.result.analysis;
  const phaseLabel = phase === 'recording' ? '● ENREGISTREMENT' : phase === 'analysing' ? 'ANALYSE GEMINI' : phase === 'preparing' ? 'CONNEXION' : phase === 'stopping' ? 'FINALISATION' : 'CAMÉRA PRÊTE';

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.header}>
        <Pressable accessibilityLabel="Retour" disabled={busy} onPress={() => router.back()}><Ionicons name="chevron-back" size={24} color="#fff" /></Pressable>
        <Text style={styles.heading}>Reportage · Gemini Vision</Text>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.videoCard}>
          {Platform.OS === 'web' ? <Text style={styles.notice}>La capture vidéo nécessite Expo Go sur un téléphone Android ou iOS.</Text> : !permission ? <ActivityIndicator color={palette.mint} /> : !permission.granted ? (
            <View style={styles.permission}>
              <Text style={styles.notice}>Autorisez la caméra pour filmer votre reportage.</Text>
              <Pressable style={styles.action} onPress={() => { void (permission.canAskAgain ? requestPermission() : Linking.openSettings()).catch(() => setError('Impossible d’ouvrir les autorisations.')); }}>
                <Text style={styles.actionText}>{permission.canAskAgain ? 'Autoriser la caméra' : 'Ouvrir les paramètres'}</Text>
              </Pressable>
            </View>
          ) : visible ? (
            <CameraView ref={camera} style={styles.preview} facing={facing} mode="video" mute={!audio} videoQuality="720p" videoBitrate={800000}
              onCameraReady={() => setReady(true)}
              onMountError={() => { interrupt(); setReady(false); setPhase('idle'); setError('La caméra ne peut pas démarrer sur cet appareil.'); }}
              onRecordingProgress={({ duration: value }) => {
                if (!recordingClip.current) return;
                recordedDuration.current = value;
                const total = currentReport.current?.clips.reduce((sum, clip) => sum + clip.durationSeconds, 0) ?? 0;
                setDuration(total + value);
              }} />
          ) : null}
          <View style={styles.badge}><Text style={styles.badgeText}>{phaseLabel}</Text><Text style={styles.timer}>{secondsLabel(duration)}</Text></View>
        </View>
        <View style={styles.controls}>
          <Pressable accessibilityLabel={audio ? 'Couper le microphone' : 'Activer le microphone'} disabled={busy} style={styles.smallButton} onPress={() => { void toggleAudio(); }}>
            <Ionicons name={audio ? 'mic-outline' : 'mic-off-outline'} size={24} color="#fff" />
          </Pressable>
          <Pressable accessibilityLabel={busy ? 'Arrêter la capture' : 'Démarrer la capture et l’analyse'} disabled={(!busy && (!ready || Platform.OS === 'web')) || phase === 'stopping'}
            style={[styles.recordButton, !ready && styles.disabled]} onPress={() => { if (busy) stop(); else void start(); }}>
            {busy ? <View style={styles.stopSquare} /> : <Ionicons name="videocam" size={30} color={palette.ink} />}
          </Pressable>
          <Pressable accessibilityLabel="Changer de caméra" disabled={busy} style={styles.smallButton} onPress={() => { setReady(false); setFacing((value) => value === 'back' ? 'front' : 'back'); }}>
            <Ionicons name="camera-reverse-outline" size={24} color="#fff" />
          </Pressable>
        </View>
        <Text style={styles.caption}>{busy ? `${clipCount} clip(s) enregistré(s). Capture et analyse successives.` : `Démarrer et analyser · ${audio ? 'microphone activé' : 'sans audio'}`}</Text>
        <Text style={styles.notice}>Clips de 6 secondes, puis envoi à Gemini pour analyse. Jusqu’à 10 clips par session. La réponse dépend du réseau et du moteur ; ce n’est pas un flux continu sans interruption.</Text>
        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        {(phase === 'analysing' || phase === 'preparing' || phase === 'stopping') ? <ActivityIndicator color={palette.mint} /> : null}
        <View style={styles.articleCard}>
          <Text style={styles.label}>OBSERVATIONS PROVISOIRES</Text>
          {observed && latest ? <>
            <Text style={styles.notice}>Clip {latest.result.sequence} · capturé à {new Date(latest.result.captured_at).toLocaleTimeString('fr-FR')}</Text>
            <Text style={styles.title}>{observed.title}</Text><Text style={styles.body}>{observed.summary}</Text>
            {observed.observations.map((item, index) => <Text key={index} style={styles.body}>{item.time_seconds.toFixed(1)} s · {item.description}</Text>)}
            {observed.limitations.map((item, index) => <Text key={index} style={styles.limit}>Limite : {item}</Text>)}
          </> : <Text style={styles.body}>Aucune analyse reçue. Les observations apparaîtront après le premier clip traité.</Text>}
        </View>
        {!busy && clipCount > 0 ? <Pressable style={styles.action} onPress={() => router.push('/terminer')}><Text style={styles.actionText}>Voir le rapport et les clips</Text></Pressable> : null}
        <Text style={styles.notice}>Les clips sont conservés temporairement dans le cache privé de l’application. Les observations ne prouvent ni le lieu, ni la date, ni la véracité d’une affirmation. Validation humaine obligatoire.</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
  heading: { flex: 1, color: '#fff', fontFamily: 'Montserrat_700Bold_Italic', fontSize: 17 },
  content: { padding: 16, paddingBottom: 40, gap: 16 },
  videoCard: { height: 300, borderRadius: 20, overflow: 'hidden', backgroundColor: '#14262c', justifyContent: 'center' },
  preview: { flex: 1 },
  permission: { padding: 20, gap: 18 },
  badge: { position: 'absolute', top: 12, left: 12, right: 12, flexDirection: 'row', justifyContent: 'space-between', pointerEvents: 'none' },
  badgeText: { backgroundColor: '#14262c', padding: 6, borderRadius: 6, color: palette.mint, fontSize: 11 },
  timer: { backgroundColor: '#14262c', padding: 6, color: '#fff', fontVariant: ['tabular-nums'] },
  controls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around' },
  smallButton: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#25373b', justifyContent: 'center', alignItems: 'center' },
  recordButton: { width: 76, height: 76, borderRadius: 38, backgroundColor: palette.mint, justifyContent: 'center', alignItems: 'center' },
  disabled: { opacity: 0.4 },
  stopSquare: { width: 24, height: 24, borderRadius: 4, backgroundColor: palette.ink },
  caption: { color: '#fff', textAlign: 'center', fontSize: 12 },
  notice: { color: '#b8cbcf', fontSize: 12, lineHeight: 19 },
  error: { color: '#ffaaaa', fontSize: 14, lineHeight: 21 },
  articleCard: { padding: 16, borderRadius: 18, backgroundColor: 'rgba(255,255,255,0.07)', gap: 10 },
  label: { color: palette.mint, fontFamily: 'Montserrat_700Bold_Italic', fontSize: 12 },
  title: { color: '#fff', fontFamily: 'Montserrat_700Bold_Italic', fontSize: 18 },
  body: { color: '#fff', fontSize: 13, lineHeight: 21 },
  limit: { color: '#ddcf98', fontSize: 12, lineHeight: 19 },
  action: { backgroundColor: palette.mint, padding: 14, borderRadius: 12, alignItems: 'center' },
  actionText: { color: palette.ink, fontFamily: 'Montserrat_700Bold_Italic' },
});
