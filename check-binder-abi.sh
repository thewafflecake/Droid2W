#!/usr/bin/env bash
# Compare the on-wire layout and command numbers used by KitKat and kernel 5.10.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p checks
cat > checks/binder-abi.c <<'EOF'
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>
#include <linux/types.h>
#define __user
#include BINDER_HEADER
const unsigned int abi[] = {
    BINDER_CURRENT_PROTOCOL_VERSION,
    sizeof(struct flat_binder_object),
    sizeof(struct binder_transaction_data),
    sizeof(struct binder_write_read),
    sizeof(struct binder_ptr_cookie),
    offsetof(struct binder_transaction_data, data),
    BINDER_WRITE_READ, BINDER_VERSION, BINDER_SET_MAX_THREADS,
    BINDER_SET_CONTEXT_MGR, BINDER_THREAD_EXIT,
    BC_TRANSACTION, BC_REPLY, BC_FREE_BUFFER, BC_INCREFS, BC_ACQUIRE,
    BC_RELEASE, BC_DECREFS, BC_INCREFS_DONE, BC_ACQUIRE_DONE,
    BC_REQUEST_DEATH_NOTIFICATION, BC_CLEAR_DEATH_NOTIFICATION,
    BC_DEAD_BINDER_DONE,
    BR_TRANSACTION, BR_REPLY, BR_TRANSACTION_COMPLETE, BR_INCREFS,
    BR_ACQUIRE, BR_RELEASE, BR_DECREFS, BR_DEAD_BINDER, BR_CLEAR_DEATH_NOTIFICATION_DONE
};
EOF
for side in kitkat kernel; do
    if [[ $side == kitkat ]]; then
        header="$PWD/aosp/bionic/libc/kernel/common/linux/binder.h"
        extra=()
    else
        header="$PWD/kernel/include/uapi/linux/android/binder.h"
        extra=(-DBINDER_IPC_32BIT)
    fi
    arm-linux-gnueabihf-gcc -c "${extra[@]}" -DBINDER_HEADER=\""$header"\" checks/binder-abi.c -o checks/"$side".o
    arm-linux-gnueabihf-objcopy -O binary --only-section=.rodata checks/"$side".o checks/"$side".bin
done
cmp checks/kitkat.bin checks/kernel.bin
echo 'PASS: checked Binder protocol, structure sizes, transaction offset, and command numbers match.'
