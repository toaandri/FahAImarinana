import React from 'react';
import { Text, View, StyleSheet } from 'react-native';
import { palette } from '@/theme/theme';

type LogoProps = {
  compact?: boolean;
};

export function Logo({ compact = false }: LogoProps) {
  const wordSize = compact ? 19 : 26;
  const accentSize = compact ? 30 : 40;

  return (
    <View style={styles.container}>
      <Text style={[styles.word, { fontSize: wordSize }]}>FAH</Text>
      <Text style={[styles.accent, { fontSize: accentSize }]}>AI</Text>
      <Text style={[styles.word, { fontSize: wordSize }]}>MARINANA</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
  },
  word: {
    color: '#fff',
    fontWeight: '800',
    fontStyle: 'italic',
    letterSpacing: -1,
    fontFamily: 'Montserrat_800ExtraBold_Italic',
  },
  accent: {
    color: palette.mint,
    fontWeight: '800',
    fontStyle: 'italic',
    letterSpacing: -1,
    fontFamily: 'Montserrat_800ExtraBold_Italic',
  },
});
