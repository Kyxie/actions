# ---------- build stage ----------
FROM --platform=$BUILDPLATFORM golang:1.27.4-alpine AS builder

ARG BPCS_VER
ARG TARGETOS
ARG TARGETARCH
WORKDIR /build

RUN apk add --no-cache git
RUN git clone --branch "${BPCS_VER}" --depth 1 https://github.com/qjfoidnh/BaiduPCS-Go.git . \
    && go mod download \
    && CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH \
       go build -trimpath -ldflags="-s -w" -o BaiduPCS-Go .

# ---------- runtime stage ----------
FROM alpine:3.20
LABEL maintainer="Kyxie <github.com/Kyxie>" \
      description="Lightweight BaiduPCS-Go image"

RUN apk add --no-cache ca-certificates mailcap tzdata

COPY --from=builder /build/BaiduPCS-Go /usr/local/bin/

VOLUME ["/data", "/root/.config/BaiduPCS-Go"]
WORKDIR /data

ENTRYPOINT ["/usr/local/bin/BaiduPCS-Go"]
