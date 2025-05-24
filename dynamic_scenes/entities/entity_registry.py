"""A registry of all the entity classes."""

from typing import Any

from ..scenes.entity_scene import EntityScene  # noqa: TID252
from .base import Entity

_entity_registry: set[type[Entity]] = set()

def register_entity(cls: type[Entity]) -> None:
    """Register an entity class."""
    # Add to the set
    _entity_registry.add(cls)

def create_entity(state: dict[str, Any], entity_id: str, scene: set[EntityScene]) -> Entity:
    """Create an entity from a state dict.

    Raises a ValueError if no entity class is registered for the entity type.
    """
    supported_entities = [
        entity for entity in _entity_registry if entity.supports(state)
    ]
    if len(supported_entities) == 0:
        raise ValueError(f"No entity class registered for {state['entity_id']}")
    if len(supported_entities) > 1:
        raise ValueError(f"Multiple entity classes registered for {state['entity_id']}")
    # Create the entity
    return supported_entities[0](entity_id, scene)
