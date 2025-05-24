"""Light state attribute for any light entity."""

from ..base import Attr  # noqa: TID252


class BrightnessAttr(Attr):
    """Class to represent a brightness attribute."""

    YAML_NAME: str = "light_state"
    HASS_NAME: str = "state"
    OFF_VALUE: str = "off"
    DEFAULT_VALUE: str = OFF_VALUE

    @staticmethod
    def _validate_value(value: str) -> None:
        if value not in ["on", "off"]:
            raise ValueError(f"Invalid brightness value: {value}")

    def _interpolate_value(self, next_val: int, ratio: float) -> int:
        return self.value
