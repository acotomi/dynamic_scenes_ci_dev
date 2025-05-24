import pytest
import sys
import os

# Dodamo pot do attributes/types
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/dynamic_scenes/attributes/types')))

from brightness import Brightness

def test_valid_brightness():
    b = Brightness()
    b.value = 100
    assert b.value == 100

def test_invalid_brightness():
    b = Brightness()
    with pytest.raises(ValueError):
        b.value = 300  # izven območja [0,255]

def test_interpolation():
    b = Brightness()
    b.value = 50
    result = b._interpolate_value(next_val=150, ratio=0.5)
    assert result == 100
