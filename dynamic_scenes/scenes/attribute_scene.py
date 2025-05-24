"""The scene of one attribute of one entity."""

import bisect

from ..attributes.base import Attr  # noqa: TID252
from ..errors import InputValidationError  # noqa: TID252


class AttrScene:
    """Class to represent a scene for one attribute of one entity."""

    # ===== Initialization and validation =====

    @staticmethod
    def _validate_attr_scene(attr_scene: list[Attr]) -> None:
        """Validate all stuff in attr_scene, so this class can funciton propperly.

        Raises InputValidationError if the scene is not valid.
        """
        # At least one attribute
        if len(attr_scene) == 0:
            raise InputValidationError("Attribute scene must have at least one attribute.")

        for i, attr in enumerate(attr_scene):
            # Times are in ascelerating order
            if i != 0 and attr_scene[i - 1].time >= attr.time:
                raise InputValidationError(
                    f"Time {attr.time} for attribute {attr} is lower then previous time."
                )

            # All attributes are of the same type
            if not isinstance(attr, attr_scene[0].__class__):
                raise InputValidationError(
                    f"Attribute {attr} is not of the same type as first attribute."
                )

    def __init__(self, attr_scene: list[Attr] | None = None) -> None:
        """Initialize the attributes scene."""
        self._attr_scene = attr_scene if attr_scene is not None else []
        self._times = [attr.time for attr in self._attr_scene]
        # Validate the attributes scene
        self._validate_attr_scene(self._attr_scene)

    # ===== Properties =====

    @property
    def type(self) -> type[Attr]:
        """Get the type of attributes in this attr scene."""
        return type(self._attr_scene[0]) # Validated that all the same type

    # ===== Getting attributes at times =====

    def get_attr_at_time(self, time: int) -> Attr:
        """Get the value of an attribute at a specific time."""
        # attr_scene has at least one attribute, and is formatted correctly
        idx = bisect.bisect_right(self._times, time)  # Rerturns index of next time!
        attr_scene = self._attr_scene

        if idx == 0 or idx == len(attr_scene):
            # Time is between the last and first attribute
            prev_attr = attr_scene[-1]  # Before midnight
            next_attr = attr_scene[0]  # After midnight
        else:
            # Time is between two attributes
            prev_attr = attr_scene[idx - 1]
            next_attr = attr_scene[idx]

        # Interpolate the new Attr
        return prev_attr.interpolate(next_attr, time)

    # ===== Helpers =====

    def __repr__(self) -> str:
        """Return a string representation of the attribute scene."""
        return "AttrScene(" + ", ".join([repr(attr) for attr in self._attr_scene]) + ")"
