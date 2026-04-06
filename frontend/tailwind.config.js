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
      keyframes: {
        fadeIn:    { from: { opacity: "0" },                       to: { opacity: "1" } },
        slideUp:   { from: { opacity: "0", transform: "translateY(20px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        slideDown: { from: { opacity: "0", transform: "translateY(-20px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        scaleIn:   { from: { opacity: "0", transform: "scale(0.95)" }, to: { opacity: "1", transform: "scale(1)" } },
        shimmer:   { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
        float:     { "0%,100%": { transform: "translateY(0px)" }, "50%": { transform: "translateY(-8px)" } },
        ping2:     { "0%,100%": { transform: "scale(1)", opacity: "1" }, "50%": { transform: "scale(1.05)", opacity: "0.9" } },
        countUp:   { from: { opacity: "0", transform: "translateY(10px)" }, to: { opacity: "1", transform: "translateY(0)" } },
      },
      animation: {
        "fade-in":    "fadeIn 0.4s ease forwards",
        "slide-up":   "slideUp 0.5s ease forwards",
        "slide-down": "slideDown 0.4s ease forwards",
        "scale-in":   "scaleIn 0.3s ease forwards",
        "shimmer":    "shimmer 1.8s infinite linear",
        "float":      "float 3s ease-in-out infinite",
        "ping2":      "ping2 2s ease-in-out infinite",
        "count-up":   "countUp 0.6s ease forwards",
      },
    },
  },
  plugins: [],
};
