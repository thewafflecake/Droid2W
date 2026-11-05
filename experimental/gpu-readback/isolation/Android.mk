LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := libd2w_egl_redirect
LOCAL_SRC_FILES := egl-redirect.c
LOCAL_SHARED_LIBRARIES := libdl liblog
LOCAL_MODULE_TAGS := optional
include $(BUILD_SHARED_LIBRARY)
