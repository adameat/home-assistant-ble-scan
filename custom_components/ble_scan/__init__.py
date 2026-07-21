"""BLE Scan integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import CONF_NAMES, DOMAIN
from .parser import normalize_address

PLATFORMS: list[Platform] = [Platform.SENSOR]

NAME_MAP_SCHEMA = vol.Schema({cv.string: cv.string})
CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Schema(
            {vol.Optional(CONF_NAMES, default={}): NAME_MAP_SCHEMA}
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Import optional YAML configuration into a config entry."""
    if domain_config := config.get(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=domain_config,
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BLE Scan from a config entry."""
    from .manager import BLEScanManager

    names = {
        normalize_address(address): name
        for address, name in entry.data.get(CONF_NAMES, {}).items()
    }
    manager = BLEScanManager(hass, names)
    entry.runtime_data = manager

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(manager.async_start())
    entry.async_on_unload(manager.async_stop)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a BLE Scan config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
