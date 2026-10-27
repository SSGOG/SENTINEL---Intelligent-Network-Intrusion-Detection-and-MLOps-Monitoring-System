# Proxy module to expose the actual implementation under src.sentinel
import sys
import pathlib

# Ensure src directory is on PYTHONPATH
project_root = pathlib.Path(__file__).resolve().parents[1]
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

# Import everything from the real predict module
from src.sentinel.predict import *  # noqa: F401,F403
