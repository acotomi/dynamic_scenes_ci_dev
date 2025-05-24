import sys
import os
import pytest
from unittest.mock import AsyncMock

# Dodamo celotno pot do dinamičnega scenes modula v sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
component_path = os.path.join(repo_root, 'custom_components', 'dynamic_scenes')
sys.path.insert(0, component_path)

# Zdaj lahko uvozimo SceneConfiguration direktno iz __init__.py
from __init__ import SceneConfiguration

@pytest.mark.asyncio
async def test_load_invalid_yaml(tmp_path):
    bad_yaml = tmp_path / "scenes.yaml"
    bad_yaml.write_text("::not valid yaml::")

    hass = AsyncMock()
    config = SceneConfiguration(hass)

    with pytest.raises(Exception):
        await config.load(file_path=bad_yaml)
