# Securo image

The image bundles the upstream Securo frontend with its backend so a single
container serves both the web UI and the API.

The Securo Checker workflow checks for stable upstream releases daily. The
Securo Builder publishes versioned images to `ghcr.io/kyxie/securo` for
`linux/amd64` and `linux/arm64`.

To build a specific upstream version locally, run this from the `securo`
directory. Pass the version without the leading `v` as the build argument.

```sh
docker build --build-arg SECURO_VERSION=0.21.0 -t securo:v0.21.0 .
```
