"""Scale-aware explainer video pipeline."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
SCHEMA_DIR = PACKAGE_DIR / "schemas"
CACHE_DIR = Path.home() / ".cache" / "explainer-video"
