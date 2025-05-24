"""Dynamic Scenes Manager."""


class EntityUpdatesManager:
    """Updates the correct entities in the correct order with the correct values."""

    # Calculations for the wanted state also happen here!

    def __init__(self, scenes: dict) -> None:
        """Initialize the scenes manager."""
        self.scenes = scenes

    def get_updates(self, ent_ids = None, time=None) -> dict:
        """Get the wanted states of a list of entities at a given time."""
        # Če ent_ids == None, vrni vse entitete katerih željeno
        # stanje je različno od trenutnega stanja
        # Če time == None, vrni stanje za zdej
