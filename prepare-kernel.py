#!/usr/bin/env python3
"""Experimental KitKat compatibility changes for pinned Raspberry Pi 5.10.

This prepares source only. Hardware compatibility is not yet established.
"""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent
kernel = root / 'kernel'
research = root / 'research'
assert (kernel / 'arch/arm/boot/dts/bcm2710-rpi-zero-2-w.dts').is_file()
makefile = kernel / 'drivers/android/Makefile'
text = makefile.read_text()
marker = '# KitKat uses Binder protocol 7 and 32-bit parcel pointers.'
if marker not in text:
    text += '\n' + marker + '\nccflags-y += -DBINDER_IPC_32BIT\n'
    makefile.write_text(text)

logger = (research / 'logger-3.16.c').read_text()
logger = logger.replace('#include <linux/module.h>', '#include <linux/module.h>\n#include <linux/uio.h>\n#include <linux/timekeeping.h>')
begin = logger.index('static ssize_t do_write_log_from_user(')
end = logger.index('static struct logger_log *get_log_from_minor', begin)
logger = logger[:begin] + '''/* Linux 5.10 write_iter adapter; retains the original logger ABI. */
static ssize_t logger_write_iter(struct kiocb *iocb, struct iov_iter *from)
{
    struct logger_log *log = file_get_log(iocb->ki_filp);
    struct logger_entry header = { 0 };
    struct timespec64 now;
    unsigned char *payload;
    size_t count = min_t(size_t, iov_iter_count(from), LOGGER_ENTRY_MAX_PAYLOAD);

    if (!count)
        return 0;
    /* Copy before changing the ring: a bad user buffer cannot corrupt entries. */
    payload = kmalloc(count, GFP_KERNEL);
    if (!payload)
        return -ENOMEM;
    if (!copy_from_iter_full(payload, count, from)) {
        kfree(payload);
        return -EFAULT;
    }
    ktime_get_real_ts64(&now);
    header.pid = task_tgid_vnr(current);
    header.tid = task_pid_vnr(current);
    header.sec = now.tv_sec;
    header.nsec = now.tv_nsec;
    header.euid = current_euid();
    header.len = count;
    header.hdr_size = sizeof(header);
    mutex_lock(&log->mutex);
    fix_up_readers(log, sizeof(header) + count);
    do_write_log(log, &header, sizeof(header));
    do_write_log(log, payload, count);
    mutex_unlock(&log->mutex);
    kfree(payload);
    wake_up_interruptible(&log->wq);
    return count;
}

''' + logger[end:]
logger = logger.replace('.aio_write = logger_aio_write,', '.write_iter = logger_write_iter,')
target = kernel / 'drivers/staging/android/kitkat_logger'
target.mkdir(exist_ok=True)
(target / 'logger.c').write_text(logger)
shutil.copyfile(research / 'logger-3.16.h', target / 'logger.h')
(target / 'Makefile').write_text('obj-$(CONFIG_KITKAT_LOGGER) += logger.o\n')
kconfig = kernel / 'drivers/staging/android/Kconfig'
text = kconfig.read_text()
if 'config KITKAT_LOGGER' not in text:
    text += '\nconfig KITKAT_LOGGER\n\tbool "KitKat legacy logger devices"\n\tdefault n\n'
    kconfig.write_text(text)
makefile = kernel / 'drivers/staging/android/Makefile'
text = makefile.read_text()
if 'kitkat_logger/' not in text:
    text += '\nobj-$(CONFIG_KITKAT_LOGGER) += kitkat_logger/\n'
    makefile.write_text(text)
print('Prepared Binder protocol 7 and legacy logger source; not runtime-tested.')

# Match Android common's CAP_SYS_NICE permission for cgroup v1 task placement.
# Reference: kernel/common 9cb202cb0d18596a8ca46b80e86a1a47d82b2ae4,
# kernel/cgroup/cgroup-v1.c. Ordinary app credentials remain restricted.
cgroup = kernel / 'kernel/cgroup/cgroup-v1.c'
text = cgroup.read_text()
old = '!uid_eq(cred->euid, tcred->suid))'
new = '!uid_eq(cred->euid, tcred->suid) &&\n\t    !ns_capable(tcred->user_ns, CAP_SYS_NICE))'
if old in text:
    assert text.count(old) == 1
    text = text.replace(old, new)
    cgroup.write_text(text)
assert 'ns_capable(tcred->user_ns, CAP_SYS_NICE)' in text
print('Prepared Android common cgroup scheduling compatibility.')

# Page flips must not reallocate/reconfigure the firmware framebuffer.
framebuffer = kernel / 'drivers/video/fbdev/bcm2708_fb.c'
text = framebuffer.read_text()
old_pan = '''\tinfo->var.xoffset = var->xoffset;
\tinfo->var.yoffset = var->yoffset;
\tresult = bcm2708_fb_set_par(info);
'''
new_pan = '''\t/* Droid2W: a page flip changes only the scanout offset. */
\tu32 offset[2] = { var->xoffset, var->yoffset };
\tstruct bcm2708_fb *fb = to_bcm2708(info);

\tset_display_num(fb);
\tresult = rpi_firmware_property(fb->fbdev->fw,
\t\tRPI_FIRMWARE_FRAMEBUFFER_SET_VIRTUAL_OFFSET,
\t\toffset, sizeof(offset));
\tif (!result && (offset[0] != var->xoffset ||
\t\t\t offset[1] != var->yoffset))
\t\tresult = -EINVAL;
\tif (!result) {
\t\tinfo->var.xoffset = offset[0];
\t\tinfo->var.yoffset = offset[1];
\t}
'''
if old_pan in text:
    assert text.count(old_pan) == 1
    framebuffer.write_text(text.replace(old_pan, new_pan))
assert new_pan in framebuffer.read_text()
