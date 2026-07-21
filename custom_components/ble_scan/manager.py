"""Bluetooth advertisement manager for BLE Scan."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import ATC_LOCAL_NAME_PREFIX, ATC_SERVICE_UUID
from .parser import ATCSensorUpdate, normalize_address, parse_atc_advertisement

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class BLEScanDevice:
    """Latest state received from one ATC sensor."""

    update: ATCSensorUpdate
    rssi: int
    source: str
    last_seen: datetime
    available: bool = True


class BLEScanManager:
    """Use Home Assistant's shared Bluetooth scanner for ATC sensors."""

    def __init__(self, hass: HomeAssistant, names: dict[str, str]) -> None:
        """Initialize the manager."""
        self.hass = hass
        self.names = {normalize_address(key): value for key, value in names.items()}
        self.devices: dict[str, BLEScanDevice] = {}
        self._listeners: set[Callable[[str], None]] = set()
        self._cancel_unavailable: dict[str, Callable[[], None]] = {}

    @callback
    def async_start(self) -> Callable[[], None]:
        """Start listening to the shared Home Assistant Bluetooth scanner."""
        cancel = bluetooth.async_register_callback(
            self.hass,
            self._async_handle_bluetooth,
            {
                "local_name": f"{ATC_LOCAL_NAME_PREFIX}*",
                "service_uuid": ATC_SERVICE_UUID,
                "connectable": False,
            },
            BluetoothScanningMode.PASSIVE,
        )

        for service_info in bluetooth.async_discovered_service_info(
            self.hass, connectable=False
        ):
            self._async_process_service_info(service_info)

        return cancel

    @callback
    def async_stop(self) -> None:
        """Cancel per-device unavailable callbacks."""
        for cancel in self._cancel_unavailable.values():
            cancel()
        self._cancel_unavailable.clear()

    @callback
    def async_add_listener(self, listener: Callable[[str], None]) -> Callable[[], None]:
        """Register an update listener."""
        self._listeners.add(listener)

        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener

    @callback
    def _async_handle_bluetooth(
        self, service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        """Handle a Bluetooth advertisement."""
        self._async_process_service_info(service_info)

    @callback
    def _async_process_service_info(
        self, service_info: BluetoothServiceInfoBleak
    ) -> None:
        """Decode and store one Bluetooth advertisement."""
        update = parse_atc_advertisement(
            service_info.address,
            service_info.name,
            service_info.service_data,
        )
        if update is None:
            return

        address = update.address
        is_new = address not in self.devices
        self.devices[address] = BLEScanDevice(
            update=update,
            rssi=service_info.rssi,
            source=service_info.source,
            last_seen=dt_util.utcnow(),
        )

        if is_new:
            _LOGGER.info("Discovered ATC BLE sensor %s (%s)", update.name, address)
            self._cancel_unavailable[address] = bluetooth.async_track_unavailable(
                self.hass,
                self._async_handle_unavailable,
                address,
                connectable=False,
            )

        self._async_notify(address)

    @callback
    def _async_handle_unavailable(
        self, service_info: BluetoothServiceInfoBleak
    ) -> None:
        """Mark a sensor unavailable when no scanner can see it."""
        address = normalize_address(service_info.address)
        if device := self.devices.get(address):
            device.available = False
            self._async_notify(address)

    @callback
    def _async_notify(self, address: str) -> None:
        """Notify listeners of a changed device."""
        for listener in tuple(self._listeners):
            listener(address)

    def device_name(self, address: str) -> str:
        """Return configured name or advertised ATC name."""
        device = self.devices[address]
        return self.names.get(address, device.update.name)

