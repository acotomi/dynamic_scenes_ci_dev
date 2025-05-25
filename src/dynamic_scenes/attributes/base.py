"""Base ATRIBUTES class."""

from abc import ABC, abstractmethod
import logging
from typing import Any, TypeVar, cast

from ..errors import InputValidationError  # noqa: TID252
from .attribute_factory import register_attr

_LOGGER = logging.getLogger(__name__)


T = TypeVar("T", bound="Attr")

class Attr(ABC):
    """Base (abstract) class for all attributes."""

    # ===== Initialization and validation =====

    @staticmethod
    def _validate_time(time: int) -> None:
        """Validate the time of this attribute.

        Throws a InputValidationError if the time is not valid.
        """
        # Time is in range 0-24h
        if time < 0 or time >= 24 * 3600:
            raise InputValidationError(f"Time {time} is not in range 0-23.59.59h.")

    @classmethod
    @abstractmethod
    def _validate_value(cls, value: Any) -> None:
        """Validate the value of this attribute.

        Throws a InputValidationError if the value is not valid.
        """

    def __init__(self, value: Any = None, time: int | None = None) -> None:
        """Initialize the attribute."""
        # Set or initialize time
        self._time = time if time is not None else 0
        # Set or initialize value
        self._value = value if value is not None else self.DEFAULT_VALUE

        try:
            # Validate the time
            self._validate_time(self._time)
            # Validate the value
            self._validate_value(self._value)
        except InputValidationError as err:
            raise InputValidationError(
                f"{self.YAML_NAME}(t={self.time}, v={self.value}): {err}"
            ) from err

    def __init_subclass__(cls) -> None:
        """Initialize the subclass.

        This method is called when the class is created.
        It checks if the constants are defined and registers the class in the registry.

        Raises NotImplementedError if the constants are not defined.
        """
        super().__init_subclass__()
        # Check if the constants are defined
        if not all(
            hasattr(cls, attr)
            for attr in ["YAML_NAME", "HASS_NAME", "OFF_VALUE", "DEFAULT_VALUE"]
        ):
            raise NotImplementedError(
                f"Missing one of the required constants in {cls.__name__}"
            )

        # Register the class in the registry
        _LOGGER.debug("Registering attribute class %s", cls.__name__)
        register_attr(cls)

    # ===== Properties =====

    YAML_NAME: str  # The name of the attribute in YAML
    HASS_NAME: str  # The name of the attribute in Home Assistant
    OFF_VALUE: Any  # The value when the attribute is off
    DEFAULT_VALUE: Any  # The default value of the attribute

    @property
    def value(self) -> Any:
        """Return the attribute value."""
        return self._value

    @property
    def time(self) -> int:
        """Return the attribute time."""
        return self._time

    # ===== Interpolation =====

    def _normalize_times_for_interpolation(
        self, time: int, prev_time: int, next_time: int
    ) -> tuple[int, int]:
        """Handle midnight wraparound by adjusting times to same 24h period."""
        if prev_time > next_time:  # wraparound case
            if time >= prev_time:
                next_time += 24 * 3600  # move next to tomorrow
            else:
                prev_time -= 24 * 3600  # move prev to yesterday
        return prev_time, next_time

    def interpolate(self, next_attr: T, time: int) -> T:
        """Interpolates this attr between this value and the next, using the provided ratio.

        If this time is greater than the next time, the function still correctly calculates
        over midnight values.

        Raises TypeError if the next attribute is not of the same type as this one.
        """
        # Check if the next attribute is of the same type
        if not isinstance(next_attr, type(self)):
            raise TypeError(
                f"Interpolation for {self.YAML_NAME}, got {type(next_attr)} instead of {type(self)}"
            )

        # Shift the times, so that current time is in between them
        prev_time, next_time = self._normalize_times_for_interpolation(
            time,
            self.time,
            next_attr.time,
        )

        # Calculate the ratio
        if prev_time != next_time:
            ratio = (time - prev_time) / (next_time - prev_time)
        else:
            # Handle the devision by zero case
            ratio = 0.0

        # Get the new time and value
        new_time = (prev_time + time) % (24 * 3600)
        new_value = self._interpolate_value(next_attr.value, ratio)

        # Create a new attribute with the new time and value
        return cast(T, type(self)(value=new_value, time=new_time))

    @abstractmethod
    def _interpolate_value(self, next_val: Any, ratio: float) -> Any:
        """Interpolate the value of this attribute.

        This method is called by the interpolate method.
        """

    # ===== Helper methods =====

    def __eq__(self, other: object) -> bool:
        """Check if two attributes are equal."""
        return (
            isinstance(other, type(self))
            and self.YAML_NAME == other.YAML_NAME
            and self._value == other._value
        )

    def __ne__(self, other: object) -> bool:
        """Check if two attributes are not equal."""
        return not self.__eq__(other)

    def __repr__(self) -> str:
        """Return a string representation of the attribute."""
        h = self.time // 3600
        m = (self.time % 3600) // 60
        s = self.time % 60
        time_str = f"{h:02}:{m:02}:{s:02}"
        return f"{self.YAML_NAME}(t={time_str}, v={self.value})"

    def __hash__(self) -> int:
        """Return a hash of the attribute."""
        return hash((self.YAML_NAME, self._value))
