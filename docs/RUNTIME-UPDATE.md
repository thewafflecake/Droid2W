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
compatibility workaround; incomplete UI/navigation drawing was still visible
in some captured frames and is not considered resolved. It is not evidence of
a frame-rate improvement. ADB key authentication remains
enabled. Do not infer that a successful build has resolved every hardware issue.
