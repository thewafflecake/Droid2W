#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec 9>build-job.lock
flock -n 9 || exit 2
trap 'rc=$?; if (( rc )); then echo "failed $rc" > network-build-status.txt; fi' EXIT
echo kernel > network-build-status.txt
python3 prepare-kernel.py
bash build-kernel.sh > network-kernel.log 2>&1
# Build only the Wi-Fi modules, not every optional Raspberry Pi driver.
cp kernel-out/vmlinux.symvers kernel-out/Module.symvers
export ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf-
wifi_cflags="-I$PWD/kernel/drivers/net/wireless/broadcom/brcm80211/include"
if grep -qx 'CONFIG_BRCMDBG=y' kernel-out/.config; then
    wifi_cflags="$wifi_cflags -DDEBUG"
fi
make -C kernel O="$PWD/kernel-out" modules_prepare >> network-modules.log 2>&1
echo modules > network-build-status.txt
make -C kernel O="$PWD/kernel-out" -j2 M="$PWD/kernel/net/wireless" CONFIG_LIB80211=n \
    CONFIG_LIB80211_CRYPT_WEP=n CONFIG_LIB80211_CRYPT_TKIP=n CONFIG_LIB80211_CRYPT_CCMP=n modules > network-modules.log 2>&1
make -C kernel O="$PWD/kernel-out" -j2 M="$PWD/kernel/drivers/net/wireless/broadcom/brcm80211/brcmutil" \
    KCFLAGS="$wifi_cflags" modules >> network-modules.log 2>&1
make -C kernel O="$PWD/kernel-out" -j2 M="$PWD/kernel/drivers/net/wireless/broadcom/brcm80211/brcmfmac" \
    KCFLAGS="$wifi_cflags -I$PWD/kernel/drivers/net/wireless/broadcom/brcm80211/brcmfmac" \
    KBUILD_EXTRA_SYMBOLS="$PWD/kernel/net/wireless/Module.symvers $PWD/kernel/drivers/net/wireless/broadcom/brcm80211/brcmutil/Module.symvers" modules >> network-modules.log 2>&1
mkdir -p aosp/device/experimental/zero2w/modules
cp kernel/net/wireless/cfg80211.ko aosp/device/experimental/zero2w/modules/
cp kernel/drivers/net/wireless/broadcom/brcm80211/brcmutil/brcmutil.ko aosp/device/experimental/zero2w/modules/
cp kernel/drivers/net/wireless/broadcom/brcm80211/brcmfmac/brcmfmac.ko aosp/device/experimental/zero2w/modules/
echo ready-to-test > network-build-status.txt
