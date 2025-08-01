/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        first: "#3fa2f6",
        second: "#003366",
        third: "#4d4d4d",
        fifth: "#ff6f61",
        important: "#00ffff",
        background: "#0d47a1",
        grey: "#64748b"
      }
    },
  },
  plugins: [],
}