import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular"],
      },
      colors: {
        bench: {
          ink: "#0a0a0c",
          paper: "#fafafa",
          accent: "#5eead4",
          warn: "#facc15",
          fail: "#f87171",
          pass: "#4ade80",
        },
      },
    },
  },
  plugins: [],
};

export default config;
