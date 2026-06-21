export const theme = {
  colors: {
    bg: '#EAE7E2',
    surface: '#F4F1EC',
    surface2: '#E1DDD6',
    ink: '#111111',
    inkMid: '#151F23',
    inkLight: '#556267',
    inkPale: '#C6A96B',
    rule: '#D3CEC6',
    ruleLight: '#E2DED8',
    accent: '#8FC7C8',
    accentInk: '#111111',
    accentBg: '#DDEEEF',
    accentBorder: '#B8D7D8',
    successBg: '#E7DDCA',
    successBorder: '#D2BC8F',
    shadow: 'rgba(17, 17, 17, 0.08)'
  },
  fonts: {
    serif: '"EB Garamond", Georgia, serif',
    sans: '"Source Sans 3", "Helvetica Neue", Arial, sans-serif'
  },
  radius: {
    sm: 2,
    md: 4,
    lg: 6
  },
  layout: {
    maxWidth: 1180
  }
}

export type QuintanaTheme = typeof theme
