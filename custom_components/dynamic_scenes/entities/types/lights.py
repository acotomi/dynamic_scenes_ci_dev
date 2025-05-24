# Specific entity type implementations


class LightEntity(Entity):
    """Base class for light entities."""

    _SUPPORTED_ATTRIBUTES = [ATTR_BRIGHTNESS]

    async def update(self, time: None | int = None) -> None:
        """Apply the calculated state to the light entity."""

        state = self._get_wanted_state(time)

        state = {attr.hass_name: attr.value for attr in state.values()}

        try:
            self._set_last_state(state)
            await self._hass.services.async_call(
                domain="light",
                service="turn_on",
                service_data={"entity_id": self._entity_id, **state},
            )
        except Exception as e:
            _LOGGER.error(
                "Failed to apply state to light entity '%s': %s", self._entity_id, e
            )


class WWLightEntity(LightEntity):
    """Light entity that supports color temperature."""

    _SUPPORTED_ATTRIBUTES = [ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN]

    # update() is inherited from LightEntity


def entity_factory(
    hass: HomeAssistant, entity_id: str, scenes: list[EntityScene]
) -> Entity:
    """Create an appropriate entity instance based on the entity type and capabilities.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to create an instance for
        scenes: List of scenes available for this entity

    Returns:
        Entity instance appropriate for the entity type

    Raises:
        ValueError: If the entity type is not supported

    """
    # Get the entity state from Home Assistant
    _LOGGER.debug("Creating entity for %s", entity_id)
    state = hass.states.get(entity_id)
    if not state:
        _LOGGER.error("Entity '%s' not found in Home Assistant", entity_id)
        raise ValueError(f"Entity {entity_id} not found")

    domain = entity_id.split(".")[0]

    # Light entities
    if domain == DOMAIN_LIGHT:
        # Check supported features
        supported_color_modes = state.attributes.get("supported_color_modes", [])

        # White light with color temperature
        if LIGHT_COLOR_MODE_COLOR_TEMP in supported_color_modes:
            return WWLightEntity(hass, entity_id, scenes)

        # Basic light
        return LightEntity(hass, entity_id, scenes)

    # Add other domains here

    # Unsupported domain
    raise ValueError(f"Unsupported entity domain: {domain}")
