#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Raspberry Pi firmware release 1.20220331, pinned for reproducibility.
revision=61966732d03de9b71baf561f920e018b54c241ac
mkdir -p boot
for file in bootcode.bin start.elf fixup.dat LICENCE.broadcom; do
    curl --fail --location --silent --show-error \
        "https://raw.githubusercontent.com/raspberrypi/firmware/$revision/boot/$file" \
        -o "boot/$file"
done
printf '%s\n' "$revision" > boot/firmware-revision.txt
(cd boot && sha256sum bootcode.bin start.elf fixup.dat LICENCE.broadcom > firmware-sha256.txt)
