import sys
import types
from typing import TypeVar, Generic

def pytest_configure():
    # Dummy Home Assistant structure
    mock_ha = types.ModuleType("homeassistant")
    mock_core = types.ModuleType("homeassistant.core")
    mock_config_entries = types.ModuleType("homeassistant.config_entries")
    mock_helpers = types.ModuleType("homeassistant.helpers")
    mock_helpers_event = types.ModuleType("homeassistant.helpers.event")
    mock_helpers_cv = types.ModuleType("homeassistant.helpers.config_validation")
    mock_helpers_cv.ensure_list = lambda x: x
    mock_helpers_cv.entity_id = lambda x=None: x
    mock_helpers_cv.string = str
    mock_helpers_cv.entity_ids = list
    mock_helpers_cv.positive_int = int


    # Generic mock Event class
    T = TypeVar("T")
    class MockEvent(Generic[T]):
        pass

    # Dummy classes
    mock_core.HomeAssistant = type("HomeAssistant", (), {})
    mock_core.ServiceCall = type("ServiceCall", (), {})
    mock_core.Event = MockEvent
    mock_core.EventStateChangedData = type("EventStateChangedData", (), {})
    mock_config_entries.ConfigEntry = type("ConfigEntry", (), {})

    # Dummy async function for event tracking
    async def dummy_async_track_state_change_event(*args, **kwargs):
        return None

    mock_helpers_event.async_track_state_change_event = dummy_async_track_state_change_event

    # Register dummy modules
    sys.modules["homeassistant"] = mock_ha
    sys.modules["homeassistant.core"] = mock_core
    sys.modules["homeassistant.config_entries"] = mock_config_entries
    sys.modules["homeassistant.helpers"] = mock_helpers
    sys.modules["homeassistant.helpers.event"] = mock_helpers_event
    sys.modules["homeassistant.helpers.config_validation"] = mock_helpers_cv

    # Also mock the missing async_interrupt dependency
    sys.modules["async_interrupt"] = types.ModuleType("async_interrupt")
