import React from 'react';
import { Text, View, StyleSheet } from 'react-native';
import { palette } from '@/theme/theme';

type LogoProps = {
  compact?: boolean;
};

export function Logo({ compact = false }: LogoProps) {
  const size = compact ? { fontSize: 18 } : { fontSize: 30 };
  const pillSize = compact ? { width: 38, height: 22, borderRadius: 8 } : { width: 54, height: 30, borderRadius: 10 };

  return (
    <View style={styles.container}>
      <Text style={[styles.word, size]}>FAH</Text>
      <View style={[styles.pill, pillSize]}>
        <Text style={[styles.pillText, compact ? { fontSize: 12 } : { fontSize: 18 }]}>AI</Text>
      </View>
      <Text style={[styles.word, size]}>MARINANA</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  word: {
    color: '#fff',
    fontWeight: '800',
    fontStyle: 'italic',
    letterSpacing: -1,
  },
  pill: {
    backgroundColor: palette.mint,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 6,
    shadowColor: palette.shadow,
    shadowOpacity: 0.18,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
  },
  pillText: {
    color: palette.ink,
    fontWeight: '800',
    fontStyle: 'italic',
  },
});
