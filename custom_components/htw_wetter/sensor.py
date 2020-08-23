"""Platform for sensor integration."""
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (ATTR_ATTRIBUTION, ATTR_FRIENDLY_NAME,
                                 CONF_NAME, DEVICE_CLASS_HUMIDITY,
                                 DEVICE_CLASS_PRESSURE,
                                 DEVICE_CLASS_TEMPERATURE, TEMP_CELSIUS)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

DEFAULT_NAME = "HTW Wetter"
ATTRIBUTION = "Weather Data provided by HTW Berlin"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)  # timedelta(seconds=60)

SENSOR_TYPES = {
    "temperature": [
        "Temperature",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
    ],
    "pressure": ["Pressure", "hPa", "mdi:gauge", DEVICE_CLASS_PRESSURE],
    "humidity": ["Humidity", "%", "mdi:water-percent", DEVICE_CLASS_HUMIDITY],
    "windspeed": ["Wind Speed", "m/s", "mdi:weather-windy", None],
    "windbearing": ["Wind Bearing", "°", "mdi:compass-outline", None],
    "solarrad": ["Solar Radiation", "W/m2", "mdi:weather-sunny", None],
}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    name = config.get(CONF_NAME)

    htw_object = HTWWetter()
    entity_list = []
    for sensor_type in SENSOR_TYPES:
        entity_list.append(HTWWetterSensor(name, sensor_type, htw_object))

    add_entities(entity_list, True)


class HTWWetter:
    """Get the latest data from HTW weather station."""

    def __init__(self):
        """Initialize the data object."""
        self.data = {
            "temperature": None,
            "pressure": None,
            "humidity": None,
            "windspeed": None,
            "windbearing": None,
            "solarrad": None,
        }

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from HTW weather station."""
        response = requests.get(url="https://wetter.htw-berlin.de/api/read/now")
        data = response.json()
        self.data["temperature"] = data["Values"][12]["Values"][0]
        self.data["pressure"] = data["Values"][13]["Values"][0]
        self.data["humidity"] = data["Values"][14]["Values"][0]
        self.data["windspeed"] = data["Values"][15]["Values"][0]
        self.data["windbearing"] = int(data["Values"][16]["Values"][0])
        self.data["solarrad"] = int(data["Values"][0]["Values"][0])
        # for i, key in enumerate(self.data):
        #     self.data[key] = data["Values"][i + 12]["Values"][0]


class HTWWetterSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, client_name, sensor_type, htw_object):
        """Initialize the sensor."""
        self._sensor = sensor_type
        self._unit_of_measurement = SENSOR_TYPES[self._sensor][1]
        self._state = None
        self._name = f"{client_name} {SENSOR_TYPES[self._sensor][0]}"
        self.htw_object = htw_object

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
        return SENSOR_TYPES[self._sensor][1]

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return SENSOR_TYPES[self._sensor][2]

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SENSOR_TYPES[self._sensor][3]

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.htw_object.update()
        self._state = self.htw_object.data[self._sensor]
