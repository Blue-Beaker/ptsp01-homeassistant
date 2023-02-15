"""A 'hub' representing 3 sockets of the powerstrip to 3 devices."""
from __future__ import annotations
import logging
import asyncio
import traceback
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry,ConfigEntryNotReady,ConfigEntryAuthFailed
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.sensor import SensorEntity
from .ptsp01telnet import ptsp01

_LOGGER = logging.getLogger(__name__)

class Hub:
    """Treats the powerstrip as a hub."""

    manufacturer = "BoomSense"

    def __init__(self, hass: HomeAssistant, host: str, port:int,password:str) -> None:
        """Init powerstrip as hub."""
        self._host = host
        self._port = port
        self._password = password
        self._hass = hass
        self._name = host
        self._id = "ptsp01_"+host.lower()
        self.strip=ptsp01_push(host,port,password)
        self.outlets=[
            OutletDevice(1,self._id+"_1",self),
            OutletDevice(2,self._id+"_2",self),
            OutletDevice(3,self._id+"_3",self)
        ]
        self.strip.outlets=self.outlets
        self.strip.start_polling()
    @property
    def firmware_version(self):
        return self.strip.version
    async def setup(self):
        self.strip.connect()
        self.strip.waitForLogin()
    @property
    def online(self):
        return self.strip.isLoggedin()==True
    @property
    def hub_id(self) -> str:
        """ID for hub."""
        return self._id

    async def test_connection(self) -> int:
        """Test connectivity to the hub is OK."""
        try:
            self.strip.connect()
            return 1 if self.strip.waitForLogin() else 3
        except ConnectionError:
            return 2
class ptsp01_push(ptsp01):
    outlets:list[OutletDevice]
    def onStatusUpdate(self,socket:int,key:str):
        outlet=self.outlets[socket-1]
        # _LOGGER.warning(f"%s,Sensor:%s",socket,key)
        if key==("Switch"):
            outlet.switch.async_write_ha_state()
        elif key==("Voltage"):
            outlet.voltage_sensor.async_write_ha_state()
        elif key==("Current"):
            outlet.current_sensor.async_write_ha_state()
        elif key==("Power"):
            outlet.power_sensor.async_write_ha_state()
        elif key==("Energy"):
            outlet.energy_sensor.async_write_ha_state()
    def switch(self, socket: int, switch: int):
        super().switch(socket, switch)
        self.getSwitch(socket)
    def onException(self,exception:Exception):
        _LOGGER.error("Exception:%s",traceback.format_exc())
    def onLoginFailure(self):
        raise ConfigEntryAuthFailed
    def onConnectionFailure(self,e):
        _LOGGER.error("Connection Failed:%s",traceback.format_exc())
        super().onConnectionFailure(e)
        # raise ConnectionError
class OutletDevice:
    _state=None
    switch: SwitchEntity
    voltage_sensor:SensorEntity
    current_sensor:SensorEntity
    power_sensor:SensorEntity
    energy_sensor:SensorEntity
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
        """Return true if the outlet is on."""
        return self._strip.states[self._socket].switch

    def turn_on(self, **kwargs: Any) -> None:
        self._strip.switch(self._socket,1)
        self._state=True

    def turn_off(self, **kwargs: Any) -> None:
        self._strip.switch(self._socket,0)
        self._state=False


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
        return self._strip.getCurrent(self._socket)
    @property
    def power(self) -> float:
        return self._strip.getPower(self._socket)
    @property
    def energy(self) -> float:
        return self._strip.getEnergy(self._socket)

