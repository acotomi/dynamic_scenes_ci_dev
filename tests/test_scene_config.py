import pytest
from custom_components.dynamic_scenes.__init__ import SceneConfiguration
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_load_invalid_yaml(tmp_path):
    # ustvari začasno neveljavno YAML datoteko
    bad_yaml = tmp_path / "scenes.yaml"
    bad_yaml.write_text("::not valid yaml::")

    hass = AsyncMock()
    config = SceneConfiguration(hass)

    with pytest.raises(Exception):
        await config.load(file_path=bad_yaml)
