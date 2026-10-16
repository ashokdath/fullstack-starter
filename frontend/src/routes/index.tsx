import { createFileRoute, Link } from "@tanstack/react-router"
import { Appearance } from "@/components/Common/Appearance"
import { Footer } from "@/components/Common/Footer"
import { Logo } from "@/components/Common/Logo"
import { Button } from "@/components/ui/button"
import { getSiteUrl, siteName } from "@/lib/site"

const description =
  "Django + Django Ninja API with a server-rendered React frontend."

// Public, server-rendered page: crawlers and link previews get the full HTML
// and meta tags. To render API data here, fetch it in a `loader`: it runs on
// the server (with API_INTERNAL_URL) and its result is used by `head`.
export const Route = createFileRoute("/")({
  head: () => {
    const url = `${getSiteUrl()}/`
    return {
      meta: [
        { title: siteName },
        { name: "description", content: description },
        { property: "og:type", content: "website" },
        { property: "og:title", content: siteName },
        { property: "og:description", content: description },
        { property: "og:url", content: url },
        { name: "twitter:card", content: "summary" },
      ],
      links: [{ rel: "canonical", href: url }],
      scripts: [
        {
          type: "application/ld+json",
          children: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebSite",
            name: siteName,
            url,
          }),
        },
      ],
    }
  },
  component: Landing,
})

const features = [
  {
    title: "Typed end to end",
    text: "The frontend client is generated from the Django Ninja OpenAPI schema.",
  },
  {
    title: "Server-side rendering",
    text: "Public pages are rendered on the server for search engines and link previews.",
  },
  {
    title: "Cloud-native files",
    text: "Static and media files live in object storage, served through a CDN.",
  },
]

function Landing() {
  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex items-center justify-between border-b px-6 py-4">
        <Logo variant="full" />
        <nav className="flex items-center gap-2">
          <Appearance />
          <Button asChild variant="ghost">
            <Link to="/login">Log In</Link>
          </Button>
          <Button asChild>
            <Link to="/signup">Sign Up</Link>
          </Button>
        </nav>
      </header>
      <main className="flex flex-1 flex-col items-center px-6 py-20">
        <section className="max-w-2xl text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            {siteName}
          </h1>
          <p className="mt-4 text-lg text-muted-foreground">{description}</p>
          <div className="mt-8 flex justify-center gap-3">
            <Button asChild size="lg">
              {/* Logged-out visitors are redirected to the login page */}
              <Link to="/dashboard">Get Started</Link>
            </Button>
          </div>
        </section>
        <section className="mt-20 grid w-full max-w-5xl gap-6 sm:grid-cols-3">
          {features.map((feature) => (
            <div key={feature.title} className="rounded-lg border p-6">
              <h2 className="font-semibold">{feature.title}</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                {feature.text}
              </p>
            </div>
          ))}
        </section>
      </main>
      <Footer />
    </div>
  )
}
