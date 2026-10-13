"""
Regenerates ui/themes/dark.qss and ui/themes/light.qss from
app/design/tokens.py, for reference / Qt Designer preview / diffing in
code review. The running app does NOT read these files anymore --
ThemeManager builds the stylesheet in memory at runtime -- but keeping
them on disk and in sync is useful for quickly eyeballing a color change
without launching the app.

Run from the project root:
    python scripts/generate_themes.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.design.tokens import PALETTES
from app.design.qss_builder import build_stylesheet

THEMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "themes")


def main():
    os.makedirs(THEMES_DIR, exist_ok=True)
    for name, palette in PALETTES.items():
        out_path = os.path.join(THEMES_DIR, f"{name}.qss")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(build_stylesheet(palette))
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
