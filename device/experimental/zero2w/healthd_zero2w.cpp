// SPDX-License-Identifier: Apache-2.0
#include <healthd.h>

void healthd_board_init(struct healthd_config* config) {
    // This development board is externally powered, with no battery gauge.
    config->periodic_chores_interval_fast = -1;
    config->periodic_chores_interval_slow = -1;
}

int healthd_board_battery_update(android::BatteryProperties* props) {
    props->chargerAcOnline = true;
    props->chargerUsbOnline = false;
    props->chargerWirelessOnline = false;
    props->batteryPresent = false;
    props->batteryStatus = android::BATTERY_STATUS_UNKNOWN;
    props->batteryHealth = android::BATTERY_HEALTH_UNKNOWN;
    // Framework compatibility value only, not a measured state of charge.
    props->batteryLevel = 100;
    props->batteryVoltage = 0;
    props->batteryTemperature = 0;
    return 1;
}
