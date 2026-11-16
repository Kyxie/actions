# BaiduPCS-Go image

This repository builds [BaiduPCS-Go](https://github.com/qjfoidnh/BaiduPCS-Go) as a container image and publishes it to GHCR at `ghcr.io/kyxie/baidupcs-go`.

## Builds and automatic updates

`baidupcs-checker.yml` checks the latest stable upstream release daily at 10:00 UTC and calls `baidupcs-builder.yml` when a release needs publishing. The success marker is saved only after the reusable builder succeeds, so failures are retried. Cache eviction can cause a harmless rebuild. Both workflows must be present on the default branch with scheduled workflows enabled; GitHub may disable schedules in inactive public repositories.

The builder publishes `linux/amd64` and `linux/arm64` under the upstream version tag and `latest`. Go is cross-compiled on the builder platform; QEMU handles runtime package installation. The static binary is available at `/usr/local/bin/BaiduPCS-Go` for other images to copy. For a manual retry or the first multi-platform publication, run **BaiduPCS Builder** from `main` with an upstream tag such as `v4.0.2`.

The `ingest` repository checks this image every six hours and rebuilds its uploader when the digest changes. It pins the resolved digest during each build; no cross-repository token is required. Make this GHCR package public so ingest can inspect and pull it anonymously. The N100 update timer is configured in ingest's deployment documentation.

This image still builds from upstream source. Existing published images remain useful if upstream disappears; keep a separate source backup if rebuilding BaiduPCS-Go must also remain possible.

## Run with Docker

```bash
docker run -d -it --name baidupcs-go \
  -v "$(pwd)/data:/data" \
  -v "$(pwd)/upload:/upload" \
  -v "$(pwd)/config:/root/.config/BaiduPCS-Go" \
  -w /upload \
  ghcr.io/kyxie/baidupcs-go:latest
```

## Run with Docker Compose

```yaml
services:
  baidupcs-go:
    image: ghcr.io/kyxie/baidupcs-go:latest
    container_name: baidupcs-go
    stdin_open: true
    tty: true
    volumes:
      - ./data:/data
      - ./upload:/upload
      - ./config:/root/.config/BaiduPCS-Go
    working_dir: /upload
```
