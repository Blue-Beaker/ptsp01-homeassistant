"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.
import random

from homeassistant.const import (
    DEVICE_CLASS_VOLTAGE,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_ENERGY,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.core import callback
from .hub import Hub,Outlet

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
        new_devices.append(VoltageSensor(outlet))
        new_devices.append(CurrentSensor(outlet))
        new_devices.append(PowerSensor(outlet))
        new_devices.append(EnergySensor(outlet))
    if new_devices:
        async_add_entities(new_devices)


# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.
class SensorBase(Entity):
    """Base representation of a Hello World Sensor."""

    should_poll = True

    def __init__(self, outlet:Outlet):
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
        """Return True if roller and hub is available."""
        return self._outlet.hub.online
        
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data[self.idx]["state"]
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._outlet.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._outlet.remove_callback(self.async_write_ha_state)


class VoltageSensor(SensorBase):
    """Representation of a Sensor."""
    # The class of this device. Note the value should come from the homeassistant.const
    # module. More information on the available devices classes can be seen here:
    # https://developers.home-assistant.io/docs/core/entity/sensor
    device_class = DEVICE_CLASS_VOLTAGE
    # The unit of measurement for this entity. As it's a DEVICE_CLASS_BATTERY, this
    # should be PERCENTAGE. A number of units are supported by HA, for some
    # examples, see:
    # https://developers.home-assistant.io/docs/core/entity/sensor#available-device-classes
    _attr_unit_of_measurement = "V"

    def __init__(self, outlet):
        """Initialize the sensor."""
        super().__init__(outlet)
        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"{self._outlet._id}_voltage"
        # The name of the entity
        self._attr_name = f"{self._outlet.name} Voltage"
        self._state = self._outlet.voltage
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._outlet.voltage

class CurrentSensor(SensorBase):
    """Representation of a Sensor."""
    # The class of this device. Note the value should come from the homeassistant.const
    # module. More information on the available devices classes can be seen here:
    # https://developers.home-assistant.io/docs/core/entity/sensor
    device_class = DEVICE_CLASS_CURRENT
    # The unit of measurement for this entity. As it's a DEVICE_CLASS_BATTERY, this
    # should be PERCENTAGE. A number of units are supported by HA, for some
    # examples, see:
    # https://developers.home-assistant.io/docs/core/entity/sensor#available-device-classes
    _attr_unit_of_measurement = "A"

    def __init__(self, outlet):
        """Initialize the sensor."""
        super().__init__(outlet)
        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"{self._outlet._id}_current"
        # The name of the entity
        self._attr_name = f"{self._outlet.name} Current"
        self._state = self._outlet.current
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._outlet.current

class PowerSensor(SensorBase):
    """Representation of a Sensor."""
    # The class of this device. Note the value should come from the homeassistant.const
    # module. More information on the available devices classes can be seen here:
    # https://developers.home-assistant.io/docs/core/entity/sensor
    device_class = DEVICE_CLASS_POWER
    # The unit of measurement for this entity. As it's a DEVICE_CLASS_BATTERY, this
    # should be PERCENTAGE. A number of units are supported by HA, for some
    # examples, see:
    # https://developers.home-assistant.io/docs/core/entity/sensor#available-device-classes
    _attr_unit_of_measurement = "W"

    def __init__(self, outlet):
        """Initialize the sensor."""
        super().__init__(outlet)
        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"{self._outlet._id}_power"
        # The name of the entity
        self._attr_name = f"{self._outlet.name} Power"
        self._state = self._outlet.power
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._outlet.power

class EnergySensor(SensorBase):
    """Representation of a Sensor."""
    # The class of this device. Note the value should come from the homeassistant.const
    # module. More information on the available devices classes can be seen here:
    # https://developers.home-assistant.io/docs/core/entity/sensor
    device_class = DEVICE_CLASS_ENERGY
    # The unit of measurement for this entity. As it's a DEVICE_CLASS_BATTERY, this
    # should be PERCENTAGE. A number of units are supported by HA, for some
    # examples, see:
    # https://developers.home-assistant.io/docs/core/entity/sensor#available-device-classes
    _attr_unit_of_measurement = "kWh"

    def __init__(self, outlet):
        """Initialize the sensor."""
        super().__init__(outlet)
        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"{self._outlet._id}_energy"
        # The name of the entity
        self._attr_name = f"{self._outlet.name} Energy"
        self._state = self._outlet.energy
    @property
    def state(self):
        """Return the state of the sensor."""
        return self._outlet.energy
