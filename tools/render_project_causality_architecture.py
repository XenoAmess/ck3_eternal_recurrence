#!/usr/bin/env python3
"""Render and verify the Project Causality Mermaid architecture atlas."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "docs" / "project-causality-architecture"
SOURCE = ATLAS / "src"
RENDERED = ATLAS / "rendered"
CONFIG = ATLAS / "mermaid-config.json"
CSS = ATLAS / "architecture.css"
MANIFEST = ATLAS / "render-manifest.json"
MERMAID_PACKAGE = "@mermaid-js/mermaid-cli@11.17.0"
BACKGROUND = "#07111f"
PNG_SCALE = 3
MIN_VIDEO_ASPECT = 1.40
MAX_VIDEO_ASPECT = 2.45


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def svg_dimensions(path: Path) -> dict[str, object]:
    head = path.read_text(encoding="utf-8")[:4096]
    match = re.search(r'viewBox="([^"]+)"', head)
    if not match:
        raise ValueError(f"SVG has no viewBox: {path}")
    values = [float(value) for value in match.group(1).split()]
    if len(values) != 4:
        raise ValueError(f"unexpected SVG viewBox: {path}")
    return {"view_box": values, "width": values[2], "height": values[3]}


def npx_command() -> str:
    override = os.environ.get("PROJECT_CAUSALITY_NPX")
    if override:
        return override
    for candidate in ("npx.cmd", "npx"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    windows_default = Path(r"C:\Program Files\nodejs\npx.cmd")
    if windows_default.is_file():
        return str(windows_default)
    raise RuntimeError("npx was not found; install Node.js or set PROJECT_CAUSALITY_NPX")


def render_one(npx: str, source: Path, destination: Path) -> None:
    command = [
        npx,
        "--yes",
        MERMAID_PACKAGE,
        "-i",
        str(source),
        "-o",
        str(destination),
        "-c",
        str(CONFIG),
        "-C",
        str(CSS),
        "-b",
        BACKGROUND,
        "-s",
        str(PNG_SCALE),
        "-q",
    ]
    environment = os.environ.copy()
    environment.setdefault("PUPPETEER_SKIP_DOWNLOAD", "true")
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


def expected_sources() -> list[Path]:
    sources = sorted(SOURCE.glob("*.mmd"))
    if not sources:
        raise RuntimeError(f"no Mermaid sources found under {SOURCE}")
    return sources


def build_manifest(sources: list[Path]) -> dict[str, object]:
    figures: list[dict[str, object]] = []
    for source in sources:
        svg = RENDERED / f"{source.stem}.svg"
        png = RENDERED / f"{source.stem}.png"
        width, height = png_dimensions(png)
        geometry = svg_dimensions(svg)
        aspect_ratio = float(geometry["width"]) / float(geometry["height"])
        if not MIN_VIDEO_ASPECT <= aspect_ratio <= MAX_VIDEO_ASPECT:
            raise ValueError(
                f"{source.name} native Mermaid aspect ratio {aspect_ratio:.3f} "
                f"is outside {MIN_VIDEO_ASPECT:.2f}..{MAX_VIDEO_ASPECT:.2f}"
            )
        figures.append(
            {
                "id": source.stem,
                "source": source.relative_to(ROOT).as_posix(),
                "source_sha256": sha256(source),
                "svg": svg.relative_to(ROOT).as_posix(),
                "svg_sha256": sha256(svg),
                "svg_geometry": geometry,
                "native_aspect_ratio": round(aspect_ratio, 6),
                "png": png.relative_to(ROOT).as_posix(),
                "png_sha256": sha256(png),
                "png_width": width,
                "png_height": height,
            }
        )
    return {
        "schema": "project-causality-architecture-render-manifest.v1",
        "renderer": MERMAID_PACKAGE,
        "background": BACKGROUND,
        "png_scale": PNG_SCALE,
        "native_video_aspect_contract": {
            "minimum": MIN_VIDEO_ASPECT,
            "maximum": MAX_VIDEO_ASPECT,
            "semantic": "Mermaid source layout; no downstream node reflow",
        },
        "config": CONFIG.relative_to(ROOT).as_posix(),
        "config_sha256": sha256(CONFIG),
        "css": CSS.relative_to(ROOT).as_posix(),
        "css_sha256": sha256(CSS),
        "figures": figures,
    }


def verify_manifest() -> None:
    if not MANIFEST.is_file():
        raise RuntimeError(f"missing render manifest: {MANIFEST}")
    actual = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = build_manifest(expected_sources())
    if actual != expected:
        raise RuntimeError(
            "architecture source/render manifest is stale; run "
            "py tools/render_project_causality_architecture.py"
        )


def render() -> None:
    sources = expected_sources()
    npx = npx_command()
    RENDERED.mkdir(parents=True, exist_ok=True)
    expected_outputs = {
        RENDERED / f"{source.stem}.{suffix}"
        for source in sources
        for suffix in ("svg", "png")
    }
    with tempfile.TemporaryDirectory(prefix="project-causality-architecture-") as temp_name:
        temp = Path(temp_name)
        for source in sources:
            for suffix in ("svg", "png"):
                temporary = temp / f"{source.stem}.{suffix}"
                render_one(npx, source, temporary)
                shutil.copyfile(temporary, RENDERED / temporary.name)
    for existing in RENDERED.iterdir():
        if existing.is_file() and existing.suffix.lower() in {".svg", ".png"}:
            if existing not in expected_outputs:
                existing.unlink()
    manifest = build_manifest(sources)
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that every source and rendered output matches the manifest",
    )
    args = parser.parse_args()
    try:
        if args.check:
            verify_manifest()
            print(f"GREEN: {len(expected_sources())} architecture figures match the manifest")
        else:
            render()
            verify_manifest()
            print(f"GREEN: rendered {len(expected_sources())} architecture figures")
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"RED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
