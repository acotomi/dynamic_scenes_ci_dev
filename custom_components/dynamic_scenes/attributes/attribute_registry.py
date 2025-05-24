"""A registry of all the attribute classes."""

from .base import Attr

_attr_registry: dict[str, type[Attr]] = {}

# ===== Put in / out of the registry =====

def register_attr(cls: type[Attr]) -> None:
    """Register an attribute class."""
    _attr_registry[cls.YAML_NAME] = cls

def _get_attr_class(yaml_name: str) -> type[Attr]:
    """Get the attribute class for a given YAML name.

    Raises a ValueError if the YAML name is not registered.
    """
    if yaml_name not in _attr_registry:
        raise ValueError(f"{yaml_name} is not registered in the attribute registry.")
    return _attr_registry[yaml_name]

# ===== Factory method =====

def create_attr(yaml_name: str, time: int, value: float | str | None = None) -> Attr:
    """Create a scene attribute.

    Raises a ValueError if the attribute is not registered.
    """
    # Get the attribute class from the registry
    attr_class = _get_attr_class(yaml_name) # Raises ValueError if not registered
    # Create an instance of the attribute class
    return attr_class(time, value)
