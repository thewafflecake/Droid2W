#!/usr/bin/env python3
"""Apply device-opt-in runtime compatibility fixes to the pinned KitKat tree."""
from pathlib import Path

root = Path(__file__).resolve().parent / 'aosp'

# Pair with the framebuffer offset-only page-flip kernel adaptation.
framebuffer = root / 'hardware/libhardware/modules/gralloc/framebuffer.cpp'
text = framebuffer.read_text()
old_post = '        if (ioctl(m->framebuffer->fd, FBIOPUT_VSCREENINFO, &m->info) == -1) {'
new_post = '''        // Droid2W: mode-setting on every mouse frame disrupts scanout.
        char usePan[PROPERTY_VALUE_MAX];
        property_get("debug.gralloc.zero2w_pan", usePan, "0");
        const unsigned long request = usePan[0] == '1'
                ? FBIOPAN_DISPLAY : FBIOPUT_VSCREENINFO;
        if (ioctl(m->framebuffer->fd, request, &m->info) == -1) {'''
if old_post in text:
    assert text.count(old_post) == 1
    text = text.replace(old_post, new_post)
if '#include <cutils/properties.h>' not in text:
    text = '#include <cutils/properties.h>\n' + text
framebuffer.write_text(text)
assert new_post in framebuffer.read_text()

text = framebuffer.read_text()
old_current = '        m->currentBuffer = buffer;'
new_current = '''        // Droid2W: retire the previous scanout before its buffer is reused.
        if (usePan[0] == '1') {
            unsigned int crtc = 0;
            if (ioctl(m->framebuffer->fd, FBIO_WAITFORVSYNC, &crtc) == -1) {
                ALOGE("FBIO_WAITFORVSYNC failed: %s", strerror(errno));
                return -errno;
            }
        }
        m->currentBuffer = buffer;'''
if '// Droid2W: retire the previous scanout' not in text:
    assert text.count(old_current) == 1
    framebuffer.write_text(text.replace(old_current, new_current))

# PixelFlinger has no FBO capture. Snapshot the active framebuffer page before
# PNG encoding, rather than encoding directly from memory reused by scanout.
screencap = root / 'frameworks/base/cmds/screencap/screencap.cpp'
text = screencap.read_text()
capture_marker = '// Droid2W stable framebuffer capture.'
if capture_marker not in text:
    text = text.replace('#include <errno.h>', '#include <errno.h>\n#include <utils/Vector.h>\n#include <string.h>\n#include <cutils/properties.h>')
    helper = '''// Droid2W stable framebuffer capture.
static bool captureZero2wFramebuffer(Vector<uint8_t>& pixels,
        uint32_t* w, uint32_t* s, uint32_t* h, uint32_t* f) {
    int fb = open("/dev/graphics/fb0", O_RDONLY);
    if (fb < 0) return false;
    fb_var_screeninfo info;
    fb_fix_screeninfo fixed;
    uint32_t bytespp;
    if (ioctl(fb, FBIOGET_VSCREENINFO, &info) ||
            ioctl(fb, FBIOGET_FSCREENINFO, &fixed) ||
            vinfoToPixelFormat(info, &bytespp, f) != NO_ERROR ||
            fixed.line_length % bytespp || !fixed.smem_len) {
        close(fb);
        return false;
    }
    void* mapping = mmap(0, fixed.smem_len, PROT_READ, MAP_SHARED, fb, 0);
    if (mapping == MAP_FAILED) { close(fb); return false; }
    *w = info.xres;
    *h = info.yres;
    *s = fixed.line_length / bytespp;
    const size_t size = size_t(fixed.line_length) * *h;
    pixels.resize(size);
    bool success = false;
    for (int attempt = 0; attempt < 12; ++attempt) {
        unsigned int crtc = 0;
        if (ioctl(fb, FBIO_WAITFORVSYNC, &crtc) ||
                ioctl(fb, FBIOGET_VSCREENINFO, &info)) break;
        const size_t offset = size_t(info.yoffset) * fixed.line_length +
                size_t(info.xoffset) * bytespp;
        if (offset > fixed.smem_len || size > fixed.smem_len - offset) break;
        memcpy(pixels.editArray(), static_cast<const uint8_t*>(mapping) + offset, size);
        fb_var_screeninfo after;
        if (ioctl(fb, FBIOGET_VSCREENINFO, &after)) break;
        if (info.xoffset == after.xoffset && info.yoffset == after.yoffset) {
            success = true;
            break;
        }
    }
    munmap(mapping, fixed.smem_len);
    close(fb);
    return success;
}

'''
    text = text.replace('int main(int argc, char** argv)\n', helper + 'int main(int argc, char** argv)\n')
    anchor = '    ScreenshotClient screenshot;\n'
    text = text.replace(anchor, '''    Vector<uint8_t> stablePixels;
    char hardware[PROPERTY_VALUE_MAX];
    property_get("ro.hardware", hardware, "");
    const bool captureFramebuffer = !strcmp(hardware, "zero2w") &&
            displayId == ISurfaceComposer::eDisplayIdMain;
''' + anchor)
    anchor = '    if (display != NULL && screenshot.update(display) == NO_ERROR) {'
    assert text.count(anchor) == 1
    text = text.replace(anchor, '''    if (captureFramebuffer) {
        if (captureZero2wFramebuffer(stablePixels, &w, &s, &h, &f)) {
            base = stablePixels.array();
            size = stablePixels.size();
        }
    } else if (display != NULL && screenshot.update(display) == NO_ERROR) {''')
    text = text.replace('            b.setPixels((void*)base);', '''            b.setPixels((void*)base);
            if (f == PIXEL_FORMAT_RGBX_8888 || f == PIXEL_FORMAT_RGB_565)
                b.setAlphaType(kOpaque_SkAlphaType);''')
    screencap.write_text(text)

surface = root / 'frameworks/native/libs/gui/Surface.cpp'
text = surface.read_text()
marker = '// Droid2W CPU window redraw compatibility.'
if marker not in text:
    anchor = '        // figure out if we can copy the frontbuffer back\n'
    assert text.count(anchor) == 1
    replacement = '''        // Droid2W CPU window redraw compatibility.
        // Return full damage to Canvas/ViewRoot so every pixel is painted into
        // the dequeued buffer, without relying on software copyback history.
        char fullRedraw[PROPERTY_VALUE_MAX];
        property_get("debug.sf.zero2w_full_redraw", fullRedraw, "0");
        if (fullRedraw[0] == '1') {
            newDirtyRegion.set(bounds);
        }

'''
    if '#include <cutils/properties.h>' not in text:
        text = text.replace('#include <android/native_window.h>',
                            '#include <android/native_window.h>\n#include <cutils/properties.h>')
    text = text.replace(anchor, replacement + anchor)
    surface.write_text(text)

status = root / 'packages/apps/Settings/src/com/android/settings/deviceinfo/Status.java'
text = status.read_text()
old = '''        if (UserHandle.myUserId() == UserHandle.USER_OWNER) {
            mPhone = PhoneFactory.getDefaultPhone();
        }'''
new = '''        // Droid2W: Wi-Fi-only devices have no initialized PhoneFactory.
        if (!Utils.isWifiOnly(getApplicationContext())
                && UserHandle.myUserId() == UserHandle.USER_OWNER) {
            mPhone = PhoneFactory.getDefaultPhone();
        }'''
if old in text:
    assert text.count(old) == 1
    text = text.replace(old, new)
    status.write_text(text)
assert new in text

# This board has no phone package to supply the radio process permissions.
# Keep the Wi-Fi-only status activity in Settings' normal system process.
manifest = root / 'packages/apps/Settings/AndroidManifest.xml'
text = manifest.read_text()
start = text.index('<activity android:name=".deviceinfo.Status"')
end = text.index('</activity>', start)
activity = text[start:end]
activity = activity.replace('android:process="com.android.phone"',
                            'android:process="com.android.settings"')
text = text[:start] + activity + text[end:]
manifest.write_text(text)

clock = root / 'frameworks/base/core/jni/android_os_SystemClock.cpp'
text = clock.read_text()
old_clock = '''    if(fd < 0) {
        ALOGW("Unable to open alarm driver: %s\\n", strerror(errno));
        return -1;
    }'''
new_clock = '''    if(fd < 0) {
        // Droid2W: modern kernels may not expose the legacy Android alarm device.
        // settimeofday still enforces CAP_SYS_TIME; ordinary apps gain no privilege.
        if (errno == ENOENT || errno == ENODEV) {
            return settimeofday(&tv, NULL);
        }
        ALOGW("Unable to open alarm driver: %s\\n", strerror(errno));
        return -1;
    }'''
if old_clock in text:
    assert text.count(old_clock) == 1
    text = text.replace(old_clock, new_clock)
    clock.write_text(text)
assert new_clock in text

adbd = root / 'system/core/adb/adb.c'
text = adbd.read_text()
old_usb = '''    int usb = 0;
    if (access(USB_ADB_PATH, F_OK) == 0 || access(USB_FFS_ADB_EP0, F_OK) == 0) {'''
new_usb = '''    int usb = 0;
    // Droid2W: a FunctionFS mount does not mean the controller is a USB device.
    // In host mode, leave it to keyboard/mouse and use the TCP transport only.
    char zero2w_usb_mode[16] = { 0 };
    int zero2w_mode_fd = adb_open("/proc/device-tree/soc/usb@7e980000/dr_mode", O_RDONLY);
    if (zero2w_mode_fd >= 0) {
        adb_read(zero2w_mode_fd, zero2w_usb_mode, sizeof(zero2w_usb_mode) - 1);
        adb_close(zero2w_mode_fd);
    }
    if (strcmp(zero2w_usb_mode, "host") != 0 &&
            (access(USB_ADB_PATH, F_OK) == 0 || access(USB_FFS_ADB_EP0, F_OK) == 0)) {'''
if old_usb in text:
    assert text.count(old_usb) == 1
    text = text.replace(old_usb, new_usb)
    adbd.write_text(text)
assert new_usb in text
print('Prepared redraw, Settings, clock and USB-role-aware ADB fixes.')
