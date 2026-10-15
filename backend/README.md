# Django Project - Backend

## Requirements

* [Docker](https://www.docker.com/).
* [uv](https://docs.astral.sh/uv/) for Python package and environment management.

## Local Development

Run the backend locally and connect it to PostgreSQL in Docker Compose.

From the project root, start PostgreSQL and Mailpit:

```console
$ docker compose up -d db mailpit
```

Then, from `./backend/`, install the dependencies, prepare the database, and start the development server:

```console
$ uv sync
$ uv run bash scripts/prestart.sh
$ uv run python manage.py runserver
```

The API is available at `http://localhost:8000/api/v1/`, with automatic interactive docs at `http://localhost:8000/api/v1/docs` and the Django admin at `http://localhost:8000/admin/`.

## Project Layout

```
backend/
├── manage.py
├── app/                      # Django project package
│   ├── settings.py           # Django settings, built from core/config.py
│   ├── urls.py               # /api/v1/ → Ninja, /admin/, everything else → React app
│   ├── api.py                # NinjaAPI instance, routers
│   ├── schemas.py            # shared schemas (Message, Token, NewPassword)
│   ├── core/
│   │   ├── config.py         # Settings (pydantic-settings, reads ../.env)
│   │   ├── security.py       # JWT creation, JWTBearer auth, current_user / require_superuser
│   │   ├── openapi.py        # FastAPI-compatible OpenAPI output (see API contract rules)
│   │   ├── email.py          # send_email + email rendering
│   │   └── views.py          # serves the built React app (index.html)
│   ├── users/                # Django app: User model, login/users/private routers, services
│   ├── items/                # Django app: example resource (model, schemas, router)
│   ├── utils_api/            # health check and test email endpoints
│   ├── email-templates/      # HTML generated from packages/react-email
│   └── frontend/             # Vite build output (git ignored)
├── scripts/                  # prestart, test, lint, format
└── tests/
```

## General Workflow

Run backend commands from `./backend/` with `uv run`. Make sure your editor uses the Python interpreter at `.venv/bin/python` in the project root.

To add a resource, follow the `items` app:

1. Create a Django app under `app/` (`apps.py` with `name = "app.<name>"`), add it to `INSTALLED_APPS`.
2. Add models in `models.py`, register them in `admin.py`.
3. Add Ninja schemas in `schemas.py`: input schemas (`XCreate`, `XUpdate`) and output schemas (`XPublic`, `XsPublic`).
4. Add a `Router(tags=["<name>"])` in `routes.py` and mount it in `app/api.py`.
5. Create the migration, add tests, then regenerate the frontend client.

Read the **API Contract Rules** in the [root README](../README.md) before adding endpoints.

### Authentication

Protect an endpoint with `auth=jwt_auth` (or on the whole `Router`). Inside the view, `current_user(request)` returns the authenticated `User`, and `require_superuser(request)` also checks the superuser flag (403 otherwise).

Login is `POST /api/v1/login/access-token` with a form body (`username`, `password`), returning a JWT bearer token.

Password reset links use Django's `PasswordResetTokenGenerator` (`app/users/tokens.py`): single use, they stop working once the password changes, and they expire after `EMAIL_RESET_TOKEN_EXPIRE_HOURS`.

## VS Code

There are already configurations in place to run the backend through the VS Code debugger, so that you can use breakpoints, pause and explore variables, etc.

The setup is also already configured so you can run the tests through the VS Code Python tests tab.

## Full Stack with Docker Compose

To run the backend and built frontend in Docker Compose:

```console
$ docker compose run --rm backend bash scripts/prestart.sh
$ docker compose watch
```

The application is available at `http://localhost:8000`.

### Docker Compose Override

The `compose.override.yml` file contains local settings for published ports, source synchronization, automatic image rebuilds, and backend reloads (`manage.py runserver`). Docker Compose applies it automatically when you run `docker compose` without an explicit file list. Without it, the image runs Gunicorn.

To open a shell in the backend container:

```console
$ docker compose exec backend bash
```

## Backend Tests

To test the backend from the `backend` directory, with PostgreSQL running, run:

```console
$ uv run bash scripts/test.sh
```

The tests run with Pytest and pytest-django: each test runs in a transaction that is rolled back, against a separate test database. Emails go to an in-memory outbox (the `mailoutbox` fixture). Modify existing tests or add new ones in `./backend/tests/`.

If you use GitHub Actions, the tests will run automatically, with a 90% coverage requirement.

### Test a Running Stack

If your stack is already up and you just want to run the tests, you can use:

```bash
docker compose exec backend bash scripts/tests-start.sh
```

Extra arguments are forwarded to `pytest`, for example, to stop on first error:

```bash
docker compose exec backend bash scripts/tests-start.sh -x
```

### Test Coverage

When the tests run, they generate `htmlcov/index.html`. Open it in your browser to inspect the test coverage.

## Linting

```console
$ uv run bash scripts/lint.sh     # mypy (strict, with django-stubs) and ruff
$ uv run bash scripts/format.sh   # ruff fix and format
```

## Migrations

After changing a model, create a migration and apply it:

```console
$ uv run python manage.py makemigrations
$ uv run python manage.py migrate
```

Commit the generated files in the app's `migrations` directory. `scripts/prestart.sh` applies migrations and creates the first superuser (`create_initial_data` command) on every start of the stack.

The `User` model (`app/users/models.py`) is a custom user model (email login, UUID primary key). Change it before the first deployment if you need extra fields: swapping user models later is hard in Django.

## Email Templates

The email templates are written with [React Email](https://react.email) in `./packages/react-email/`. The `emails` directory holds one component per email and the `ui` directory holds the shared components (layout, heading, button, link, callout).

The rendered HTML in `./backend/app/email-templates/` is generated from those components. It is what the application sends and should not be edited by hand.

To preview the emails while editing them, start the dev server from the root of the project:

```console
$ bun run email:dev
```

Values coming from the backend are declared as placeholders in the component props, for example `username = "{{ username }}"`, rendered with the Django template engine. The context for each email is built in `generate_*_email()` in `./backend/app/core/email.py`, so a new placeholder needs to be added there too.

Once you are done, regenerate the templates used by the application:

```console
$ bun run email:export
```
