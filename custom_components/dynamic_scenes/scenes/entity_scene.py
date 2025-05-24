"""A scene of all attributes of an entity."""

from ..attributes.base import Attr  # noqa: TID252
from ..constants import MAX_PRIORITY  # noqa: TID252
from ..errors import InputValidationError  # noqa: TID252
from .attribute_scene import AttrScene


class EntityScene:
    """A scene of all attributes of an entity."""

    # ===== Initialization and validation =====

    @staticmethod
    def _validate_priority(priority: int) -> None:
        """Validate the priority of this scene.

        Throws a InputValidationError if the priority is not valid.
        """
        # Priority is in range 0-100
        if priority < 0 or priority > MAX_PRIORITY-1: # -1 as custom scene has to be at max!
            raise InputValidationError(f"Priority {priority} is not in range 0-{MAX_PRIORITY-1}.")

    @staticmethod
    def _validate_scene(scene: set[AttrScene]) -> None:
        """Validate the scene of this entity.

        Throws a InputValidationError if the scene is not valid.
        """
        # At least one attribute
        if len(scene) == 0:
            raise InputValidationError("Scene must have at least one attribute.")

        # No AttrScene has the same type as another
        for i, attr_scene_1 in enumerate(scene):
            for j, attr_scene_2 in enumerate(scene):
                if i != j and not isinstance(attr_scene_1, type(attr_scene_2)):
                    raise InputValidationError(
                        f"Attribute {attr_scene_1} is the same as {attr_scene_2}."
                    )

    def __init__(self, name: str, priority: int, scene: set[AttrScene]) -> None:
        """Initialize the entitys scene."""
        # Set and validate
        self._name = name
        self._priority = priority

        # Validate the scene
        try:
            self._validate_priority(self._priority)
            self._validate_scene(scene)
        except InputValidationError as err:
            raise InputValidationError(
                f"{self._name} (p={self._priority}, s={scene}): {err}"
            ) from err

        # Make dict, keys are attr types
        self._scene = {attr_scene.type: attr_scene for attr_scene in scene}

    # ===== Properties =====

    @property
    def name(self) -> str:
        """Get the name of the scene."""
        return self._name

    @property
    def priority(self) -> int:
        """Get the priority of the scene."""
        return self._priority

    @property
    def attributes(self) -> set[type[Attr]]:
        """Get the attributes of this scene.

        Returns a set of attribute types.
        """
        return set(self._scene.keys())

    # ===== Getting attributes at times =====

    def get_attr_at_time(self, time: int) -> dict[type[Attr], Attr]:
        """Get the value of this scenes attributes at a specific time.

        Returns a dict of attribute types and their values at the given time.
        """
        # attr_scene has at least one attribute, and is formatted correctly
        attrs: dict[type[Attr], Attr] = {}
        for attr_type, attr_scene in self._scene.items():
            attrs[attr_type] = attr_scene.get_attr_at_time(time)
        return attrs
