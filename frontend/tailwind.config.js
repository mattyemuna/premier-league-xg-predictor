/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base:    '#0D0E12',
        panel:   '#15171C',
        card:    '#1C1F26',
        rim:     '#262A33',
        text:    '#F4F5F7',
        sub:     '#8A909C',
        accent:  '#10E0A0',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
