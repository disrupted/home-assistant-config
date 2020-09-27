"""Config flow for Coronavirus integration."""
import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (  # pylint: disable=unused-import
    CONF_DISABLE_ENTITY,
    CONF_LIGHTS,
    CONF_SLEEP_ENTITY,
    DOMAIN,
    EXTRA_VALIDATION,
    NONE_STR,
    VALIDATION_TUPLES,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Adaptive Lighting."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input["name"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("name"): str}),
            errors=errors,
        )

    async def async_step_import(self, user_input=None):
        """Handle configuration by yaml file."""
        await self.async_set_unique_id(user_input["name"])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=user_input["name"], data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


def validate_options(user_input, errors):
    """Validate the options in the OptionsFlow.

    This is an extra validation step because the validators
    in `EXTRA_VALIDATION` cannot be serialized to json.
    """
    for key, (validate, _) in EXTRA_VALIDATION.items():
        # these are unserializable validators
        try:
            value = user_input.get(key)
            if value is not None and value != NONE_STR:
                validate(value)
        except vol.Invalid:
            _LOGGER.exception("Configuration option %s=%s is incorrect", key, value)
            errors["base"] = "option_error"


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Adaptive Lighting."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        conf = self.config_entry
        if conf.source == config_entries.SOURCE_IMPORT:
            return self.async_show_form(step_id="init", data_schema={})
        errors = {}
        if user_input is not None:
            validate_options(user_input, errors)
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        all_lights = sorted(self.hass.states.async_entity_ids("light"))
        all_entities = sorted(self.hass.states.async_entity_ids())
        to_replace = {
            CONF_LIGHTS: cv.multi_select(all_lights),
            CONF_DISABLE_ENTITY: vol.In([NONE_STR] + all_entities),
            CONF_SLEEP_ENTITY: vol.In([NONE_STR] + all_entities),
        }

        options_schema = {}
        for name, default, validation in VALIDATION_TUPLES:
            key = vol.Optional(name, default=conf.options.get(name, default))
            value = to_replace.get(name, validation)
            options_schema[key] = value

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(options_schema), errors=errors
        )
