/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#f3f5f4',
        surface: '#ffffff',
        'surface-2': '#f8faf9',
        border: '#e3e8e6',
        ink: '#16211c',
        'ink-muted': '#64766e',
        'ink-faint': '#93a29b',

        brand: {
          DEFAULT: '#1e6f4c',
          dark: '#144d34',
          light: '#e6f0ea',
          tint: '#eef6f1',
        },
        amber: { DEFAULT: '#a5670c', bg: '#fff4e0' },
        red: { DEFAULT: '#b3261e', bg: '#fde8e8' },
        teal: { DEFAULT: '#227a8f', bg: '#e4f3f6' },
        orange: { DEFAULT: '#c26b2c', bg: '#fbeade' },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
      },
      borderRadius: {
        sm: '8px',
        DEFAULT: '12px',
        lg: '16px',
      },
      boxShadow: {
        sm: '0 1px 2px rgba(16, 40, 28, 0.06)',
        DEFAULT: '0 4px 16px rgba(16, 40, 28, 0.07)',
        lg: '0 12px 32px rgba(16, 40, 28, 0.12)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(-4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        fadeIn: 'fadeIn 0.2s ease-out',
      },
    },
  },
  plugins: [],
};
