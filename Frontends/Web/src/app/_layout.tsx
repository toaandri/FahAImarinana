import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { InteractionProvider } from '../components/ui';
import { colors } from '../theme';

export default function RootLayout() {
  return (
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
  );
}
