"""Microsoft Fluent Emoji 3D fetcher (MIT licensed, https://github.com/microsoft/fluentui-emoji).

Stickers are referenced by their Fluent folder name, e.g. "Party popper", "Red heart",
"Smiling face with heart-eyes". Files are downloaded once and cached locally.
Source images are 256x256 — keep rendered size <= ~420 px to stay sharp.
"""
import os
import urllib.parse
import urllib.request

BASE = "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets"
CACHE = os.environ.get(
    "PANORAMA_EMOJI_CACHE",
    os.path.join(os.path.expanduser("~"), ".cache", "appstore-panorama", "fluent3d"),
)


def _slug(name: str) -> str:
    return name.lower().replace(" ", "_")


def _candidates(name: str):
    folder = urllib.parse.quote(name)
    slug = _slug(name)
    # Plain emoji
    yield f"{BASE}/{folder}/3D/{slug}_3d.png"
    # Emoji with skin tones (e.g. hands, people)
    yield f"{BASE}/{folder}/Default/3D/{slug}_3d_default.png"


def fetch(name: str) -> str:
    """Return a local path to the 3D PNG for a Fluent emoji folder name (downloads once)."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, _slug(name) + "_3d.png")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    last = None
    for url in _candidates(name):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                data = r.read()
            with open(path, "wb") as f:
                f.write(data)
            return path
        except Exception as e:  # try next candidate
            last = e
    raise FileNotFoundError(
        f'Fluent 3D emoji "{name}" not found ({last}). Use the exact folder name from '
        f"https://github.com/microsoft/fluentui-emoji/tree/main/assets"
    )
