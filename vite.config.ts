import tailwindcss from "@tailwindcss/vite";
import solidPlugin from "vite-plugin-solid";
import { defineConfig } from "vitest/config";

export default defineConfig(({ command }) => ({
  base: command === "build" ? "/static/dist/" : "/",
  plugins: [tailwindcss(), solidPlugin()],
  build: {
    outDir: "web/static/dist",
    assetsDir: "",
    manifest: "manifest.json",
    rolldownOptions: {
      input: {
        main: "web/typescript/index.tsx",
        styles: "web/typescript/globals.css",
        loadTheme: "web/typescript/load-theme.ts",
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    origin: "http://localhost:5173",
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./web/typescript/test/setup.ts"],
  },
}));
