FROM node:20-slim AS deps
WORKDIR /app
COPY package.json ./
RUN npm install

FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Build-time public env vars must be present at `next build`, not just at
# container run — Next.js inlines NEXT_PUBLIC_* values into the client
# bundle. docker-compose passes these through as build args below.
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

# Non-root, same rationale as backend/Dockerfile. Create the user BEFORE
# copying anything, then set ownership via COPY's own --chown flag rather
# than a separate `RUN chown -R` pass afterward. Functionally identical
# result, but --chown sets ownership as part of the single write each file
# already gets during COPY, instead of a second full-tree walk touching
# every file in node_modules again immediately after. That second pass is
# expensive on its own, and on a strained/flaky Docker filesystem layer
# (e.g. a nearly-full or degraded WSL2 virtual disk on Windows) is exactly
# the kind of bulk metadata operation that surfaces as an Input/output
# error touching hundreds of files at once.
RUN useradd --create-home --shell /bin/bash appuser
COPY --from=builder --chown=appuser:appuser /app/next.config.mjs ./
COPY --from=builder --chown=appuser:appuser /app/public ./public
COPY --from=builder --chown=appuser:appuser /app/.next ./.next
COPY --from=builder --chown=appuser:appuser /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appuser /app/package.json ./package.json

USER appuser

EXPOSE 3000
CMD ["npm", "start"]
