# Flash the experimental image

Download the `.img.gz` asset and its `.sha256` checksum from the matching
[GitHub release](https://github.com/thewafflecake/Droid2W/releases).
The separately downloadable kernel source archive is for development; it is
not an SD-card image.

1. Use a microSD card of **4 GB or larger**. Flashing erases its contents.
2. Verify the SHA-256 of the downloaded compressed image. In PowerShell,
   `Get-FileHash <image.img.gz> -Algorithm SHA256` should match the checksum file.
3. Decompress `.img.gz` to `.img`. In Raspberry Pi Imager select **Use custom**
   and choose that `.img`, then select the intended microSD and write it.
4. Skip Raspberry Pi OS customization. Wi-Fi and Android settings are configured
   on the device after boot.
5. The public image defaults to USB host. Disconnect the PC data cable, power
   through **PWR IN**, and attach keyboard/mouse through USB OTG. Connect HDMI.
6. Allow Android to prepare its apps on the first boot. Configure Wi-Fi through
   Android Settings. For network ADB, run `adb connect <board-ip>:5556` and approve
   the computer's key on the device screen.

No Wi-Fi password, personal data or preauthorized computer keys are included.
The Android display is 320x480 at 160 dpi, centered within 1280x720 HDMI output.
The data partition is fixed at 1 GiB; larger cards do not expand it automatically.

For USB ADB instead of USB keyboard/mouse, power down and copy
`config-usb-adb.txt` over `config.txt` on the FAT boot partition. Disconnect input
devices before connecting the board's USB data port to the computer. USB host
and USB peripheral modes use the same controller and cannot run simultaneously.

The image is a legacy development prerelease with software graphics and
permissive SELinux. Audio, Bluetooth, camera and cellular modem are not brought
up. See each release's notes for whether that exact fresh image has been booted
on hardware; successful file checks alone do not demonstrate a successful boot.
