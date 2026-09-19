#!/usr/bin/env python3
"""Render native-Mermaid 2560x1440 plates from the architecture atlas.

The checked-in Mermaid SVG remains authoritative.  This renderer may change
only camera, opacity and emphasis; node coordinates and edges are never
reflowed after Mermaid has laid them out.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "docs" / "project-causality-architecture"
ATLAS_MANIFEST = ATLAS / "render-manifest.json"
DEFAULT_PLAN = ROOT / "promo" / "project_causality" / "30m" / "architecture-shot-plan.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "project-causality" / "architecture-video"
ATMOSPHERES = {
    "spell": ROOT / "images" / "project_causality" / "character" / "generated_atmospheres" / "spell-court-v1.png",
    "method": ROOT / "images" / "project_causality" / "character" / "generated_atmospheres" / "method-scriptorium-v1.png",
    "principle": ROOT / "images" / "project_causality" / "character" / "generated_atmospheres" / "principle-archive-v1.png",
    "vision": ROOT / "images" / "project_causality" / "character" / "generated_atmospheres" / "vision-four-loops-v1.png",
}
WIDTH = 2560
HEIGHT = 1440
BACKGROUND = "#07111f"


class ArchitectureVideoError(RuntimeError):
    """Raised when a video projection cannot be rendered faithfully."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ArchitectureVideoError(f"missing JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArchitectureVideoError(
            f"invalid JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise ArchitectureVideoError(f"JSON root must be an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ArchitectureVideoError(f"not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def _find_browser(override: str | None = None) -> Path:
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override))
    for command in ("chrome-headless-shell", "chrome", "msedge"):
        resolved = shutil.which(command)
        if resolved:
            candidates.append(Path(resolved))
    playwright = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
    candidates.extend(
        sorted(
            playwright.glob(
                "chromium_headless_shell-*/chrome-headless-shell-win64/chrome-headless-shell.exe"
            ),
            reverse=True,
        )
    )
    candidates.extend(
        [
            Path(os.environ.get("PROGRAMFILES", ""))
            / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", ""))
            / "Microsoft/Edge/Application/msedge.exe",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise ArchitectureVideoError(
        "no Chromium browser found; pass --browser or install Playwright Chromium"
    )


def _slug(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z_-]+", "-", value).strip("-")
    return value or "view"


def _data_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _atmosphere_key(diagram_id: str, view: str) -> str:
    """Choose a generated chapter scene; the raw avatar is never used as artwork."""

    if diagram_id == "01-overall-system":
        for key in ("spell", "method", "principle", "vision"):
            if view.startswith(key):
                return key
        return "vision"
    if diagram_id in {"02-loop-a-player-products", "09-product-family"}:
        return "spell"
    if diagram_id in {
        "03-loop-b-agent-capability",
        "04-loop-c-tooling-semantics",
        "06-agent-mcp-architecture",
        "07-automated-acceptance",
        "10-source-of-truth-projections",
    }:
        return "method"
    if diagram_id in {"05-loop-d-evidence-release", "08-authority-and-evidence"}:
        return "principle"
    return "vision"


def _atmosphere_url(diagram_id: str, view: str) -> str:
    path = ATMOSPHERES[_atmosphere_key(diagram_id, view)]
    if not path.is_file():
        raise ArchitectureVideoError(f"missing generated atmosphere: {path}")
    return _data_url(path)


def _svg_viewbox_size(svg: str) -> tuple[float, float]:
    match = re.search(r'\bviewBox="([^"]+)"', svg)
    if not match:
        raise ArchitectureVideoError("Mermaid SVG has no viewBox")
    values = [float(value) for value in match.group(1).split()]
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        raise ArchitectureVideoError(f"invalid Mermaid SVG viewBox: {match.group(1)}")
    return values[2], values[3]


def _emphasize_native_svg(svg: str, focus: list[str], topology: bool) -> str:
    """Apply opacity to Mermaid nodes without changing topology or coordinates."""

    if topology:
        return svg
    active = set(focus)
    node_tag = re.compile(r'<g(?P<attrs>[^>]*class="[^"]*\bnode\b[^"]*"[^>]*)>')

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        id_match = re.search(r'\bid="([^"]+)"', attrs)
        node_id = ""
        if id_match:
            element_id = id_match.group(1)
            flowchart = re.search(r'(?:^|-)flowchart-([A-Za-z0-9]+)-\d+$', element_id)
            simple = re.fullmatch(r'my-svg-([A-Za-z0-9]+)', element_id)
            if flowchart:
                node_id = flowchart.group(1)
            elif simple:
                node_id = simple.group(1)
        opacity = "1" if node_id in active else "0.18"
        glow = (
            "filter:drop-shadow(0 0 7px rgba(85,200,255,.5));"
            if node_id in active
            else ""
        )
        style = f' style="opacity:{opacity};{glow}"'
        return f"<g{attrs}{style}>"

    return node_tag.sub(replace, svg)


DIAGRAM_TITLES: dict[str, tuple[str, str]] = {
    "01-overall-system": ("整套系统", "SYSTEM ARCHITECTURE"),
    "02-loop-a-player-products": ("Loop A｜玩家产品", "PLAYER PRODUCT LOOP"),
    "03-loop-b-agent-capability": ("Loop B｜智能体能力", "AGENT CAPABILITY LOOP"),
    "04-loop-c-tooling-semantics": ("Loop C｜工具与语义", "TOOLING & SEMANTICS LOOP"),
    "05-loop-d-evidence-release": ("Loop D｜证据与发行", "EVIDENCE & RELEASE LOOP"),
    "06-agent-mcp-architecture": ("自动游玩智能体 + MCP", "AUTONOMOUS PLAYER + MCP"),
    "07-automated-acceptance": ("自动化验收", "AUTOMATED ACCEPTANCE"),
    "08-authority-and-evidence": ("权威与证据", "AUTHORITY & EVIDENCE"),
    "09-product-family": ("产品族与共享底座", "PRODUCT FAMILY & SHARED FOUNDATION"),
    "10-source-of-truth-projections": ("权威源与派生投影", "SOURCE OF TRUTH & PROJECTIONS"),
    "11-four-loop-flywheel": ("四环飞轮", "THE FOUR-LOOP FLYWHEEL"),
}


def _escape_script_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def _atlas_html(
    svg: str,
    *,
    diagram_id: str,
    focus: list[str],
    view: str,
    purpose: str,
) -> str:
    title_zh, title_en = DIAGRAM_TITLES[diagram_id]
    atmosphere = _atmosphere_url(diagram_id, view)
    topology = view == "topology_silhouette"
    svg = _emphasize_native_svg(svg, focus, topology)
    source_width, source_height = _svg_viewbox_size(svg)
    native_scale = min(2200 / source_width, 960 / source_height, 1.70)
    native_left = (2320 - source_width * native_scale) / 2
    native_top = (1040 - source_height * native_scale) / 2
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><style>
html,body{{margin:0;width:{WIDTH}px;height:{HEIGHT}px;overflow:hidden;background:{BACKGROUND};}}
body{{font-family:'Microsoft YaHei UI','Segoe UI',sans-serif;color:#f4f8ff;
background:radial-gradient(circle at 78% 18%,#244b70 0%,#10263d 36%,#091522 100%);}}
#atmosphere{{position:absolute;left:-28px;right:-28px;bottom:-24px;height:82%;background:url('{atmosphere}') center bottom/cover no-repeat;opacity:{.34 if topology else .4};filter:blur(3px) saturate(.86) contrast(.96) brightness(1.08);transform:scale(1.025);-webkit-mask-image:linear-gradient(to bottom,transparent 0%,rgba(0,0,0,.24) 18%,rgba(0,0,0,.82) 52%,#000 100%);}}
#atmosphere-shade{{position:absolute;inset:0;background:linear-gradient(to bottom,rgba(5,13,24,.86) 0 18%,rgba(5,13,24,.56) 48%,rgba(5,13,24,.22) 100%);}}
#grain{{position:absolute;inset:0;opacity:.14;background-image:linear-gradient(115deg,transparent 0 48%,rgba(85,200,255,.09) 49%,transparent 50%),linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px);background-size:780px 780px,42px 42px;}}
#eyebrow{{position:absolute;left:120px;top:66px;color:#55c8ff;font-size:24px;font-weight:700;letter-spacing:4px;}}
#title{{position:absolute;left:120px;top:104px;font-size:48px;font-weight:800;letter-spacing:1px;}}
#title-en{{position:absolute;left:120px;top:166px;color:#a9c1dd;font-size:22px;font-weight:700;letter-spacing:2px;}}
#purpose{{position:absolute;right:120px;top:106px;width:980px;text-align:right;color:#dce9f7;font-size:29px;line-height:1.45;}}
#rule{{position:absolute;left:120px;right:120px;top:218px;height:2px;background:linear-gradient(90deg,#55c8ff,rgba(85,200,255,.08));}}
#viewport{{position:absolute;left:120px;top:236px;width:2320px;height:1040px;overflow:hidden;border-radius:30px;background:rgba(3,8,16,.28);box-shadow:inset 0 0 0 2px rgba(146,198,239,.28),0 28px 90px rgba(0,0,0,.28);}}
#diagram{{position:absolute;left:0;top:0;width:{source_width}px;height:{source_height}px;will-change:transform;transform-origin:0 0;transform:translate({native_left}px,{native_top}px) scale({native_scale});}}
#diagram svg{{display:block;overflow:visible;background:transparent !important;max-width:none !important;width:{source_width}px !important;height:{source_height}px !important;}}
#view-label{{position:absolute;left:144px;top:1302px;color:#86a9ca;font-size:24px;letter-spacing:2px;text-transform:uppercase;}}
#legend{{position:absolute;right:120px;top:1297px;display:flex;gap:28px;color:#9fb5cc;font-size:20px;}}
.dot{{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:9px;}}
#subtitle-guard{{display:none;}}
</style></head><body>
<div id="atmosphere"></div><div id="atmosphere-shade"></div><div id="grain"></div><div id="eyebrow">PROJECT CAUSALITY / ARCHITECTURE</div>
<div id="title">{title_zh}</div><div id="title-en">{title_en}</div>
<div id="purpose">{purpose}</div><div id="rule"></div>
<div id="viewport"><div id="diagram">{svg}</div></div>
<div id="view-label">{view.replace('_', ' ')}</div>
<div id="legend"><span><i class="dot" style="background:#38d6c5"></i>CURRENT</span><span><i class="dot" style="background:#ff8a4c"></i>LOOP</span><span><i class="dot" style="background:#ff6b6b"></i>RED / BOUNDARY</span></div>
<div id="subtitle-guard"></div>
<script>
const focus={_escape_script_json(focus)};
const topology={str(topology).lower()};
const viewport=document.getElementById('viewport');
const holder=document.getElementById('diagram');
const svg=holder.querySelector('svg');
const sourceW=svg.viewBox.baseVal.width||parseFloat(svg.getAttribute('width'));
const sourceH=svg.viewBox.baseVal.height||parseFloat(svg.getAttribute('height'));
svg.style.cssText=`display:block;overflow:visible;background:transparent;max-width:none;width:${{sourceW}}px;height:${{sourceH}}px`;
svg.setAttribute('width',sourceW);svg.setAttribute('height',sourceH);
function node(id){{
  return document.getElementById('my-svg-'+id) ||
    document.querySelector('[id^="my-svg-flowchart-'+id+'-"]') ||
    document.querySelector('[id*="-flowchart-'+id+'-"]');
}}
const allNodes=[...svg.querySelectorAll('g.node')];
const active=new Set(focus.map(node).filter(Boolean));
allNodes.forEach(el=>{{
  const on=topology||active.has(el);
  el.style.opacity=on?'1':'0.18';
  if(on&&!topology) el.style.filter='drop-shadow(0 0 7px rgba(85,200,255,.5))';
}});
const focusedTokens=new Set(focus);
svg.querySelectorAll('path.flowchart-link').forEach(path=>{{
  const value=path.id||path.parentElement?.id||'';
  const hits=[...focusedTokens].filter(token=>value.includes('_'+token+'_')||value.endsWith('_'+token+'_0'));
  path.style.opacity=topology?'0.72':(hits.length>=2?'1':hits.length===1?'0.5':'0.12');
  if(hits.length>=2&&!topology){{path.style.strokeWidth='4px';path.style.filter='drop-shadow(0 0 5px rgba(85,200,255,.55))';}}
}});
svg.querySelectorAll('.edgeLabel').forEach(label=>{{
  const text=(label.textContent||'').trim();
  label.style.opacity=topology?'0.8':(text?'0.58':'0.18');
}});
// Every plate shows the complete Mermaid-native graph.  Focus changes emphasis,
// never framing: this prevents a local beat from hiding a loop return edge or
// turning SVG viewport units into a second, incompatible coordinate system.
const scale=Math.min(2200/sourceW,960/sourceH,1.70);
const left=(2320-sourceW*scale)/2;
const top=(1040-sourceH*scale)/2;
holder.style.transformOrigin='0 0';
holder.style.transform=`translate(${{left}}px,${{top}}px) scale(${{scale}})`;
document.body.dataset.ready='1';
</script></body></html>"""


def _screenshot(browser: Path, html: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(browser),
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--allow-file-access-from-files",
        "--force-device-scale-factor=1",
        f"--window-size={WIDTH},{HEIGHT}",
        "--virtual-time-budget=1000",
        f"--screenshot={destination}",
        html.resolve().as_uri(),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0 or not destination.is_file():
        raise ArchitectureVideoError(
            f"Chromium screenshot failed ({completed.returncode}): {completed.stdout[-2000:]}"
        )
    if _png_dimensions(destination) != (WIDTH, HEIGHT):
        raise ArchitectureVideoError(
            f"unexpected screenshot size for {destination}: {_png_dimensions(destination)}"
        )


def render(plan_path: Path, output: Path, browser: Path) -> dict[str, Any]:
    plan = _load_json(plan_path)
    atlas = _load_json(ATLAS_MANIFEST)
    atlas_rows = {row["id"]: row for row in atlas.get("figures", [])}
    records: list[dict[str, Any]] = []
    output.mkdir(parents=True, exist_ok=True)
    expected: set[Path] = set()
    with tempfile.TemporaryDirectory(prefix="project-causality-architecture-video-") as name:
        temporary = Path(name)
        for shot in plan.get("shots", []):
            if not isinstance(shot, dict):
                raise ArchitectureVideoError("shot plan entries must be objects")
            diagram_id = str(shot["diagram_id"])
            atlas_row = atlas_rows.get(diagram_id)
            if atlas_row is None:
                raise ArchitectureVideoError(f"unknown atlas figure: {diagram_id}")
            svg_path = ROOT / str(atlas_row["svg"])
            svg_text = svg_path.read_text(encoding="utf-8")
            for index, beat in enumerate(shot.get("beats", [])):
                if not str(beat.get("kind", "")).startswith("diagram"):
                    continue
                view = str(beat.get("view", f"view-{index + 1}"))
                focus = [str(value) for value in beat.get("focus", [])]
                filename = f"{_slug(str(shot['id']))}-{index + 1:02d}-{_slug(view)}.png"
                destination = output / filename
                expected.add(destination)
                html_text = _atlas_html(
                    svg_text,
                    diagram_id=diagram_id,
                    focus=focus,
                    view=view,
                    purpose=str(shot.get("purpose", "")),
                )
                html = temporary / f"{filename}.html"
                html.write_text(html_text, encoding="utf-8", newline="\n")
                _screenshot(browser, html, destination)
                records.append(
                    {
                        "shot_id": shot["id"],
                        "segment_id": shot["segment_id"],
                        "diagram_id": diagram_id,
                        "beat_index": index,
                        "kind": beat["kind"],
                        "view": view,
                        "focus": focus,
                        "source_start": beat["start"],
                        "source_end": beat["end"],
                        "path": destination.relative_to(ROOT).as_posix(),
                        "sha256": _sha256(destination),
                        "width": WIDTH,
                        "height": HEIGHT,
                    }
                )
    for existing in output.glob("*.png"):
        if existing not in expected:
            existing.unlink()
    result = {
        "schema": "project-causality-architecture-video-plates.v1",
        "plan": plan_path.relative_to(ROOT).as_posix(),
        "plan_sha256": _sha256(plan_path),
        "atlas_manifest": ATLAS_MANIFEST.relative_to(ROOT).as_posix(),
        "atlas_manifest_sha256": _sha256(ATLAS_MANIFEST),
        "browser": str(browser),
        "width": WIDTH,
        "height": HEIGHT,
        "projection_mode": "native-mermaid-svg-full-topology-with-emphasis-only",
        "node_reflow": False,
        "atmospheres": [
            {
                "chapter": key,
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": _sha256(path),
            }
            for key, path in ATMOSPHERES.items()
        ],
        "plates": records,
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


def verify(plan_path: Path, output: Path) -> dict[str, Any]:
    manifest_path = output / "manifest.json"
    manifest = _load_json(manifest_path)
    if manifest.get("plan_sha256") != _sha256(plan_path):
        raise ArchitectureVideoError("video plate manifest is stale against shot plan")
    if manifest.get("atlas_manifest_sha256") != _sha256(ATLAS_MANIFEST):
        raise ArchitectureVideoError("video plate manifest is stale against atlas")
    atmosphere_rows = {
        row.get("chapter"): row for row in manifest.get("atmospheres", [])
    }
    for key, path in ATMOSPHERES.items():
        row = atmosphere_rows.get(key)
        if row is None or not path.is_file() or row.get("sha256") != _sha256(path):
            raise ArchitectureVideoError(
                f"video plate manifest is stale against atmosphere: {key}"
            )
    for row in manifest.get("plates", []):
        path = ROOT / str(row["path"])
        if not path.is_file() or _sha256(path) != row.get("sha256"):
            raise ArchitectureVideoError(f"missing or stale plate: {path}")
        if _png_dimensions(path) != (WIDTH, HEIGHT):
            raise ArchitectureVideoError(f"plate has wrong dimensions: {path}")
    return manifest


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    result.add_argument("--browser")
    result.add_argument("--check", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        plan = args.plan.expanduser().resolve()
        output = args.output.expanduser().resolve()
        if args.check:
            manifest = verify(plan, output)
            print(f"GREEN: {len(manifest['plates'])} architecture video plates match")
        else:
            browser = _find_browser(args.browser)
            manifest = render(plan, output, browser)
            verify(plan, output)
            print(f"GREEN: rendered {len(manifest['plates'])} architecture video plates")
            print(f"MANIFEST: {output / 'manifest.json'}")
        return 0
    except (ArchitectureVideoError, OSError, ValueError) as exc:
        print(f"RED: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


