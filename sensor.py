"""Sensors of the powerstrip."""
from typing import Any
from homeassistant.const import (
    DEVICE_CLASS_VOLTAGE,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_ENERGY,
)
from homeassistant.components.sensor import SensorEntity
from .hub import Hub,OutletDevice
from .const import DOMAIN


# See cover.py for more details.
# Note how both entities for each roller sensor (battry and illuminance) are added at
# the same time to the same list. This way only a single async_add_devices call is
# required.
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    hub:Hub = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for outlet in hub.outlets:
        u=VoltageSensor(outlet)
        new_devices.append(u)
        outlet.voltage_sensor=u
        i=CurrentSensor(outlet)
        new_devices.append(i)
        outlet.current_sensor=i
        p=PowerSensor(outlet)
        new_devices.append(p)
        outlet.power_sensor=p
        w=EnergySensor(outlet)
        new_devices.append(w)
        outlet.energy_sensor=w
    if new_devices:
        async_add_entities(new_devices)


# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.
class SensorBase(SensorEntity):
    """Base representation of a Sensor."""

    should_poll = False
    _state:Any
    def __init__(self, outlet:OutletDevice):
        """Initialize the sensor."""
        self._outlet = outlet

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._outlet._id)}}

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if powerstrip is available."""
        return self._outlet.hub.online

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._outlet.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._outlet.remove_callback(self.async_write_ha_state)
    # @property
    # def native_value(self):
    #     """Return the state of the sensor."""
    #     return None


class VoltageSensor(SensorBase):
    """Representation of a Sensor."""
    device_class = DEVICE_CLASS_VOLTAGE
    native_unit_of_measurement = "V"

    def __init__(self, outlet):
        """Initialize the sensor."""
        super().__init__(outlet)
        self._attr_unique_id = f"{self._outlet._id}_voltage"
        # The name of the entity
        self._attr_name = f"{self._outlet.name} Voltage"
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._outlet.voltage

class CurrentSensor(SensorBase):
    """Representation of a Sensor."""
    device_class = DEVICE_CLASS_CURRENT
    native_unit_of_measurement = "A"

    def __init__(self, outlet):
        """Initialize the sensor."""
        super().__init__(outlet)
        self._attr_unique_id = f"{self._outlet._id}_current"
        # The name of the entity
        self._attr_name = f"{self._outlet.name} Current"
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._outlet.current
class PowerSensor(SensorBase):
    """Representation of a Sensor."""
    device_class = DEVICE_CLASS_POWER
    native_unit_of_measurement = "W"

    def __init__(self, outlet):
        """Initialize the sensor."""
        super().__init__(outlet)
        self._attr_unique_id = f"{self._outlet._id}_power"
        # The name of the entity
        self._attr_name = f"{self._outlet.name} Power"
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._outlet.power
class EnergySensor(SensorBase):
    """Representation of a Sensor."""
    device_class = DEVICE_CLASS_ENERGY
    native_unit_of_measurement = "Wh"

    def __init__(self, outlet):
        """Initialize the sensor."""
        super().__init__(outlet)
        self._attr_unique_id = f"{self._outlet._id}_energy"
        # The name of the entity
        self._attr_name = f"{self._outlet.name} Energy"
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._outlet.energy