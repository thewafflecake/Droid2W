# Basic apps and runtime update

The update was installed on the development board on 2026-11-02. Android
completed boot after correcting the emulated-storage environment and FUSE
layout. A subsequent reboot with the normal ramdisk also completed, and
authenticated Wi-Fi ADB reconnected on the development card's port 5556.
The temporary offline installer and diagnostic server are absent from that
normal ramdisk. A clean full image remains untested.

Browser rendered a local HTML page, Gallery indexed the test JPEG, Calculator
computed 2+2, and Calendar, Clock, Music and Downloads opened. Settings' device
status screen was also checked after moving it out of the phone process.
These checks do not establish audio playback or modern website compatibility.

## Added applications

- Browser
- Legacy Gallery
- Calculator
- DeskClock
- Calendar and CalendarProvider
- Music
- DocumentsUI file picker and ExternalStorageProvider
- Downloads UI and the existing DownloadProvider
- Certificate installer and KeyChain

Only the applications and their required framework components are included;
Google applications and services are not added. Music playback still requires
audio hardware bring-up, and modern website compatibility is constrained by
KitKat's old WebView and certificate store.

## Device adaptations

- Full CPU-window redraw opt-in to investigate disappearing navigation/UI content.
- Wi-Fi-only network/radio resource configuration and a guarded Settings status screen.
- Complete emulated-storage environment, legacy aliases and multiuser FUSE
  layout, following the KitKat mini-emulator configuration.
- External-power healthd implementation, with no physical battery measurement.
- Wall-clock setting fallback for kernels without `/dev/alarm`.
- Skip USB gadget initialization in ADB when the device tree selects USB host.
- Include the small stock UI sound assets expected by the framework.

This update does not add graphics acceleration. The full-redraw change is a
compatibility workaround, not evidence of a frame-rate improvement. ADB key
authentication remains enabled.

## Framebuffer capture and compact lock screen

The development card was updated and rebooted on 2026-11-03 with these changes:

- `framebuffer_swap=0` aligns the firmware framebuffer channels with generic
  gralloc's RGBX output. The hardware tester confirmed matching HDMI colors.
- The opt-in gralloc path uses `FBIOPAN_DISPLAY`; the kernel changes only the
  firmware scanout offset rather than reconfiguring the mode for every frame.
  Gralloc also waits for vertical synchronization after a page flip.
- On this device, `screencap` snapshots the active framebuffer page into owned
  memory before PNG encoding, using the actual row stride and checking that
  the page offset remains unchanged during the copy. This avoids the unsupported
  PixelFlinger FBO capture and encoding directly from a reused display buffer.
  RGBX screenshots are marked opaque.
- A portrait Keyguard overlay reduces the unlock challenge height and clock
  font size to leave enough room for the clock and date at 320x480. Previously,
  the status widget was clipped to approximately 29 logical pixels in height.

In the rapid relative-mouse-motion reproduction, seven of ten baseline captures
had incomplete navigation icons. Both the temporary patched capture binary and
the installed version after reboot produced ten of ten complete navigation
regions. The clock and date are visible in the post-update capture, and no
framebuffer ioctl errors were observed in the inspected post-boot log.
The hardware tester also confirmed that the clock is visible and the reported
HDMI flickering no longer occurs when moving the mouse. This covers the reported
reproduction on one board, not every application or workload. A clean rebuilt
image remains untested.
