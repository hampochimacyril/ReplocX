/// <reference types="vitest/config" />
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// The Python backend serves the built app from frontend/dist at the site root,
// so assets are referenced from "/". During `npm run dev` we proxy /api to the
// local backend (default 127.0.0.1:8787) to preserve the same-origin contract.
const apiTarget = process.env.RLE_DEV_API ?? "http://127.0.0.1:8787";

export default defineConfig({
  plugins: [react()],
  base: "/",
  build: {
    outDir: "dist",
    // Overwrite in place rather than wiping the directory. dist/ is gitignored
    // and rebuilt from scratch in the Docker/CI image, so stale hashed files
    // (if any) never ship; index.html always references the freshest chunks.
    emptyOutDir: false,
    sourcemap: false,
    // Hashed filenames land under /assets/* which the backend mounts.
    assetsDir: "assets",
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks: {
          maplibre: ["maplibre-gl"],
          echarts: ["echarts/core", "echarts/charts", "echarts/components", "echarts/renderers"],
          vendor: ["react", "react-dom", "react-router-dom", "@tanstack/react-query"],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: apiTarget, changeOrigin: true },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
});
