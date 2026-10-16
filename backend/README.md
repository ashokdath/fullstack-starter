# Django Project - Backend

Django 6.1 + [Django Ninja](https://django-ninja.dev) REST API, PostgreSQL, JWT authentication. API-only: the frontend is a separate app (`../frontend`), and static and media files are served from object storage.

- API: `/api/v1/` — interactive docs at `/api/v1/docs`, schema at `/api/v1/openapi.json`
- Django admin: `/django-admin/` (superusers), themed with [Unfold](https://unfoldadmin.com). Not `/admin/`: on the shared domain that path is the React app's user management page
- Everything else: 404

## Contents

- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Project Layout](#project-layout)
- [Configuration](#configuration)
- [API](#api)
- [Adding a Resource](#adding-a-resource)
- [Database and Migrations](#database-and-migrations)
- [Django Admin](#django-admin)
- [Emails](#emails)
- [Tests](#tests)
- [Linting and Formatting](#linting-and-formatting)
- [Docker](#docker)
- [Command Reference](#command-reference)
- [Troubleshooting](#troubleshooting)

## Requirements

- [Docker](https://www.docker.com/), for PostgreSQL and Mailpit (and the full stack).
- [uv](https://docs.astral.sh/uv/), for Python 3.14 and the dependencies.

## Quick Start

From the project root, start PostgreSQL and Mailpit:

```console
$ docker compose up -d db mailpit
```

From `./backend/`, install the dependencies, prepare the database and start the development server:

```console
$ uv sync
$ uv run bash scripts/prestart.sh
$ uv run python manage.py runserver
```

`prestart.sh` applies the migrations and creates the first superuser (`FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` from `.env`, `admin@example.com` / `changethis` by default).

| URL | What |
|---|---|
| <http://localhost:8000/api/v1/docs> | Interactive API docs (Swagger UI) |
| <http://localhost:8000/django-admin/> | Django admin |
| <http://localhost:8025> | Mailpit, emails sent in development |
| <http://localhost:5173> | Frontend dev server, if started with `bun run dev` from the project root |

The virtual environment is created at the project root (`../.venv`, a uv workspace). Point your editor to `.venv/bin/python`.

## Project Layout

```
backend/
├── manage.py
├── pyproject.toml              # dependencies, ruff, mypy, pytest, coverage config
├── Dockerfile                  # builds the frontend, then the Python image (gunicorn)
├── scripts/
│   ├── prestart.sh             # migrate + create_initial_data (run before every start)
│   ├── test.sh                 # pytest with coverage
│   ├── tests-start.sh          # entrypoint for tests in a running container
│   ├── lint.sh                 # mypy + ruff checks
│   └── format.sh               # ruff fix + format
├── app/                        # Django project package
│   ├── settings.py             # Django settings, all values come from core/config.py
│   ├── urls.py                 # /api/v1/ → Ninja, /django-admin/ (everything else: 404)
│   ├── api.py                  # NinjaAPI instance: routers, auth error handler
│   ├── schemas.py              # shared schemas: Message, Token, TokenPayload, NewPassword
│   ├── wsgi.py / asgi.py
│   ├── core/
│   │   ├── config.py           # Settings (pydantic-settings, reads ../.env)
│   │   ├── security.py         # JWT, JWTBearer auth, current_user(), require_superuser()
│   │   ├── openapi.py          # FastAPI-compatible OpenAPI output (frontend client contract)
│   │   ├── email.py            # send_email() and the generate_*_email() builders
│   │   └── views.py            # spa_index: serves the built React app
│   ├── users/                  # Django app "users"
│   │   ├── models.py           # custom User model (email login, UUID pk)
│   │   ├── schemas.py          # UserPublic, UserCreate, UserUpdate, ... + login form
│   │   ├── services.py         # create_user, update_user, authenticate, ...
│   │   ├── tokens.py           # single-use password reset tokens
│   │   ├── login.py            # router "login": token, password recovery/reset
│   │   ├── routes.py           # router "users"
│   │   ├── private.py          # router "private" (development only, used by Playwright)
│   │   ├── admin.py
│   │   └── management/commands/create_initial_data.py
│   ├── items/                  # Django app "items": the reference example resource
│   │   ├── models.py  schemas.py  routes.py  admin.py  migrations/
│   ├── utils_api/routes.py     # router "utils": health check, test email
│   └── email-templates/        # HTML generated from ../packages/react-email (don't edit)
└── tests/
    ├── conftest.py             # fixtures: client, superuser/normal user token headers
    ├── api/routes/             # one test module per router
    ├── users/test_services.py
    ├── test_openapi.py         # API contract checks
    ├── test_frontend.py        # SPA serving, admin
    └── utils/                  # APIClient, random data, user/item factories
```

## Configuration

All configuration comes from environment variables, validated by the `Settings` class in `app/core/config.py` (pydantic-settings). Locally they are read from the `.env` file at the project root; in Docker Compose they are passed by `compose.yml`. `app/settings.py` builds the Django settings from them: don't read `os.environ` anywhere else.

| Variable | Default | Description |
|---|---|---|
| `PROJECT_NAME` | required | Shown in API docs and emails |
| `SECRET_KEY` | required | Django secret key and JWT signing key |
| `DATABASE_URL` | required | `postgresql://user:password@host:5432/db` |
| `FIRST_SUPERUSER` | required | Email of the superuser created by `create_initial_data` |
| `FIRST_SUPERUSER_PASSWORD` | required | Its password |
| `ENVIRONMENT` | unset | `development` enables `DEBUG`, the `/api/v1/private` endpoints, and allows placeholder secrets |
| `FRONTEND_HOST` | `http://localhost:5173` | Used in email links and for CORS |
| `AWS_STORAGE_BUCKET_NAME` | unset | Enables object storage for static and media files; unset keeps them on the local disk |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | unset | Bucket credentials |
| `AWS_S3_REGION_NAME` | unset | Bucket region |
| `AWS_S3_ENDPOINT_URL` | unset | Only for S3-compatible services (R2, MinIO, Spaces, ...) |
| `AWS_S3_CUSTOM_DOMAIN` | unset | CDN domain in front of the bucket, e.g. `cdn.example.com`; file URLs use it |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `11520` (8 days) | JWT lifetime |
| `EMAIL_RESET_TOKEN_EXPIRE_HOURS` | `48` | Password reset link lifetime |
| `SMTP_HOST` | unset | Emails are enabled only when `SMTP_HOST` and `EMAILS_FROM_EMAIL` are set |
| `SMTP_PORT` | `587` | |
| `SMTP_USER` / `SMTP_PASSWORD` | unset | SMTP credentials |
| `SMTP_TLS` / `SMTP_SSL` | `True` / `False` | Connection security |
| `EMAILS_FROM_EMAIL` | unset | Sender address |
| `EMAILS_FROM_NAME` | `PROJECT_NAME` | Sender name |
| `SENTRY_DSN` | unset | Enables Sentry outside development |

Unless `ENVIRONMENT=development`, the app refuses to start when `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD` or the database password is still `changethis`. Generate real values with:

```console
$ python -c "import secrets; print(secrets.token_urlsafe(32))"
```

To add a setting: add a field to `Settings`, use it as `settings.MY_SETTING` (from `app.core.config`), and, if Django needs it, map it in `app/settings.py`. Pass it to the container in `compose.yml` when needed.

## API

### Endpoints

All under `/api/v1`. "user" means a valid bearer token, "superuser" a token of a superuser.

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/login/access-token` | — | Form body `username`, `password` → `{access_token, token_type}` |
| POST | `/login/test-token` | user | Returns the current user |
| POST | `/password-recovery/{email}` | — | Emails a reset link (same reply whether the email exists or not) |
| POST | `/reset-password/` | — | `{token, new_password}` |
| POST | `/password-recovery-html-content/{email}` | superuser | Preview of the reset email (HTML) |
| GET | `/users/` | superuser | List users (`skip`, `limit`) |
| POST | `/users/` | superuser | Create a user (sends a new account email when emails are enabled) |
| GET / PATCH / DELETE | `/users/me` | user | Own profile; superusers can't delete themselves |
| PATCH | `/users/me/password` | user | `{current_password, new_password}` |
| POST | `/users/signup` | — | Self registration |
| GET / PATCH / DELETE | `/users/{user_id}` | user / superuser / superuser | A user by id (users can read only themselves) |
| GET / POST | `/items/` | user | List (superusers see all, others their own) / create |
| GET / PUT / DELETE | `/items/{id}` | user | Owner or superuser only. `PUT` updates only the fields sent |
| POST | `/utils/test-email/?email_to=` | superuser | Sends a test email (201) |
| GET | `/utils/health-check/` | — | `true` |
| POST | `/private/users/` | — | Development only: create a user directly (Playwright) |

### Authentication

- Login (`POST /login/access-token`) takes an OAuth2 password form (`application/x-www-form-urlencoded`) and returns a JWT (HS256, signed with `SECRET_KEY`, `sub` = user id).
- Clients send it as `Authorization: Bearer <token>`.
- Protect an endpoint with `auth=jwt_auth` on the operation or on the whole `Router`. Missing/invalid token → `401 {"detail": "Not authenticated"}`; deleted user → 404; inactive user → 400.
- In the view, `current_user(request)` returns the `User`; `require_superuser(request)` returns it or raises 403.
- Passwords are hashed with Argon2. Users with an older hash (e.g. PBKDF2) are upgraded on their next login.
- Password reset links use Django's `PasswordResetTokenGenerator` (`app/users/tokens.py`): the token is `<uidb64>.<token>`, single use (it stops working once the password changes) and expires after `EMAIL_RESET_TOKEN_EXPIRE_HOURS`.

### Responses and Errors

- Errors: `raise HttpError(status, "message")` → `{"detail": "message"}`.
- Validation errors: `422` `{"detail": [{"type", "loc", "msg", "ctx"}]}`. The frontend shows `msg`.
- Lists: `skip` / `limit` query parameters (defaults `0` / `100`), response `{"data": [...], "count": total}`.
- Creates return `200` (except `/utils/test-email/`, `201`), same as the original FastAPI template.

### API Contract and the Frontend Client

The frontend client (`../frontend/src/client`) is generated from `/api/v1/openapi.json`, so names in the backend become names in the frontend:

| Backend | Frontend |
|---|---|
| `Router(tags=["users"])` | `UsersService` |
| `def read_user_me(request)` in that router | `UsersService.readUserMe()` (operation id `users-read_user_me`) |
| `class UserPublic(Schema)` | `type UserPublic` |

Rules:

- Use plain `ninja.Schema` classes with explicit names, not `ModelSchema`.
- One tag per router; unique function names within a tag.
- Keep a docstring on each endpoint: it becomes the description in the docs and the client.
- After any API change, regenerate the client from the project root and commit it:

  ```console
  $ bash scripts/generate-client.sh
  ```

  The *Check Frontend Client* workflow fails when the committed client is out of date.

`app/core/openapi.py` post-processes Ninja's schema to keep it identical to what FastAPI produced (operation ids, `OAuth2PasswordBearer` security scheme, `422` responses, `Body_*` names for form bodies). `tests/test_openapi.py` covers it.

## Adding a Resource

The `items` app is the reference: copy its structure. Example for a `projects` resource:

1. **Create the app** `app/projects/` with `__init__.py`, `migrations/__init__.py` and `apps.py`:

   ```python
   from django.apps import AppConfig


   class ProjectsConfig(AppConfig):
       name = "app.projects"
       label = "projects"
   ```

   Add `"app.projects"` to `INSTALLED_APPS` in `app/settings.py`.

2. **Model** in `models.py` (UUID primary key, `created_at`, owner if needed), and register it in `admin.py`.

3. **Schemas** in `schemas.py`:

   ```python
   class ProjectCreate(Schema):
       name: str = Field(min_length=1, max_length=255)


   class ProjectPublic(Schema):
       id: uuid.UUID
       name: str
       created_at: datetime | None = None


   class ProjectsPublic(Schema):
       data: list[ProjectPublic]
       count: int
   ```

4. **Router** in `routes.py`:

   ```python
   router = Router(tags=["projects"], auth=jwt_auth)


   @router.get("/", response=ProjectsPublic)
   def read_projects(
       request: HttpRequest, skip: int = 0, limit: int = 100
   ) -> ProjectsPublic:
       """
       Retrieve projects.
       """
       projects = Project.objects.filter(owner=current_user(request))
       return ProjectsPublic(
           data=[ProjectPublic.model_validate(p) for p in projects[skip : skip + limit]],
           count=projects.count(),
       )
   ```

   Use the `uuid:` path converter for ids (`"/{uuid:id}"`), so fixed paths like `/me` never collide with ids.

5. **Mount it** in `app/api.py`: `api.add_router("/projects", projects_router)`.

6. **Migrate**: `uv run python manage.py makemigrations projects && uv run python manage.py migrate`.

7. **Test** in `tests/api/routes/test_projects.py` (see `test_items.py`).

8. **Regenerate the client** (`bash scripts/generate-client.sh` from the root) and build the frontend page; `ProjectsService` is now available.

Keep business logic that more than one view uses in a `services.py` module (see `app/users/services.py`), and keep views thin.

## Database and Migrations

PostgreSQL through psycopg 3, configured from `DATABASE_URL`.

After changing a model, create and apply a migration, then commit the generated file:

```console
$ uv run python manage.py makemigrations
$ uv run python manage.py migrate
```

`scripts/prestart.sh` runs `migrate` and `create_initial_data` on every start of the stack (and in the Docker deploy workflow), so deployed databases are migrated automatically.

**Custom user model.** `app.users.User` (`AUTH_USER_MODEL = "users.User"`) logs in with `email`, has a UUID primary key, `full_name`, `is_active`, `is_superuser` and `created_at`. `is_staff` is kept equal to `is_superuser` on save, so every superuser can use the Django admin. Add any extra user fields before the first deployment of a project: swapping user models later is hard in Django.

**Starting over locally:**

```console
$ docker compose down -v          # from the project root: deletes the database volume
$ docker compose up -d db mailpit
$ uv run bash scripts/prestart.sh
```

## Django Admin

Available at `/django-admin/` for superusers, with session login (separate from the API's JWT). Users and Items are registered (`app/*/admin.py`). Register new models with:

```python
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin[Project]):
    list_display = ("name", "created_at")
```

## Emails

Emails are sent through the SMTP mailer configured in `MAILERS` (Django 6.1+) from the `SMTP_*` variables. Sending is enabled only when `SMTP_HOST` and `EMAILS_FROM_EMAIL` are set. In development they go to Mailpit (<http://localhost:8025>); in tests they go to an in-memory outbox.

Emails sent by the app:

| Email | Trigger | Builder |
|---|---|---|
| Password recovery | `POST /password-recovery/{email}` | `generate_reset_password_email()` |
| New account (includes the password) | `POST /users/` by a superuser | `generate_new_account_email()` |
| Test email | `POST /utils/test-email/` | `generate_test_email()` |

### Email Templates

The templates are written with [React Email](https://react.email) in `../packages/react-email/` (`emails/` has one component per email, `ui/` the shared components). The HTML in `app/email-templates/` is generated from them and rendered with the Django template engine: don't edit it by hand.

Preview while editing, from the project root:

```console
$ bun run email:dev
```

Backend values are placeholders in the component props, e.g. `username = "{{ username }}"`. Add new placeholders to the context in the matching `generate_*_email()` in `app/core/email.py`. Then regenerate the HTML:

```console
$ bun run email:export
```

## Tests

PostgreSQL must be running (`docker compose up -d db` from the root). From `./backend/`:

```console
$ uv run bash scripts/test.sh                # whole suite with coverage
$ uv run bash scripts/test.sh -x -k login    # extra arguments go to pytest
```

- [pytest-django](https://pytest-django.readthedocs.io) creates a separate `test_app` database; each test runs in a transaction that is rolled back.
- `conftest.py` creates the first superuser for every test and provides the `client`, `superuser_token_headers` and `normal_user_token_headers` fixtures.
- `client` (`tests/utils/utils.py:APIClient`) goes through the real Django URL routing and middleware. Use `json_body=` for JSON and `data=` for form bodies:

  ```python
  def test_create_item(
      client: APIClient, superuser_token_headers: dict[str, str]
  ) -> None:
      r = client.post(
          f"{settings.API_V1_STR}/items/",
          headers=superuser_token_headers,
          json_body={"title": "Foo"},
      )
      assert r.status_code == 200
  ```

- Emails: request the `mailoutbox` fixture and patch `app.core.config.settings.SMTP_HOST` to enable sending (see `test_utils.py`).
- Factories: `tests/utils/user.py:create_random_user()`, `tests/utils/item.py:create_random_item()`.

Coverage is written to `htmlcov/index.html`. CI requires at least 90%.

To run the tests inside a running Compose stack:

```console
$ docker compose exec backend bash scripts/tests-start.sh -x
```

The end-to-end tests (Playwright) live in `../frontend/tests`; see the [frontend README](../frontend/README.md).

## Linting and Formatting

```console
$ uv run bash scripts/lint.sh     # mypy (strict, with django-stubs) + ruff check + ruff format --check
$ uv run bash scripts/format.sh   # ruff fix + ruff format
```

The same checks run as pre-commit hooks (`uv run prek install -f` from the root) and in CI.

## Docker

`Dockerfile` (built from the project root by Compose):

1. installs the Python dependencies with uv,
2. starts **gunicorn** with 4 workers on port 8000.

Django never serves files in deployments. `scripts/prestart.sh` runs `collectstatic`, which uploads the admin assets to the bucket when `AWS_STORAGE_BUCKET_NAME` is set; uploads (`FileField`, `ImageField`) go to the `media/` prefix of the same bucket. Static URLs are public; media URLs are signed unless `AWS_S3_CUSTOM_DOMAIN` (a CDN) is set.

`compose.override.yml` (applied automatically locally) replaces gunicorn with `manage.py runserver` and syncs `./backend` into the container with `docker compose watch`.

```console
$ docker compose run --rm backend bash scripts/prestart.sh   # from the project root
$ docker compose watch
$ docker compose logs backend
$ docker compose exec backend bash
```

Stop a local `runserver` first: both use port 8000.

## Command Reference

Run from `./backend/` (prefix with `uv run`, or with `docker compose exec backend` inside the stack).

| Command | Purpose |
|---|---|
| `python manage.py runserver` | Development server |
| `python manage.py makemigrations` / `migrate` | Create / apply migrations |
| `python manage.py create_initial_data` | Create the first superuser if missing |
| `python manage.py createsuperuser` | Create another superuser interactively |
| `python manage.py changepassword <email>` | Reset a user's password |
| `python manage.py shell` | Django shell |
| `python manage.py export_openapi_schema --api app.api.api` | Print the OpenAPI schema |
| `bash scripts/prestart.sh` | Migrate + initial data + collectstatic |
| `bash scripts/test.sh [pytest args]` | Tests with coverage |
| `bash scripts/lint.sh` / `format.sh` | Checks / auto-fix |

## Troubleshooting

- **`ValueError: The value of SECRET_KEY is "changethis"`** — set real secrets, or `ENVIRONMENT=development` for local work.
- **`connection ... port 5432 failed: Connection refused`** — PostgreSQL isn't running: `docker compose up -d db`.
- **404 at `/`** — expected: the backend is API-only. Open the frontend (<http://localhost:5173>) or the API docs (`/api/v1/docs`).
- **Django admin without styles in a deployment** — set the `AWS_*` object storage variables and run `scripts/prestart.sh` (it runs `collectstatic`).
- **`/api/v1/private/...` returns 404** — those endpoints exist only with `ENVIRONMENT=development`.
- **Frontend types out of date / Check Frontend Client fails** — run `bash scripts/generate-client.sh` from the root and commit `frontend/src/client`.
- **CORS errors from the Vite dev server** — `FRONTEND_HOST` must match the dev server origin (`http://localhost:5173`).
