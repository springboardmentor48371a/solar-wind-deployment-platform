/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        lavender: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
          950: '#3b0764',
        },
        solar: {
          50: '#fffbe8',
          100: '#fff5c3',
          200: '#ffe685',
          300: '#ffd147',
          400: '#ffb91a',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
      },
      animation: {
        'spin-slow': 'spin 14s linear infinite',
        'spin-medium': 'spin 9s linear infinite',
        'spin-fast': 'spin 6s linear infinite',
        'sun-pulse': 'sunPulse 6s ease-in-out infinite',
        'cloud-drift-1': 'cloudDrift 60s linear infinite',
        'cloud-drift-2': 'cloudDrift 90s linear infinite',
        'cloud-drift-3': 'cloudDrift 120s linear infinite',
        'wind-particle-1': 'windParticle 8s linear infinite',
        'wind-particle-2': 'windParticle 12s linear infinite',
        'wind-particle-3': 'windParticle 15s linear infinite',
        'solar-glint': 'solarGlint 7s ease-in-out infinite',
        'node-pulse': 'nodePulse 3s ease-in-out infinite',
      },
      keyframes: {
        sunPulse: {
          '0%, 100%': { transform: 'scale(1)', opacity: '0.85' },
          '50%': { transform: 'scale(1.08)', opacity: '1' },
        },
        cloudDrift: {
          '0%': { transform: 'translateX(-20%)' },
          '100%': { transform: 'translateX(120%)' },
        },
        windParticle: {
          '0%': { transform: 'translateX(-100px) translateY(0px)', opacity: '0' },
          '20%': { opacity: '0.7' },
          '80%': { opacity: '0.7' },
          '100%': { transform: 'translateX(100vw) translateY(-20px)', opacity: '0' },
        },
        solarGlint: {
          '0%, 100%': { opacity: '0.2', transform: 'translateX(-100%)' },
          '50%': { opacity: '0.8', transform: 'translateX(200%)' },
        },
        nodePulse: {
          '0%, 100%': { r: '3', opacity: '0.5' },
          '50%': { r: '5', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
