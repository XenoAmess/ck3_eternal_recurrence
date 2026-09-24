"""Episode-specific pixel witness that the Messina battle marker stays visible.

The reference screenshot and template rectangle must be manually checked once.
This gate supplements the native camera postcondition; it is not a generic
battle detector and does not prove strategic or mechanical claims.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2


DEFAULT_TEMPLATE_RECT = (423, 318, 447, 351)
DEFAULT_SEARCH_RECT = (220, 150, 780, 545)


def battle_marker_score(
    reference: Path,
    frame: Path,
    *,
    template_rect: tuple[int, int, int, int] = DEFAULT_TEMPLATE_RECT,
    search_rect: tuple[int, int, int, int] = DEFAULT_SEARCH_RECT,
) -> dict[str, object]:
    source = cv2.imread(str(reference), cv2.IMREAD_COLOR)
    target = cv2.imread(str(frame), cv2.IMREAD_COLOR)
    if source is None or target is None or source.shape != target.shape:
        raise ValueError("reference and frame must be readable images of the same size")
    x0, y0, x1, y1 = template_rect
    sx0, sy0, sx1, sy1 = search_rect
    height, width = source.shape[:2]
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError("template rectangle is outside the reference")
    if not (0 <= sx0 < sx1 <= width and 0 <= sy0 < sy1 <= height):
        raise ValueError("search rectangle is outside the frame")
    template = source[y0:y1, x0:x1]
    search = target[sy0:sy1, sx0:sx1]
    if search.shape[0] < template.shape[0] or search.shape[1] < template.shape[1]:
        raise ValueError("search area is smaller than the template")
    correlation = cv2.matchTemplate(search, template, cv2.TM_CCOEFF_NORMED)
    _minimum, maximum, _min_location, location = cv2.minMaxLoc(correlation)
    return {
        "score": float(maximum),
        "match_top_left": [sx0 + location[0], sy0 + location[1]],
        "template_rect": list(template_rect),
        "search_rect": list(search_rect),
        "image_size": [width, height],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--frame", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(battle_marker_score(args.reference, args.frame), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
