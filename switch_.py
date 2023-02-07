"""Platform for light integration."""
from __future__ import annotations

import logging
import traceback
import voluptuous as vol
from typing import Any
# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import (PLATFORM_SCHEMA,SwitchEntity)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .ptsp01telnet import ptsp01

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default='23'): cv.port,
    vol.Optional(CONF_PASSWORD, default=''): cv.string,
    vol.Optional(CONF_NAME, default=''): cv.string,
})


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    password = config.get(CONF_PASSWORD)
    name = config[CONF_NAME]

    # Setup connection with devices/cloud
    strip = ptsp01(host,int(port),password)
    if name.__len__()>0:
        strip.name=name
    try:
        strip.connect()
    except:
        _LOGGER.error("Could not connect to PTSP01: "+traceback.format_exc())
    # Verify that passed in configuration works
    if not strip.waitForLogin():
        _LOGGER.error("Login to PTSP01 Failed.")
    # Add devices
    add_entities(SP01Socket(strip,socket) for socket in [1,2,3])

class SP01Socket(SwitchEntity):
    """Representation of an Awesome Light."""

    def __init__(self, strip:ptsp01, socket) -> None:
        """Initialize an AwesomeLight."""
        self._strip:ptsp01 = strip
        self._socket:int = socket
        self._name = strip.name+str(socket)
        self._state = None

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs: Any) -> None:
        self._strip.switch(self._socket,1)
        self._state=True

    def turn_off(self, **kwargs: Any) -> None:
        self._strip.switch(self._socket,0)
        self._state=False

    # def update(self) -> None:
    #     self._strip.getStatus()