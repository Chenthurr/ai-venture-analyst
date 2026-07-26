import type { Config } from "tailwindcss";

/**
 * Design tokens for the "Investment Committee" visual direction:
 * a near-black ledger background, a restrained gold accent (not the
 * default terracotta/acid-green), and a serif+mono pairing that reads
 * like a printed IC memo rather than a generic SaaS dashboard.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0B0E14", // page background
          panel: "#12161F", // card / panel background
          raised: "#171C27", // hover / raised surfaces
          border: "#232837", // hairline dividers
        },
        paper: {
          DEFAULT: "#E8EAED", // primary text
          muted: "#8890A0", // secondary text
          faint: "#5A6274", // tertiary / labels
        },
        gold: {
          DEFAULT: "#C9A24B",
          bright: "#E0BB68",
          dim: "#8A7038",
        },
        signal: {
          positive: "#4F9D69",
          negative: "#C1554A",
          neutral: "#5B7BA6",
        },
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "serif"],
        body: ["var(--font-plex-sans)", "sans-serif"],
        mono: ["var(--font-plex-mono)", "monospace"],
      },
      borderRadius: {
        none: "0px",
        sm: "2px",
        DEFAULT: "3px",
        md: "4px",
        lg: "6px",
      },
    },
  },
  plugins: [],
};

export default config;
