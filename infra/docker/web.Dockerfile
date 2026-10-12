# Diyneco web app image: one Dockerfile for the five Next.js apps, built from the repository root.
#
#   docker build -f infra/docker/web.Dockerfile --build-arg APP=merchant \
#     --build-arg NEXT_PUBLIC_API_URL=https://api.example.com -t diyneco-merchant .
#
# APP is admin, merchant, kitchen, guest or room-service. NEXT_PUBLIC_API_URL (and, when files
# are not on Supabase, NEXT_PUBLIC_STORAGE_URL) are fixed at build time: they are compiled into
# the pages and their Content-Security-Policy, so build one image per environment. They are
# public addresses, never secrets; no secret is ever passed to a web image.
FROM node:24-slim AS build
ARG APP
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_STORAGE_URL=
RUN test -n "$APP" && test -n "$NEXT_PUBLIC_API_URL" || (echo "APP and NEXT_PUBLIC_API_URL are required" && exit 1)
ENV NEXT_TELEMETRY_DISABLED=1 NEXT_OUTPUT=standalone PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL NEXT_PUBLIC_STORAGE_URL=$NEXT_PUBLIC_STORAGE_URL
RUN corepack enable
WORKDIR /repo
COPY . .
# The whole workspace: the apps use the shared packages through their source (transpilePackages),
# so those packages' own dependencies must be installed too.
RUN pnpm install --frozen-lockfile
RUN pnpm --filter "./apps/${APP}" build && mkdir -p "apps/${APP}/public"

FROM node:24-slim
ARG APP
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0 APP=${APP}
RUN useradd --system --uid 10001 --home /app web
WORKDIR /app
COPY --from=build --chown=web:web /repo/apps/${APP}/.next/standalone ./
COPY --from=build --chown=web:web /repo/apps/${APP}/.next/static ./apps/${APP}/.next/static
COPY --from=build --chown=web:web /repo/apps/${APP}/public ./apps/${APP}/public
USER web
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s \
  CMD node -e "fetch('http://127.0.0.1:3000/').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["sh", "-c", "exec node apps/$APP/server.js"]
