"""Platform for Switch integration."""
from __future__ import annotations
import logging
from typing import Any
# These constants are relevant to the type of entity we are using.
# See below for how they are used.
from homeassistant.components.switch import (PLATFORM_SCHEMA,SwitchEntity,SwitchDeviceClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .hub import Hub,OutletDevice
from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)
# This function is called as part of the __init__.async_setup_entry (via the
# hass.config_entries.async_forward_entry_setup call)
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add cover for passed config_entry in HA."""
    # The hub is loaded from the associated hass.data entry that was created in the
    # __init__.async_setup_entry function
    hub:Hub = hass.data[DOMAIN][config_entry.entry_id]

    # Add all entities to HA
    new_devices = []
    for outlet in hub.outlets:
        s=OutletEntity(outlet)
        new_devices.append(s)
        outlet.switch=s
    if new_devices:
        async_add_entities(new_devices)
    # async_add_entities(OutletEntity(outlet) for outlet in hub.outlets)

# This entire class could be written to extend a base class to ensure common attributes
# are kept identical/in sync. It's broken apart here between the Cover and Sensors to
# be explicit about what is returned, and the comments outline where the overlap is.
class OutletEntity(SwitchEntity):
    """Representation of a dummy Cover."""

    # Our dummy class is PUSH, so we tell HA that it should not be polled
    should_poll = False
    device_class = SwitchDeviceClass.OUTLET

    def __init__(self, outlet:OutletDevice) -> None:
        """Initialize the sensor."""
        # Usual setup is done here. Callbacks are added in async_added_to_hass.
        self._outlet = outlet

        # A unique_id for this entity with in this domain. This means for example if you
        # have a sensor on this cover, you must ensure the value returned is unique,
        # which is done here by appending "_cover". For more information, see:
        # https://developers.home-assistant.io/docs/entity_registry_index/#unique-id-requirements
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._outlet._id}_outlet"

        # This is the name for this *entity*, the "name" attribute from "device_info"
        # is used as the device name for device screens in the UI. This name is used on
        # entity screens, and used to build the Entity ID that's used is automations etc.
        self._attr_name = self._outlet.name

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Importantly for a push integration, the module that will be getting updates
        # needs to notify HA of changes. The dummy device has a registercallback
        # method, so to this we add the 'self.async_write_ha_state' method, to be
        # called where ever there are changes.
        # The call back registration is done once this entity is registered with HA
        # (rather than in the __init__)
        self._outlet.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._outlet.remove_callback(self.async_write_ha_state)

    # Information about the devices that is partially visible in the UI.
    # The most critical thing here is to give this entity a name so it is displayed
    # as a "device" in the HA UI. This name is used on the Devices overview table,
    # and the initial screen when the device is added (rather than the entity name
    # property below). You can then associate other Entities (eg: a battery
    # sensor) with this device, so it shows more like a unified element in the UI.
    # For example, an associated battery sensor will be displayed in the right most
    # column in the Configuration > Devices view for a device.
    # To associate an entity with this device, the device_info must also return an
    # identical "identifiers" attribute, but not return a name attribute.
    # See the sensors.py file for the corresponding example setup.
    # Additional meta data can also be returned here, including sw_version (displayed
    # as Firmware), model and manufacturer (displayed as <model> by <manufacturer>)
    # shown on the device info screen. The Manufacturer and model also have their
    # respective columns on the Devices overview table. Note: Many of these must be
    # set when the device is first added, and they are not always automatically
    # refreshed by HA from it's internal cache.
    # For more information see:
    # https://developers.home-assistant.io/docs/device_registry_index/#device-properties
    @property
    def device_info(self) -> DeviceInfo:
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._outlet._id)},
            # If desired, the name for the device could be different to the entity
            "name": self.name,
            "sw_version": self._outlet.firmware_version,
            "model": self._outlet.model,
            "manufacturer": self._outlet.hub.manufacturer,
        }

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return self._outlet.hub.online
    @property
    def is_on(self) -> bool:
        """Return True if roller and hub is available."""
        return self._outlet.is_on==True
    def turn_on(self, **kwargs: Any) -> None:
        self._outlet.turn_on()
        self.async_write_ha_state()
    def turn_off(self, **kwargs: Any) -> None:
        self._outlet.turn_off()
        self.async_write_ha_state()

