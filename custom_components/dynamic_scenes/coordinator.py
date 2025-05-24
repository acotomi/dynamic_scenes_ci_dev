"""Main coordinator for the integration."""

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .constants import INTEGRATION_DOMAIN as DOMAIN
from .entities.entity import Entity

_LOGGER = logging.getLogger(__name__)


class Coordinator(DataUpdateCoordinator):
    """Coordinates all the things in the integration."""

    def __init__(
        self, hass: HomeAssistant, rerun_interval: int, entities: dict[str, Entity]
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Dynamic Scenes",
            update_interval=timedelta(
                seconds=rerun_interval
            ),  # Set the update interval
        )

        self.__entities = entities
        self._unsub_timer = None
        self._unsub_state_listener = None
        _LOGGER.debug("Coordinator initialized")

    @property
    def _entities(self) -> list[Entity]:
        """Get the entities."""
        return self.__entities.values()

    async def async_setup(self) -> callable:
        """Set up the coordinator."""
        # Set up the coordinator
        self._unsub_state_listener = async_track_state_change_event(
            self.hass, list(self.__entities.keys()), self._handle_state_change
        )

        # Set up periodic update timer
        self._unsub_timer = async_track_time_interval(
            self.hass, self._handle_time_update, timedelta(seconds=30)
        )
        _LOGGER.debug("Coordinator setup complete")
        return self.async_shutdown()

    async def async_shutdown(self):
        """Shut down the coordinator."""
        if self._unsub_state_listener:
            self._unsub_state_listener()
            self._unsub_state_listener = None

        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        _LOGGER.debug("Coordinator shutdown complete")

    def _get_entity(self, entity_id: str) -> Entity | None:
        """Get an entity by its ID."""
        entity = self.__entities.get(entity_id)
        if entity is None:
            _LOGGER.error("Entity %s not found in the coordinator", entity_id)
            return None
        return entity

    # ===== Called by Home Assistant =====

    @callback
    def _handle_state_change(self, event):
        """Handle state changes from Home Assistant."""
        # Get the entity
        entity = self._get_entity(event.data["entity_id"])

        _LOGGER.debug("State change, setting entity to custom: %s", event.data)
        entity.custom_active()

    @callback
    async def _handle_time_update(self, now):
        """Handle periodic time updates."""
        _LOGGER.debug("Periodic update triggered at %s", now)
        await self._update_entities()

    # ===== Called by services =====

    # Scenes

    async def set_scene_condition_met(self, entity_ids: list[str], scene: str) -> None:
        """Set scene of entites to active, updates entities if needed."""
        _LOGGER.debug("Setting scene %s to active for entities: %s", scene, entity_ids)

        update_needed = []
        for entity_id in entity_ids:
            # Get the entity
            entity = self._get_entity(entity_id)

            # Set scene confition to met
            if entity.activate_scene(scene):
                # If the scene is the highest priority active scene, update the entity
                update_needed.append(entity_id)
            _LOGGER.debug("Set scene %s of entity %s", scene, entity_id)

        if update_needed:
            # If the scene is the highest priority active scene, update the entities
            await self._update_entities(update_needed)

    async def unset_scene_condition_met(self, entity_ids: list[str], scene: str) -> None:
        """Set scene of entites to inactive, updates entities if needed."""
        _LOGGER.debug(
            "Setting scene %s to inactive for entities: %s", scene, entity_ids
        )

        update_needed = []
        for entity_id in entity_ids:
            # Get the entity
            entity = self._get_entity(entity_id)

            # Set scene confition to not met
            if entity.deactivate_scene(scene):
                # If the scene is the highest priority active scene, update the entity
                update_needed.append(entity_id)
            _LOGGER.debug("Unset scene %s of entity %s", scene, entity_id)

        if update_needed:
            # If the scene is the highest priority active scene, update the entities
            await self._update_entities(update_needed)

    async def reset_custom_scene(self, entity_ids: list[str]) -> None:
        """Reset the scene of entities from custom, updates entities."""
        _LOGGER.debug("Resetting custom scene for entities: %s", entity_ids)
        for entity_id in entity_ids:
            # Get the entity
            entity = self._get_entity(entity_id)

            # Reset the scene
            entity.custom_inactive()
            _LOGGER.debug("Reset custom scene of entity %s", entity_id)

        # Update the entities
        await self._update_entities(entity_ids)

    # Timeshifts

    async def set_timeshift(self, entity_ids: list[str], timeshift: int) -> None:
        """Set the timeshift of entities."""
        _LOGGER.debug("Setting timeshift %s for entities: %s", timeshift, entity_ids)

        for entity_id in entity_ids:
            # Get the entity
            entity = self._get_entity(entity_id)

            # Set the timeshift
            entity.set_timeshift(timeshift)
            _LOGGER.debug("Set timeshift %s of entity %s", timeshift, entity_id)

        # Update the entities
        await self._update_entities(entity_ids)

    async def shift_time(self, entity_ids: list[str], timeshift: int) -> None:
        """Shift the timeshift of entities."""
        _LOGGER.debug("Shifting timeshift %s for entities: %s", timeshift, entity_ids)

        for entity_id in entity_ids:
            # Get the entity
            entity = self._get_entity(entity_id)

            # Shift the timeshift
            entity.shift_time(timeshift)
            _LOGGER.debug("Shifted timeshift %s of entity %s", timeshift, entity_id)

        # Update the entities
        await self._update_entities(entity_ids)

    # ===== Methods =====

    async def _update_entities(self, entity_ids: None | list[str] = None) -> None:
        """Update the entities to their current wanted state."""
        if entity_ids is None:
            entities = self._entities
        else:
            entities = [self._get_entity(entity_id) for entity_id in entity_ids]

        for entity in entities:
            # Update the entity
            await entity.update_if_needed()
