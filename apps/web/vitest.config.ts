import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.test.tsx",
        "src/test/**",
        "src/main.tsx", // browser bootstrap
        "src/App.tsx", // QueryClientProvider wiring; Dashboard is covered
        "src/vite-env.d.ts",
      ],
      thresholds: { lines: 85, functions: 85, branches: 75, statements: 85 },
    },
  },
});
