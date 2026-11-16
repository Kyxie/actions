# BaiduPCS-Go image

This repository builds [BaiduPCS-Go](https://github.com/qjfoidnh/BaiduPCS-Go) as a container image and publishes it to GHCR at `ghcr.io/kyxie/baidupcs-go`.

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
