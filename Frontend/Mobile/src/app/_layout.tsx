import { Stack } from 'expo-router';
import { useFonts } from 'expo-font';
import { View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { palette } from '@/theme/theme';

export default function RootLayout() {
  const [loaded] = useFonts({
    Montserrat_600SemiBold_Italic: require('@expo-google-fonts/montserrat/600SemiBold_Italic/Montserrat_600SemiBold_Italic.ttf'),
    Montserrat_700Bold_Italic: require('@expo-google-fonts/montserrat/700Bold_Italic/Montserrat_700Bold_Italic.ttf'),
    Montserrat_800ExtraBold: require('@expo-google-fonts/montserrat/800ExtraBold/Montserrat_800ExtraBold.ttf'),
    Montserrat_800ExtraBold_Italic: require('@expo-google-fonts/montserrat/800ExtraBold_Italic/Montserrat_800ExtraBold_Italic.ttf'),
  });

  if (!loaded) {
    return <View style={{ flex: 1, backgroundColor: palette.background }} />;
  }

  return (
    <>
      <StatusBar style="light" />
      <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }} />
    </>
  );
}
