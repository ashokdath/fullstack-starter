#! /usr/bin/env bash
#
# Turn a fresh clone of the template into a new project.
#
#   bash scripts/init-project.sh "My Project" [--slug my-project] [--no-install] [--no-git] [--keep-script]
#
# What it does:
#   1. Renames the project everywhere the template name is hardcoded
#   2. Generates a local SECRET_KEY in .env (other dev secrets stay "changethis";
#      Playwright and Compose read them from .env)
#   3. Writes a short project README and keeps the template README as docs/template-README.md
#   4. Adds .DS_Store to .gitignore
#   5. Detaches git from the template (removes the template remote, or git init)
#      and makes the initial commit
#   6. Installs dependencies and prepares the local database
#      (docker compose db + mailpit, uv sync, prestart, bun install, prek hooks)
#   7. Deletes itself
#
# The Items example is kept on purpose: it is the reference pattern for new
# resources. Remove it by hand when you no longer need it (see README).

set -euo pipefail

TEMPLATE_NAME="Full Stack Django Project"
TEMPLATE_TITLE="Full Stack Django Template"
TEMPLATE_SLUG="fullstack-starter"

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
}

PROJECT_NAME=""
SLUG=""
INSTALL=1
GIT=1
KEEP_SCRIPT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --slug) SLUG="$2"; shift 2 ;;
    --no-install) INSTALL=0; shift ;;
    --no-git) GIT=0; shift ;;
    --keep-script) KEEP_SCRIPT=1; shift ;;
    -h|--help) usage ;;
    -*) echo "Unknown option: $1"; usage ;;
    *) if [ -z "$PROJECT_NAME" ]; then PROJECT_NAME="$1"; shift; else usage; fi ;;
  esac
done

[ -n "$PROJECT_NAME" ] || usage

if [ -z "$SLUG" ]; then
  SLUG="$(printf '%s' "$PROJECT_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! grep -q "$TEMPLATE_SLUG" package.json 2>/dev/null; then
  echo "package.json no longer references $TEMPLATE_SLUG: this project looks already initialized."
  exit 1
fi

for tool in perl python3; do
  command -v "$tool" >/dev/null || { echo "Missing required tool: $tool"; exit 1; }
done
if [ "$INSTALL" = 1 ]; then
  for tool in uv bun docker; do
    command -v "$tool" >/dev/null || { echo "Missing required tool: $tool (or pass --no-install)"; exit 1; }
  done
fi

echo "==> Project: $PROJECT_NAME  (slug: $SLUG)"

# Escape for use in a perl substitution replacement
pesc() { printf '%s' "$1" | sed -e 's/[\/&\\]/\\&/g' -e 's/\$/\\$/g' -e 's/@/\\@/g'; }
NAME_ESC="$(pesc "$PROJECT_NAME")"
SLUG_ESC="$(pesc "$SLUG")"

replace() { # replace <search> <replacement> <file>...
  local search="$1" repl="$2"; shift 2
  perl -pi -e "s/\Q$search\E/$repl/g" "$@"
}

echo "==> Renaming"
replace "$TEMPLATE_NAME"  "$NAME_ESC" .env frontend/src/lib/site.ts frontend/src/routes/__root.tsx deployment-docker-compose.md
replace "$TEMPLATE_TITLE" "$NAME_ESC" frontend/src/components/Common/Footer.tsx
replace "$TEMPLATE_SLUG"  "$SLUG_ESC" package.json
replace "$TEMPLATE_TITLE contributors" "$NAME_ESC contributors" LICENSE
# Python package name in pyproject (if the template slug is used there)
if grep -q "$TEMPLATE_SLUG" pyproject.toml 2>/dev/null; then
  replace "$TEMPLATE_SLUG" "$SLUG_ESC" pyproject.toml
fi

echo "==> Generating local SECRET_KEY"
SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
perl -pi -e "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET/" .env

echo "==> README"
mkdir -p docs
git mv -f README.md docs/template-README.md 2>/dev/null || mv README.md docs/template-README.md
cat > README.md <<EOF
# $PROJECT_NAME

Django + Django Ninja API with a server-rendered React (TanStack Start) frontend.

## Development

\`\`\`bash
docker compose up -d db mailpit
cd backend && uv sync && uv run bash scripts/prestart.sh && uv run python manage.py runserver
# in another terminal, from the project root
bun install && bun run dev
\`\`\`

- App: <http://localhost:5173> (dashboard at \`/dashboard\`)
- API docs: <http://localhost:8000/api/v1/docs>
- Django admin: <http://localhost:8000/django-admin>
- Mailpit: <http://localhost:8025>

Full docs: [development.md](./development.md), [backend/README.md](./backend/README.md),
[frontend/README.md](./frontend/README.md), [deployment-docker-compose.md](./deployment-docker-compose.md).
Template notes (API contract rules, removing the Items example): [docs/template-README.md](./docs/template-README.md).
EOF

echo "==> .gitignore"
grep -qx '.DS_Store' .gitignore 2>/dev/null || printf '\n.DS_Store\n' >> .gitignore

if [ "$KEEP_SCRIPT" = 0 ]; then
  echo "==> Removing init script"
  rm -f "scripts/init-project.sh"
fi

if [ "$GIT" = 1 ]; then
  echo "==> Git"
  if [ -d .git ]; then
    origin="$(git remote get-url origin 2>/dev/null || true)"
    if printf '%s' "$origin" | grep -q "$TEMPLATE_SLUG"; then
      echo "    Removing template remote: $origin"
      git remote remove origin
    fi
  else
    git init -q
  fi
  git add -A
  git -c commit.gpgsign=false commit -q -m "Initialize $PROJECT_NAME from $TEMPLATE_SLUG" || true
fi

if [ "$INSTALL" = 1 ]; then
  echo "==> Starting db + mailpit"
  docker compose up -d db mailpit

  echo "==> Backend dependencies + database"
  (cd backend && uv sync && uv run bash scripts/prestart.sh)

  echo "==> Frontend dependencies"
  bun install

  echo "==> Git hooks"
  if [ "$GIT" = 1 ]; then uv run prek install -f || true; fi
fi

cat <<EOF

Done. $PROJECT_NAME is ready.

Next:
  1. Start the backend:   cd backend && uv run python manage.py runserver
  2. Start the frontend:  bun run dev
  3. Open http://localhost:5173/dashboard  (login: $(grep '^FIRST_SUPERUSER=' .env | cut -d= -f2) / $(grep '^FIRST_SUPERUSER_PASSWORD=' .env | cut -d= -f2))
  4. Replace the logo in frontend/public/assets/images and review frontend/src/components/Common/Footer.tsx
  5. Add a remote and push:  git remote add origin <url> && git push -u origin main
  6. For deployment, set real secrets in GitHub Actions (never in .env):
       python3 -c "import secrets; print(secrets.token_urlsafe(32))"
EOF
