#!/usr/bin/env bash
# Host-side incremental rebuild and clean image packaging; no block-device writes.
set -euo pipefail
cd "$(dirname "$0")"
exec 9>build-job.lock
flock -n 9 || { echo 'Another build holds build-job.lock'; exit 2; }
output="${1:-artifacts-public-$(date -u +%Y%m%d-%H%M%S)}"
status=public-image-status.txt
trap 'rc=$?; if (( rc )); then echo "failed exit=$rc" > "$status"; fi' EXIT
echo preparing > "$status"
python3 prepare-device.py --no-authorized-keys
python3 prepare-android.py
python3 prepare-runtime.py
python3 prepare-kernel.py
echo building-kernel > "$status"
make -C kernel O="$PWD/kernel-out" ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- -j1 zImage dtbs
echo building-android > "$status"
/snap/bin/lxc exec zero2w-kitkat-build -- bash /work/build-android.sh
echo checking-staging > "$status"
python3 - <<'PY'
from pathlib import Path
p = Path('aosp/out/target/product/zero2w')
assert not (p / 'root/adb_keys').read_bytes().strip(), 'Public image contains an ADB key'
assert 'ro.adb.secure=1' in (p / 'root/default.prop').read_text()
prop = (p / 'system/build.prop').read_text()
for value in ('ro.config.size_override=320,480', 'service.adb.tcp.port=5556',
              'debug.gralloc.zero2w_pan=1', 'debug.sf.zero2w_full_redraw=1'):
    assert value in prop, value
for name in ('Gallery', 'Browser', 'Calculator', 'DeskClock', 'Calendar', 'Music'):
    assert any((p / 'system' / d / (name + '.apk')).is_file() for d in ('app', 'priv-app')), name
for name in ('cfg80211', 'brcmutil', 'brcmfmac'):
    assert (p / 'system/lib/modules' / (name + '.ko')).is_file(), name
for base in (p / 'data', p / 'root', p / 'system'):
    for name in ('adbkey', 'adbkey.pub', 'accounts.db', 'settings.db'):
        assert not list(base.rglob(name)), 'Personal-data candidate: ' + name
assert not list((p / 'data').rglob('wpa_supplicant.conf'))
PY
echo checking-filesystems > "$status"
# The legacy container creates these generated files as root.
/snap/bin/lxc exec zero2w-kitkat-build -- chown "$(id -u):$(id -g)" \
    /work/aosp/out/target/product/zero2w/system.img \
    /work/aosp/out/target/product/zero2w/userdata.img \
    /work/aosp/out/target/product/zero2w/cache.img
for image in system userdata cache; do
    # KitKat make_ext4fs may leave inode-bitmap padding unset. Normalize only
    # these generated image files before they are copied into the SD image.
    rc=0
    e2fsck -fy "aosp/out/target/product/zero2w/$image.img" || rc=$?
    (( rc <= 1 )) || exit "$rc"
    e2fsck -fn "aosp/out/target/product/zero2w/$image.img"
done
echo assembling-image > "$status"
python3 assemble-image.py --variant usb-host --output-dir "$output"
fsck.vfat -n "$output/boot-fat.img"
(cd "$output" && sha256sum -c *.sha256)
python3 verify-public-image.py "$output"
echo image-created-hardware-unverified > "$status"
printf 'Image directory: %s\n' "$output"
