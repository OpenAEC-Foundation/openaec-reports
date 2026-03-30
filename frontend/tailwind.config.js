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
        chrome: {
          bg: 'var(--theme-bg)',
          'bg-lighter': 'var(--theme-bg-lighter)',
          surface: 'var(--theme-surface)',
          accent: 'var(--theme-accent)',
          'accent-hover': 'var(--theme-accent-hover)',
          text: 'var(--theme-text)',
          'text-secondary': 'var(--theme-text-secondary)',
          border: 'var(--theme-border)',
        },
        // OpenAEC Design System palette
        oaec: {
          bg: {
            DEFAULT: 'var(--oaec-bg)',
            lighter: 'var(--oaec-bg-lighter)',
            surface: 'var(--oaec-bg-surface)',
            input: 'var(--oaec-bg-input)',
          },
          accent: {
            DEFAULT: 'var(--oaec-accent)',
            hover: 'var(--oaec-accent-hover)',
            soft: 'var(--oaec-accent-soft)',
            text: 'var(--oaec-accent-text)',
          },
          text: {
            DEFAULT: 'var(--oaec-text)',
            secondary: 'var(--oaec-text-secondary)',
            muted: 'var(--oaec-text-muted)',
            faint: 'var(--oaec-text-faint)',
          },
          border: {
            DEFAULT: 'var(--oaec-border)',
            subtle: 'var(--oaec-border-subtle)',
          },
          hover: {
            DEFAULT: 'var(--oaec-hover)',
            strong: 'var(--oaec-hover-strong)',
          },
          danger: {
            DEFAULT: 'var(--oaec-danger)',
            hover: 'var(--oaec-danger-hover)',
            soft: 'var(--oaec-danger-soft)',
          },
          success: {
            DEFAULT: 'var(--oaec-success)',
            soft: 'var(--oaec-success-soft)',
          },
          warning: {
            DEFAULT: 'var(--oaec-warning)',
            soft: 'var(--oaec-warning-soft)',
          },
        },
      },
      borderColor: {
        oaec: {
          DEFAULT: 'var(--oaec-border)',
          subtle: 'var(--oaec-border-subtle)',
        },
      },
    },
  },
  plugins: [],
};
