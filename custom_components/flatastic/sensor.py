"""Platform for sensor integration."""
import json
import logging
from datetime import datetime, timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.rest.sensor import RestData
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_FRIENDLY_NAME,
    CONF_NAME,
    DEVICE_CLASS_TIMESTAMP,
)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Flatastic"
ATTRIBUTION = "Data provided by Flatastic"

CONF_API_KEY = "api_key"
CONF_USER_ID = "user_id"

SCAN_INTERVAL = timedelta(minutes=360)

SENSOR_TYPES = {
    "chore": ["Chore", None, "mdi:broom", None],
    "time_remaining": ["Time", "days", "mdi:timer", None],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_USER_ID): cv.positive_int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    api_key = config.get(CONF_API_KEY)
    user_id = config.get(CONF_USER_ID)
    name = config.get(CONF_NAME)

    api = FlatasticAPI(api_key, user_id)
    entity_list = []
    for sensor_type in SENSOR_TYPES:
        entity_list.append(FlatasticSensor(name, sensor_type, api))

    add_entities(entity_list, True)


class FlatasticAPI:
    """Get the latest data from Flatastic API."""

    def __init__(self, api_key, user_id):
        """Initialize the data object."""
        self.user_id = user_id
        self.available = True
        resource = "https://api.flatastic-app.com/index.php/api/chores"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "X-Api-Key": api_key,
            "X-Api-Version": "2.0.0",
        }
        self._rest = RestData("GET", resource, None, headers, None, True)
        self.data = {
            "chore": None,
            "time_remaining": None,
        }
        self.user_chores = []

    @Throttle(SCAN_INTERVAL)
    def update(self):
        """Get the latest data from Flatastic."""
        try:
            self._rest.update()
            self.chores = json.loads(self._rest.data)
            # sort chores by their due date
            self.chores.sort(key=lambda chore: chore["timeLeftNext"])
            for chore in self.chores:
                if chore.get("currentUser") == self.user_id:
                    # self.user_chores.append(chore)
                    self.data["chore"] = chore.get("title")
                    self.data["time_remaining"] = int(chore.get("timeLeftNext") / 86400)
                    break
            # self.data["chore"] = data.get("temperature") / 10
            # self.data["time"] = datetime.fromtimestamp(timestamp / 1000).isoformat()
        except TypeError:
            _LOGGER.error("Unable to fetch data from Flatastic API")
            self.available = False


class FlatasticSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, client_name, sensor_type, flatastic_api):
        """Initialize the sensor."""
        self._sensor = sensor_type
        self._unit_of_measurement = SENSOR_TYPES[self._sensor][1]
        self._icon = SENSOR_TYPES[self._sensor][2]
        self._device_class = SENSOR_TYPES[self._sensor][3]
        self._state = None
        self._name = f"{client_name} {SENSOR_TYPES[self._sensor][0]}"
        self._api = flatastic_api

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return self._icon

    # @property
    # def device_class(self):
    #     """Return the device class of the sensor."""
    #     return self._device_class

    @property
    def available(self):
        """Could the device be accessed during the last update call."""
        return self._api.available

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._api.update()
        self._state = self._api.data[self._sensor]
        # for chore in self._api.chores:
        #     if chore.id == self._api.user_id:
        #         pass
