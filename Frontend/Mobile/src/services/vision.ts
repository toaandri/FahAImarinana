import { File } from 'expo-file-system';
import { apiRequest } from './api';
import { readMediaBase64 } from './media';
import type { RecordedClip } from './video-session';

export type VisionCapabilities = {
  capture_id: string;
  configured: boolean;
  provider: 'gemini';
  model: string;
  clip_seconds: number;
  max_video_bytes: number;
  max_duration_seconds: number;
  requires_human_review: true;
};

export type VideoAnalysis = {
  id: number;
  status: 'running' | 'completed' | 'failed';
  capture_key: string;
  empreinte_sha256: string;
  cree_le: string;
  requires_human_review: true;
  result: {
    version: number;
    provider: 'gemini';
    model: string;
    capture_id: string;
    sequence: number;
    captured_at: string;
    duration_seconds: number;
    review_notice: string;
    error?: { code: string; message: string };
    analysis?: {
      title: string;
      summary: string;
      observations: { time_seconds: number; description: string }[];
      limitations: string[];
      questions_to_verify: string[];
    };
  };
};

export function getVisionCapabilities(signal?: AbortSignal) {
  return apiRequest<VisionCapabilities>('/vision/status', { signal });
}

export async function analyzeVideoClip(
  captureId: string, clip: RecordedClip, maxBytes: number, signal?: AbortSignal,
) {
  const file = new File(clip.uri);
  if (!file.exists || file.size <= 0) throw new Error('Le clip enregistré est vide ou introuvable.');
  if (file.size > maxBytes) throw new Error('Le clip dépasse 4 Mio. Réduisez sa durée ou sa qualité.');
  const videoBase64 = await file.base64();
  if (signal?.aborted) throw new Error('Envoi du clip interrompu.');
  return apiRequest<VideoAnalysis>('/vision/video', {
    method: 'POST', signal,
    body: JSON.stringify({
      capture_id: captureId, sequence: clip.sequence, captured_at: clip.capturedAt,
      duration_seconds: clip.durationSeconds,
      mime_type: /\.mov(?:$|\?)/i.test(clip.uri) ? 'video/quicktime' : 'video/mp4',
      video_base64: videoBase64, language: 'fr',
    }),
  });
}

export function getVideoAnalyses(captureId: string) {
  return apiRequest<VideoAnalysis[]>('/vision/analyses?capture_id=' + encodeURIComponent(captureId));
}

export type PublicationMedia = { uri: string; type?: string | null; mimeType?: string | null; duration?: number | null; fileName?: string | null };
export type PublicationAnalysis = { labels: string[]; text: string; notice: string; summary?: string };

export async function analyzePublicationMedia(media: PublicationMedia, signal?: AbortSignal): Promise<PublicationAnalysis> {
  if (media.type !== 'image' && media.type !== 'video') throw new Error('Type de média non reconnu.');
  const durationSeconds = typeof media.duration === 'number' ? media.duration / 1000 : null;
  if (media.type === 'video' && (durationSeconds == null || durationSeconds <= 0 || durationSeconds > 10)) {
    throw new Error('Choisissez un clip vidéo dont la durée est connue et ne dépasse pas 10 secondes.');
  }
  const encoded = await readMediaBase64(media.uri, 4 * 1024 * 1024, signal);
  if (signal?.aborted) throw new Error('Analyse interrompue.');
  if (media.type === 'image') {
    return apiRequest<PublicationAnalysis>('/vision/image', { method: 'POST', signal, body: JSON.stringify({ image_base64: encoded }) });
  }
  const capabilities = await getVisionCapabilities(signal);
  if (!capabilities.configured) throw new Error('Analyse vidéo indisponible : Gemini n’est pas configuré.');
  const isMov = media.mimeType === 'video/quicktime' || /\.mov(?:$|\?)/i.test(media.fileName || media.uri);
  if (media.mimeType && media.mimeType !== 'video/mp4' && media.mimeType !== 'video/quicktime') {
    throw new Error('Pour l’analyse, choisissez une vidéo MP4 ou MOV.');
  }
  const video = await apiRequest<VideoAnalysis>('/vision/video', { method: 'POST', signal, body: JSON.stringify({
    capture_id: capabilities.capture_id, sequence: 1, captured_at: new Date().toISOString(),
    duration_seconds: durationSeconds, mime_type: isMov ? 'video/quicktime' : 'video/mp4', video_base64: encoded, language: 'fr',
  }) });
  const analysis = video.result?.analysis;
  if (!analysis) throw new Error(video.result?.error?.message || 'Analyse vidéo indisponible.');
  return { labels: analysis.observations.map((item) => item.description), text: '', summary: analysis.summary,
    notice: 'Ces observations ne déterminent pas si la vidéo est authentique, fausse ou générée par IA. Vérification humaine nécessaire.' };
}
