import { StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { colors } from '../theme';

export const authTypography = { fontSize: 16, lineHeight: 24, fontStyle: 'italic' as const };

export function AuthBrand() {
  const { width } = useWindowDimensions();
  const wordSize = width < 360 ? 19 : width < 480 ? 26 : 34;
  return (
    <View accessible accessibilityLabel="FAH AI MARINANA" style={styles.logo}>
      <Text style={[styles.word, { fontSize: wordSize, lineHeight: wordSize * 1.25 }]}>FAH</Text>
      <Text style={[styles.word, styles.accent, { fontSize: wordSize * 1.54, lineHeight: wordSize * 1.54 * 1.25 }]}>AI</Text>
      <Text style={[styles.word, { fontSize: wordSize, lineHeight: wordSize * 1.25 }]}>MARINANA</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  logo: { flexDirection: 'row', alignItems: 'baseline', justifyContent: 'center', gap: 6 },
  word: { color: colors.white, fontWeight: '800', fontStyle: 'italic', letterSpacing: -1, includeFontPadding: false },
  accent: { color: colors.accent },
});
