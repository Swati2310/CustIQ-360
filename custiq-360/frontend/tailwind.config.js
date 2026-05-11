/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        banking: {
          gold:   '#b45309',
          goldBg: '#fef3c7',
          navy:   '#1e3a5f',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card:  '0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.06)',
        glow:  '0 0 20px rgb(99 102 241 / 0.35)',
        'glow-sm': '0 0 10px rgb(99 102 241 / 0.25)',
      },
      keyframes: {
        fadeIn:    { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp:   { from: { opacity: '0', transform: 'translateY(24px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        slideInLeft: { from: { opacity: '0', transform: 'translateX(-16px)' }, to: { opacity: '1', transform: 'translateX(0)' } },
        scaleIn:   { from: { opacity: '0', transform: 'scale(0.95)' }, to: { opacity: '1', transform: 'scale(1)' } },
        float:     { '0%, 100%': { transform: 'translateY(0px)' }, '50%': { transform: 'translateY(-14px)' } },
        shimmer:   { from: { backgroundPosition: '-200% 0' }, to: { backgroundPosition: '200% 0' } },
        pulse2:    { '0%, 100%': { opacity: '1' }, '50%': { opacity: '0.5' } },
        spin3d:    { from: { transform: 'rotate(0deg)' }, to: { transform: 'rotate(360deg)' } },
        blobMove:  { '0%, 100%': { borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%' }, '50%': { borderRadius: '30% 60% 70% 40% / 50% 60% 30% 60%' } },
        countUp:   { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
      animation: {
        'fade-in':      'fadeIn 0.4s ease-out both',
        'slide-up':     'slideUp 0.5s cubic-bezier(0.16,1,0.3,1) both',
        'slide-up-slow':'slideUp 0.7s cubic-bezier(0.16,1,0.3,1) both',
        'slide-in-left':'slideInLeft 0.4s ease-out both',
        'scale-in':     'scaleIn 0.35s cubic-bezier(0.16,1,0.3,1) both',
        'float':        'float 5s ease-in-out infinite',
        'float-slow':   'float 7s ease-in-out infinite',
        'shimmer':      'shimmer 2.5s linear infinite',
        'blob':         'blobMove 7s ease-in-out infinite',
        'blob-slow':    'blobMove 10s ease-in-out infinite',
        'count-up':     'countUp 0.4s ease-out both',
      },
    },
  },
  plugins: [],
}
