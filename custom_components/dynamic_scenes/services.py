import logging

from homeassistant.core import HomeAssistant, ServiceCall
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .coordinator import Coordinator

from .constants import (
    DOMAIN,
    ATTR_ENTITY_ID,
    ATTR_SCENE,
    ATTR_TIMESHIFT,
    SERVICE_SET_SCENE_CONDITION_MET,
    SERVICE_UNSET_SCENE_CONDITION_MET,
    SERVICE_RESET_CUSTOM_SCENE,
    SERVICE_SET_TIMESHIFT,
    SERVICE_SHIFT_TIME,
)

_LOGGER = logging.getLogger(__name__)

# Schema definitions for service validation
SCENE_CONDITION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required(ATTR_SCENE): cv.string,
    }
)

RESET_CUSTOM_SCENE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    }
)

TIMESHIFT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required(ATTR_TIMESHIFT): cv.positive_int,
    }
)

RESET_TIMESHIFT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    }
)


async def async_register_services(hass: HomeAssistant, coordinator: Coordinator):
    """Register services for the integration.

    Returns: The function to unregister the services.
    """

    _LOGGER.debug("Registering services")

    # ===== Scenes =====

    async def handle_set_scene_condition_met(call: ServiceCall) -> None:
        """Tells the integration that the conditions for some scene are met."""
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        scene = call.data.get(ATTR_SCENE)
        await coordinator.set_scene_condition_met(entity_ids, scene)

    async def handle_unset_scene_condition_met(call: ServiceCall):
        """Tells the integration that the conditions for some scene are not met anymore."""
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        scene = call.data.get(ATTR_SCENE)
        await coordinator.unset_scene_condition_met(entity_ids, scene)

    async def handle_reset_custom_scene(call: ServiceCall):
        """Reset the scene from custom to the currently active scene."""
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        await coordinator.reset_custom_scene(entity_ids)

    # ===== Timeshifts =====

    async def handle_set_timeshift(call: ServiceCall):
        """Set the timeshift of entities."""
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        timeshift = call.data.get(ATTR_TIMESHIFT)
        await coordinator.set_timeshift(entity_ids, timeshift)

    async def handle_shift_time(call: ServiceCall):
        """Shift the timeshift of entities."""
        entity_ids = call.data.get(ATTR_ENTITY_ID)
        timeshift = call.data.get(ATTR_TIMESHIFT)
        await coordinator.shift_time(entity_ids, timeshift)

    # ===== Register the services =====

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SCENE_CONDITION_MET,
        handle_set_scene_condition_met,
        schema=SCENE_CONDITION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UNSET_SCENE_CONDITION_MET,
        handle_unset_scene_condition_met,
        schema=SCENE_CONDITION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_CUSTOM_SCENE,
        handle_reset_custom_scene,
        schema=RESET_CUSTOM_SCENE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN, SERVICE_SET_TIMESHIFT, handle_set_timeshift, schema=TIMESHIFT_SCHEMA
    )

    hass.services.async_register(
        DOMAIN, SERVICE_SHIFT_TIME, handle_shift_time, schema=TIMESHIFT_SCHEMA
    )

    # Return an unregister function
    return lambda: unregister_services(hass)


def unregister_services(hass: HomeAssistant):
    """Unregister services."""
    hass.services.async_remove(DOMAIN, SERVICE_SET_SCENE_CONDITION_MET)
    hass.services.async_remove(DOMAIN, SERVICE_UNSET_SCENE_CONDITION_MET)
    hass.services.async_remove(DOMAIN, SERVICE_RESET_CUSTOM_SCENE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_TIMESHIFT)
    hass.services.async_remove(DOMAIN, SERVICE_SHIFT_TIME)
