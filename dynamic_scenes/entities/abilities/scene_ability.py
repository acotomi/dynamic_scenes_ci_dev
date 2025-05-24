"""Ability to set a scene."""

from collections.abc import Callable
import threading

from ...attributes.base import Attr  # noqa: TID252
from ...constants import MAX_PRIORITY, SCENE  # noqa: TID252
from ...errors import InputValidationError, SceneNameError  # noqa: TID252
from ...scenes.attribute_scene import AttrScene  # noqa: TID252
from ...scenes.entity_scene import EntityScene  # noqa: TID252


class SceneAbility:
    """Class that gives entities scene setting ability."""

    @staticmethod
    def _validate_scene(
        scenes: set[EntityScene], supported_attributes: set[type[Attr]]
    ) -> None:
        """Check if all attributes in scenes are valid for this entity.

        Throws a InputValidationError if the priority is not valid.
        """
        # Scene has at least one attribute (checked in EntityScene)
        # Check if all attributes in scenes are supported by entity
        for scene in scenes:
            for attr in scene.attributes:
                if attr not in supported_attributes:
                    raise InputValidationError(
                        f"{scene.name} has attr {attr} that isnt supported by the entity."
                    )

    @staticmethod
    def _create_off_scene(supported_attributes: set[type[Attr]]) -> EntityScene:
        """Create the off scene for this entity.

        The off scene uses off values for all supported attributes, but it can be empty.
        """
        off_attrs: set[AttrScene] = set()
        for attr in supported_attributes:
            # Create a off attribute and put in AttrScene
            if attr.OFF_VALUE is not None:
                off_attr = attr(0, attr.OFF_VALUE)
                off_attrs.add(AttrScene([off_attr]))

        return EntityScene(SCENE.OFF, 0, off_attrs)

    def __init__(
        self,
        scenes: set[EntityScene],
        supported_attributes: set[type[Attr]],
        on_scene_change_callback: Callable[[EntityScene], None],
    ) -> None:
        """Initialize the scene ability.

        Raises InputValidationError if the scene is not valid for this entity.
        """
        # Create off scene and custom scene (built in)
        self._off_scene = self._create_off_scene(supported_attributes)
        self._custom_scene: EntityScene | None = None  # Custom scene is not set yet

        # Set and validate scenes
        self._scenes = {scene.name: scene for scene in scenes}
        self._validate_scene(
            scenes, supported_attributes
        )  # Raises InputValidationError

        # Scene stuff variables
        self._active_scenes: set[EntityScene] = {self._off_scene}  # Always active
        self._current_scene = self._off_scene
        self._scene_lock = threading.RLock()

        self._on_scene_change = on_scene_change_callback

    # ===== Properties =====

    @property
    def current_scene(self) -> EntityScene:
        """Get the current scene of the entity."""
        with self._scene_lock:
            return self._current_scene

    # ===== Scene management =====

    def set_scene_active(self, scene_name: str) -> None:
        """Set a scene to active state.

        If the scene has the highest priority,it will be set as current scene,
        and the on_scene_change method will be called.

        Raises SceneNameError if the scene does not exist for this entity.
        """
        # Check input
        if scene_name not in self._scenes:
            raise SceneNameError(f"Scene {scene_name} does not exist for this entity.")
        if scene_name == SCENE.OFF:
            raise SceneNameError("Cannot activate off scene, always active.")
        if scene_name == SCENE.CUSTOM:
            raise SceneNameError(
                "Cannot activate custom scene directly, call set_custom_active instead."
            )

        scene = self._scenes[scene_name]

        # Check if scene is already active
        if scene in self._active_scenes:
            return

        # Set scene active, and update entity if it is the highest priority
        with self._scene_lock:
            self._active_scenes.add(scene)
            if scene.priority > self._current_scene.priority:
                # Set as current scene
                self._current_scene = scene
                # Call on scene change method
                self._on_scene_change(scene)

    def set_scene_inactive(self, scene_name: str) -> None:
        """Set a scene to inactive state.

        If the scene is the current scene, the next highest priority scene will be set as current,
        and the on_scene_change method will be called.

        Raises SceneNameError if the scene does not exist for this entity.
        """
        # Check input
        if scene_name not in self._scenes:
            raise SceneNameError(f"Scene {scene_name} does not exist for this entity.")
        if scene_name == SCENE.OFF:
            raise SceneNameError("Cannot deactivate off scene, always active.")
        if scene_name == SCENE.CUSTOM:
            raise SceneNameError(
                "Cannot deactivate custom scene directly, call set_custom_inactive instead."
            )

        scene = self._scenes[scene_name]

        # Check if scene is active
        if scene not in self._active_scenes:
            return

        # Set scene inactive, and update entity if it is the current scene
        with self._scene_lock:
            self._active_scenes.remove(scene)
            if scene == self._current_scene:
                # Set the new highest priority scene
                self._current_scene = self._get_highest_priority_scene()
                # Call on scene change method
                self._on_scene_change(self._current_scene)

    def set_custom_active(self, state: set[Attr]) -> None:
        """Set the custom scene to active with the given state values."""
        # Create custom scene
        custom_attrs: set[AttrScene] = {AttrScene([attr]) for attr in state}
        custom_scene = EntityScene(SCENE.CUSTOM, MAX_PRIORITY, custom_attrs)
        # Set the custom scene
        with self._scene_lock:
            self._custom_scene = custom_scene
            self._current_scene = custom_scene
            self._active_scenes.add(custom_scene)
            # Dont call on_change as the change originated from hass aniways!

    def set_custom_inactive(self) -> None:
        """Set the custom scene to inactive."""
        with self._scene_lock:
            # Check if custom scene is active
            if self._custom_scene in self._active_scenes:
                # Remove custom scene
                self._active_scenes.remove(self._custom_scene)
                self._custom_scene = None
                # Set the new highest priority scene
                self._current_scene = self._get_highest_priority_scene()
                # Call on scene change method
                self._on_scene_change(self._current_scene)

    # ===== Helpers =====

    def _get_highest_priority_scene(self) -> EntityScene:
        """Get the highest priority scene from the active scenes."""
        with self._scene_lock:
            return max(self._active_scenes, key=lambda s: s.priority)
