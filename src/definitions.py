import os
from pathlib import Path

"""
Contains some global constants and paths used in the project.
"""

ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = os.path.join(ROOT_DIR, "configuration.conf")
DATA_DIR = os.path.join(ROOT_DIR, "data")
