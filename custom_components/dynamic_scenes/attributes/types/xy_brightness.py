"""BY Brightness attribute for any light entity."""

from ..base import Attr  # noqa: TID252


class XYBrightness(Attr):
    """Class to represent a brightness attribute."""

    YAML_NAME: str = "xy_brightness"
    HASS_NAME: str = "brightness"
    OFF_VALUE: int = 0
    DEFAULT_VALUE: int = OFF_VALUE

    @staticmethod
    def _validate_value(value: int) -> None:
        if not 0 <= value <= 255:
            raise ValueError(f"Invalid brightness value: {value}")

    def _interpolate_value(self, next_val: int, ratio: float) -> int:
        return int(self.value + (next_val - self.value) * ratio)
