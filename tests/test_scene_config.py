import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/dynamic_scenes')))
from __init__ import SceneConfiguration

import pytest
from dynamic_scenes import SceneConfiguration
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_load_invalid_yaml(tmp_path):
    bad_yaml = tmp_path / "scenes.yaml"
    bad_yaml.write_text("::not valid yaml::")

    hass = AsyncMock()
    config = SceneConfiguration(hass)

    with pytest.raises(Exception):
        await config.load(file_path=bad_yaml)
