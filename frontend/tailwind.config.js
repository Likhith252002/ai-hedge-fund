/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg:       "#050508",
          panel:    "#0a0c10",
          border:   "#151b26",
          border2:  "#1e2535",
          text:     "#c9d1d9",
          dim:      "#4b5563",
          muted:    "#374151",
          orange:   "#f59e0b",
          green:    "#00d964",
          red:      "#ff2d55",
          blue:     "#38bdf8",
          amber:    "#fbbf24",
          purple:   "#a78bfa",
        },
      },
      fontFamily: {
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
      animation: {
        blink:       "blink 1.2s step-end infinite",
        "pulse-dot": "pulse-dot 2s ease-in-out infinite",
        "slide-in":  "slide-in 0.3s ease-out",
        "fade-in":   "fade-in 0.4s ease-out",
      },
      keyframes: {
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%":      { opacity: "0.4", transform: "scale(0.8)" },
        },
        "slide-in": {
          from: { opacity: "0", transform: "translateY(-6px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
