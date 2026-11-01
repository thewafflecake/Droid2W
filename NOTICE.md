# Licensing and provenance

New Droid2W build scripts and device configuration are provided under Apache-2.0
unless a file states otherwise. Third-party code retains its original license;
the root license does not relicense it.

- `third_party/logger/logger-3.16.c` and `.h`: legacy Android logger from
  https://github.com/trevd/android_kernel_broadcom_rpi, branch
  `rpi-3.16-android`, `drivers/staging/android/logger.c` and `logger.h`.
  These files retain their Google copyright and GPL version 2 notices.
  A copy of GPLv2 is in `third_party/logger/COPYING`.
- Android source revisions are recorded in the AOSP manifest. Android projects
  retain their respective upstream licenses.
- Raspberry Pi Linux is obtained separately and retains its upstream licenses.
- Raspberry Pi boot firmware and Broadcom Wi-Fi firmware are fetched separately;
  their redistribution terms are not replaced by the Droid2W license.
  Fetch scripts retain the relevant upstream license files.

No firmware blobs, Google proprietary applications or device access credentials
are distributed in this repository.
