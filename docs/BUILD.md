# Build guide: development baseline

Run from the repository root on an x86-64 Linux build host. Full AOSP sources
and build outputs consume many tens of GB; allow substantial free space.
The development host used two CPU cores, 4 GB RAM and swap. Android was built
with one job, the kernel with two. Build times are not guaranteed.

## Environments

Kernel/preparation tools: Python 3.9+, git, curl, make, an ARM hard-float cross
compiler (`arm-linux-gnueabihf-`), kernel build dependencies, mtools and dosfstools.
Kernel development used GCC 14. Android needs a separate legacy environment:
Ubuntu 14.04, OpenJDK 6, GCC 4.8, Python 2.7 and make 3.81. Keep the obsolete
Android toolchain isolated; the original development used an LXD container
with the repository mounted at `/work`.

## Sources

Install the Android `repo` tool using the official AOSP instructions, then:

```sh
mkdir -p aosp
cd aosp
repo init -u https://android.googlesource.com/platform/manifest -b android-4.4.4_r2
cp ../manifests/android-source-lock.xml .repo/manifests/droid2w-lock.xml
repo init -m droid2w-lock.xml
repo sync -j2
cd ..
git clone --branch rpi-5.10.y https://github.com/raspberrypi/linux.git kernel
git -C kernel checkout 8e1110a580887f4b82303b9354c25d7e2ff5860e
mkdir -p research
git clone https://github.com/RPi-Distro/firmware-nonfree.git research/rpi-wifi-firmware
git -C research/rpi-wifi-firmware checkout c91cd2804cf7463aab913e7247c176049f16bbd6
git clone https://github.com/RPi-Distro/bluez-firmware.git research/rpi-bluez-firmware
git -C research/rpi-bluez-firmware checkout cdf61dc691a49ff01a124752bd04194907f0f9cd
```

Generate your own ADB key using Android Platform Tools if needed. Only the
public `adbkey.pub` is staged in the device image; never upload either key here.

```sh
python3 prepare-device.py --adb-public-key "$HOME/.android/adbkey.pub"
python3 prepare-android.py
python3 prepare-runtime.py
python3 prepare-wifi-firmware.py
python3 prepare-audio.py
python3 prepare-bluetooth.py
bash fetch-boot-firmware.sh
bash build-network-kernel.sh
bash check-binder-abi.sh
```

The network kernel script also prepares the Binder/logger patches and stages
the three matching Wi-Fi modules. Do not mix modules from another kernel build.
For a distributable image, use `python3 prepare-device.py --no-authorized-keys`
instead of embedding a developer's public key. New ADB hosts then require
approval on the device; key authentication remains enabled.

## Android

Inside the legacy environment, with this repository mounted at `/work`:

```sh
bash /work/build-android.sh
```

The build script explicitly uses OpenJDK 6 and retains AOSP's Java 1.6 version
checks. A successful build should produce ramdisk, system, data and cache images
under `aosp/out/target/product/zero2w/`.

## Assemble an SD image file

On the Linux host:

```sh
python3 assemble-image.py --variant usb-host
```

The assembler writes a regular image file and checksums under `artifacts-usb-host/`;
it does not flash a device and refuses to overwrite an existing image. It needs
the boot firmware, kernel, device trees and Android images from previous steps.
The current partition layout needs a card larger than the resulting ~2.08 GB image.
Use a 4 GB or larger card. Image creation does not prove hardware compatibility.

The `usb-host` variant selects the host profile automatically. The `usb-adb`
variant selects the peripheral profile; `original` retains `boot/config.txt`.
You can also copy a profile's contents to `config.txt` on the card's boot partition.
Power down before rewiring. Disconnect the PC data cable for host mode; power
through PWR IN and attach input devices through OTG. To restore USB ADB use
`config-usb-adb.txt` as `config.txt`.

The device defaults now select a 320x480 logical display at 160 dpi. On a running
development board, the same settings were tested with:

```sh
adb shell wm size 320x480
adb shell wm density 160
```

Connect Wi-Fi through Android Settings. Authenticated TCP ADB listens on port
5556 for use alongside USB host input. Connect with `adb connect <board-ip>:5556`
and approve the computer's key on the device. Keep this legacy development image
on a trusted network.

## Incremental public image build on the configured server

Once the legacy container, sources, boot firmware and matching Wi-Fi modules
are prepared, run on the Linux host:

```sh
bash build-public-image.sh artifacts-public-YYYYMMDD > public-image-build.log 2>&1
python3 verify-public-image.py artifacts-public-YYYYMMDD
```

The script builds the kernel and Android images, selects USB host, omits
preauthorized ADB keys, checks the staged data and filesystems, and creates
`.img.gz` files with SHA-256 sums. It refuses to overwrite existing image files.
Before packaging, host `e2fsck` normalizes the legacy `make_ext4fs` inode-bitmap
padding in the generated partition files and a read-only check must pass.
`public-image-status.txt` records the current stage. View progress with
`tail -n 40 -f public-image-build.log`. Verification compares packaged partition
contents, checks boot-file permissions and confirms the updated graphics files.
It does not replace a boot test of the fresh image on hardware.

This guide captures the development workflow; clean-checkout reproducibility
and a freshly assembled image remain to be independently tested.
