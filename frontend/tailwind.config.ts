import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // acento azul LinkedIn
        brand: {
          DEFAULT: "#0A66C2",
          dark: "#004182",
          light: "#378FE9",
        },
        ink: {
          DEFAULT: "#1D2226",
          soft: "#56687A",
        },
      },
      fontFamily: {
        sans: ["system-ui", "Segoe UI", "Roboto", "Helvetica", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
