"""Swap heavy remote images in page content for small inline WebP copies.

The content pages embed multi-megabyte PNG/GIF files from raw.githubusercontent.com. Next to each
one lives a `<name>_web.webp` copy (at most 2000 px wide); when it exists, the page shows that copy
inline instead of downloading the original on every visit. The link that wraps the image still points
to the full-size original, so clicking it opens the sharp version.
"""

from __future__ import annotations

import base64
import re
from functools import lru_cache
from pathlib import Path

IMAGES_DIR = Path(__file__).resolve().parents[2] / "resources" / "content" / "images"

_REMOTE_IMG = re.compile(
    r'(<img\b[^>]*?\bsrc=")https://raw\.githubusercontent\.com/spark-hydro/txpwc-dashboard/main/'
    r'resources/content/images/([^"/]+?)\.(?:png|jpe?g|gif)"'
)


@lru_cache(maxsize=32)
def _webp_data_uri(name: str) -> str:
    path = IMAGES_DIR / f"{name}_web.webp"
    if not path.exists():
        return ""
    return "data:image/webp;base64," + base64.b64encode(path.read_bytes()).decode()


def inline_local_images(html: str) -> str:
    def swap(m: re.Match) -> str:
        uri = _webp_data_uri(m.group(2))
        return f'{m.group(1)}{uri}"' if uri else m.group(0)

    return _REMOTE_IMG.sub(swap, html)
