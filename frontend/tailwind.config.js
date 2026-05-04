/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      screens: {
        'xs': '400px',
      },
      keyframes: {
        'pulse-border': {
          '0%, 100%': { boxShadow: '0 0 0 2px rgba(245,158,11,0.15)' },
          '50%': { boxShadow: '0 0 0 4px rgba(245,158,11,0.35)' },
        },
      },
      animation: {
        'pulse-border': 'pulse-border 1.5s ease-in-out infinite',
      },
      colors: {
        "primary-dark": "#0F1A2E",
        "primary-mid": "#1A2F4E",
        "accent-blue": "#2563EB",
        "accent-blue-light": "#3B82F6",
        "gold": "#F59E0B",
        "success": "#10B981",
        "high-risk": "#EF4444",
        "med-risk": "#F59E0B",
        "note-blue": "#3B82F6",
        "text-primary": "#F8FAFC",
        "text-secondary": "#94A3B8",
        "border-col": "#334155",
      },
    },
  },
  plugins: [],
}
