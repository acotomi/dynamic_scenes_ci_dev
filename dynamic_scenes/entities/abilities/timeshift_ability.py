"""Ability to shift the time of a scene."""

from collections.abc import Callable
import threading


class TimeshiftAbility:
    """Class that gives entities timeshifting ability."""

    def __init__(self, on_timeshift_change_callback: Callable[[int], None]) -> None:
        """Initialize the timeshift."""
        # Set the timeshift to 0
        self._timeshift: int = 0
        self._timeshift_lock = threading.RLock()

        # Set the callback
        self._on_timeshift_change = on_timeshift_change_callback

    # ===== Properties =====

    @property
    def timeshift(self) -> int:
        """Get the current timeshift in seconds."""
        with self._timeshift_lock:
            return self._timeshift

    # ===== Timeshift management =====

    def set(self, timeshift: int) -> None:
        """Set the timeshift to a specific value in seconds."""
        with self._timeshift_lock:
            self._timeshift = self._correct_for_12h(timeshift)
            self._on_timeshift_change(self._timeshift)

    def shift(self, shift: int) -> None:
        """Adjust the timeshift by a relative amount in seconds."""
        # Make sure the timeshift is in the range -12h to +12h
        with self._timeshift_lock:
            self._timeshift = self._correct_for_12h(self._timeshift + shift)
            self._on_timeshift_change(self._timeshift)

    # ===== Helpers =====

    @staticmethod
    def _correct_for_12h(timeshift: int) -> int:
        """Correct the timeshift so it is in the -12h to +12h range."""
        # Make sure the time is in the range -12h to +12h
        return ((timeshift + 12 * 3600) % (24 * 3600)) - 12 * 3600
