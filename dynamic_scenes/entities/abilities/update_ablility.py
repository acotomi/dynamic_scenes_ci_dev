"""Ability to update an entity's attributes."""

from collections.abc import Callable
import threading

from ...attributes.base import Attr  # noqa: TID252
from ...entity_updates import schedule_update  # noqa: TID252


class UpdateAbility:
    """Ability to update an entity's attributes."""

    def __init__(
        self,
        entity_id: str,
        internal_update_wrapper: Callable[[Callable[[], None]], None],
        update_method: Callable[[dict[str, Attr]], None],
    )-> None:
        """Initialize the update ability."""
        self._entity_id = entity_id
        self._internal_update_wrapper = internal_update_wrapper
        self._update_method = update_method
        self._update_lock = threading.RLock()

        # Stores previous update so we dont update the same attributes again
        self._prev_update: dict[str, Attr] | None = None

    async def schedule_update(self, update: dict[str, Attr], entity_delay: float = 0) -> None:
        """Schedule an entity update."""
        with self._update_lock:
            # If the update is the same as the previous one, do not schedule it
            if self._prev_update == update:
                return

            # Update the previous update
            self._prev_update = update

            # Schedule the update
            await schedule_update(
                self._entity_id,
                lambda: self._internal_update_wrapper(lambda: self._update_method(update)),
                entity_delay,
            )
