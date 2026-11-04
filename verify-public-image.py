#!/usr/bin/env python3
"""Read-only checks of a freshly packaged public development image."""
import argparse
import gzip
from pathlib import Path
import struct
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent
product = root / 'aosp/out/target/product/zero2w'
images = list(args.directory.glob('*.img'))
images = [p for p in images if p.name != 'boot-fat.img']
assert len(images) == 1, images
image = images[0]
with image.open('rb') as f:
    mbr = f.read(512)
    assert mbr[510:] == b'\x55\xaa'
    expected = [args.directory / 'boot-fat.img'] + [product / (s + '.img') for s in ('system', 'userdata', 'cache')]
    for i, source in enumerate(expected):
        entry = mbr[446 + i * 16:462 + i * 16]
        _, _, kind, _, start, sectors = struct.unpack('<B3sB3sII', entry)
        assert kind == (0x0c if i == 0 else 0x83)
        assert start > 0 and source.stat().st_size <= sectors * 512
        f.seek(start * 512)
        with source.open('rb') as src:
            while True:
                data = src.read(1024 * 1024)
                if not data:
                    break
                assert f.read(len(data)) == data, source
    assert image.stat().st_size == (start + sectors) * 512

def boot_file(name):
    return subprocess.check_output(['mtype', '-i', str(args.directory / 'boot-fat.img'), '::/' + name])

config = boot_file('config.txt').decode()
for value in ('framebuffer_swap=0', 'dtoverlay=dwc2,dr_mode=host', 'dtparam=audio=on', 'dtparam=krnbt=off'):
    assert value in config, value
assert 'console=ttyAMA0' not in boot_file('cmdline.txt').decode(), 'UART is reserved for Bluetooth'
for name, source in [('kernel7.img', root / 'kernel-out/arch/arm/boot/zImage'),
                     ('ramdisk.img', product / 'ramdisk.img')]:
    assert boot_file(name) == source.read_bytes(), name

archive = gzip.decompress(boot_file('ramdisk.img'))
files = {}
pos = 0
while pos < len(archive):
    assert archive[pos:pos + 6] in (b'070701', b'070702')
    fields = [int(archive[pos + 6 + i * 8:pos + 14 + i * 8], 16) for i in range(13)]
    mode, uid, gid, size, namesize = fields[1], fields[2], fields[3], fields[6], fields[11]
    name = archive[pos + 110:pos + 110 + namesize - 1].decode()
    pos = (pos + 110 + namesize + 3) & ~3
    data = archive[pos:pos + size]
    pos = (pos + size + 3) & ~3
    if name == 'TRAILER!!!':
        break
    files[name.removeprefix('./')] = (mode, uid, gid, data)
for name in ('init.rc', 'init.zero2w.rc', 'init.zero2w.usb.rc'):
    mode, uid, gid, data = files[name]
    assert uid == 0 and not mode & 0o022, (name, oct(mode), uid, gid)
assert not files['adb_keys'][3].strip(), 'Preauthorized ADB key in public ramdisk'
assert b'ro.adb.secure=1' in files['default.prop'][3]
assert b'EMULATED_STORAGE_SOURCE /mnt/shell/emulated' in files['init.zero2w.rc'][3]
assert b'chown bluetooth bluetooth /sys/class/gpio/gpio42/value' in files['init.zero2w.rc'][3]
assert b'/dev/snd/* 0660 system audio' in files['ueventd.zero2w.rc'][3]
assert not any('droid2w-update' in name or 'diagnostic' in name for name in files)

def system_file(name):
    return subprocess.check_output(['debugfs', '-R', 'cat /' + name, str(product / 'system.img')], stderr=subprocess.DEVNULL)

prop = system_file('build.prop').decode()
for value in ('ro.config.size_override=320,480', 'service.adb.tcp.port=5556', 'debug.gralloc.zero2w_pan=1'):
    assert value in prop, value
for name in ('bin/screencap', 'lib/hw/gralloc.default.so', 'priv-app/Keyguard.apk',
             'lib/hw/audio.primary.zero2w.so', 'lib/libtinyalsa.so', 'etc/audio_policy.conf',
             'app/Bluetooth.apk', 'lib/hw/bluetooth.default.so', 'vendor/lib/libbt-vendor.so',
             'etc/permissions/android.hardware.bluetooth.xml', 'etc/firmware/brcm/BCM43430A1.hcd'):
    assert system_file(name) == (product / 'system' / name).read_bytes(), name
print('PASS: partition contents, boot profile, ramdisk permissions, ADB authentication, display defaults and updated graphics/Keyguard files')
print('Fresh image boot on hardware remains unverified.')
