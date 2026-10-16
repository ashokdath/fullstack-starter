# Django Project - Frontend

The frontend is built with [TanStack Start](https://tanstack.com/start) (server-side rendering on top of [Vite](https://vitejs.dev/) and [TanStack Router](https://tanstack.com/router)), [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [TanStack Query](https://tanstack.com/query), [Tailwind CSS](https://tailwindcss.com/), and [shadcn/ui](https://ui.shadcn.com/).

## Rendering: Public Pages and the App

| Routes | Rendering | Why |
|---|---|---|
| `/` and other public pages | On the server (SSR) | Search engines and link previews get the full HTML and meta tags |
| `/robots.txt`, `/sitemap.xml` | Server routes | SEO |
| `/login`, `/signup`, password recovery, and the app under `_layout` (`/dashboard`, `/items`, `/admin`, `/settings`) | In the browser (`ssr: false`) | The access token is in `localStorage`, which only exists in the browser |

### Adding an SEO Page

1. Create a route file in `src/routes`, e.g. `pricing.tsx`. Routes render on the server by default.
2. Set its title, description, Open Graph tags and canonical link in `head`, like `src/routes/index.tsx`.
3. Add its path to `publicPaths` in `src/lib/site.ts` for the sitemap.
4. To show API data, fetch it in the route's `loader`: during SSR it calls the API at `API_INTERNAL_URL`, without the user's token. Use public (anonymous) API endpoints only.

Server-only code must not read browser APIs (`window`, `localStorage`, `document`) while rendering. Read them in effects or event handlers, or mark the route `ssr: false`.

## Configuration

| Variable | When | Purpose |
|---|---|---|
| `VITE_API_URL` | Build time | Only for an API on another domain. Default: the same origin (`/api`, routed to Django by the reverse proxy, or by the Vite dev server proxy in development) |
| `VITE_ASSETS_URL` | Build time | CDN URL serving the built assets (`dist/client`), e.g. `https://cdn.example.com/frontend`. Unset: the frontend server serves them |
| `API_INTERNAL_URL` | Runtime (server) | Django URL used during server-side rendering, e.g. `http://backend:8000`; in development also the target of the Vite dev proxy. Default `http://localhost:8000` |
| `SITE_URL` | Runtime (server) | Public site URL for canonical links, Open Graph tags and the sitemap |
| `PORT` | Runtime (server) | Port of the production server (default `3000`) |

## Requirements

- [Bun](https://bun.sh/)

## Quick Start

From the project root, install the dependencies and start the frontend development server:

```bash
bun install
bun run dev
```

Then open <http://localhost:5173/> in your browser.

Run `uv run bash scripts/prestart.sh` and `uv run python manage.py runserver` from the `backend` directory, with PostgreSQL running in Docker Compose. See [../development.md](../development.md) for the complete setup.

To run the production build, run `bun run build` and `bun run start` from the `frontend` directory and open <http://localhost:3000>.

Check `frontend/package.json` to see the other available commands.

## Removing the Frontend

If you are developing an API-only app and want to remove the frontend, you can do it easily:

* Remove the `./frontend` directory.

* In the `compose.yml` and `compose.deploy.yml` files, remove the `frontend` service, and in `compose.override.yml`, remove the `frontend` and `playwright` services.

* Remove the `.github/workflows/playwright.yml` and `.github/workflows/check-client.yml` workflows.

Done, you now have an API-only app. 🤓

## Generate Client

### Automatically

* From the project root, run the script:

```bash
bash ./scripts/generate-client.sh
```

* Commit the changes.

### Manually

* Make sure the backend is running.

* Download the OpenAPI JSON file from `http://localhost:8000/api/v1/openapi.json` and copy it to a new file `openapi.json` at the root of the `frontend` directory.

* To generate the frontend client, run:

```bash
bun run generate-client
```

* Commit the changes.

Regenerate the client whenever backend changes affect the OpenAPI schema.

## Using a Remote API

By default, the browser calls the API on its own origin (`/api`). To run the Vite development server against another backend, point the dev proxy at it in `frontend/.env`:

```env
API_INTERNAL_URL=https://my-domain.example.com
```

To build a frontend that calls an API on a different domain (CORS then applies), set `VITE_API_URL` at build time.

## Code Structure

The frontend code is structured as follows:

* `frontend/src` - The main frontend code.
* `frontend/public` - Static assets.
* `frontend/src/client` - The generated OpenAPI client.
* `frontend/src/components` - The components of the frontend, including the shadcn/ui components in `frontend/src/components/ui`.
* `frontend/src/hooks` - Custom hooks.
* `frontend/src/lib` - Shared frontend utilities.
* `frontend/src/routes` - The frontend routes and pages.

## End-to-End Testing with Playwright

The frontend includes initial end-to-end tests using Playwright. To run the tests, you need to have the Docker Compose stack running. Start the stack with the following command:

```bash
docker compose run --rm backend bash scripts/prestart.sh
docker compose up -d --wait backend
```

Then, you can run the tests with the following command:

```bash
bunx playwright test
```

You can also run your tests in UI mode to see the browser and interact with it running:

```bash
bunx playwright test --ui
```

To stop and remove the Docker Compose stack and clean the data created in tests, use the following command:

```bash
docker compose down -v
```

To update the tests, navigate to the tests directory and modify the existing test files or add new ones as needed.

For more information on writing and running Playwright tests, refer to the official [Playwright documentation](https://playwright.dev/docs/intro).
