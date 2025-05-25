import pytest
from dynamic_scenes.attributes.types.brightness import Brightness
from dynamic_scenes.entity_scenes import AttrScene


def test_attr_scene_interpolation_halfway():
    attr1 = Brightness(time=0, value=0)
    attr2 = Brightness(time=60, value=255)
    scene = AttrScene(attr1, attr2)

    result = scene.interpolate(30)
    assert isinstance(result, Brightness)
    assert result.value == 127 or result.value == 128  # int rounding
    assert result.time == 30


def test_attr_scene_before_start():
    attr1 = Brightness(time=10, value=100)
    attr2 = Brightness(time=60, value=200)
    scene = AttrScene(attr1, attr2)

    result = scene.interpolate(0)
    assert result.value == 100


def test_attr_scene_after_end():
    attr1 = Brightness(time=10, value=100)
    attr2 = Brightness(time=60, value=200)
    scene = AttrScene(attr1, attr2)

    result = scene.interpolate(100)
    assert result.value == 200
