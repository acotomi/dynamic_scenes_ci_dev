"""Ability to get and use ha state of an entity."""

from collections.abc import Callable
import logging
import threading
from typing import Any

from homeassistant.core import Event, EventStateChangedData, HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

from ...attributes.base import Attr  # noqa: TID252

_LOGGER = logging.getLogger(__name__)

class StateAbility:
    """Ability to get and use Home Assistant state of an entity."""

    # ===== Initalization and delition =====

    def __init__(
            self,
            hass: HomeAssistant,
            entity_id: str,
            translate_state_method: Callable[[dict[str, Any]], dict[str, Attr]],
            external_state_change_callback: Callable[[dict[str, Attr]], None],
    ) -> None:
        """Initialize the state ability."""
        # Initialize local variables
        self._hass = hass
        self._translate_state_method = translate_state_method
        self._external_state_change_callback = external_state_change_callback

        self._entity_id = entity_id # Entity exists.

        # This entity state
        self._state_lock = threading.RLock()
        self._internal_state_change = False
        self._current_state: dict[str, Attr] = self.__get_state()

        # Set up the state listener
        self._unsub_state_listener = async_track_state_change_event(
            hass, [entity_id], self._handle_state_change_event
        )

    def __del__(self) -> None:
        """Clean up the state ability."""
        self._unsub_state_listener()
        _LOGGER.debug("Unsubscribed from state change events for entity '%s'", self._entity_id)

    # ===== HASS State updates =====

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

            # Check if the state change was internal
            if self._internal_state_change:
                _LOGGER.debug(
                    "Internal state change for entity '%s': %s",
                    self._entity_id,
                    self._current_state,
                )
                return # Ignore internal state changes

            # Check if the state has changed
            if not self.has_changed(translated_state):
                _LOGGER.debug(
                    "State of entity '%s' has not changed, ignoring event",
                    self._entity_id,
                )
                return  # No change, nothing to do

            # State has changed.
            _LOGGER.info(
                "Entity '%s' state changed: %s",
                event.data["entity_id"],
                translated_state,
            )
            self._external_state_change_callback(self._current_state)

    # ===== Methods =====

    def has_changed(self, new_state: dict[str, Attr]) -> bool:
        """Check if the state is different from the current hass state."""
        with self._state_lock:
            # Compare the new state with the current state
            if len(new_state) != len(self._current_state):
                return True

            for key, value in new_state.items():
                if key not in self._current_state or self._current_state[key] != value:
                    return True

        return False

    def with_internal_state_change(self, state_change_func: Callable[[], None]) -> None:
        """Tells the state ability that the next state change will be internal.

        Call this method with the function that will change the HA state immediately after!
        """
        with self._state_lock:
            self._internal_state_change = True
            try:
                state_change_func()
            finally:
                self._internal_state_change = False

    # ===== Helpers =====

    def __get_state(self) -> dict[str, Attr]:
        """Get the current state of the entity from Home Assistant."""
        state = self._hass.states.get(self._entity_id)
        if not state:
            _LOGGER.warning("Entity '%s' not found in Home Assistant", self._entity_id)
            return {}

        # Extract relevant attributes
        return self._translate_state_method(state.attributes) # type: ignore[]
