#!/usr/bin/env python3
"""Stage the tracked device tree and the builder's public ADB key only."""
from pathlib import Path
import argparse, shutil

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--adb-public-key', type=Path, required=True)
args = parser.parse_args()
key = args.adb_public_key.read_text().strip()
if not key or 'PRIVATE KEY' in key or not args.adb_public_key.name.endswith('.pub'):
    raise SystemExit('Supply your adbkey.pub public key, never a private key.')
if not (root / 'aosp/build/core/main.mk').is_file():
    raise SystemExit('Sync AOSP first; see docs/BUILD.md.')
target = root / 'aosp/device/experimental/zero2w'
shutil.copytree(root / 'device/experimental/zero2w', target, dirs_exist_ok=True)
(target / 'adb_keys').write_text(key + '\n')
research = root / 'research'
research.mkdir(exist_ok=True)
for name in ('logger-3.16.c', 'logger-3.16.h'):
    shutil.copyfile(root / 'third_party/logger' / name, research / name)
print('Staged device configuration and public ADB key.')
