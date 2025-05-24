"""Manage updates, so they are in the right order with the right delay."""

import asyncio
from collections.abc import Callable
import threading
from typing import Any


class _EntityUpdate:
    """Class that represents an update for an entity."""

    def __init__(self, entity_id: str, update_coro: Callable[[], Any], entity_delay: float = 0):
        self.entity_id = entity_id
        self.update_coro = update_coro  # The actual update coroutine
        self.entity_delay = entity_delay
        self._task: asyncio.Task[None] | None = None

    # ===== Scheduling and calcelation logic =====

    def schedule(self, delay: float = 0):
        """Schedules a update, that can be canceled."""
        # If there is an existing task, cancel it
        if self._task:
            self._task.cancel()

        # Create a new task with the specified delay
        self._task = asyncio.create_task(self._execute_delayed_update(delay))

    def cancel(self):
        """Cancel the update task if it exists."""
        if self._task:
            self._task.cancel()
            self._task = None

    # ===== Helpers =====
    async def _execute_delayed_update(self, delay: float = 0):
        """Execute the update after a delay."""
        try:
            if delay > 0:
                await asyncio.sleep(delay)

            # Execute the actual update
            await self.update_coro()
        except asyncio.CancelledError:
            # Task was cancelled - this is expected behavior
            pass
        finally:
            # Clean up
            self._task = None

# ===== Global state for managing updates =====

_pending_updates: dict[str, _EntityUpdate] = {}  # entity_id -> EntityUpdate
_pending_updates_lock = threading.RLock()  # Lock for thread-safe access to _pending_updates

async def schedule_update(update_id: str, update_coro: Callable[[], None], entity_delay: float = 0):
    """Schedule an update for an entity with a optional delay."""
    with _pending_updates_lock:
        # Cancel existing update for this entity
        if update_id in _pending_updates:
            _pending_updates[update_id].cancel()

        # Create new update
        update = _EntityUpdate(update_id, update_coro, entity_delay)
        _pending_updates[update_id] = update

        # Schedule with delay
        update.schedule(update.entity_delay) # for now just use the entity delay
