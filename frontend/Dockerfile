# Build context is ./frontend (see docker-compose.yml).
# Three stages: install deps, build the Next.js app, then run only the small standalone output.

# ---- 1. deps: install node_modules from the lockfile (cached until package*.json changes)
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# ---- 2. builder: compile the app
FROM node:22-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

# NEXT_PUBLIC_* values are baked into the JS bundle at build time (changing them means rebuilding).
# The current frontend code does not read them yet; they are declared so docker-compose can pass
# them without a "build-arg not consumed" warning and so the wiring is ready for the real API.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_USE_MOCK=false
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_USE_MOCK=$NEXT_PUBLIC_USE_MOCK

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- 3. runner: minimal image, non-root user
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -S -g 1001 nodejs && adduser -S -u 1001 -G nodejs nextjs

# next.config.ts sets output: 'standalone', so .next/standalone has server.js and only the
# node_modules it needs. public/ and .next/static are not included in it and are copied by hand.
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
  CMD wget -qO /dev/null http://127.0.0.1:3000/api/status || exit 1

CMD ["node", "server.js"]
