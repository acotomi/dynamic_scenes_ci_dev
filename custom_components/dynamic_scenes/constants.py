"""Constants for the DynamicScenes integration."""

INTEGRATION_DOMAIN = "dynamic_scenes"

# The maximum priority a scene can have (custom scene has this priority)
MAX_PRIORITY = 100

class SERVICE:
    """The service names exposed by the integration."""

    SET_SCENE_CONDITION_MET = "set_scene_condition_met"
    UNSET_SCENE_CONDITION_MET = "unset_scene_condition_met"
    RESET_CUSTOM_SCENE = "reset_custom_scene"
    SET_TIMESHIFT = "set_timeshift"
    SHIFT_TIME = "shift_time"

class DATA:
    """The data keys used in the integration storage."""

    ENTITIES = "entities"
    RERUN_INTERVAL = "rerun_interval"
    UNLOAD_SERVICES = "unload_services"
    UNLOAD_COORDINATOR = "unload_coordinator"
    COMPONENTS = "components"

class PATH:
    """The paths to files used by the integration."""

    SCENES_FILE = "scenes.yaml"

class SCENE:
    """Built-in scenes."""

    OFF = "off"
    CUSTOM = "custom"

DOMAIN = "dynamic_scenes"

# TODO: Kaj so tej?
# Service attributes
ATTR_ENTITY_ID = "entity_id"
ATTR_SCENE = "scene"
ATTR_TIMESHIFT = "timeshift"
