#!/usr/bin/env bash
# Run inside zero2w-kitkat-build with the workspace mounted at /work.
set -eo pipefail
cd /work/aosp
export JAVA_HOME=/usr/lib/jvm/java-6-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
export USE_CCACHE=0
export LC_ALL=C
source build/envsetup.sh
lunch zero2w-userdebug
# Deliberately one job on the 4 GB build server.
make -j1 ramdisk systemimage userdataimage cacheimage
