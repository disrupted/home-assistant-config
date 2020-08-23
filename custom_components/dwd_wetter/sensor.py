"""Platform for sensor integration."""
import logging
from datetime import datetime, timedelta
import voluptuous as vol
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_FRIENDLY_NAME,
    CONF_NAME,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
)
from homeassistant.util import Throttle
import requests

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "DWD Wetter"
ATTRIBUTION = "Weather Data provided by DWD"

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=60)

SENSOR_TYPES = {
    "temperature": [
        "Temperature",
        TEMP_CELSIUS,
        "mdi:thermometer",
        DEVICE_CLASS_TEMPERATURE,
    ],
    "precipitation": ["Precipitation", "mm", "mdi:weather-rainy", None],
    "pressure": ["Pressure", "hPa", "mdi:gauge", DEVICE_CLASS_PRESSURE],
    "windspeed": ["Wind Speed", "km/h", "mdi:weather-windy", None],
    "windbearing": ["Wind Bearing", "°", "mdi:compass-outline", None],
    "sunshine": ["Sunshine", "min", "mdi:weather-sunny", None],
}
# {"timestamp":"2020-05-22T19:00:00+02:00","source_id":2013,"precipitation":0.0,"pressure_msl":1019.3,"sunshine":9.0,"temperature":20.6,"wind_direction":147,"wind_speed":16.7}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    name = config.get(CONF_NAME)

    dwd_object = DWDWetter()
    entity_list = []
    for sensor_type in SENSOR_TYPES:
        entity_list.append(DWDWetterSensor(name, sensor_type, dwd_object))

    add_entities(entity_list, True)


class DWDWetter:
    """Get the latest data from DWD weather station."""

    def __init__(self):
        """Initialize the data object."""
        self.data = {
            "temperature": None,
            "precipitation": None,
            "pressure": None,
            "windspeed": None,
            "windbearing": None,
            "sunshine": None,
        }

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from DWD weather station."""
        date = datetime.now().astimezone().replace(minute=0).isoformat("T", "minutes")
        response = requests.get(
            url="https://api.brightsky.dev/weather",
            params={"station_id": "10384", "date": date, "last_date": date},
        )
        data = response.json()
        current = data["weather"][0]
        self.data["temperature"] = current.get("temperature")
        self.data["precipitation"] = current.get("precipitation")
        self.data["pressure"] = current.get("pressure_msl")
        self.data["windspeed"] = current.get("wind_speed")
        self.data["windbearing"] = current.get("wind_direction")
        self.data["sunshine"] = int(current.get("sunshine"))
        # for i, key in enumerate(self.data):
        #     self.data[key] = data["Values"][i + 12]["Values"][0]


class DWDWetterSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, client_name, sensor_type, dwd_object):
        """Initialize the sensor."""
        self._sensor = sensor_type
        self._unit_of_measurement = SENSOR_TYPES[self._sensor][1]
        self._state = None
        self._name = f"{client_name} {SENSOR_TYPES[self._sensor][0]}"
        self.dwd_object = dwd_object

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
        self.dwd_object.update()
        self._state = self.dwd_object.data[self._sensor]
