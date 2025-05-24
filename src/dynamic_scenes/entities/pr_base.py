"""Base ENTITIES class."""
from homeassistant.core import HomeAssistant

class Entity:
    """Base class for all entities that can have dynamic scenes."""

    # Define supported attributes in subclasses
    _SUPPORTED_ATTRIBUTES: list[str] = []

    def __init__(
        self, hass: HomeAssistant, entity_id: str, scenes: list[EntityScene]
    ) -> None:
        """Initialize the entity.

        Args:
            hass: Home Assistant instance
            entity_id: The entity ID in Home Assistant
            scenes: List of all scenes available for this entity

        """
        self._hass = hass
        self._entity_id = entity_id

        # Create components using composition
        self._timeshift = Timeshift()
        self._scenes = Scene(entity_id, scenes, self._SUPPORTED_ATTRIBUTES)

        # Track the last state we set
        self._last_state: dict[str, Any] = {}

    @property
    def entity_id(self) -> str:
        """Get the entity ID."""
        return self._entity_id

    # ===== Current state methods =====

    def _get_ha_state(self) -> dict[str, Attr]:
        """Get the current state of the entity from Home Assistant."""
        state = self._hass.states.get(self._entity_id)
        if not state:
            _LOGGER.warning("Entity '%s' not found in Home Assistant", self._entity_id)
            return {}

        # Extract relevant attributes
        result = {}
        for attr_name in self._SUPPORTED_ATTRIBUTES:
            if attr_name in state.attributes:
                result[attr_name] = attr_factory(attr_name, state.attributes[attr_name])
            else:
                _LOGGER.warning(
                    "Attribute '%s' not found in state for entity '%s'",
                    attr_name,
                    self._entity_id,
                )

        return result

    def _get_wanted_state(self, time=None) -> dict[str, Attr]:
        """Calculate the current state for this entity based on active scenes and time.

        This method considers:
        - Which scene is currently active (based on priority)
        - Current time (with timeshift applied)
        - Custom state (if active)

        Returns:
            Dict with the calculated state attributes

        """
        # If custom state is active, use that
        if self._scenes.is_custom_active:
            return self._scenes.custom_state

        # Otherwise, get the highest priority active scene
        active_scene = self._scenes.current_scene

        # Get current time (adjusted for timeshift)
        if time is not None:
            # If a specific time is provided, use that
            shifted_seconds = time
        else:
            # Get the current time and apply timeshift
            now = datetime.now().time()
            current_seconds = now.hour * 3600 + now.minute * 60 + now.second
            shifted_seconds = self._timeshift.apply(current_seconds)

        # Get the scene state at the current time
        return active_scene.get_attrs_at_time(shifted_seconds)

    def _has_changed(self) -> bool:
        """Check if the entity needs an update based on calculated state vs current HA state."""
        calculated_state = self._get_wanted_state()
        current_state = self._get_ha_state()

        # Compare relevant attributes
        for attr in self._SUPPORTED_ATTRIBUTES:
            if attr in calculated_state and (
                attr not in current_state
                or calculated_state[attr] != current_state[attr]
            ):
                _LOGGER.debug(
                    "Entity '%s's attribute %s changed: %s != %s",
                    self._entity_id,
                    attr,
                    calculated_state[attr].value,
                    current_state.get(attr).value,
                )
                return True

        return False

    # ===== Public methods =====

    # Timeshift methods
    def set_timeshift(self, timeshift: int) -> None:
        """Set the timeshift for this entity."""
        self._timeshift.set(timeshift)

    def shift_time(self, timeshift: int) -> None:
        """Shift the timeshift for this entity."""
        self._timeshift.shift(timeshift)

    # Scene passthrough methods

    def custom_active(self) -> None:
        """Set the custom scene to active."""
        self._scenes.set_custom_active(self._get_ha_state())

    def custom_inactive(self) -> None:
        """Set the custom scene to inactive."""
        self._scenes.set_custom_inactive()

    def activate_scene(self, scene_name: str) -> bool:
        """Activate a scene for this entity."""
        return self._scenes.activate_scene(scene_name)

    def deactivate_scene(self, scene_name: str) -> bool:
        """Deactivate a scene for this entity."""
        return self._scenes.deactivate_scene(scene_name)

    # Updates methods

    def get_update_command(self, time: None | int = None) -> callable:
        """Get the command to update the entity state to the current wanted state.

        Returns:
            None if no update is needed, otherwise a callable to apply the state.

        """
        if self._has_changed():
            return lambda: self.update(time)
        return None

    async def update_if_needed(self, time: None | int = None) -> None:
        """Update the entity if needed."""
        if self._has_changed() and not self._scenes.is_custom_active:
            await self.update(time)
        else:
            _LOGGER.debug(
                "No update needed for entity '%s' (custom state: %s)",
                self._entity_id,
                self._scenes.is_custom_active,
            )

    async def update(self, time: None | int = None) -> None:
        """Apply the calculated state to the entity in Home Assistant."""
        _LOGGER.error("apply_state() not implemented for entity '%s'", self._entity_id)
