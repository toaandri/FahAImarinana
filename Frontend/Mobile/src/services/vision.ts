import { File } from 'expo-file-system';
import { apiRequest } from './api';
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
