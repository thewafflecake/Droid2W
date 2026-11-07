# Isolated glmark2 hardware tests

Tested on the development Zero 2 W card on 2026-11-05 and 2026-11-08,
Android 4.4.4, 64 MiB GPU memory. The alpha.2 release image is unchanged:
it contains neither glmark2 nor the experimental GPU bridge.

## Setup and scope

The user supplied glmark2 2023.01 (version code 2). Its original package is
retained. A locally signed test copy uses a separate package and process name
so that KitKat's temporary `wrap.*` property can isolate the GPU driver.
The original process suffix contains a colon, which this build rejects in
property names. Native libraries and assets were retained byte for byte;
only package/process manifest strings and signatures changed. Neither APK nor
the local signing key is distributed here.

The preload redirects EGL loading only in the selected app. It also strips
`RTLD_NODELETE` (0x1000), which glmark2 requests but KitKat's linker rejects.
This workaround is confined to the opted-in test process and does not provide
the unloading semantics of that flag. Sources are in
[`experimental/gpu-readback/isolation/`](../experimental/gpu-readback/isolation/).

Logs report Broadcom / VideoCore IV HW / OpenGL ES 2.0. Although glmark2 prints
an initial 100x100 placeholder before the Android resize callback, subsequent
viewport and readback diagnostics show **320x432** rendering. The logical screen
is 320x480; the navigation bar occupies the remaining height. The selected EGL
configuration uses RGB565 and depth16.

## Measurements

These are short selected-scene checks, **not a full default glmark2 score**.
Results include GPU rendering, synchronous CPU readback/copy and software
system composition. They are not the GPU's standalone throughput.

| Date | Scene | Duration | FPS | Frame time |
| --- | --- | ---: | ---: | ---: |
| Nov 5 | build, VBO off | 3 s | 20 | 50.000 ms |
| Nov 5 | build, VBO on | 3 s | 20 | 50.000 ms |
| Nov 5 | texture, nearest | 3 s | 20 | 50.000 ms |
| Nov 5 | texture, linear | 3 s | 20 | 50.000 ms |
| Nov 5 | texture, mipmap | 3 s | 20 | 50.000 ms |
| Nov 5 | shading, Gouraud | 3 s | 20 | 50.000 ms |
| Nov 5 | shading, Phong | 3 s | 21 | 47.619 ms |
| Nov 8 | build, VBO on | 10 s | 15 | 66.667 ms |
| Nov 8 | shading, Phong | 10 s | 18 | 55.556 ms |
| Nov 8 | bump, high-poly | 5 s | 20 | 50.000 ms |
| Nov 8 | bump, normals | 5 s | 20 | 50.000 ms |
| Nov 8 | bump, height | 5 s | 20 | 50.000 ms |
| Nov 8 | shading, cel | 5 s | 20 | 50.000 ms |
| Nov 8 | pulsar, 5 quads, no texture/light | 5 s | 20 | 50.000 ms |
| Nov 8 | desktop, 4 windows, shadow | 5 s | 20 | 50.000 ms |

All three Nov 8 suites reached their completion marker without a fatal signal
or Java fatal exception in the captured main log. Their selected-suite scores
were 16 (repeat), 20 (bump) and 20 (effects). The full default suite, terrain,
refract, long stress testing and exhaustive visual validation remain untested.

A framebuffer capture during the texture tests shows a textured 3D cube.
Raw framebuffer capture is not synchronized with presentation and may tear;
it is not a validation of every frame or of every later scene. Ordinary
`screencap` sometimes returns an empty file while the experimental app runs.

The wrapper property is cleared after launch. Each suite ends by force-stopping
the test process, returning Home, and verifying the unchanged software EGL alias
and PixelFlinger SurfaceFlinger renderer. No global driver switch is needed.
Minecraft is removed and was not tested in this session.

## Remaining work

This demonstrates selected GLES 2 scenes through the prototype. It does not
complete native-buffer/EGLImage integration, zero-copy presentation, resize
handling, general application compatibility or system-wide GPU acceleration.
No gameplay performance is inferred from these results. The difference between
the short and longer runs also precludes treating 20 FPS as a stable maximum.

Upstream references: [default scenes](https://github.com/glmark2/glmark2/blob/2023.01/src/default-benchmarks.h),
[Android frontend](https://github.com/glmark2/glmark2/blob/2023.01/src/canvas-android.cpp),
[library loading](https://github.com/glmark2/glmark2/blob/2023.01/src/shared-library.cpp).
