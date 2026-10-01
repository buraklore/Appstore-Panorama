"""Command line: python -m panorama {build,init,sizes}"""
import argparse
import json
import os
import sys

from .engine import SIZES, load

STARTER = {
    "canvas": {"panels": 6, "panel_width": 1320, "panel_height": 2868},
    "output": {"sizes": ["iphone-6.9", "iphone-6.5"]},
    "background": {
        "transition_px": 70,
        "scenes": [
            {"panels": [0, 1], "colors": ["#4B2FD6", "#7A5CFA"]},
            {"panels": [2, 3], "colors": ["#F5479B", "#E8338A"]},
            {"panels": [4, 5], "colors": ["#1FA8C8", "#1FC8A0"]},
        ],
    },
    "brand": {"x": 0.09, "y": 120, "icon": "icon.png", "name": "My App"},
    "headlines": [
        {"panel": 0, "lines": ["Your main", "value promise"], "pill_line": 1, "pill_color": "#FFD166", "pill_text": "#2A1B6B"},
        {"panel": 1, "lines": ["Second", "benefit"], "pill_line": 1},
        {"panel": 2, "lines": ["Third", "benefit"], "pill_line": 1, "pill_text": "#C2185B"},
        {"panel": 3, "lines": ["Fourth", "benefit"], "pill_line": 1, "pill_text": "#C2185B"},
        {"panel": 4, "lines": ["Fifth", "benefit"], "pill_line": 1, "pill_text": "#0E8F7A"},
        {"panel": 5, "lines": ["Sixth", "benefit"], "pill_line": 1, "pill_text": "#0E8F7A"},
    ],
    "phones": [
        {"screen": "screens/01.png", "x": 1.0, "y": 1960, "width": 880, "angle": -5},
        {"screen": "screens/02.png", "x": 3.0, "y": 1960, "width": 880, "angle": -4},
        {"screen": "screens/03.png", "x": 5.0, "y": 1960, "width": 880, "angle": -5},
    ],
    "stickers": [
        {"emoji": "Party popper", "x": 0.23, "y": 1560, "size": 400, "angle": 12},
        {"emoji": "Red heart", "x": 2.02, "y": 1180, "size": 380, "angle": -14},
        {"emoji": "Video game", "x": 4.0, "y": 2360, "size": 380, "angle": 16},
    ],
}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="panorama", description="Seamless panoramic store screenshots")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="render a config into store screenshots")
    b.add_argument("config")
    b.add_argument("--out", default=None, help="output dir (default: <config dir>/out)")
    b.add_argument("--sizes", nargs="*", help=f"any of: {', '.join(SIZES)}")
    b.add_argument("--strict", action="store_true", help="exit 1 if the validator reports warnings")
    i = sub.add_parser("init", help="write a starter config")
    i.add_argument("path", nargs="?", default="panorama.json")
    sub.add_parser("sizes", help="list supported store sizes")
    a = ap.parse_args(argv)

    if a.cmd == "sizes":
        for k, (w, h) in SIZES.items():
            print(f"{k:15s} {w}x{h}")
        return
    if a.cmd == "init":
        if os.path.exists(a.path):
            sys.exit(f"{a.path} already exists")
        with open(a.path, "w", encoding="utf-8") as f:
            json.dump(STARTER, f, ensure_ascii=False, indent=2)
        print(f"wrote {a.path} — put your screen captures in screens/ and run: python -m panorama build {a.path}")
        return

    pano = load(a.config)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.config)), "out")
    files = pano.save(out, sizes=a.sizes)
    print(f"✓ {len(files)} files → {out}")
    print(f"  preview: {os.path.join(out, '_preview_panorama.png')}")
    print(f"  panels:  {os.path.join(out, '_preview_panels.png')}")
    if pano.warnings:
        print(f"\n⚠ {len(pano.warnings)} warning(s):")
        for w in pano.warnings:
            print("  -", w)
        if a.strict:
            sys.exit(1)
    else:
        print("✓ validator: no warnings")


if __name__ == "__main__":
    main()
