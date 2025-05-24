"""Ability to get / set hass state of an entity."""

from collections.abc import Callable
import logging
import threading
from typing import Any

from homeassistant.core import Event, EventStateChangedData, HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

from ...attributes.base import Attr  # noqa: TID252

_LOGGER = logging.getLogger(__name__)


class StateAbility:
    """Ability to get / set hass state of an entity."""

    # ===== Initalization and validation =====

    def __init__(
            self,
            hass: HomeAssistant,
            entity_id: str,
            translate_state_method: Callable[[dict[str, Any]], dict[str, Attr]],
            update_method: Callable[[dict[str, Attr]], None],
    ) -> None:
        """Initialize the state ability."""
        # Initialize local variables
        self._hass = hass
        self._translate_state_method = translate_state_method
        self._update_method = update_method

        self._entity_id = entity_id # Entity exists.

        # This entity state
        self._state_lock = threading.RLock()
        self._current_state: dict[str, Attr] = self.__get_state()

        # Set up the state listener
        self._unsub_state_listener = async_track_state_change_event(
            hass, [entity_id], self._handle_state_change_event
        )

    # ===== HASS State management =====

    def _handle_state_change_event(self, event: Event[EventStateChangedData]) -> None:
        """Handle hass state change event."""
        # Check some stuff..
        if event.data["new_state"] is None:
            _LOGGER.warning(
                "Entity '%s's new state is None",
                event.data["entity_id"],
            )
            return
        if event.data["old_state"] is None:
            _LOGGER.warning(
                "Entity '%s's old state is None",
                event.data["entity_id"],
            )
            return

        # Translate the state
        translated_state = self._translate_state_method(
            event.data["new_state"].attributes) # type: ignore[]
        # Update the current state
        with self._state_lock:
            # Update the current state
            self._current_state = translated_state

        # TODO: Ce nism js spremenil, more it v custom scene.

    # ===== IDK =====
    def update(self, new_state: dict[str, Attr]) -> None:
        """Updates the entity if an update is needed."""
        # Sends this update to the appropreate class
    # ===== Helpers =====

    def __get_state(self) -> dict[str, Attr]:
        """Get the current state of the entity from Home Assistant."""
        state = self._hass.states.get(self._entity_id)
        if not state:
            _LOGGER.warning("Entity '%s' not found in Home Assistant", self._entity_id)
            return {}

        # Extract relevant attributes
        return self._translate_state_method(state.attributes) # type: ignore[]
