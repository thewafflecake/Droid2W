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

- Battery/power-supply reporting is not implemented for this externally powered board.
- Some legacy Android network/vendor commands remain unsupported.
- The current firmware set lacks regulatory.db; some channels may be unavailable.
- Old Android lowmemorykiller is absent from this kernel; low-RAM properties
  alone do not establish correct behavior under memory pressure.
- Audio, Bluetooth, camera and cellular integration remain untested.
- 320×480 is a logical display override, not a physical HDMI mode.
- SELinux is permissive in the development boot command line.
- Performance, power consumption and clean-image reproducibility need measurement.
