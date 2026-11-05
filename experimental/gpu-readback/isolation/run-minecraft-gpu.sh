#!/system/bin/sh
export DROID2W_GPU_TEST=1
export LD_PRELOAD=/data/local/tmp/zero2w-multimedia/libd2w_egl_redirect.so
exec "$@"
