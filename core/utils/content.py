from pathlib import Path

# Map UI model names to file-safe names
MODEL_MAP = {
    "SWAT+ gwflow": "swat+gwflow",
    "SWAT+": "swat+",
    "ARMS": "arms",
}


def _normalize_basin(basin: str) -> str:
    """Convert basin name to folder-safe key."""
    return basin.strip().lower().replace(" ", "_")


def _normalize_model(model: str) -> str:
    """Convert model name to file-safe key."""
    return MODEL_MAP.get(model, model.strip().lower().replace(" ", ""))


def get_model_info_path(basin: str, model: str) -> Path:
    """Return markdown path for Model Info page."""
    basin_key = _normalize_basin(basin)
    model_key = _normalize_model(model)
    return Path(f"resources/content/model_info/{basin_key}/{model_key}.md")


def load_model_info(basin: str, model: str) -> str:
    """Read Model Info markdown for selected basin/model."""
    path = get_model_info_path(basin, model)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"### Model Info\n\nNo content for `{basin} / {model}` yet."


def get_water_quality_path(basin: str, model: str) -> Path:
    """Return markdown path for Water Quality page."""
    basin_key = _normalize_basin(basin)
    model_key = _normalize_model(model)
    return Path(f"resources/content/water_quality/{basin_key}/{model_key}.md")


def load_water_quality(basin: str, model: str) -> str:
    """Read Water Quality markdown for selected basin/model."""
    path = get_water_quality_path(basin, model)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"### Water Quality\n\nNo content for `{basin} / {model}` yet."


def get_scenarios_path(basin: str, model: str) -> Path:
    """Return markdown path for Scenarios page."""
    basin_key = _normalize_basin(basin)
    model_key = _normalize_model(model)
    return Path(f"resources/content/scenarios/{basin_key}/{model_key}.md")


def load_scenarios(basin: str, model: str) -> str:
    """Read Scenarios markdown for selected basin/model."""
    path = get_scenarios_path(basin, model)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"### Scenarios\n\nNo content for `{basin} / {model}` yet."


def get_data_driven_path(basin: str, model: str) -> Path:
    """Return markdown path for Data-Driven page."""
    basin_key = _normalize_basin(basin)
    model_key = _normalize_model(model)
    return Path(f"resources/content/data_driven/{basin_key}/{model_key}.md")


def load_data_driven(basin: str, model: str) -> str:
    """Read Data-Driven markdown for selected basin/model."""
    path = get_data_driven_path(basin, model)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"### Data-Driven Analysis\n\nNo content for `{basin} / {model}` yet."


def get_hydrology_path(basin: str, model: str) -> Path:
    """Return markdown path for Hydrology page."""
    basin_key = _normalize_basin(basin)
    model_key = _normalize_model(model)
    return Path(f"resources/content/hydrology/{basin_key}/{model_key}.md")


def load_hydrology(basin: str, model: str) -> str:
    """Read Hydrology markdown for selected basin/model."""
    path = get_hydrology_path(basin, model)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"### Hydrology\n\nNo content for `{basin} / {model}` yet."