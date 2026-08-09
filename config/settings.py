from pathlib import Path

APP_TITLE = "Texas Produced Water Dashboard"
APP_ICON = "💧"

ROOT_DIR = Path(__file__).resolve().parents[1]
RESOURCES_DIR = ROOT_DIR / "resources"
CONTENT_DIR = RESOURCES_DIR / "content"
TXPWC_DIR = RESOURCES_DIR / "txpwc"
CATALOG_PATH = TXPWC_DIR / "catalogs" / "catalog.json"

DEFAULT_BASIN_ID = "Pecos"
DEFAULT_MODEL_TYPE = "SWAT+gwflow"
DEFAULT_SCENARIO_ID = "baseline"
