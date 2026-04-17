import tailwindcss from "@tailwindcss/vite";
import solidPlugin from "vite-plugin-solid";
import { defineConfig } from "vitest/config";
import { HmrContext } from "vite";

function djangoTemplateReload() {
  return {
    name: "django-template-reload",
    handleHotUpdate: (ctx: HmrContext) => {
      // merge this?
      const templateDirs = ["web/templates/", "templates/"];
      if (ctx.file.endsWith(".html") && templateDirs.some((dir) => ctx.file.includes(dir))) {
        ctx.server.ws.send({ type: "full-reload" });
        return [];
      }
    },
  };
}

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
        styles: "web/typescript/globals.css",
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
