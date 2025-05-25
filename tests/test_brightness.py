import pytest
from dynamic_scenes.attributes.types.brightness import Brightness

def test_valid_brightness_value():
    b = Brightness(time=0, value=100)
    assert b.value == 100
    assert b.time == 0

def test_invalid_brightness_value():
    with pytest.raises(ValueError):
        Brightness(time=0, value=300)

def test_interpolation_midpoint():
    b1 = Brightness(time=0, value=50)
    result = b1._interpolate_value(next_val=150, ratio=0.5)
    assert result == 100

def test_interpolation_start():
    b1 = Brightness(time=0, value=50)
    result = b1._interpolate_value(next_val=150, ratio=0.0)
    assert result == 50

def test_interpolation_end():
    b1 = Brightness(time=0, value=50)
    result = b1._interpolate_value(next_val=150, ratio=1.0)
    assert result == 150

