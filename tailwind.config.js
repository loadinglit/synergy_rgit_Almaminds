/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#1E90FF', // Blue
        secondary: '#FFD700', // Yellow
        background: '#FFFFFF', // White
        textPrimary: '#1E1E1E', // Dark text for better contrast
      },
    },
  },
  darkMode: 'class', // Enable dark mode with 'class'
  theme: {
    extend: {},
  },
  plugins: [],
};
