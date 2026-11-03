import { File } from 'expo-file-system';
import { Platform } from 'react-native';

export async function readMediaBase64(uri: string, maxBytes: number, signal?: AbortSignal): Promise<string> {
  if (signal?.aborted) throw new Error('Lecture du média interrompue.');
  if (Platform.OS !== 'web') {
    try {
      const file = new File(uri);
      if (!file.exists || file.size <= 0) throw new Error('Le média est vide ou introuvable.');
      if (file.size > maxBytes) throw new Error(`Le média dépasse ${Math.round(maxBytes / (1024 * 1024))} Mio.`);
      const encoded = await file.base64();
      if (signal?.aborted) throw new Error('Lecture du média interrompue.');
      if (!encoded) throw new Error('Le média est vide ou introuvable.');
      return encoded;
    } catch (error) {
      if (error instanceof Error && (error.message.startsWith('Le média') || error.message === 'Lecture du média interrompue.')) throw error;
      throw new Error('Impossible de lire le média sélectionné sur cet appareil.');
    }
  }
  const response = await fetch(uri, { signal });
  if (!response.ok) throw new Error('Impossible de lire le média sélectionné.');
  const blob = await response.blob();
  if (!blob.size) throw new Error('Le média est vide ou introuvable.');
  if (blob.size > maxBytes) throw new Error(`Le média dépasse ${Math.round(maxBytes / (1024 * 1024))} Mio.`);
  const encoded = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => typeof reader.result === 'string' ? resolve(reader.result.split(',')[1] || '') : reject(new Error('Média illisible.'));
    reader.onerror = () => reject(new Error('Média illisible.'));
    reader.readAsDataURL(blob);
  });
  if (signal?.aborted) throw new Error('Lecture du média interrompue.');
  if (!encoded) throw new Error('Le média est vide ou introuvable.');
  return encoded;
}
