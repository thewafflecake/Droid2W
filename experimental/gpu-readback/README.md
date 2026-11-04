# Legacy GPU readback checkpoint

This prototype is **not part of the default build or alpha.2 image**. It is not
ready for general use. Do not select it globally for SurfaceFlinger: Android
native-buffer/EGLImage integration is incomplete. Testing can leave the board
unresponsive to a warm reboot. Keep a working boot card and physical access.

## Sources and build

The patch applies inside `trevd/android_vendor_broadcom_rpi` at commit
`3529fe83bfce73d5a6a6ddd2fdd267a702e7a80f`. Retain the upstream license files.
Header dependencies were taken from `trevd/android_hardware_broadcom_bcm2708`
at `90fe9b4def9356820f56cf1d00d259355ce1ed6c`.

In a separate KitKat development tree, stage upstream `opengl/` and
`BoardConfigVendor.mk` under `vendor/broadcom/rpi/`, and the hardware header tree
under `hardware/broadcom/bcm2708/`. Apply `gpu-readback.patch` in the vendor
source directory with `patch -p1`. Use this opt-in vendor `Android.mk`:

```make
ifeq ($(DROID2W_BUILD_LEGACY_GPU),true)
include vendor/broadcom/rpi/BoardConfigVendor.mk
include vendor/broadcom/rpi/opengl/Android.mk
endif
```

After the usual Java 6 environment setup and `lunch zero2w-userdebug`, build:

```sh
make -j1 DROID2W_BUILD_LEGACY_GPU=true \
  ONE_SHOT_MAKEFILE=vendor/broadcom/rpi/Android.mk libGLES_bcm2708
```

This installs experimental libraries into Android's **build output staging**.
It does not safely switch an installed system. Keep these libraries out of a
standard image; the public image verifier rejects a stale legacy GPU driver.
The default renderer must remain the software driver while testing individual
applications. No automatic installer or global driver-selection change is
provided here.

## What the patch does

- Builds the old GLES driver against KitKat headers, with local symbol binding
  and libsync for BufferQueue fences.
- Creates a GPU pbuffer behind the Android window surface.
- Reads GPU pixels, flips rows and copies into the native window buffer.
- Handles RGBA8888 and RGB565 output buffers, including Minecraft's RGB565 request.
- Logs a frame summary every 60 successfully prepared frames for diagnosis.

It is a CPU-copy bridge, not zero-copy graphics. Window resizing, complete EGL
attribute validation, imported Android native buffers and broad app compatibility
remain unfinished.

## Observations

A VideoCore IV GLES 2 context passed clear/readback and shader triangle tests.
The native-window red/blue test displayed correctly; its simple clear/copy loop
ran around 4.8 frames/s. That number is not a gameplay measurement.

Minecraft PE 0.14.0 requests an RGB565 window. Accepting that buffer fixed the
previous rejection of every frame. Full-frame readback and frame queueing now
advance, but the observed screen is a solid green fill with no game menu.
A playable game has not been demonstrated. Increasing GPU memory to 128 MiB
provided no improvement. See `../../docs/MULTIMEDIA.md` for hardware-test scope.
