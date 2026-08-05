export const colors = {
  background: '#F7F8F7',
  surface: '#FFFFFF',
  input: '#F1F3F2',
  text: '#111814',
  textSecondary: '#64706A',
  placeholder: '#8B9590',
  brand: '#1F7A5A',
  brandPressed: '#176047',
  brandSoft: '#E7F2ED',
  border: '#DCE3DF',
  error: '#B54747',
  errorSoft: '#FBEDED',
  success: '#2D7A5D',
  white: '#FFFFFF',
} as const;

export const spacing = {
  x1: 4,
  x2: 8,
  x3: 12,
  x4: 16,
  x5: 20,
  x6: 24,
  x8: 32,
  x10: 40,
} as const;

export const radii = {
  small: 8,
  input: 12,
  button: 14,
  card: 16,
  round: 999,
} as const;

export const typography = {
  brandTitle: 32,
  pageTitle: 28,
  sectionTitle: 19,
  body: 16,
  helper: 14,
  caption: 13,
  button: 16,
} as const;

export const layout = {
  pagePadding: spacing.x6,
  controlHeight: 54,
  minimumTouchTarget: 44,
  maxContentWidth: 560,
} as const;

export const theme = {
  colors,
  spacing,
  radii,
  typography,
  layout,
} as const;

export type AppTheme = typeof theme;
