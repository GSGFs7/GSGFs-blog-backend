import tailwindcss from "@tailwindcss/vite";
import solidPlugin from "vite-plugin-solid";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [tailwindcss(), solidPlugin()],
  build: {
    outDir: "web/static/dist",
    assetsDir: "",
    manifest: "manifest.json",
    rolldownOptions: {
      input: {
        main: "web/typescript/index.tsx",
        styles: "web/typescript/globals.css",
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
});
