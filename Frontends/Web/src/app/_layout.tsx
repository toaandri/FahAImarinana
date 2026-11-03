import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { InteractionProvider } from '../components/ui';
import { LanguageProvider } from '../components/i18n';
import { colors } from '../theme';

export default function RootLayout() {
  return (
    <LanguageProvider>
      <InteractionProvider>
        <>
          <StatusBar style="auto" />
          <Stack
            screenOptions={{
              headerShown: false,
              contentStyle: { backgroundColor: colors.background },
              animation: 'none',
            }}
          />
        </>
      </InteractionProvider>
    </LanguageProvider>
  );
}
