#!/usr/bin/env python3
"""Assemble a regular image FILE; never opens or writes a block device."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import shutil
import struct
import subprocess

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--variant', choices=('original', 'usb-adb'), default='original')
variant = parser.parse_args().variant
product = root / 'aosp/out/target/product/zero2w'
boot = root / 'boot'
kernel = root / 'kernel-out/arch/arm/boot'
output = root / ('artifacts-usb-adb' if variant == 'usb-adb' else 'artifacts')
output.mkdir(exist_ok=True)
assert not output.is_symlink(), 'Refuse a symlink output directory'
image = output / ('zero2w-kitkat-4.4.4-usb-adb-experimental.img' if variant == 'usb-adb' else 'zero2w-kitkat-4.4.4-experimental.img')
assert not image.exists(), 'Refuse to overwrite an existing image'
required = {
    'kernel7.img': kernel / 'zImage',
    'bcm2710-rpi-zero-2-w.dtb': kernel / 'dts/bcm2710-rpi-zero-2-w.dtb',
    'ramdisk.img': product / 'ramdisk.img',
}
for name, path in required.items():
    if not path.is_file():
        raise SystemExit('Missing artifact: ' + str(path))
assert required['kernel7.img'].read_bytes()[0x24:0x28] == bytes.fromhex('18286f01')
assert required['bcm2710-rpi-zero-2-w.dtb'].read_bytes()[:4] == bytes.fromhex('d00dfeed')
assert required['ramdisk.img'].read_bytes()[:2] == b'\x1f\x8b'
for name, path in required.items():
    shutil.copy2(path, boot / name)
(boot / 'overlays').mkdir(exist_ok=True)
for name in ('dwc2.dtbo', 'disable-bt.dtbo'):
    source = kernel / 'dts/overlays' / name
    if not source.is_file():
        raise SystemExit('Missing overlay: ' + str(source))
    shutil.copy2(source, boot / 'overlays' / name)
for name in ('bootcode.bin', 'start.elf', 'fixup.dat', 'LICENCE.broadcom', 'config.txt', 'cmdline.txt'):
    assert (boot / name).is_file(), name

fat = output / 'boot-fat.img'
assert not fat.exists(), 'Refuse to overwrite existing FAT staging file'
with fat.open('xb') as stream:
    stream.truncate(64 * 1024 * 1024)
subprocess.run(['mkfs.vfat', '-F', '32', '-n', 'KITKATBOOT', str(fat)], check=True)
for path in sorted(boot.iterdir()):
    subprocess.run(['mcopy', '-s', '-i', str(fat), str(path), '::/'], check=True)

# MBR: 64 MiB boot, 768 MiB system, 1024 MiB data, 128 MiB cache.
partitions = [(fat, 64, 0x0c), (product / 'system.img', 768, 0x83),
              (product / 'userdata.img', 1024, 0x83), (product / 'cache.img', 128, 0x83)]
sector = 2048
mbr = bytearray(512)
offsets = []
for index, (path, mib, kind) in enumerate(partitions):
    length = mib * 2048
    assert path.is_file() and path.stat().st_size <= length * 512, str(path)
    if kind == 0x83:
        with path.open('rb') as stream:
            stream.seek(1080)
            assert stream.read(2) == b'\x53\xef', 'Expected raw ext4: ' + str(path)
    mbr[446 + 16 * index:462 + 16 * index] = struct.pack(
        '<B3sB3sII', 0x80 if index == 0 else 0, b'\xfe\xff\xff', kind,
        b'\xfe\xff\xff', sector, length)
    offsets.append(sector * 512)
    sector += length
mbr[510:512] = b'\x55\xaa'
with image.open('xb') as dest:
    dest.truncate(sector * 512)
    dest.seek(0)
    dest.write(mbr)
    for offset, (path, _, _) in zip(offsets, partitions):
        dest.seek(offset)
        with path.open('rb') as source:
            shutil.copyfileobj(source, dest, 1024 * 1024)
digest = hashlib.sha256()
with image.open('rb') as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        digest.update(chunk)
(output / (image.name + '.sha256')).write_text(digest.hexdigest() + '  ' + image.name + '\n')
(output / 'status.json').write_text(json.dumps({
    'status': 'experimental-unbooted',
    'android': 'android-4.4.4_r2',
    'board': 'Raspberry Pi Zero 2 W',
    'partitions': ['boot', 'system', 'data', 'cache'],
    'hardware_tested': False,
    'variant': variant,
}, indent=2) + '\n')
compressed = image.with_suffix(image.suffix + '.gz')
with image.open('rb') as source, compressed.open('xb') as raw:
    with gzip.GzipFile(filename='', mode='wb', fileobj=raw, compresslevel=1, mtime=0) as dest:
        shutil.copyfileobj(source, dest, 1024 * 1024)
digest = hashlib.sha256()
with compressed.open('rb') as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        digest.update(chunk)
(output / (compressed.name + '.sha256')).write_text(digest.hexdigest() + '  ' + compressed.name + '\n')
print('Created experimental image. Hardware boot, HDMI and USB are UNVERIFIED:', image)
