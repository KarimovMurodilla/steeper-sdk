/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        tg: {
          bg: "#17212b",
          "bg-secondary": "#0e1621",
          "bg-sidebar": "#0e1621",
          surface: "#182533",
          "surface-hover": "#1e2f40",
          primary: "#5288c1",
          "primary-hover": "#6ba0d6",
          accent: "#64b5ef",
          text: "#f5f5f5",
          "text-secondary": "#7e919e",
          "text-muted": "#546778",
          border: "#1b2a3a",
          "msg-out": "#2b5278",
          "msg-in": "#182533",
          green: "#4fae4e",
          red: "#e53935",
          orange: "#f5a623",
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
