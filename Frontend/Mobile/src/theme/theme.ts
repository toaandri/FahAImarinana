export const palette = {
  background: '#3B4D52',
  backgroundDeep: '#2F4249',
  headerTint: '#FDECEC',
  mint: '#00FFC8',
  mintDark: '#10D6B5',
  text: '#FFFFFF',
  textMuted: 'rgba(255,255,255,0.7)',
  ink: '#0B2B2B',
  card: 'rgba(255,255,255,0.12)',
  cardBorder: 'rgba(255,255,255,0.18)',
  chip: 'rgba(14,24,31,0.24)',
  danger: '#FF5E60',
  shadow: 'rgba(0,0,0,0.24)',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 28,
} as const;

export const radius = {
  sm: 10,
  md: 16,
  lg: 22,
  xl: 28,
  round: 999,
} as const;

export const typography = {
  title: { fontSize: 24, lineHeight: 28 },
  cardTitle: { fontSize: 13, lineHeight: 16 },
  body: { fontSize: 12, lineHeight: 16 },
  tiny: { fontSize: 10, lineHeight: 12 },
};
