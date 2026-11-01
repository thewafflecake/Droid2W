#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabihf-
mkdir -p kernel-out
make -C kernel O="$PWD/kernel-out" bcm2709_defconfig
kernel/scripts/kconfig/merge_config.sh -m -O "$PWD/kernel-out" kernel-out/.config kitkat-kernel.fragment
make -C kernel O="$PWD/kernel-out" olddefconfig
for config in ANDROID_BINDER_IPC ASHMEM KITKAT_LOGGER USB_DWCOTG USB_HID FB_BCM2708 EXT4_FS; do
    grep -qx "CONFIG_${config}=y" kernel-out/.config || { echo "Missing built-in $config" >&2; exit 1; }
done
make -C kernel O="$PWD/kernel-out" -j2 zImage dtbs
