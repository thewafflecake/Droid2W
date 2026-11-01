/* SPDX-License-Identifier: Apache-2.0
 * Minimal Android 4.4 private-command bridge for mainline brcmfmac.
 * All normal association/scanning commands use the standard nl80211 backend.
 * Unsupported vendor-specific features return an explicit error.
 */
#include <errno.h>
#include <net/if.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>

int wpa_driver_nl80211_driver_cmd(void *priv, char *cmd, char *buf, size_t buflen)
{
    struct ifreq request;
    int fd, result = -EOPNOTSUPP;
    (void)priv;
    if (!cmd || !buf)
        return -EINVAL;
    memset(&request, 0, sizeof(request));
    strncpy(request.ifr_name, "wlan0", IFNAMSIZ - 1);
    fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0)
        return -errno;
    if (!strcasecmp(cmd, "MACADDR")) {
        if (ioctl(fd, SIOCGIFHWADDR, &request) < 0) {
            result = -errno;
        } else {
            const unsigned char *a = (const unsigned char *)request.ifr_hwaddr.sa_data;
            result = snprintf(buf, buflen, "Macaddr = %02x:%02x:%02x:%02x:%02x:%02x\n",
                              a[0], a[1], a[2], a[3], a[4], a[5]);
        }
    } else if (!strcasecmp(cmd, "START") || !strcasecmp(cmd, "STOP")) {
        if (ioctl(fd, SIOCGIFFLAGS, &request) < 0) {
            result = -errno;
        } else {
            if (!strcasecmp(cmd, "START"))
                request.ifr_flags |= IFF_UP;
            else
                request.ifr_flags &= ~IFF_UP;
            result = ioctl(fd, SIOCSIFFLAGS, &request) < 0 ? -errno : 0;
        }
    }
    close(fd);
    return result;
}
