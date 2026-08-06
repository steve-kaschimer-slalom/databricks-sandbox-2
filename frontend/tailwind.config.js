/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // brand palette
        navy: '#003087',
        'navy-dark': '#001F5B',
        'navy-light': '#0047B3',
        gold: '#F5A800',
        'gold-dark': '#CC8C00',
        'gold-light': '#FFD04D',
        white: '#FFFFFF',
        'gray-50': '#F5F5F5',
        'gray-100': '#E8E8E8',
        'gray-300': '#AAAAAA',
        'gray-600': '#666666',
        'gray-900': '#1A1A1A',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 2px 8px rgba(0, 48, 135, 0.12)',
        'card-hover': '0 4px 16px rgba(0, 48, 135, 0.2)',
      },
    },
  },
  plugins: [],
}
