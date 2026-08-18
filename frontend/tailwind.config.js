/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Earth-tone palette: deep terrain green (primary), sun amber (solar),
        // sky slate (wind), used consistently across dashboards and score badges.
        terrain: {
          50: "#f1f6f3",
          100: "#dcebe1",
          400: "#4c8a6a",
          600: "#2f6b4d",
          800: "#1f4835",
          900: "#153726",
        },
        sun: {
          400: "#f2b544",
          600: "#d9932a",
        },
        sky: {
          400: "#5f88a6",
          600: "#3f6683",
        },
        excellent: "#2f6b4d",
        highlySuitable: "#4c8a6a",
        moderatelySuitable: "#d9932a",
        lowSuitability: "#c96a3e",
        unsuitable: "#a13d3d",
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        body: ["'Inter'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
