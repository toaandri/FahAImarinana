import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import fr from '@/locales/fr.json';
import en from '@/locales/en.json';
import mg from '@/locales/mg.json';

export type Language = 'fr' | 'en' | 'mg';
type TranslationKey = keyof typeof fr;
type Dictionary = Record<TranslationKey, string>;

const dictionaries: Record<Language, Dictionary> = { fr, en, mg };
const LANGUAGE_STORAGE_KEY = 'app-language';

type LanguageContextValue = {
  language: Language;
  ready: boolean;
  persistenceFailed: boolean;
  setLanguage: (language: Language) => Promise<void>;
  t: (key: TranslationKey, values?: Record<string, string | number>) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

async function readSavedLanguage(): Promise<Language | null> {
  let value: string | null;
  if (Platform.OS === 'web') {
    const storage = globalThis.localStorage;
    if (!storage) throw new Error('Browser storage is unavailable.');
    value = storage.getItem(LANGUAGE_STORAGE_KEY);
  } else {
    value = await SecureStore.getItemAsync(LANGUAGE_STORAGE_KEY);
  }
  return value === 'fr' || value === 'en' || value === 'mg' ? value : null;
}

async function saveLanguage(language: Language) {
  if (Platform.OS === 'web') {
    const storage = globalThis.localStorage;
    if (!storage) throw new Error('Browser storage is unavailable.');
    storage.setItem(LANGUAGE_STORAGE_KEY, language);
    return;
  }
  await SecureStore.setItemAsync(LANGUAGE_STORAGE_KEY, language);
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>('fr');
  const [ready, setReady] = useState(false);
  const [persistenceFailed, setPersistenceFailed] = useState(false);

  useEffect(() => {
    let active = true;
    readSavedLanguage()
      .then((saved) => {
        if (active && saved) setLanguageState(saved);
      })
      .catch((error: unknown) => {
        console.warn('Unable to load the saved language preference.', error);
        if (active) setPersistenceFailed(true);
      })
      .finally(() => {
        if (active) setReady(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const setLanguage = async (nextLanguage: Language) => {
    setLanguageState(nextLanguage);
    setPersistenceFailed(false);
    try {
      await saveLanguage(nextLanguage);
    } catch (error) {
      console.warn('Unable to save the language preference.', error);
      setPersistenceFailed(true);
    }
  };

  const value = useMemo<LanguageContextValue>(() => ({
    language,
    ready,
    persistenceFailed,
    setLanguage,
    t: (key, values) => {
      let text = dictionaries[language][key];
      if (values) {
        for (const [name, replacement] of Object.entries(values)) {
          text = text.replaceAll(`{${name}}`, String(replacement));
        }
      }
      return text;
    },
  }), [language, ready, persistenceFailed]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error('useLanguage must be used within a LanguageProvider.');
  return context;
}
