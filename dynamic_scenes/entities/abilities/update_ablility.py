"""Ability to update an entity's attributes."""

from collections.abc import Awaitable, Callable
import logging
import threading

from ...attributes import Attr  # noqa: TID252
from ...entity_updates import cancel_update, schedule_update  # noqa: TID252

_LOGGER = logging.getLogger(__name__)


class UpdateAbility:
    """Ability to update an entity's attributes."""

    def __init__(
        self,
        internal_update_wrapper: Callable[[Callable[[], Awaitable[None]]], Awaitable[None]],
        update_method: Callable[[dict[type[Attr], Attr]], Awaitable[None]],
    )-> None:
        """Initialize the update ability."""
        self._internal_update_wrapper = internal_update_wrapper
        self._update_method = update_method

        self._update_lock = threading.RLock()

        # Stores previous update so we dont update the same attributes again
        self._prev_update_ids: set[str] = set()

    # ===== Update method =====

    def schedule_update(
            self,
            wanted_state: dict[type[Attr], Attr],
            update_id: str,
            entity_delay: float = 0
    ) -> None:
        """Schedule an entity update."""
        with self._update_lock:
            # Schedule the update
            self._prev_update_ids.add(update_id)
            schedule_update(
                update_id,
                lambda: self._internal_update_wrapper(lambda: self._update_method(wanted_state)),
                entity_delay,
            )

    def cancel_updates(self) -> None:
        """Cancel all scheduled updates."""
        with self._update_lock:
            # Cancel all previous updates
            for update_id in self._prev_update_ids:
                _LOGGER.debug("Cancelling update with id '%s'", update_id)
                cancel_update(update_id)
