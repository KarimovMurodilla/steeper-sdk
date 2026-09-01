/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        tg: {
          bg: "rgb(var(--tg-bg) / <alpha-value>)",
          "bg-secondary": "rgb(var(--tg-bg-secondary) / <alpha-value>)",
          "bg-sidebar": "rgb(var(--tg-bg-sidebar) / <alpha-value>)",
          surface: "rgb(var(--tg-surface) / <alpha-value>)",
          "surface-hover": "rgb(var(--tg-surface-hover) / <alpha-value>)",
          primary: "rgb(var(--tg-primary) / <alpha-value>)",
          "primary-hover": "rgb(var(--tg-primary-hover) / <alpha-value>)",
          accent: "rgb(var(--tg-accent) / <alpha-value>)",
          text: "rgb(var(--tg-text) / <alpha-value>)",
          "text-secondary": "rgb(var(--tg-text-secondary) / <alpha-value>)",
          "text-muted": "rgb(var(--tg-text-muted) / <alpha-value>)",
          border: "rgb(var(--tg-border) / <alpha-value>)",
          "msg-out": "rgb(var(--tg-msg-out) / <alpha-value>)",
          "msg-in": "rgb(var(--tg-msg-in) / <alpha-value>)",
          green: "rgb(var(--tg-green) / <alpha-value>)",
          red: "rgb(var(--tg-red) / <alpha-value>)",
          orange: "rgb(var(--tg-orange) / <alpha-value>)",
          // Hairlines and hover fills: white on dark, near-black on light.
          overlay: "rgb(var(--tg-overlay) / <alpha-value>)",
        },
      },
      backdropBlur: {
        glass: "20px",
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "slide-right": "slideRight 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideRight: {
          "0%": { opacity: "0", transform: "translateX(-10px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
      },
    },
  },
  plugins: [],
};
