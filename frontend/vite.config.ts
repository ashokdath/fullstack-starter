import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackStart } from "@tanstack/react-start/plugin/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig, loadEnv } from "vite"

// https://tanstack.com/start/latest/docs/framework/react/build-from-scratch
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  // CDN in front of the bucket the built assets are uploaded to, e.g.
  // https://cdn.example.com/frontend. Empty: assets are served by the app.
  const assetsUrl = env.VITE_ASSETS_URL
  // Django backend, for the dev proxy and for SSR in `vite dev`
  const apiUrl = env.API_INTERNAL_URL || "http://localhost:8000"
  process.env.API_INTERNAL_URL ??= apiUrl
  return {
    server: {
      port: 5173,
      // Single origin in development too, like the reverse proxy in production
      proxy: Object.fromEntries(
        ["/api", "/django-admin", "/static"].map((path) => [path, apiUrl]),
      ),
    },
    experimental: {
      // Every built asset URL (scripts, styles, images) points at the CDN
      renderBuiltUrl: (filename: string) =>
        assetsUrl ? `${assetsUrl.replace(/\/$/, "")}/${filename}` : undefined,
    },
    resolve: {
      alias: {
        "@": path.resolve(import.meta.dirname, "./src"),
      },
    },
    plugins: [
      tanstackStart({
        router: {
          autoCodeSplitting: true,
        },
      }),
      // Must come after tanstackStart()
      react(),
      tailwindcss(),
    ],
  }
})
