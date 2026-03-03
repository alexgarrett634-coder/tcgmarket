import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#07080f',
        surface: '#0d1117',
        'surface-2': '#131c2e',
        accent: '#8b5cf6',
        'accent-hover': '#7c3aed',
        highlight: '#f0a500',
        yes: '#22c55e',
        no: '#ef4444',
        gold: '#f0a500',
        muted: '#6b7280',
      },
      boxShadow: {
        'glow': '0 0 16px 2px rgba(139,92,246,0.25)',
        'gold-glow': '0 0 16px 2px rgba(240,165,0,0.25)',
      },
    },
  },
  plugins: [],
}

export default config
