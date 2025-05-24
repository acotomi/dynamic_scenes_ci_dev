import sys
import os
import pytest
from unittest.mock import AsyncMock

# Dodamo custom_components v sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
custom_components_path = os.path.join(repo_root, 'custom_components')
sys.path.insert(0, custom_components_path)

from dynamic_scenes import SceneConfiguration

@pytest.mark.asyncio
async def test_load_invalid_yaml(tmp_path):
    bad_yaml = tmp_path / "scenes.yaml"
    bad_yaml.write_text("::not valid yaml::")

    hass = AsyncMock()
    config = SceneConfiguration(hass)

    with pytest.raises(Exception):
        await config.load(file_path=bad_yaml)
