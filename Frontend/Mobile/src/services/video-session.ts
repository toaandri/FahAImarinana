import type { VideoAnalysis } from './vision';

export type RecordedClip = {
  sequence: number;
  uri: string;
  capturedAt: string;
  durationSeconds: number;
  analysis?: VideoAnalysis;
  error?: string;
};

export type VideoReport = {
  captureId: string;
  startedAt: string;
  endedAt?: string;
  clips: RecordedClip[];
};

// Private, in-memory session only. Never route footage or transcripts through URL params.
let report: VideoReport | null = null;

export function setVideoReport(value: VideoReport | null) {
  report = value;
}

export function getVideoReport() {
  return report;
}
