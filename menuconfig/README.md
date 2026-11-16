A Docker environment designed for generating OpenWrt `.config` files. It saves you from installing gigabytes of dependencies on your host machine.

## Features

- Pre-cloned LEDE source code and updated feeds
- Slim image size (< 300MB)
- Generate `.config`

## How to run

- Run in bash

  ```bash
  docker run --rm -it \
    -v $(pwd)/openwrt:/mnt/output \
    ghcr.io/kyxie/menuconfig:latest \
    bash -c "[ -f /mnt/output/.config ] && cp /mnt/output/.config .config; make menuconfig && cp .config /mnt/output/.config"
  ```

- After configuration, will generate the `.config` in same folder
