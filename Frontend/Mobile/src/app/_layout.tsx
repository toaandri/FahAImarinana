import { Stack, usePathname } from 'expo-router';
import { useFonts } from 'expo-font';
import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Animated, Easing, Platform, StyleSheet, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { palette } from '@/theme/theme';
import { LanguageProvider } from '@/i18n/LanguageProvider';
import { restoreTokens } from '@/services/api';

export default function RootLayout() {
  const pathname = usePathname();
  const previousPath = useRef(pathname);
  const [transitionProgress] = useState(() => new Animated.Value(1));
  const isWeb = Platform.OS === 'web';
  const [loaded] = useFonts({
    Montserrat_600SemiBold_Italic: require('@expo-google-fonts/montserrat/600SemiBold_Italic/Montserrat_600SemiBold_Italic.ttf'),
    Montserrat_700Bold_Italic: require('@expo-google-fonts/montserrat/700Bold_Italic/Montserrat_700Bold_Italic.ttf'),
    Montserrat_800ExtraBold: require('@expo-google-fonts/montserrat/800ExtraBold/Montserrat_800ExtraBold.ttf'),
    Montserrat_800ExtraBold_Italic: require('@expo-google-fonts/montserrat/800ExtraBold_Italic/Montserrat_800ExtraBold_Italic.ttf'),
  });
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    restoreTokens().finally(() => setAuthReady(true));
  }, []);

  useLayoutEffect(() => {
    if (previousPath.current === pathname) return;
    previousPath.current = pathname;
    if (!isWeb) return;

    transitionProgress.setValue(0);
    Animated.timing(transitionProgress, {
      toValue: 1,
      duration: 220,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
      isInteraction: false,
    }).start();
  }, [isWeb, pathname, transitionProgress]);

  const transitionStyle = {
    opacity: transitionProgress.interpolate({ inputRange: [0, 1], outputRange: [0.9, 1] }),
    transform: [{ translateY: transitionProgress.interpolate({ inputRange: [0, 1], outputRange: [8, 0] }) }],
  };

  if (!loaded || !authReady) {
    return <View style={{ flex: 1, backgroundColor: palette.background }} />;
  }

  return (
    <LanguageProvider>
      <StatusBar style="light" />
      <Animated.View style={[styles.navigator, isWeb && transitionStyle]}>
        <Stack screenOptions={{ headerShown: false, animation: 'default' }} />
      </Animated.View>
    </LanguageProvider>
  );
}

const styles = StyleSheet.create({
  navigator: { flex: 1 },
});
