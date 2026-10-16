import { createIsomorphicFn } from "@tanstack/react-start"

export const siteName = "Full Stack Django Project"

/**
 * Public origin of the site (e.g. https://example.com), for absolute URLs in
 * canonical links, Open Graph tags and the sitemap. Set SITE_URL on the
 * server; the browser uses its own origin.
 */
export const getSiteUrl = createIsomorphicFn()
  .server(() => (process.env.SITE_URL ?? "").replace(/\/$/, ""))
  .client(() => window.location.origin)

/** Public, indexable pages. Add new SEO pages here for the sitemap. */
export const publicPaths = ["/"] as const
