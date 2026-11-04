#!/usr/bin/env python3
"""Prepare the KitKat Broadcom UART vendor library for Zero 2 W bring-up."""
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parent
vendor = root / 'aosp/hardware/broadcom/libbt'
device = root / 'aosp/device/experimental/zero2w'
(vendor / 'include/vnd_zero2w.txt').write_text('''BLUETOOTH_UART_DEVICE_PORT = "/dev/ttyAMA0"
FW_PATCHFILE_LOCATION = "/system/etc/firmware/brcm/"
UART_TARGET_BAUD_RATE = 921600
FW_PATCH_SETTLEMENT_DELAY_MS = 200
LPM_SLEEP_MODE = 0
BT_WAKE_VIA_PROC = FALSE
BT_WAKE_VIA_USERIAL_IOCTL = FALSE
SCO_CFG_INCLUDED = FALSE
DROID2W_BT_POWER_GPIO = TRUE
BTHW_DBG = TRUE
''')

path = vendor / 'src/upio.c'
text = path.read_text()
anchor = '    /* check if we have rfkill interface */'
block = '''#if defined(DROID2W_BT_POWER_GPIO) && DROID2W_BT_POWER_GPIO
    /* GPIO is exported and permissioned by the board's root init script. */
    fd = open("/sys/class/gpio/gpio42/value", O_WRONLY);
    if (fd < 0) {
        ALOGE("Cannot open Bluetooth power GPIO: %s", strerror(errno));
        return -1;
    }
    sz = write(fd, &buffer, 1);
    close(fd);
    if (sz != 1) return -1;
    if (on == UPIO_BT_POWER_ON) usleep(200000);
    return 0;
#endif

'''
if 'Cannot open Bluetooth power GPIO' not in text:
    assert text.count(anchor) == 1
    text = text.replace(anchor, block + anchor)
    path.write_text(text)

path = vendor / 'src/hardware.c'
text = path.read_text()
text = text.replace('(i < LOCAL_NAME_BUFFER_LEN)||(*(p_name+i) != 0)',
                    '(i < LOCAL_NAME_BUFFER_LEN) && (*(p_name+i) != 0)')
path.write_text(text)

path = device / 'BoardConfig.mk'
text = path.read_text()
if 'BOARD_HAVE_BLUETOOTH_BCM' not in text:
    path.write_text(text + '\nBOARD_HAVE_BLUETOOTH := true\nBOARD_HAVE_BLUETOOTH_BCM := true\n')

firmware = root / 'research/rpi-bluez-firmware'
revision = subprocess.check_output(['git', '-C', str(firmware), 'rev-parse', 'HEAD'], text=True).strip()
assert revision == 'cdf61dc691a49ff01a124752bd04194907f0f9cd', revision
target = device / 'firmware/brcm'
target.mkdir(parents=True, exist_ok=True)
shutil.copyfile(firmware / 'debian/firmware/broadcom/BCM43430A1.hcd', target / 'BCM43430A1.hcd')
shutil.copyfile(firmware / 'debian/copyright', target.parent / 'bluetooth-copyright')
(target.parent / 'bluetooth-source-revision.txt').write_text(revision + '\n')
print('Prepared board UART/power configuration and pinned BCM43430A1 firmware.')
