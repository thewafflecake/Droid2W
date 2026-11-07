# Legacy GPU readback checkpoint

This prototype is **not part of the default build or alpha.2 image**. It is not
ready for general use. Do not select it globally for SurfaceFlinger: Android
native-buffer/EGLImage integration is incomplete. Testing can leave the board
unresponsive after reboot if a global alias still selects it. A persistent alias
caused a black-screen boot during development; recovery has since been verified.
Keep a working boot card and physical access.

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

Selected glmark2 scenes have since passed this isolated path; see
[the measurements and test setup](../../docs/GLMARK2.md). The generic wrapper is
`isolation/run-gpu-test.sh`. The app-only redirect includes a KitKat linker
workaround for glmark2's `RTLD_NODELETE` request. This does not enable the
prototype for the system UI.

A VideoCore IV GLES 2 context passed clear/readback and shader triangle tests.
The native-window red/blue test displayed correctly; its simple clear/copy loop
ran around 4.8 frames/s. That number is not a gameplay measurement.

Minecraft PE 0.14.0 requests an RGB565 window. Accepting that buffer fixed the
previous rejection of every frame. Full-frame readback and frame queueing now
advance, but the observed screen is a solid green fill with no game menu.
A playable game has not been demonstrated. Increasing GPU memory to 128 MiB
provided no improvement. See `../../docs/MULTIMEDIA.md` for hardware-test scope.

## Isolated app-process launch checkpoint

`isolation/` contains the small redirect library and app wrapper tested on this
KitKat build. The wrapper preloads the redirect only into the application
process. It redirects `dlopen("/system/lib/egl/libGLES.so", ...)` to a private
prototype library when the test environment variable is set and the process is
an app UID. It never changes a system symlink or the system-wide renderer.
Bionic's special libdl lookup on this release requires `RTLD_DEFAULT`; this is
not a portable interceptor for arbitrary Android releases.

For a separate development tree, copy `isolation/` to
`device/experimental/zero2w/gpu-isolation/` and, after the usual environment setup,
run:

```sh
make -j1 ONE_SHOT_MAKEFILE=device/experimental/zero2w/gpu-isolation/Android.mk \
  libd2w_egl_redirect
```

Keep both the redirect and prototype out of the standard system staging directory
when building a distributable image. For the tested runtime layout, the private
files under `/data/local/tmp/zero2w-multimedia/` are:

- `libd2w_egl_redirect.so`: the redirect library.
- `libGLES_app_test.so`: the separately built readback prototype.
- `run-minecraft-gpu-isolated.sh`: the supplied wrapper, executable with LF endings.

The legacy prototype also needs its matching `libvc4.so`. Testing used a private
development installation where that dependency was already available. These
instructions do not install it or provide a complete automatic deployment.

On the test card, root temporarily set `wrap.com.mojang.minecraftpe` to the
wrapper path for one app launch. The property was cleared immediately after
launch, with cleanup in a host-side `finally` block. The software EGL alias and
SurfaceFlinger renderer were checked before and after. Do not leave the wrapper
property set, overwrite libraries while the app is running, or place a prototype
in a global EGL search directory. A reboot clears this nonpersistent wrapper
property but is not a substitute for cleanup.

The native probe passed this isolated path. Minecraft's shaders compiled and
linked successfully, but its menu still did not render. Screen capture could
return empty output while the app was active. This isolation checkpoint improves
test recovery; it does not make Minecraft playable or finish the GPU port.
