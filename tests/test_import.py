import sys
import os
import pathlib
import json

# Ensure project root is in PYTHONPATH
project_root = pathlib.Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

def test_engine_import():
    try:
        from sentinel.predict import engine
        assert engine is not None
    except Exception as e:
        raise AssertionError(f"Engine import failed: {e}")
