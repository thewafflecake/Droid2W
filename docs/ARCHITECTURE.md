# Architecture

- Android: AOSP `android-4.4.4_r2` / KTU84Q; exact project revisions are
  recorded in `manifests/android-source-lock.xml`.
- Kernel: raspberrypi/linux `rpi-5.10.y`, commit
  `8e1110a580887f4b82303b9354c25d7e2ff5860e` (5.10.110-v7).
- Boot firmware: raspberrypi/firmware revision
  `61966732d03de9b71baf561f920e018b54c241ac`.
- Wi-Fi firmware: RPi-Distro/firmware-nonfree revision
  `c91cd2804cf7463aab913e7247c176049f16bbd6`.

Kernel preparation enables the 32-bit Binder protocol 7 ABI, adapts the legacy
Android logger to Linux 5.10 write_iter and applies Android common's
CAP_SYS_NICE check for cgroup v1 task placement. The logger adapter retains
upstream GPLv2 notices. The cgroup check follows Android common commit
`9cb202cb0d18596a8ca46b80e86a1a47d82b2ae4`.

The device uses software GLES with a `libGLES.so` alias for KitKat's loader.
Hardware HWUI is disabled. No GPU acceleration claim is made. The original
Linux framebuffer console is unbound after boot to avoid overwriting Android.

Wi-Fi uses cfg80211/brcmfmac, a small nl80211 driver command library and the
KitKat wpa_supplicant. Android commands go to a global control socket; the
per-interface socket lives in a separate directory. DHCP uses KitKat dhcpcd.

## Known limitations

- The healthd board hook describes external power with no battery present. Its
  level value of 100 is a framework compatibility placeholder, not a measurement.
  Actual battery hardware will require a different power-supply integration.
- Some legacy Android network/vendor commands remain unsupported.
- The current firmware set lacks regulatory.db; some channels may be unavailable.
- Old Android lowmemorykiller is absent from this kernel; low-RAM properties
  alone do not establish correct behavior under memory pressure.
- Audio, Bluetooth, camera and cellular integration remain untested.
- 320×480 is a logical display override, not a physical HDMI mode.
- SELinux is permissive in the development boot command line.
- Performance, power consumption and clean-image reproducibility need measurement.

## Runtime adaptation

`prepare-runtime.py` applies device compatibility changes to the pinned AOSP tree:

- Opt-in complete damage for CPU-drawn windows through
  `debug.sf.zero2w_full_redraw=1`. Canvas receives a full-window dirty rectangle,
  avoiding dependence on buffer copyback history. This is a compatibility
  workaround under evaluation, not a claimed GPU or frame-rate improvement.
- Wi-Fi-only Settings skips PhoneFactory access in the device status screen
  and runs that activity in the Settings process, avoiding the absent phone
  package's radio-process permissions.
- If `/dev/alarm` is absent, SystemClock falls back to `settimeofday` for wall
  clock changes. The kernel still requires CAP_SYS_TIME. Alarm delivery continues
  to use KitKat's existing Java fallback; suspend/wakeup alarms are not validated.
- ADB checks the device-tree USB role and avoids initializing the FunctionFS
  gadget transport when the controller is in host mode. TCP transport and key
  authentication remain unchanged; peripheral mode continues to support USB ADB.

The storage overlay declares emulated storage. Init exports both
`EMULATED_STORAGE_SOURCE=/mnt/shell/emulated` and
`EMULATED_STORAGE_TARGET=/storage/emulated`; sdcard uses `-l` to export
`/data/media` with user IDs at the top level. Legacy paths point to user 0.
Omitting the environment while declaring storage emulated makes Zygote's
application forks abort, leaving Android stuck during startup.

Basic application selection includes legacy Gallery, Browser, Calculator,
DeskClock, Calendar, Music, DocumentsUI and Downloads, with their providers.
The legacy Gallery avoids Gallery2's more demanding graphics path. Camera and
audio playback functionality do not follow merely from installing these apps.
