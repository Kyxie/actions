# syntax=docker/dockerfile:1

ARG SECURO_VERSION=0.21.0
FROM --platform=$BUILDPLATFORM ghcr.io/securo-finance/securo-frontend:${SECURO_VERSION} AS frontend

FROM ghcr.io/securo-finance/securo-backend:${SECURO_VERSION}
ARG SECURO_VERSION
LABEL org.opencontainers.image.version="${SECURO_VERSION}" \
      org.opencontainers.image.licenses="AGPL-3.0-only"

COPY --from=frontend /usr/share/nginx/html/ /app/frontend-dist/
ENV FRONTEND_DIST_PATH=/app/frontend-dist
