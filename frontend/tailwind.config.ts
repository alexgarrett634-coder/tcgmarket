import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0f0f14',
        surface: '#1a1a24',
        'surface-2': '#22222e',
        accent: '#e3350d',
        'accent-hover': '#c02c0b',
        yes: '#22c55e',
        no: '#ef4444',
        gold: '#f59e0b',
        muted: '#6b7280',
      },
      boxShadow: {
        'red-glow': '0 0 16px 2px rgba(227,53,13,0.25)',
      },
    },
  },
  plugins: [],
}

export default config
