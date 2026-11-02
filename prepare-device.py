#!/usr/bin/env python3
"""Stage the device tree with an optional preauthorized public ADB key."""
from pathlib import Path
import argparse, shutil

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
keys = parser.add_mutually_exclusive_group(required=True)
keys.add_argument('--adb-public-key', type=Path)
keys.add_argument('--no-authorized-keys', action='store_true',
                  help='Public image: require on-device approval for each new ADB host.')
args = parser.parse_args()
key = ''
if args.adb_public_key:
    key = args.adb_public_key.read_text().strip()
    if not key or 'PRIVATE KEY' in key or not args.adb_public_key.name.endswith('.pub'):
        raise SystemExit('Supply your adbkey.pub public key, never a private key.')
if not (root / 'aosp/build/core/main.mk').is_file():
    raise SystemExit('Sync AOSP first; see docs/BUILD.md.')
target = root / 'aosp/device/experimental/zero2w'
shutil.copytree(root / 'device/experimental/zero2w', target, dirs_exist_ok=True)
(target / 'adb_keys').write_text(key + '\n' if key else '')
research = root / 'research'
research.mkdir(exist_ok=True)
for name in ('logger-3.16.c', 'logger-3.16.h'):
    shutil.copyfile(root / 'third_party/logger' / name, research / name)
print('Staged device configuration; preauthorized ADB keys:', bool(key))
