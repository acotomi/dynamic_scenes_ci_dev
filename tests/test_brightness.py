from dynamic_scenes.attributes.types.brightness import Brightness

def test_brightness_interpolation():
    b = Brightness(value=50)
    result = b._interpolate_value(next_val=150, ratio=0.5)
    assert result == 100

def test_brightness_validation():
    b = Brightness()
    b._validate_value(255)  # OK
    try:
        b._validate_value(300)
        assert False  # Should not reach here
    except ValueError:
        assert True
