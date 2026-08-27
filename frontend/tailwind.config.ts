import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#17212b",
        slateblue: "#31536f",
        signal: "#0f766e",
        review: "#b45309",
        surface: "#f7f9fb",
      },
      boxShadow: {
        soft: "0 18px 50px rgba(23, 33, 43, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;

