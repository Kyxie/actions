# ==============================================================================
#  Default
# ==============================================================================

# List all available commands
default:
    @just --list

# ==============================================================================
#  Menuconfig
# ==============================================================================
menuconfig_image_name := "ghcr.io/kyxie/menuconfig:latest"
menuconfig_output_dir := "openwrt"

# Generate OpenWrt .config
menuconfig:
    @mkdir -p {{menuconfig_output_dir}}
    docker run --rm -it \
        -v $(pwd)/{{menuconfig_output_dir}}:/mnt/output \
        {{menuconfig_image_name}} \
        bash -c "cp -f .config /mnt/output/.config 2>/dev/null || true; make menuconfig && cp .config /mnt/output/.config && echo 'Done: .config saved to {{menuconfig_output_dir}}/'"
