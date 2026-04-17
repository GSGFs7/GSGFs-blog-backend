import tailwindcss from "@tailwindcss/vite";
import type { Plugin } from "vite";
import solidPlugin from "vite-plugin-solid";
import { defineConfig } from "vitest/config";

// reload entre page when django template has updated
const djangoTemplateReload = (): Plugin => ({
  name: "django-template-reload",
  configureServer: (server) => {
    const templateDirs = ["web/templates/", "templates/"];
    console.log(templateDirs);
    server.watcher.add(templateDirs);

    const reload = (path: string): void => {
      if (path.endsWith(".html")) {
        server.ws.send({ type: "full-reload" });
      }
    };
    server.watcher.on("add", reload);
    server.watcher.on("change", reload);
    server.watcher.on("unlink", reload);
  },
});

export default defineConfig(({ command }) => ({
  base: command === "build" ? "/static/dist/" : "/",
  plugins: [tailwindcss(), solidPlugin(), djangoTemplateReload()],
  build: {
    outDir: "web/static/dist",
    assetsDir: "",
    manifest: "manifest.json",
    rolldownOptions: {
      input: {
        main: "web/typescript/index.tsx",
        styles: "web/typescript/styles/globals.css",
        loadTheme: "web/typescript/load-theme.ts",
        htmx: "web/typescript/htmx.ts",
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
