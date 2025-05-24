"""Behavior interfaces and implementations for entities.

This module defines the core behavior interfaces that entities can implement,
along with their base implementations.
"""

from abc import ABC, abstractmethod


class TimeshiftBehavior(ABC):
    """Interface for entities that support time shifting."""

    @abstractmethod
    def set_timeshift(self, timeshift: int) -> None:
        """Set the timeshift to a specific value in seconds."""

    @abstractmethod
    def shift_time(self, shift: int) -> None:
        """Adjust the timeshift by a relative amount in seconds."""

    @abstractmethod
    def apply_timeshift(self, time_seconds: int) -> int:
        """Apply the timeshift to a time value in seconds."""


class SceneManagementBehavior(ABC):
    """Interface for entities that support scene management."""

    @abstractmethod
    def activate_scene(self, scene_name: str) -> bool:
        """Activate a scene for this entity."""

    @abstractmethod
    def deactivate_scene(self, scene_name: str) -> bool:
        """Deactivate a scene for this entity."""

    @abstractmethod
    def set_custom_active(self, state: dict[str, Attr]) -> None:
        """Set custom scene as active with the given state values."""

    @abstractmethod
    def set_custom_inactive(self) -> None:
        """Deactivate the custom scene."""

    @property
    @abstractmethod
    def active_scene_names(self) -> set[str]:
        """Get the names of all currently active scenes."""

    @property
    @abstractmethod
    def is_custom_active(self) -> bool:
        """Check if the custom scene is active."""


# Export interfaces
__all__ = [
    "SceneManagementBehavior",
    "TimeshiftBehavior",
]
