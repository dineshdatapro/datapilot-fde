/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Source Serif 4", "Georgia", "serif"],
        display: ["Fraunces", "Georgia", "serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      colors: {
        ink: "#1c1917",
        paper: "#f7f4ef",
        mist: "#efeae2",
        line: "#e4ddd2",
        accent: "#1f4d3a",
      },
    },
  },
  plugins: [],
};
