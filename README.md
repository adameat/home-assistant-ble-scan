# BLE Scan for Home Assistant

Direct, local Bluetooth support for Xiaomi LYWSD03MMC temperature and humidity
sensors running ATC custom firmware.

BLE Scan subscribes to Home Assistant's shared Bluetooth scanner. It does not
start a second `BleakScanner`, connect to a database, or use a message broker.
Advertisements are decoded inside Home Assistant.

## Supported advertisement format

- Local name: `ATC_*`
- Environmental Sensing service UUID: `0x181A`
- ATC 13-byte custom payload: MAC address, temperature, humidity, battery
  percentage, battery voltage, and packet counter

Other Bluetooth devices, including Samsung SmartTags, do not match these
conditions and are ignored.

## Entities

Each detected sensor becomes a Home Assistant device with these entities:

- temperature
- humidity
- battery percentage
- last seen timestamp, updated for every received advertisement
- battery voltage (diagnostic, disabled by default)
- RSSI (diagnostic, disabled by default)

## Installation

### HACS custom repository

1. Open HACS, select **Custom repositories**, and add
   `https://github.com/adameat/home-assistant-ble-scan` as an **Integration**.
2. Install **BLE Scan** and restart Home Assistant.
3. Open **Settings → Devices & services → Add integration → BLE Scan**.

The integration may also appear automatically when Home Assistant discovers an
`ATC_*` sensor.

### Manual

Copy `custom_components/ble_scan` into the `custom_components` directory of the
Home Assistant configuration, restart Home Assistant, and add **BLE Scan** in
**Settings → Devices & services**.

## Optional YAML name import

Home Assistant devices use their advertised `ATC_XXXXXX` name by default. For a
new installation, an optional one-time YAML import can assign friendly names:

```yaml
ble_scan:
  names:
    "A4:C1:38:6E:3E:9A": Living room
    "A4:C1:38:90:7D:08": Kitchen
```

Restart Home Assistant once. After the config entry has been created, this YAML
block can be removed; the imported names remain in the config entry. Devices can
also be renamed normally in the Home Assistant UI.

## Bluetooth behavior

BLE Scan uses Home Assistant's `bluetooth` and `bluetooth_adapters` APIs and
accepts advertisements from connectable and non-connectable scanners. Multiple
local adapters and Bluetooth proxies are handled by Home Assistant; the most
recent advertisement updates the device.

## License

MIT
