"""Sensor entities for BLE Scan."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.bluetooth import DOMAIN as BLUETOOTH_DOMAIN
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import MANUFACTURER, MODEL
from .manager import BLEScanDevice, BLEScanManager


@dataclass(frozen=True, kw_only=True)
class BLEScanSensorEntityDescription(SensorEntityDescription):
    """Describe a BLE Scan sensor."""

    value_fn: Callable[[BLEScanDevice], float | int | datetime]


SENSOR_DESCRIPTIONS: tuple[BLEScanSensorEntityDescription, ...] = (
    BLEScanSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda device: device.update.temperature,
    ),
    BLEScanSensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.update.humidity,
    ),
    BLEScanSensorEntityDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.update.battery,
    ),
    BLEScanSensorEntityDescription(
        key="voltage",
        translation_key="voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda device: device.update.voltage,
    ),
    BLEScanSensorEntityDescription(
        key="rssi",
        translation_key="signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda device: device.rssi,
    ),
    BLEScanSensorEntityDescription(
        key="last_seen",
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: device.last_seen,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[BLEScanManager],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up BLE Scan sensor entities."""
    manager = entry.runtime_data
    known_addresses: set[str] = set()

    @callback
    def async_add_new_device(address: str) -> None:
        if address in known_addresses:
            return
        known_addresses.add(address)
        async_add_entities(
            BLEScanSensor(manager, address, description)
            for description in SENSOR_DESCRIPTIONS
        )

    entry.async_on_unload(manager.async_add_listener(async_add_new_device))
    for address in manager.devices:
        async_add_new_device(address)


class BLEScanSensor(SensorEntity):
    """One metric from an ATC BLE sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        manager: BLEScanManager,
        address: str,
        description: BLEScanSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self.manager = manager
        self.address = address
        self.entity_description = description
        self._attr_unique_id = f"{address}-{description.key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            identifiers={(BLUETOOTH_DOMAIN, address)},
            name=manager.device_name(address),
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to Bluetooth updates after the entity is registered."""
        await super().async_added_to_hass()
        self.async_on_remove(self.manager.async_add_listener(self._async_handle_update))

    @callback
    def _async_handle_update(self, address: str) -> None:
        """Write state when this device changes."""
        if address == self.address:
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return whether Home Assistant can still see the sensor."""
        return self.manager.devices[self.address].available

    @property
    def native_value(self) -> float | int | datetime:
        """Return the latest decoded metric."""
        return self.entity_description.value_fn(self.manager.devices[self.address])

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose reception details on the RSSI entity only."""
        if self.entity_description.key != "rssi":
            return None
        device = self.manager.devices[self.address]
        return {
            "source": device.source,
            "last_seen": device.last_seen.isoformat(),
            "packet_counter": device.update.packet_counter,
        }
