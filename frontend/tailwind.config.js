/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base:      '#0d1117',
        surface:   '#161b22',
        'surface-2':'#1c2230',
        border:    'rgba(255,255,255,0.07)',
        accent:    '#4f8ef7',
        'accent-2':'#6366f1',
        muted:     '#8b949e',
        dim:       '#6e7681',
        high:      '#ea580c',
        'high-bg': 'rgba(234,88,12,0.18)',
        medium:    '#d97706',
        'med-bg':  'rgba(217,119,6,0.18)',
        low:       '#16a34a',
        'low-bg':  'rgba(22,163,74,0.18)',
        critical:  '#dc2626',
        'crit-bg': 'rgba(220,38,38,0.18)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease forwards',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)'   },
        },
      },
    },
  },
  plugins: [],
}
