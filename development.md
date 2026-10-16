# Django Project - Development

## Local Development

For local development, run PostgreSQL and Mailpit with Docker Compose, and run the Django and Vite development servers locally.

The project is two apps: Django serves only the API and the admin, and the frontend (TanStack Start) server-renders the public pages and serves the React app. The Vite development server also does server-side rendering, so what you see locally is what crawlers get in production.

Start the supporting services:

```bash
docker compose up -d db mailpit
```

Then, from the `backend` directory, install the dependencies and prepare the database:

```bash
uv sync
uv run bash scripts/prestart.sh
```

Start the Django development server:

```bash
uv run python manage.py runserver
```

In another terminal, from the project root, install the frontend dependencies and start the Vite development server:

```bash
bun install
bun run dev
```

Now you can open these URLs:

Frontend development server (landing page, server-rendered): <http://localhost:5173>

App dashboard (rendered in the browser): <http://localhost:5173/dashboard>

Backend API: <http://localhost:8000>

Automatic interactive API documentation with Swagger UI: <http://localhost:8000/api/v1/docs>

Django admin: <http://localhost:8000/django-admin> (also through the frontend at <http://localhost:5173/django-admin>)

Mailpit: <http://localhost:8025>

The Vite development server proxies `/api` and `/django-admin` to the backend at `http://localhost:8000` (`API_INTERNAL_URL` in `frontend/.env`), so the browser uses a single origin, like in production.

### Production Frontend Build

Build and run the frontend server from the `frontend` directory:

```bash
bun run build
bun run start
```

It listens on <http://localhost:3000>. Set `PORT` to change it, `API_INTERNAL_URL` for the API URL used during server-side rendering, and `SITE_URL` for the absolute URLs in meta tags and the sitemap.

### Object Storage

Without object storage settings, Django keeps static and media files on the local disk and `runserver` serves the static files. To test with a bucket locally, set the `AWS_*` variables in `.env` (see the comments there) and run `uv run python manage.py collectstatic`.

## Full Stack with Docker Compose

To run the backend and the production frontend server in Docker Compose:

```bash
docker compose run --rm backend bash scripts/prestart.sh
docker compose watch
```

Now you can open these URLs:

Application, through the nginx proxy on a single domain (frontend, `/api` and `/django-admin`): <http://localhost>

Backend API, directly: <http://localhost:8000>

Automatic interactive API documentation with Swagger UI: <http://localhost:8000/api/v1/docs>

Django admin: <http://localhost/django-admin>

Adminer, database web administration: <http://localhost:8080>

Mailpit: <http://localhost:8025>

Stop a locally running Django server before starting the Compose stack because both use port `8000`.


**Note**: The first time you start the stack, it might take a minute for all the services to be ready. To monitor it, use `docker compose logs`, or `docker compose logs backend` for the backend service.

## Mailpit

[Mailpit](https://mailpit.axllent.org) captures emails sent during local development instead of delivering them. The local backend connects to it at `localhost:1025`, and the Compose backend connects to the `mailpit` service. Captured emails are available at <http://localhost:8025>.

## Docker Compose Files and Environment Variables

The main `compose.yml` file contains the configuration shared by the whole stack. Docker Compose loads it automatically.

The `compose.override.yml` file adds local development settings, such as mounting the source code as a volume, the gateway (`proxy`, `nginx/gateway.conf`) on port 80, and the local-only services: Adminer, Mailpit and Playwright. Docker Compose also loads it automatically and applies it on top of `compose.yml`.

The `compose.deploy.yml` file contains the deployment-specific settings: restart policies, and the gateway published on `127.0.0.1:APP_PORT` for the server's nginx. It is explicitly combined with `compose.yml` when deploying the application.

The backend reads local settings from the `.env` file. Docker Compose also uses it for variable interpolation and passes the settings each container needs.

After changing variables, make sure you restart the stack:

```bash
docker compose watch
```

## The `.env` File

The tracked `.env` file contains local development defaults (with `ENVIRONMENT=development`, which enables `DEBUG`, the dev-only `/api/v1/private` endpoints used by Playwright, and allows the `changethis` placeholder secrets), passwords, and other configuration. Its hostnames use `localhost` for processes running on your machine. Docker Compose overrides hostnames such as the database and SMTP server with their Compose service names.

Do not store deployment secrets in `.env`. Configure them as described in the [Docker Compose deployment guide](./deployment-docker-compose.md).

## Pre-commit Hooks and Code Linting

The project uses [prek](https://prek.j178.dev/), a modern alternative to [pre-commit](https://pre-commit.com/), for code linting and formatting.

You can find a file `.pre-commit-config.yaml` with configurations at the root of the project.

### Install `prek` to Run Automatically

`prek` is already part of the dependencies of the project.

From the project root, install the Git hook so that `prek` runs automatically before each commit:

```bash
uv run prek install -f
```

The `-f` flag forces the installation, in case there was already a `pre-commit` hook previously installed.

Now whenever you try to commit, for example with:

```bash
git commit
```

`prek` will check and format the code you are about to commit. If it modifies any files, add those files to Git again before committing.

### Run `prek` Manually

You can also run `prek` manually on all files from the project root:

```bash
uv run prek run --all-files
```
