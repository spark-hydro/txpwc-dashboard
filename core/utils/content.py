from pathlib import Path

# Map UI model names to file-safe names
MODEL_MAP = {
    "SWAT+ gwflow": "swat+gwflow",
    "SWAT+": "swat+",
}

def get_model_info_path(basin: str, model: str) -> Path:
    """Return the markdown file path for the selected basin/model."""
    basin_key = basin.lower().replace(" ", "_")
    model_key = MODEL_MAP.get(model, model.lower().replace(" ", ""))
    return Path(f"resources/content/model_info/{basin_key}/{model_key}.md")


def load_model_info(basin: str, model: str) -> str:
    """Read markdown content for the selected basin/model."""
    path = get_model_info_path(basin, model)

    if path.exists():
        return path.read_text(encoding="utf-8")

    return f"### Model Info\n\nNo content for `{basin} / {model}` yet."