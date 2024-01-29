"""Config flow for Hello World integration."""
from __future__ import annotations

import logging
from typing import Any, Callable

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant

from .const import CONF_INTERVAL, DOMAIN,CONF_PORT,CONF_HOST,CONF_ID,CONF_PASS
from .hub import Hub

_LOGGER = logging.getLogger(__name__)

# This is the schema that used to display the UI to the user. This simple
# schema has a single required host field, but it could include a number of fields
# such as username, password etc. See other components in the HA core code for
# further examples.
# Note the input displayed to the user will be translated. See the
# translations/<lang>.json file and strings.json. See here for further information:
# https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#translations
# At the time of writing I found the translations created by the scaffold didn't
# quite work as documented and always gave me the "Lokalise key references" string
# (in square brackets), rather than the actual translated value. I did not attempt to
# figure this out or look further into it.
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Optional(CONF_PORT,default=23): int,
    vol.Optional(CONF_PASS,default=''): str,
    vol.Optional(CONF_ID,default=''): str,
    vol.Optional(CONF_INTERVAL,default=30): int,})


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    hub = Hub(hass, data)
    result = await hub.test_connection()
    if result==2:
        raise InvalidAuth
    elif result==3:
        raise CannotConnect

    return {CONF_HOST: data[CONF_HOST], CONF_PORT:data[CONF_PORT], CONF_PASS:data[CONF_PASS],CONF_ID:data[CONF_ID],CONF_INTERVAL:data[CONF_INTERVAL]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info[CONF_HOST] if info[CONF_ID].__len__()==0 else info[CONF_ID], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
