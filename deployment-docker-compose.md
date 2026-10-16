# Django Project - Docker Compose Deployment

You can deploy the project to your own server with Docker Compose, behind the server's own nginx. One nginx can serve several projects on the same server: each project listens on a single port on `127.0.0.1`, and nginx forwards each domain to its project and handles HTTPS.

## Architecture

```
example.com → server nginx (HTTPS) → 127.0.0.1:APP_PORT → project gateway (nginx container)
                                                          ├── /api, /django-admin → backend (Django)
                                                          └── everything else     → frontend (TanStack Start SSR)
cdn.example.com → CDN → bucket: /static (admin), /media (uploads), /frontend (built JS/CSS)
```

Everything runs on one domain: the browser calls the API on its own origin, so there is no CORS, and one TLS certificate covers the app. Each project's gateway (`nginx/gateway.conf`, the same container and config used locally and in CI) routes by path, so API calls go straight to Django and never wait behind page rendering in the frontend server. Server-side rendering calls the backend directly inside the Compose network.

Django never serves files. Static and media files live in object storage (S3 or an S3-compatible service such as Cloudflare R2, MinIO or DigitalOcean Spaces), served through a CDN. The frontend's built assets can be served from the same CDN.

## Preparation

* Have a remote server ready and available.
* Configure a DNS record pointing to the server for the application domain, such as `django-project.example.com`.
* Install nginx and certbot on the server (`apt install nginx certbot python3-certbot-nginx` on Debian/Ubuntu).
* Create an object storage bucket and an access key that can write to it. Put a CDN in front of the bucket (CloudFront, Cloudflare, or the provider's own CDN), for example at `cdn.django-project.example.com`. The `static/` and `frontend/` prefixes must be publicly readable through the CDN; `media/` can stay private (Django then returns signed URLs) unless you serve it through the CDN as well.
* Install and configure [Docker](https://docs.docker.com/engine/install/) on the remote server (Docker Engine, not Docker Desktop).

## Copy the Code

```bash
rsync -av --exclude=".git/" --filter=":- .gitignore" ./ root@your-server.example.com:/root/code/app/
```

The `--filter=":- .gitignore"` option tells `rsync` to use the same ignore rules as Git, excluding files such as the Python virtual environment.

## Configure the Application

### Environment Variables

Set the application domain, project name, first superuser email, and the local port the server's nginx forwards to. Use a port no other project on the server uses:

```bash
export DOMAIN=django-project.example.com
export PROJECT_NAME="Full Stack Django Project"
export FIRST_SUPERUSER=admin@example.com
export APP_PORT=8000
```

The Compose project name (the directory name, or `COMPOSE_PROJECT_NAME`) prefixes the images, containers and the database volume, so keep it unique per project on the server.

You can also configure these environment variables as needed:

* `SMTP_HOST`: The SMTP server host from your email provider.
* `SMTP_USER`: The SMTP server user.
* `EMAILS_FROM_EMAIL`: The email account used to send emails.
* `SENTRY_DSN`: The DSN for Sentry.

Object storage for Django static and media files:

* `AWS_STORAGE_BUCKET_NAME`: The bucket name. Without it, the Django admin has no styles in deployments.
* `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`: The access key (secret).
* `AWS_S3_REGION_NAME`: The bucket region.
* `AWS_S3_ENDPOINT_URL`: Only for S3-compatible services, e.g. `https://<account>.r2.cloudflarestorage.com`.
* `AWS_S3_CUSTOM_DOMAIN`: The CDN domain in front of the bucket, e.g. `cdn.django-project.example.com`. File URLs then point at the CDN.

Frontend assets on the CDN (optional):

* `ASSETS_URL`: The CDN URL of the `frontend/` prefix in the bucket, e.g. `https://cdn.django-project.example.com/frontend`. The frontend is built to load its JavaScript, CSS and images from there. Without it, the frontend server serves them itself.

### Secrets

Generate and set secure values for the database password, token signing key, and first superuser password:

```bash
export POSTGRES_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export FIRST_SUPERUSER_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

To use an authenticated email provider, also set `SMTP_PASSWORD`.

## Deploy

```bash
cd /root/code/app/
docker compose -f compose.yml -f compose.deploy.yml build
docker compose -f compose.yml -f compose.deploy.yml run --rm backend bash scripts/prestart.sh
docker compose -f compose.yml -f compose.deploy.yml up -d
```

The `compose.deploy.yml` file adds restart policies and publishes the gateway (the `proxy` service) on `127.0.0.1:APP_PORT`, the only published port. Explicitly listing both files excludes the local settings from `compose.override.yml` (Adminer, Mailpit, Playwright, and the gateway on port 80).

`scripts/prestart.sh` runs the migrations and uploads the Django admin static files to the bucket (`collectstatic`).

With `ASSETS_URL` set, upload the built frontend assets to the bucket before starting the new version (the GitHub Actions workflow below does this for you):

```bash
image=$(docker compose -f compose.yml -f compose.deploy.yml config --images frontend | grep -- '-frontend$')
container=$(docker create "$image")
docker cp "$container:/app/frontend/dist/client" frontend-assets
docker rm "$container"
aws s3 sync frontend-assets "s3://$AWS_STORAGE_BUCKET_NAME/frontend"
```

The frontend Docker image builds the app, so the server does not need Bun or prebuilt frontend files.

## Configure nginx

Do this once per project. Render the site config from `nginx/host-site.conf.template` with the domain and port, enable it, and add HTTPS with certbot:

```bash
SERVER_NAME=$DOMAIN APP_PORT=$APP_PORT \
  envsubst '$SERVER_NAME $APP_PORT' \
  < nginx/host-site.conf.template | sudo tee /etc/nginx/sites-available/$DOMAIN
sudo ln -s /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d $DOMAIN
```

`certbot --nginx` adds the `listen 443 ssl` lines and the HTTP-to-HTTPS redirect to the site file, and renews the certificate automatically.

The site config only forwards the domain to the project's port; the project's gateway does the path routing. It always sets `X-Forwarded-Proto` and passes the `Host` header with `$http_host`: the gateway passes them on, and Django relies on them to know a request came over HTTPS (the admin login fails its CSRF check without them). If you write your own config instead, keep those headers.

The database admin UI (Adminer) only runs locally. To inspect the production database, use `docker compose -f compose.yml -f compose.deploy.yml exec db psql -U postgres app` on the server.

## Deploy with GitHub Actions

The included `.github/workflows/deploy-docker-compose.yml` workflow runs the deployment commands on the server when manually triggered from GitHub Actions.

Use a self-hosted runner only for a repository whose contributors and workflow code you trust. GitHub recommends using self-hosted runners with private repositories because workflows execute directly on the runner machine.

### Configure Repository Variables and Secrets

In the repository, go to **Settings** > **Secrets and variables** > **Actions** and add these repository variables:

* `DOMAIN`
* `PROJECT_NAME`
* `FIRST_SUPERUSER`

To enable emails, add these optional repository variables:

* `SMTP_HOST`
* `SMTP_USER`
* `EMAILS_FROM_EMAIL`

To enable Sentry, add the optional `SENTRY_DSN` repository variable.

Add the repository variable `APP_PORT` (the port configured in nginx for this project).

For object storage, add the repository variables `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`, optionally `AWS_S3_ENDPOINT_URL` and `ASSETS_URL`, and the repository secrets `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. When `ASSETS_URL` is set, the workflow uploads the frontend assets to the bucket with the `amazon/aws-cli` Docker image.

Add these repository secrets:

* `POSTGRES_PASSWORD`
* `SECRET_KEY`
* `FIRST_SUPERUSER_PASSWORD`

To use an authenticated email provider, add the optional `SMTP_PASSWORD` repository secret.

### Install a Self-Hosted Runner

On the server, create a dedicated user and grant it access to Docker:

```bash
sudo adduser github
sudo usermod -aG docker github
sudo su - github
```

In the GitHub repository, go to **Settings** > **Actions** > **Runners**, select **New self-hosted runner**, choose Linux, and follow the commands GitHub provides to download, configure, and register the runner. Install it in `/home/github/actions-runner`.

After registering the runner, exit the `github` user session and install the runner as a system service:

```bash
exit
cd /home/github/actions-runner
sudo ./svc.sh install github
sudo ./svc.sh start
sudo ./svc.sh status
```

See GitHub's guides for [adding a self-hosted runner](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners) and [configuring the runner as a service](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application?platform=linux).

### Run the Deployment

When the runner is online, open the repository's **Actions** tab, select **Deploy with Docker Compose**, and select **Run workflow**.

## URLs

Replace `django-project.example.com` with your domain.

Frontend: `https://django-project.example.com`

API: `https://django-project.example.com/api/v1/`

Interactive API docs: `https://django-project.example.com/api/v1/docs`

Django admin: `https://django-project.example.com/django-admin`
