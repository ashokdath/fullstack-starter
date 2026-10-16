import { expect, test } from "@playwright/test"

// Crawlers and link previews read the raw HTML, without running JavaScript
test("Landing page is server-rendered with SEO tags", async ({ request }) => {
  const response = await request.get("/")
  expect(response.status()).toBe(200)
  const html = await response.text()
  expect(html).toContain("<h1")
  expect(html).toContain('<meta name="description"')
  expect(html).toContain('<meta property="og:title"')
  expect(html).toContain('<link rel="canonical"')
  expect(html).toContain("application/ld+json")
})

test("Unknown page returns a 404 status", async ({ request }) => {
  const response = await request.get("/this-page-does-not-exist")
  expect(response.status()).toBe(404)
})

test("robots.txt points to the sitemap", async ({ request }) => {
  const response = await request.get("/robots.txt")
  expect(response.status()).toBe(200)
  expect(await response.text()).toContain("Sitemap: ")
})

test("sitemap.xml lists the public pages", async ({ request }) => {
  const response = await request.get("/sitemap.xml")
  expect(response.status()).toBe(200)
  expect(response.headers()["content-type"]).toContain("application/xml")
  expect(await response.text()).toContain("<urlset")
})

test("Get Started leads logged-in users to the dashboard", async ({ page }) => {
  await page.goto("/")
  await page.getByRole("link", { name: "Get Started" }).click()
  await page.waitForURL("/dashboard")
})
