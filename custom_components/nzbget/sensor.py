"""Monitor the NZBGet API."""
import logging

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from . import DATA_NZBGET, DATA_UPDATED, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "NZBGet"


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Create NZBGet sensors."""

    if discovery_info is None:
        return

    nzbget_data = hass.data[DATA_NZBGET]
    name = discovery_info["client_name"]

    devices = []
    for sensor_config in discovery_info["monitored_variables"]:
        new_sensor = NZBGetSensor(
            nzbget_data,
            SENSOR_TYPES[sensor_config][0],
            name,
            SENSOR_TYPES[sensor_config][1],
            SENSOR_TYPES[sensor_config][2],
        )
        devices.append(new_sensor)

    add_entities(devices, True)


class NZBGetSensor(Entity):
    """Representation of a NZBGet sensor."""

    def __init__(
        self, nzbget_data, sensor_type, client_name, sensor_name, unit_of_measurement
    ):
        """Initialize a new NZBGet sensor."""
        self._name = f"{client_name} {sensor_name}"
        self.type = sensor_type
        self.client_name = client_name
        self.nzbget_data = nzbget_data
        self._state = None
        self._unit_of_measurement = unit_of_measurement

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
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def available(self):
        """Return whether the sensor is available."""
        return self.nzbget_data.available

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, DATA_UPDATED, self._schedule_immediate_update
            )
        )

    @callback
    def _schedule_immediate_update(self):
        self.async_schedule_update_ha_state(True)

    def update(self):
        """Update state of sensor."""

        if self.nzbget_data.status is None:
            _LOGGER.debug(
                "Update of %s requested, but no status is available", self._name
            )
            return

        value = self.nzbget_data.status.get(self.type)
        if value is None:
            _LOGGER.warning("Unable to locate value for %s", self.type)
            return

        if "DownloadRate" in self.type and value > 0:
            # Convert download rate from Bytes/s to MBytes/s
            self._state = round(value / 2 ** 20, 2)
        elif "UpTimeSec" in self.type and value > 0:
            # Convert uptime from seconds to minutes
            self._state = round(value / 60, 2)
        else:
            self._state = value
