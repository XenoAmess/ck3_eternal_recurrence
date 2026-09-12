"""Map coordinates from a rendered image preview to the live desktop.

The caller must provide the exact rendered preview dimensions.  There are no
defaults because preview renderers may independently resize either axis.
Interactive clicks additionally require a full-resolution desktop screenshot
and an after receipt screenshot.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Mapping:
    preview_bounds: tuple[float, float, int, int]
    observed_point: tuple[float, float]
    source_image_size: tuple[int, int]
    live_screen_size: tuple[int, int]
    screen_point: tuple[int, int]


def map_point(
    *,
    preview_bounds: tuple[float, float, int, int],
    observed_point: tuple[float, float],
    target_size: tuple[int, int],
) -> tuple[int, int]:
    preview_left, preview_top, preview_width, preview_height = preview_bounds
    observed_x, observed_y = observed_point
    target_width, target_height = target_size

    if preview_width <= 0 or preview_height <= 0:
        raise ValueError("preview dimensions must both be positive")
    if target_width <= 0 or target_height <= 0:
        raise ValueError("target dimensions must both be positive")
    preview_x = observed_x - preview_left
    preview_y = observed_y - preview_top
    if not 0 <= preview_x < preview_width:
        raise ValueError("observed x is outside the supplied image-content bounds")
    if not 0 <= preview_y < preview_height:
        raise ValueError("observed y is outside the supplied image-content bounds")

    # Scale axes independently.  Never infer or require an aspect ratio.
    target_x = round(preview_x * target_width / preview_width)
    target_y = round(preview_y * target_height / preview_height)
    return (
        min(max(target_x, 0), target_width - 1),
        min(max(target_y, 0), target_height - 1),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-image", type=Path, required=True)
    parser.add_argument("--preview-left", type=float, required=True)
    parser.add_argument("--preview-top", type=float, required=True)
    parser.add_argument("--preview-width", type=int, required=True)
    parser.add_argument("--preview-height", type=int, required=True)
    parser.add_argument("--observed-x", type=float, required=True)
    parser.add_argument("--observed-y", type=float, required=True)
    parser.add_argument("--click", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.click and args.receipt is None:
        parser.error("--click requires --receipt")
    if not args.click and args.receipt is not None:
        parser.error("--receipt is only valid with --click")
    return args


def main() -> int:
    args = parse_args()

    from PIL import Image
    import pyautogui

    with Image.open(args.source_image) as image:
        source_image_size = image.size
    live_screen_size = tuple(pyautogui.size())

    if source_image_size != live_screen_size:
        raise SystemExit(
            "refusing stale/foreign screenshot: "
            f"source image is {source_image_size[0]}x{source_image_size[1]}, "
            f"live screen is {live_screen_size[0]}x{live_screen_size[1]}"
        )

    screen_point = map_point(
        preview_bounds=(
            args.preview_left,
            args.preview_top,
            args.preview_width,
            args.preview_height,
        ),
        observed_point=(args.observed_x, args.observed_y),
        target_size=live_screen_size,
    )
    result = Mapping(
        preview_bounds=(
            args.preview_left,
            args.preview_top,
            args.preview_width,
            args.preview_height,
        ),
        observed_point=(args.observed_x, args.observed_y),
        source_image_size=source_image_size,
        live_screen_size=live_screen_size,
        screen_point=screen_point,
    )

    if args.click:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        pyautogui.click(*screen_point)
        receipt = pyautogui.screenshot(str(args.receipt))
        if receipt.size != live_screen_size:
            raise SystemExit(
                "receipt screenshot size changed after click: "
                f"{receipt.size} != {live_screen_size}"
            )

    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
