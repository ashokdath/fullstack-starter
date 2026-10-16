FROM oven/bun:1 AS build

WORKDIR /app

COPY package.json bun.lock /app/
COPY frontend/package.json /app/frontend/

WORKDIR /app/frontend

RUN bun install

COPY ./frontend /app/frontend

# Build-time settings, baked into the browser bundle (both optional):
# an API on another domain (empty: same origin, /api) and the CDN serving the
# built assets (empty: served by this server)
ARG VITE_API_URL=
ARG VITE_ASSETS_URL=

RUN bun run build


FROM oven/bun:1-slim

WORKDIR /app

COPY package.json bun.lock /app/
COPY frontend/package.json /app/frontend/

WORKDIR /app/frontend

# The server bundle imports its dependencies at runtime
RUN bun install --production

COPY --from=build /app/frontend/dist /app/frontend/dist

ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

CMD ["bun", "run", "start"]
