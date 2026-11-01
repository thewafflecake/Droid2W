LOCAL_PATH := $(call my-dir)

ifeq ($(TARGET_DEVICE),zero2w)
include $(CLEAR_VARS)
LOCAL_MODULE := lib_driver_cmd_zero2w
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := driver_cmd_zero2w.c
include $(BUILD_STATIC_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := libhealthd.zero2w
LOCAL_SRC_FILES := healthd_zero2w.cpp
LOCAL_C_INCLUDES := system/core/healthd
include $(BUILD_STATIC_LIBRARY)

# Stock KitKat searches this exact driver filename before scanning vendor names.
# It deliberately excludes libGLES_android.so from the generic wildcard search.
zero2w_egl_alias := $(TARGET_OUT)/lib/egl/libGLES.so
$(zero2w_egl_alias): $(TARGET_OUT)/lib/egl/libGLES_android.so
	@mkdir -p $(dir $@)
	$(hide) ln -sf libGLES_android.so $@
ALL_DEFAULT_INSTALLED_MODULES += $(zero2w_egl_alias)
endif
