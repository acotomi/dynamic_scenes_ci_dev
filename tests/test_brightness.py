import sys
import os
import pytest

# Dodamo root mape v sys.path
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/dynamic_scenes'))
sys.path.insert(0, os.path.join(base_path, 'attributes/types'))
sys.path.insert(0, os.path.join(base_path, 'attributes'))

from attributes.types.brightness import Brightness

def test_brightness_valid_value():
    b = Brightness(time=3600, value=128)
    assert b.value == 128
    assert b.time == 3600

def test_brightness_invalid_value():
    with pytest.raises(ValueError):
        Brightness(time=0, value=300)

def test_brightness_interpolation():
    b1 = Brightness(time=0, value=50)
    b2 = Brightness(time=3600, value=150)
    interpolated = b1.interpolate(b2, 1800)
    assert interpolated.value == 100
