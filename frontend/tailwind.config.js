/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        olive:   "#696e21",
        orange:  "#df802c",
        apricot: "#e39168",
        gold:    "#c9b965",
        cream:   "#f1dcc4",
        dark:    "#2d2a1e",
      },
      fontFamily: {
        heading: ["Lora", "serif"],
        body:    ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
