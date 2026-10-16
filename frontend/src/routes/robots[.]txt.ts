import { createFileRoute } from "@tanstack/react-router"
import { getSiteUrl } from "@/lib/site"

export const Route = createFileRoute("/robots.txt")({
  server: {
    handlers: {
      GET: () => {
        const body = [
          "User-agent: *",
          "Allow: /",
          // The logged-in app is rendered in the browser, nothing to index
          "Disallow: /dashboard",
          "Disallow: /items",
          "Disallow: /admin",
          "Disallow: /settings",
          "Disallow: /api/",
          "Disallow: /django-admin/",
          "",
          `Sitemap: ${getSiteUrl()}/sitemap.xml`,
          "",
        ].join("\n")
        return new Response(body, {
          headers: { "Content-Type": "text/plain; charset=utf-8" },
        })
      },
    },
  },
})
