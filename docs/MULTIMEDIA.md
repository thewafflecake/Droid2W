# Multimedia development, 2026-11-04

These are results from an incrementally updated development card, not a claim
about the existing downloadable release or a freshly flashed image.

## HDMI audio

The kernel builds `SND`, `SND_TIMER`, `SND_PCM` and `SND_BCM2835` into the image.
Boot profiles enable `dtparam=audio=on`. `prepare-audio.py` derives a small
output-only HAL from the Apache-licensed AOSP template. AudioFlinger mixes at
48 kHz, stereo, PCM16; tinyalsa writes to card 0/device 0 by default.

A quiet two-second test was audible both with tinyplay and the stock Music
application. The tester confirmed both signals. AudioFlinger used the new HAL
again after reboot. Microphone capture, HDMI hotplug and Bluetooth audio routing
are not validated. Bluetooth discovery does not imply A2DP audio support.

An I2S DAC/amplifier is needed for GPIO-connected speakers. No such module is
available on the test board. No GPIO speaker support is claimed. Future ALSA
cards can be selected with `persist.zero2w.audio.card` and
`persist.zero2w.audio.device`; their kernel driver, overlay and electrical
connections still need module-specific work.

## Bluetooth

The tested board's controller identifies as BCM43430A1. Android's Broadcom UART
vendor library uses `/dev/ttyAMA0`, hardware flow control and 921600 baud. The
initial 115200-baud configuration exceeded KitKat's three-second preload timeout
while downloading firmware. GPIO 42 controls controller power, exported by root
init and then writable only by the Bluetooth account. The serial console is
removed from this UART. `krnbt=off` leaves transport ownership with Android.

Firmware comes from RPi-Distro/bluez-firmware commit
`cdf61dc691a49ff01a124752bd04194907f0f9cd`; preparation retains its copyright and
revision files. The local chip-name parsing loop is bounded correctly before
looking up the firmware file.

Verified: firmware download, Android adapter ON state, automatic startup after
reboot, and discovery of the tester's OnePlus 10 Pro. Pairing, file transfer,
Bluetooth HID, BLE and A2DP have not been tested. Other controller variants need
their own identification and firmware validation.

## GPU experiment

The default system renderer remains software GLES 1.x. In a separate development
experiment, the old Broadcom userspace driver initialized VideoCore IV hardware,
created an OpenGL ES 2.0 context, and passed pbuffer clear/readback and shader
triangle tests, including a complete 480x320 readback.

A prototype copies GPU pbuffer pixels into an Android BufferQueue with the
existing gralloc allocator. A red/blue test appeared with the correct orientation
and colors in an Android window and its screenshot. Sixty simple clear/copy
frames ran at about 4.8 frames/s. This is a test of that path, not a game benchmark.
Readback and software composition remain expensive; zero-copy integration is
not implemented. The prototype is not enabled in the standard image.

The owner's Minecraft PE 0.14.0 APK loads its ARMv7 native libraries. With the
software driver it aborts when it cannot create a GLES 2 surface. With the
experimental driver it loads the GPU library and creates a window surface.
The app requests an RGB565 native buffer; the first bridge accepted only
RGBA8888 and discarded these frames. The prototype now converts GPU RGBA pixels
to the requested RGB565 buffer and queues frames successfully. Both full-frame
and row-by-row readback were observed advancing. This corrected an output
format mismatch, not game rendering: the current result is a solid green frame,
without the Minecraft menu. A playable game and gameplay FPS have not been
demonstrated. The APK is not distributed with Droid2W.

A warm reboot following the GPU tests stopped at a black HDMI screen and lost
network connectivity; recovery and repeatability remain under investigation.
The GPU prototype stays outside the standard image. Increasing `gpu_mem` from
64 to 128 did not resolve the rendering issue. Returning to 64 was followed by
a failed boot; causation is not established. Recovery is being tested with the
previous 128 MiB configuration and a forced software-driver alias before Android
services start. The diagnostic source patch is retained in
`experimental/gpu-readback/`; it is a developer checkpoint, not a supported driver.

## Camera

No camera is connected. Android still uses its camera stub; no working camera
HAL or camera hardware feature is advertised. Kernel MMAL/Unicam options alone
do not provide an Android camera implementation. Sensor choice, driver/firmware
compatibility and a real capture test are prerequisites for claiming support.
