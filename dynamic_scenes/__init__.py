"""The Dynamic Scenes integration."""

from __future__ import annotations
import asyncio

import logging
from pathlib import Path
from typing import Any, Callable

import voluptuous as vol
import yaml
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .coordinator import Coordinator
from .entity.entity import entity_factory, Entity
from .scenes.old_ent_sc import AttrScene, EntityScene
from .services import async_register_services
from .constants import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_ENTITIES,
    ATTR_PRIORITY,
    ATTR_TIMES,
    ATTR_XY_BRIGHTNESS,
    ATTR_XY_COLOR,
    DOMAIN,
    DATA_ENTITIES,
    DATA_RERUN_INTERVAL,
    SCENES_FILE,
)

_LOGGER = logging.getLogger(__name__)

# Schema for validating scene configurations
ENTITY_ATTRIBUTES_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITIES): cv.ensure_list(cv.entity_id),
        vol.Optional(ATTR_BRIGHTNESS): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
        vol.Optional(ATTR_COLOR_TEMP_KELVIN): vol.All(
            vol.Coerce(int), vol.Range(min=2000, max=6000)
        ),
        vol.Optional(ATTR_XY_BRIGHTNESS): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=255)
        ),
        vol.Optional(ATTR_XY_COLOR): vol.All(
            vol.Length(min=2, max=2),
            [vol.All(vol.Coerce(float), vol.Range(min=0, max=1))],
        ),
    }
)

TIME_ENTRIES_SCHEMA = vol.Schema([ENTITY_ATTRIBUTES_SCHEMA])

SCENE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PRIORITY): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=255)
        ),
        vol.Required(ATTR_TIMES): {
            str: TIME_ENTRIES_SCHEMA,
        },
    }
)

SCENES_SCHEMA = vol.Schema(
    {
        cv.string: SCENE_SCHEMA,
    }
)


class SceneConfiguration:
    """Handle loading, validation, and conversion of scene configurations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the scene configuration handler."""
        self.hass = hass

    async def load(self, file_path: None | Path = None) -> dict[str, Entity]:
        """Load scene data from YAML and convert to internal format.

        Returns:
            - A dictionary of scenes with entity IDs as keys and their attributes.
            - A list of all entity IDs found in the scenes.

        """
        raw_data = await self._load_yaml(file_path)
        _LOGGER.debug("Loaded scene data: %s", raw_data)
        validated_data = self._validate(raw_data)
        scene_data = self._convert(validated_data)
        _LOGGER.debug("Converted scene data: %s", scene_data)
        return scene_data

    async def _load_yaml(self, file_path: None | Path = None) -> dict[str, Any]:
        """Load the YAML file and return its contents asynchronously."""
        if file_path is None:
            file_path = Path(__file__).parent / SCENES_FILE

        # Check file existence asynchronously
        exists = await self.hass.async_add_executor_job(file_path.exists)
        if not exists:
            raise FileNotFoundError(f"Scene file {file_path} does not exist")

        try:
            # Read and parse YAML file asynchronously
            data = await self.hass.async_add_executor_job(
                self._read_yaml_file, file_path
            )
        except yaml.YAMLError as err:
            raise yaml.YAMLError(f"Invalid YAML format in {file_path}: {err}") from err

        return data

    def _read_yaml_file(self, file_path: Path) -> dict[str, Any]:
        """Read YAML file and return its contents."""
        with file_path.open("r") as f:
            return yaml.safe_load(f)

    def _validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate the scene configuration using voluptuous."""
        try:
            return SCENES_SCHEMA(data)
        except vol.Invalid as err:
            _LOGGER.error("Scene configuration validation failed: %s", err)
            raise ValueError(f"Invalid scene configuration: {err}") from err

    def __parse_time(self, time_str: str) -> int:
        """Parse the time in HH:MM format into seconds since midnight."""
        hours, minutes = map(int, time_str.split(":"))
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError("Hours must be 0-23 and minutes 0-59")
        return hours * 3600 + minutes * 60

    def __create_entity_scenes_attributes_dict(
        self,
        scenes: dict[str, Any],
    ) -> dict[str, dict[str, dict[str, AttrScene]]]:
        """Create a dictionary of entity scenes and their attributes."""
        ents_scens_attrs = {}  # Structure: {entity_id: {scene_id: {attr_id: AttrScene}}}
        validation_errors = []
        for scene_name, scene in scenes.items():
            for time_str, entries in scene[ATTR_TIMES].items():
                try:
                    time_sec = self.__parse_time(time_str)
                except ValueError as err:
                    validation_errors.append(
                        f"Invalid time format in scene {scene_name}: {time_str} - {err}"
                    )
                    continue

                for entry in entries:
                    for ent_id in entry[ATTR_ENTITIES]:
                        # Initialize entity if not already present
                        ents_scens_attrs.setdefault(ent_id, {})
                        # Initialize scene if not already present
                        ents_scens_attrs[ent_id].setdefault(scene_name, {})

                        for attr_name, value in entry.items():
                            if attr_name == ATTR_ENTITIES:
                                continue

                            # Initialize attribute if not already present
                            ents_scens_attrs[ent_id][scene_name].setdefault(
                                attr_name, AttrScene()
                            )
                            # Add attribute to the scene
                            try:
                                ents_scens_attrs[ent_id][scene_name][attr_name].add(
                                    time_sec, attr_name, value
                                )
                            except ValueError as err:
                                validation_errors.append(
                                    f"Invalid attribute {attr_name} for entity {ent_id} in scene {scene_name}: {err}"
                                )
                                continue

        # Check if any validation errors occurred
        if validation_errors:
            raise ValueError("\n".join(validation_errors))

        return ents_scens_attrs

    def __create_entity_scenes_dict(
        self,
        ents_scens_attrs: dict[str, dict[str, dict[str, AttrScene]]],
        scenes: dict[str, Any],
    ) -> dict[str, Entity]:
        """Create a dictionary of entities and their scenes."""
        entities_dict = {}
        # Create the EntityScenes for each entity
        for ent_id, scenes_dict in ents_scens_attrs.items():
            ents_scen = []
            for scene_name, attrs_dict in scenes_dict.items():
                # Create a new EntityScene for each scene
                entity_scene = EntityScene(
                    scene_name, scenes[scene_name][ATTR_PRIORITY], attrs_dict
                )
                # Add the scene to the entity's scenes
                ents_scen.append(entity_scene)
            # Create the entity with its scenes
            entity = entity_factory(self.hass, ent_id, ents_scen)
            # Add the entity to the entities_dict
            entities_dict[ent_id] = entity

        return entities_dict

    def _convert(self, scenes: dict[str, Any]) -> dict[str, Entity]:
        """Convert the scenes from the YAML format into per-entity format.

        Returns:
            - A dictionary of scenes with entity IDs as keys and their attributes.
            - A list of all entity IDs used in the scenes.

        """
        # Get the ents, scens, attrs dict; Structure: {entity_id: {scene_id: {attr_id: AttrScene}}}
        ents_scens_attrs = self.__create_entity_scenes_attributes_dict(scenes)

        return self.__create_entity_scenes_dict(ents_scens_attrs, scenes)


class ComponentManager:
    """Manage the lifecycle of dynamic scenes components."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the component manager."""
        self.hass = hass
        self._unload_callbacks: list[Callable] = []

    async def create_components(
        self, rerun_interval: int, entities: dict[str, Entity]
    ) -> dict[str, Any]:
        """Create and initialize all components needed for the integration."""

        # Create core components
        coordinator = Coordinator(
            self.hass,
            rerun_interval,
            entities,
        )

        # Register services and setup coordinator
        unload_services = await async_register_services(self.hass, coordinator)
        self._unload_callbacks.append(unload_services)

        # Set up coordinator
        coordinator_unload = await coordinator.async_setup()
        self._unload_callbacks.append(coordinator_unload)

        # Return components for reference
        return {
            "coordinator": coordinator,
        }

    async def unload_components(self) -> bool:
        """Unload all components and clean up resources."""
        success = True

        for unload_callback in reversed(self._unload_callbacks):
            try:
                if callable(unload_callback):
                    result = unload_callback()
                    # If it's a coroutine, await it
                    if hasattr(result, "__await__"):
                        await result
            except Exception:
                _LOGGER.exception("Error during component unloading")
                success = False

        self._unload_callbacks.clear()
        return success


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dynamic Scenes from a config entry."""
    # Add delay to allow for virtual lights to be created
    await asyncio.sleep(2)
    _LOGGER.debug("Setting up entry: %s", entry.entry_id)

    # Set up hass.data for the integration
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    data = hass.data[DOMAIN][entry.entry_id]

    # Get rerun interval from config
    try:
        rerun_interval = entry.data.get(DATA_RERUN_INTERVAL)
        if not isinstance(rerun_interval, int) or rerun_interval <= 0:
            _LOGGER.error("Invalid rerun interval: %s", rerun_interval)
            return False
        data[DATA_RERUN_INTERVAL] = rerun_interval
    except (KeyError, TypeError) as err:
        _LOGGER.error("Failed to load rerun interval from entry data: %s", err)
        return False

    # Load and validate scene configurations
    try:
        scene_config = SceneConfiguration(hass)
        entities = await scene_config.load()
        data[DATA_ENTITIES] = entities
    except (FileNotFoundError, yaml.YAMLError, ValueError) as err:
        _LOGGER.error("Failed to load scene configuration: %s", err)
        return False

    # Initialize components
    try:
        component_manager = ComponentManager(hass)
        await component_manager.create_components(
            data[DATA_RERUN_INTERVAL], data[DATA_ENTITIES]
        )

        # Store components and manager for later use
        data["component_manager"] = component_manager

        _LOGGER.debug("Setup complete for entry: %s", entry.entry_id)
        return True
    except Exception:
        _LOGGER.exception("Error initializing components: %s")
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.entry_id not in hass.data.get(DOMAIN, {}):
        return True

    data = hass.data[DOMAIN][entry.entry_id]

    # Unload components using the component manager
    success = True
    if "component_manager" in data:
        try:
            success = await data["component_manager"].unload_components()
        except Exception:
            _LOGGER.exception("Error unloading components")
            success = False

    # Clean up hass.data
    try:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    except KeyError:
        _LOGGER.warning("Failed to clean up hass.data, keys already removed")

    return success
