#!/usr/bin/env python3
"""Apply device-opt-in runtime compatibility fixes to the pinned KitKat tree."""
from pathlib import Path

root = Path(__file__).resolve().parent / 'aosp'
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
