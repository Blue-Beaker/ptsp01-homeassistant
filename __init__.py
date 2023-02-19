"""The Detailed Hello World Push integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry,ConfigEntryNotReady,ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant

from .hub import Hub
from .const import DOMAIN

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
PLATFORMS: list[str] = ["switch", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hello World from a config entry."""
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.
    hub=Hub(hass, entry.data)
    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    try:
        await hub.setup()
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except ConfigEntryAuthFailed as ex:
        raise ConfigEntryAuthFailed(f"Invalid password for {hub._host}") from ex
    except (EOFError,OSError,ConnectionError,BrokenPipeError) as ex:
        raise ConfigEntryNotReady(f"Failed connecting to {hub._host}") from ex
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
