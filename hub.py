"""A demonstration 'hub' that connects several devices."""
from __future__ import annotations

# In a real implementation, this would be in an external library that's on PyPI.
# The PyPI package needs to be included in the `requirements` section of manifest.json
# See https://developers.home-assistant.io/docs/creating_integration_manifest
# for more information.
# This dummy hub always returns 3 rollers.
import asyncio
import random
from typing import Any, Callable

from homeassistant.core import HomeAssistant

from .ptsp01telnet import ptsp01


class Hub:
    """Dummy hub for Hello World example."""

    manufacturer = "BoomSense"

    def __init__(self, hass: HomeAssistant, host: str, port:int,password:str) -> None:
        """Init dummy hub."""
        self._host = host
        self._port = port
        self._password = password
        self._hass = hass
        self._name = host
        self._id = "ptsp01_"+host.lower()
        self.strip=ptsp01(host,port,password)
        self.outlets=[
            Outlet(1,self._id+"_1",self),
            Outlet(2,self._id+"_2",self),
            Outlet(3,self._id+"_3",self)
        ]
        self.strip.connect()
        self.online = self.strip.waitForLogin()

    @property
    def firmware_version(self):
        return self.strip.version

    @property
    def hub_id(self) -> str:
        """ID for dummy hub."""
        return self._id

    async def test_connection(self) -> bool:
        """Test connectivity to the Dummy hub is OK."""
        try:
            self.strip.connect()
            return self.strip.waitForLogin()
        except:
            return False

class Outlet:
    _state=None
    def __init__(self, socket:int,name:str,hub:Hub):
        self._socket=socket
        self._id=hub._id+"_"+str(socket)
        self.hub=hub
        self._strip=hub.strip
        self.name=name
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self.model = "PTSP01"
    @property
    def firmware_version(self):
        return self.hub.firmware_version
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

    async def publish_updates(self) -> None:
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    async def delayed_update(self) -> None:
        """Publish updates, with a random delay to emulate interaction with device."""
        if not self._strip.isLoggedin():
            self.firmware_version=self._strip.version
        await self.publish_updates()

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when Roller changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)
    @property
    def voltage(self) -> float:
        return self._strip.getVoltage(self._socket)
    @property
    def current(self) -> float:
        return self._strip.getVoltage(self._socket)
    @property
    def power(self) -> float:
        return self._strip.getVoltage(self._socket)
    @property
    def energy(self) -> float:
        return self._strip.getVoltage(self._socket)

