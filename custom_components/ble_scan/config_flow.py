"""Config flow for BLE Scan."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_NAMES, DOMAIN
from .parser import parse_atc_advertisement


class BLEScanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure BLE Scan."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Create the singleton scanner entry from the UI."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="BLE Scan", data={CONF_NAMES: {}})
        return self.async_show_form(step_id="user")

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle discovery of a supported ATC sensor."""
        if (
            parse_atc_advertisement(
                discovery_info.address,
                discovery_info.name,
                discovery_info.service_data,
            )
            is None
        ):
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {"name": discovery_info.name}
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery and create the singleton scanner entry."""
        if user_input is not None:
            return self.async_create_entry(title="BLE Scan", data={CONF_NAMES: {}})
        return self.async_show_form(step_id="confirm")

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Import the optional YAML name mapping."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title="BLE Scan",
            data={CONF_NAMES: dict(import_data.get(CONF_NAMES, {}))},
        )
