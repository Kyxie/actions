# syntax=docker/dockerfile:1

ARG POSTGRES_TAG=17.11-alpine3.24
FROM postgres:${POSTGRES_TAG} AS extensions
ARG PGVECTOR_VERSION=0.8.7

RUN apk add --no-cache gcc git linux-headers make musl-dev
RUN git clone --branch "v${PGVECTOR_VERSION}" --depth 1 \
        https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && make -C /tmp/pgvector -j "$(nproc)" OPTFLAGS="" with_llvm=no \
    && make -C /tmp/pgvector install OPTFLAGS="" with_llvm=no DESTDIR=/extension-root \
    && install -D /tmp/pgvector/LICENSE /extension-root/usr/local/share/licenses/pgvector/LICENSE

FROM postgres:${POSTGRES_TAG}
COPY --from=extensions /extension-root/ /
