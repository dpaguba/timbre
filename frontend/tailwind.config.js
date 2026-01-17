/** @type {import('tailwindcss').Config} */
// Every value here comes from DESIGN.md. Components reference these names and
// never inline a hex, so a token change reaches the whole interface at once.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Two columns are only worth it on a genuinely wide display. Tailwind's
      // own scale stops at 1536, which is a laptop.
      screens: { wide: "1600px" },
      colors: {
        ink: "#0c0a09",
        primary: { DEFAULT: "#292524", active: "#0c0a09" },
        canvas: { DEFAULT: "#f5f5f5", soft: "#fafafa", deep: "#0c0a09" },
        surface: {
          card: "#ffffff",
          strong: "#f0efed",
          dark: "#0c0a09",
          "dark-elevated": "#1c1917",
        },
        hairline: { DEFAULT: "#e0ddda", soft: "#ebe8e5", strong: "#9e9891" },
        body: { DEFAULT: "#4e4e4e", strong: "#292524" },
        // Darkened from #777169 / #a8a29e, which measured 4.43 and 2.31 against
        // the canvas. The lighter one failed every threshold while carrying real
        // copy: file sizes, model hints, empty states.
        muted: { DEFAULT: "#5f594f", soft: "#706a62" },
        "on-primary": "#ffffff",
        "on-dark": { DEFAULT: "#ffffff", soft: "#a8a29e" },
        gradient: {
          mint: "#a7e5d3",
          peach: "#f4c5a8",
          lavender: "#c8b8e0",
          sky: "#a8c8e8",
          rose: "#e8b8c4",
        },
        semantic: { success: "#16a34a", error: "#dc2626" },
      },
      fontFamily: {
        // EB Garamond stands in for the licensed Waldenburg Light.
        display: ["'EB Garamond'", "'Times New Roman'", "serif"],
        sans: ["Inter", "sans-serif"],
      },
      fontSize: {
        "display-mega": ["64px", { lineHeight: "1.05", letterSpacing: "-1.92px", fontWeight: "300" }],
        "display-xl": ["48px", { lineHeight: "1.08", letterSpacing: "-0.96px", fontWeight: "300" }],
        "display-lg": ["36px", { lineHeight: "1.17", letterSpacing: "-0.36px", fontWeight: "300" }],
        "display-md": ["32px", { lineHeight: "1.13", letterSpacing: "-0.32px", fontWeight: "300" }],
        "display-sm": ["24px", { lineHeight: "1.2", letterSpacing: "0", fontWeight: "300" }],
        "title-md": ["20px", { lineHeight: "1.35", letterSpacing: "0", fontWeight: "500" }],
        "title-sm": ["18px", { lineHeight: "1.44", letterSpacing: "0.18px", fontWeight: "500" }],
        "body-md": ["16px", { lineHeight: "1.5", letterSpacing: "0.16px" }],
        "body-sm": ["15px", { lineHeight: "1.47", letterSpacing: "0.15px" }],
        caption: ["14px", { lineHeight: "1.5", letterSpacing: "0" }],
        "caption-uppercase": ["12px", { lineHeight: "1.4", letterSpacing: "0.96px", fontWeight: "600" }],
        button: ["15px", { lineHeight: "1", letterSpacing: "0", fontWeight: "500" }],
      },
      spacing: { section: "96px" },
      borderRadius: { xl: "16px", xxl: "24px", pill: "9999px" },
      boxShadow: { soft: "0 4px 16px rgba(0, 0, 0, 0.04)" },
      maxWidth: { content: "1200px" },
    },
  },
  plugins: [],
};
