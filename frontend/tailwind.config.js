/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: 'rgb(var(--brand-primary) / <alpha-value>)',
          'primary-dark': 'rgb(var(--brand-primary-dark) / <alpha-value>)',
          'primary-light': 'rgb(var(--brand-primary-light) / <alpha-value>)',
          secondary: 'rgb(var(--brand-secondary) / <alpha-value>)',
          'secondary-dark': 'rgb(var(--brand-secondary-dark) / <alpha-value>)',
          'secondary-light': 'rgb(var(--brand-secondary-light) / <alpha-value>)',
          'header-bg': 'rgb(var(--brand-header-bg) / <alpha-value>)',
          'header-text': 'rgb(var(--brand-header-text) / <alpha-value>)',
        },
      },
    },
  },
  plugins: [],
};
