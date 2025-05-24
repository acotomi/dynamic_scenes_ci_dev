# tests/conftest.py
import sys
import os

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../custom_components/dynamic_scenes'))
sys.path.insert(0, base_dir)
