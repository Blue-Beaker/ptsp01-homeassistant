"""A 'hub' representing 3 sockets of the powerstrip to 3 devices."""
from __future__ import annotations
import logging
import asyncio
import time
import traceback
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry,ConfigEntryNotReady,ConfigEntryAuthFailed
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.sensor import SensorEntity
from .ptsp01telnet import ptsp01
from .const import CONF_INTERVAL, CONF_PASS,CONF_HOST,CONF_ID,CONF_PORT

_LOGGER = logging.getLogger(__name__)

class Hub:
    """Treats the powerstrip as a hub."""

    manufacturer = "BoomSense"

    def __init__(self, hass: HomeAssistant, data: dict) -> None:
        """Init powerstrip as hub."""
        self._host = data[CONF_HOST]
        self._port = data[CONF_PORT]
        self._password = data[CONF_PASS]
        self._interval = data[CONF_INTERVAL] if CONF_INTERVAL in data.keys() else 30
        self._hass = hass
        self._id = data[CONF_ID] if CONF_ID in data.keys() and len(data[CONF_ID])>0 else "ptsp01_"+self._host.lower()
        self._name = self._id
        self.strip=ptsp01_push(self._host,self._port,self._password)
        self.strip.update_interval=self._interval
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
    def onMessage(self, message: str):
        _LOGGER.debug(f"From PTSP01:%s",message)
        return super().onMessage(message)
    def onStatusUpdate(self,socket:int,key:str):
        outlet=self.outlets[socket-1]
        if key==("Switch"):
            outlet.switch.schedule_update_ha_state()
        elif key==("Voltage"):
            outlet.voltage_sensor.schedule_update_ha_state()
        elif key==("Current"):
            outlet.current_sensor.schedule_update_ha_state()
        elif key==("Power"):
            outlet.power_sensor.schedule_update_ha_state()
        elif key==("EnergyMeter.SingleCount"):
            outlet.energy_sensor.schedule_update_ha_state()
    def switch(self, socket: int, switch: int):
        super().switch(socket, switch)
        self.getSwitch(socket)
    def onException(self,exception:Exception):
        _LOGGER.error("Exception:%s",traceback.format_exc())
    def onLoginFailure(self):
        super().onLoginFailure()
        raise ConfigEntryAuthFailed(f"Cant login to {self.host} with given password")
    def onConnectionFailure(self,e):
        _LOGGER.warning("Connection Error:%s",traceback.format_exc())
        super().onConnectionFailure(e)
        for outlet in self.outlets:
            outlet.switch.schedule_update_ha_state()
            outlet.voltage_sensor.schedule_update_ha_state()
            outlet.current_sensor.schedule_update_ha_state()
            outlet.power_sensor.schedule_update_ha_state()
            outlet.energy_sensor.schedule_update_ha_state()
        self.tryReconnect()
    def tryReconnect(self):
        connected=False
        while(not connected):
            try:
                self.closeConnection()
                self.connect()
                connected=self.waitForLogin()
                if not connected:
                    _LOGGER.warning("Reconnect Failed, retrying in %s seconds", 20)
                    time.sleep(20)
            except:
                _LOGGER.warning("Reconnect Failed:%s, retrying in %s seconds",traceback.format_exc(), 20)
                time.sleep(20)
        # raise ConnectionError
    def logMessage(self, *values):
        _LOGGER.warning("%s",values.__str__())
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
        """Register callback."""
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

