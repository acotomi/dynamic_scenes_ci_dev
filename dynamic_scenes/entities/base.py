"""Base ENTITIES class."""

from abc import ABC, abstractmethod
from typing import Any

from homeassistant.core import HomeAssistant

from ..attributes.base import Attr  # noqa: TID252
from ..errors import InputValidationError  # noqa: TID252
from ..scenes.entity_scene import EntityScene  # noqa: TID252  # noqa: TID252
from .abilities.scene_ability import SceneAbility
from .abilities.state_ability import StateAbility
from .abilities.timeshift_ability import TimeshiftAbility
from .abilities.update_ablility import UpdateAbility
from .entity_registry import register_entity


class Entity(ABC):
    """Base class for all entities."""

    # ===== Initialization and validation =====

    def _validate_entity(self) -> None:
        """Check if the entity ID is a valid entity in HASS.

        Throws a InputValidationError if the entity ID is not valid.
        """
        # Check if the entity ID is a valid entity in HASS
        if not self._hass.states.get(self._entity_id):
            raise InputValidationError(f"Entity {self._entity_id} is not a valid entity in HASS.")

    def __init__(self, entity_id: str, scene: set[EntityScene], hass: HomeAssistant) -> None:
        """Initialize the entity.

        Throws InputValidationError if entity / the scene is not valid for this entity.
        """
        self._hass = hass

        self._entity_id = entity_id
        self._validate_entity() # Throws InputValidationError if the entity ID is not valid

        # Set up the abilities
        try:
            self._scene_ability = SceneAbility(
                scene,
                self.SUPPORTED_ATTRIBUTES,
                self.__on_scene_change,
            )
            self._timeshift_ability = TimeshiftAbility(
                self.__on_timeshift_change,
            )
            self._state_ability = StateAbility(
                hass,
                entity_id,
                self.__convert_state,
                self.__on_external_state_change,
            )
            self._update_ability = UpdateAbility(
                self._entity_id,
                self._state_ability.with_internal_state_change,
                self.__update_entity,
            )
        except InputValidationError as err:
            raise InputValidationError(
                f"{self._entity_id}: {err}"
            ) from err

    def __init_subclass__(cls) -> None:
        """Initialize the subclass.

        This method is called when the class is created.
        It checks if the constants are defined and registers the class in the registry.

        Raises NotImplementedError if the constants are not defined.
        """
        # Check if the constants are defined
        if not all(
            hasattr(cls, attr)
            for attr in ["SUPPORTED_ATTRIBUTES"]
        ):
            raise NotImplementedError(f"Missing one of the required constants in {cls.__name__}")

        # Register the class in the registry
        register_entity(cls)
        return super().__init_subclass__()

    # ===== Properties =====

    SUPPORTED_ATTRIBUTES: set[type[Attr]]

    @property
    def entity_id(self) -> str:
        """Get the entity ID."""
        return self._entity_id

    # ===== Entity creation methods =====

    @staticmethod
    @abstractmethod
    def supports(state: dict[str, Any]) -> bool:
        """Check if this entity class supports the given entity based on its state.

        This method is used to check if the entity class can handle the entity.
        """

    # ===== Fasade properties =====

    # Scene ability
    @property
    def _scene(self) -> EntityScene:
        """Get the current scene of the entity."""
        return self._scene_ability.current_scene

    # Timeshift ability
    @property
    def _timeshift(self) -> int:
        """Get the current timeshift of the entity."""
        return self._timeshift_ability.timeshift

    # ===== Fasade methods =====

    # Scene ability
    def set_scene_active(self, scene_name: str) -> None:
        """Set a scene to active state.

        If the scene has the highest priority,it will be set as current scene,
        and the on_scene_change method will be called.
        """
        self._scene_ability.set_scene_active(scene_name)

    def set_scene_inactive(self, scene_name: str) -> None:
        """Set a scene to inactive state.

        If the scene is the current scene, the next highest priority scene will be set as current,
        and the on_scene_change method will be called.
        """
        self._scene_ability.set_scene_inactive(scene_name)

    # Timeshift ability
    def set_timeshift(self, timeshift: int) -> None:
        """Set the timeshift of the entity.

        This will call the on_timeshift_change method.
        """
        self._timeshift_ability.set(timeshift)

    def shift_timeshift(self, shift: int) -> None:
        """Shift the timeshift of the entity.

        This will call the on_timeshift_change method.
        """
        self._timeshift_ability.shift(shift)

    # Update ability
    def update_entity(self) -> None:
        """Trigger an update of the entity manually.

        This method is used to make the entity update periodically.
        """

    # ===== Fasade Helpers =====

    # Scene ability
    def __on_scene_change(self, scene: EntityScene) -> None:
        """Called when the scene changes."""  # noqa: D401

    # Timeshift ability
    def __on_timeshift_change(self, timeshift: int) -> None:
        """Called when the timeshift changes."""  # noqa: D401

    # State ability
    def __convert_state(self, ha_state: dict[str, Any]) -> dict[str, Attr]:
        """Convert full Home Assistant state to a dict of Attrs important to this entity.

        This method is used to convert HA state to the internal state representation.
        Subclasses should ovreride this if they have a specific way of converting the state
        aka. rgbww lights that have color mode and temp mode...
        """
        state: dict[str, Attr] = {}

        for attr_type in self.SUPPORTED_ATTRIBUTES:
            # Check if the attribute type is in the HA state
            if attr_type not in ha_state:
                raise InputValidationError(
                    f"Entity {self._entity_id} does not have attribute {attr_type} in its state."
                )
            # Convert the HA state to the Attr type
            state[attr_type.YAML_NAME] = attr_type(value=ha_state[attr_type.HASS_NAME])

        return state

    def __on_external_state_change(self, state: dict[str, Attr]) -> None:
        """When the external state changes.

        This method is used to put the entity into custom scene.
        """

    # Update abiliry
    @abstractmethod
    def __update_entity(self, state: dict[str, Attr]) -> None:
        """Update the entity with the given state.

        This method should call the appropreate Home Assistant service to update the entity state.
        """
