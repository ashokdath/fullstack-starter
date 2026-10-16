import { createFileRoute } from "@tanstack/react-router"
import { getSiteUrl, publicPaths } from "@/lib/site"

export const Route = createFileRoute("/sitemap.xml")({
  server: {
    handlers: {
      GET: () => {
        const siteUrl = getSiteUrl()
        // For dynamic pages (blog posts, products, ...) fetch their slugs
        // from the API here and add them to the list
        const urls = publicPaths
          .map((path) => `  <url><loc>${siteUrl}${path}</loc></url>`)
          .join("\n")
        const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`
        return new Response(body, {
          headers: { "Content-Type": "application/xml; charset=utf-8" },
        })
      },
    },
  },
})
