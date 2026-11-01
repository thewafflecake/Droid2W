# Basic apps and runtime update

Build status: kernel unchanged; Android system image and updated ramdisk built
successfully. Hardware deployment and validation of this update are in progress.
The hardware status table in the main README describes the earlier baseline.

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
- Emulated storage configuration matching the existing FUSE service.
- External-power healthd implementation, with no physical battery measurement.
- Wall-clock setting fallback for kernels without `/dev/alarm`.
- Skip USB gadget initialization in ADB when the device tree selects USB host.
- Include the small stock UI sound assets expected by the framework.

This update does not add graphics acceleration. The full-redraw change is a
compatibility workaround and needs confirmation on the physical HDMI display;
it is not evidence of a frame-rate improvement. ADB key authentication remains
enabled. Do not infer that a successful build has resolved every hardware issue.
