$(call inherit-product, $(SRC_TARGET_DIR)/product/core_base.mk)
$(call inherit-product, frameworks/base/data/fonts/fonts.mk)
$(call inherit-product, frameworks/base/data/keyboards/keyboards.mk)
$(call inherit-product, frameworks/webview/chromium/chromium.mk)

PRODUCT_PACKAGES += \
    InputDevices Keyguard LatinIME Launcher2 Provision Settings SystemUI \
    audio.primary.default audio_policy.default power.default \
    gralloc.default libGLES_android librs_jni local_time.default e2fsck \
    wpa_supplicant wpa_cli dhcpcd dhcpcd-run-hooks 20-dns.conf 95-configured

PRODUCT_COPY_FILES += \
    device/experimental/zero2w/init.zero2w.rc:root/init.zero2w.rc \
    device/experimental/zero2w/init.zero2w.usb.rc:root/init.zero2w.usb.rc \
    device/experimental/zero2w/adb_keys:root/adb_keys \
    device/experimental/zero2w/ueventd.zero2w.rc:root/ueventd.zero2w.rc \
    device/experimental/zero2w/fstab.zero2w:root/fstab.zero2w \
    device/experimental/zero2w/wpa_supplicant.conf:system/etc/wifi/wpa_supplicant.conf \
    external/dhcpcd/android.conf:system/etc/dhcpcd/dhcpcd.conf \
    frameworks/native/data/etc/android.hardware.wifi.xml:system/etc/permissions/android.hardware.wifi.xml \
    frameworks/native/data/etc/android.hardware.usb.host.xml:system/etc/permissions/android.hardware.usb.host.xml

# Built by build-network-kernel.sh for this exact kernel configuration.
PRODUCT_COPY_FILES += $(foreach file,$(wildcard device/experimental/zero2w/modules/*.ko),$(file):system/lib/modules/$(notdir $(file)))
PRODUCT_COPY_FILES += $(foreach file,$(wildcard device/experimental/zero2w/firmware/brcm/*),$(file):system/etc/firmware/brcm/$(notdir $(file)))
PRODUCT_COPY_FILES += $(foreach file,$(wildcard device/experimental/zero2w/firmware/copyright device/experimental/zero2w/firmware/source-revision.txt),$(file):system/etc/firmware/$(notdir $(file)))

DEVICE_PACKAGE_OVERLAYS := device/experimental/zero2w/overlay
PRODUCT_LOCALES := en_US ru_RU
PRODUCT_AAPT_CONFIG := normal large mdpi hdpi
PRODUCT_AAPT_PREF_CONFIG := mdpi
PRODUCT_NAME := zero2w
PRODUCT_DEVICE := zero2w
PRODUCT_BRAND := experimental
PRODUCT_MODEL := Raspberry Pi Zero 2 W KitKat bring-up
PRODUCT_MANUFACTURER := Raspberry Pi
PRODUCT_CHARACTERISTICS := tablet,nosdcard
