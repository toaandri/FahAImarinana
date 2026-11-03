import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { palette } from '@/theme/theme';

type CredibilityRingProps = {
  value?: number | null;
  size?: number;
  label?: string;
};

export function CredibilityRing({ value = null, size = 60, label }: CredibilityRingProps) {
  const numericValue = value ?? 0;
  const radius = size / 2 - 5;
  const circumference = 2 * Math.PI * radius;
  const arc = Math.min(1, Math.max(0, numericValue / 100));
  const dashOffset = circumference * (1 - arc);

  return (
    <View style={styles.wrapper}>
      <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <Circle cx={size / 2} cy={size / 2} r={radius} stroke="rgba(255,255,255,0.24)" strokeWidth={4} fill="transparent" />
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={palette.mint}
          strokeWidth={4}
          fill="transparent"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </Svg>
      <Text style={[styles.value, { fontSize: Math.max(12, size * 0.23) }]}>{value == null ? '—' : `${numericValue} %`}</Text>
      {label ? <Text style={styles.label}>{label}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  value: {
    position: 'absolute',
    color: '#fff',
    fontWeight: '800',
    fontStyle: 'italic',
  },
  label: {
    marginTop: 8,
    fontSize: 10,
    color: 'rgba(255,255,255,0.8)',
    fontWeight: '600',
    fontStyle: 'italic',
  },
});
