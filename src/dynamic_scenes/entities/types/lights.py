"""Light entity types."""

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from ...attributes.types import Brightness, ColorTemp, LightState  # noqa: TID252
from ...constants import SERVICECALLS  # noqa: TID252
from .. import Entity  # noqa: TID252

if TYPE_CHECKING:
    from attributes import Attr

_LOGGER = logging.getLogger(__name__)


class Light(Entity):
    """A light entity."""

    SUPPORTED_ATTRIBUTES = {Brightness, LightState}

    DOMAIN = "light"

    @classmethod
    def supports(cls, domain: str, attributes: dict[str, Any]) -> bool:
        """Check if the entity is a light without color / color temperature."""
        _LOGGER.debug("Checking if domain %s, attributes %s is light entity.", domain, attributes)

        if domain != cls.DOMAIN:
            _LOGGER.debug("Is not, domain missmatch (%s != %s).", domain, cls.DOMAIN)
            return False

        if "brightness" not in attributes:
            _LOGGER.debug("Is not, missing brightness attribute.")
            return False

        if attributes.get("supported_color_modes"): # IS NOT empty or None
            _LOGGER.debug("Is not, supports_color_modes.")
            return False

        _LOGGER.debug("Is a light entity.")
        return True

    async def _set_entity_state(self, state: dict[type['Attr'], 'Attr']) -> None:
        """Call the light.turn_on or light.turn_off service."""
        if (state.get(LightState) is None or state[LightState] == "on"):
            # If state is None or "on", turn on the light
            kwargs = {
                attr_type.HASS_NAME: attr.value for attr_type, attr in state.items()
                if attr_type != LightState
            }
            _LOGGER.debug("Turning on light %s with attributes: %s", self.entity_id, kwargs)
            #kwargs[SERVICECALLS.ENTITY_ID] = self.entity_id
            # TODO: TEMPORARY FIX: Template lights only change one attribute at a time.
            for kwarg, data in kwargs.items():
                await asyncio.sleep(0.1)  # Avoid flooding the service call
                await self._hass.services.async_call(
                    self.DOMAIN, "turn_on",
                    {SERVICECALLS.ENTITY_ID: self.entity_id, kwarg: data}
                )
        else:
            # If state is "off", turn off the light
            _LOGGER.debug("Turning off light %s", self.entity_id)
            await self._hass.services.async_call(self.DOMAIN, "turn_off",
                                     {SERVICECALLS.ENTITY_ID: self.entity_id}
            )
            # TODO: Add transition!

class WWLight(Light):
    """A light that supports color temperature."""

    SUPPORTED_ATTRIBUTES = {Brightness, LightState, ColorTemp}

    DOMAIN = "light"

    @classmethod
    def supports(cls, domain: str, attributes: dict[str, Any]) -> bool:
        """Check if the entity is a color temperature light."""
        _LOGGER.debug("Checking if domain %s, attributes %s is "
                      "color temperature light entity.", domain, attributes)

        if domain != cls.DOMAIN:
            _LOGGER.debug("Is not, domain missmatch (%s != %s).", domain, cls.DOMAIN)
            return False

        if "brightness" not in attributes:
            _LOGGER.debug("Is not, missing brightness attribute.")
            return False

        if "color_temp" not in attributes:
            _LOGGER.debug("Is not, missing color_temp attribute.")
            return False

        supported_color_modes = attributes.get("supported_color_modes", [])
        if not supported_color_modes or "color_temp" not in supported_color_modes: # Hasnt got / ..
            _LOGGER.debug("Is not, missing color_temp in supported_color_modes.")
            return False

        _LOGGER.debug("Is a color temperature light entity.")
        return True
