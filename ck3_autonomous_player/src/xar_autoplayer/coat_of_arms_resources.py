"""Offline MCP catalog for CK3's base-game coat-of-arms designer assets."""

from __future__ import annotations

import base64
import colorsys
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Final


CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_BUILD: Final = "1.19.0.6"
CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256: Final = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
CK3_COAT_OF_ARMS_RESOURCE_KINDS: Final = (
    "pattern",
    "colored_emblem",
    "color",
)
_MAX_MANIFEST_BYTES: Final = 2 * 1024 * 1024
_MAX_ASSET_BYTES: Final = 1024 * 1024
_MAX_PAGE_SIZE: Final = 200
_MANIFESTS: Final = {
    "pattern": Path(
        "game/gfx/coat_of_arms/patterns/50_coa_designer_patterns.txt"
    ),
    "colored_emblem": Path(
        "game/gfx/coat_of_arms/colored_emblems/50_coa_designer_emblems.txt"
    ),
    "color": Path(
        "game/gfx/coat_of_arms/color_palettes/50_coa_designer_palettes.txt"
    ),
}
_ASSET_DIRECTORIES: Final = {
    "pattern": Path("game/gfx/coat_of_arms/patterns"),
    "colored_emblem": Path("game/gfx/coat_of_arms/colored_emblems"),
}
_RENDER_MASK: Final = Path("game/gfx/coat_of_arms/coa_mask_texture.dds")
_TEXTURED_EMBLEM_DEFAULT: Final = Path(
    "game/gfx/coat_of_arms/textured_emblems/_default.dds"
)
_NAMED_COLORS: Final = Path("game/common/named_colors/default_colors.txt")
_RENDER_SHADER_SOURCES: Final = (
    Path("clausewitz/gfx/FX/cw/utility.fxh"),
    Path("jomini/gfx/FX/coat_of_arms/coat_of_arms_pattern.fxh"),
    Path("jomini/gfx/FX/coat_of_arms/coat_of_arms_textured_emblem.fxh"),
    Path("game/gfx/FX/coat_of_arms/coat_of_arms_pattern.shader"),
    Path("game/gfx/FX/coat_of_arms/coat_of_arms_textured_emblem.shader"),
)
_NAMED_COLOR_LINE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
    r"(hsv360|hsv|rgb)?\s*\{\s*"
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s+"
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s+"
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*\}"
)


class CoatOfArmsResourceCatalogError(RuntimeError):
    """Raised when an installation cannot provide the strict v1 catalog."""


@dataclass(frozen=True)
class _Token:
    value: str
    line: int
    column: int


@dataclass(frozen=True)
class _Scalar:
    value: str


@dataclass(frozen=True)
class _Block:
    entries: tuple[tuple[str, "_Value"], ...]


_Value = _Scalar | _Block


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _dds_metadata(data: bytes) -> dict[str, object]:
    if len(data) < 128 or data[:4] != b"DDS ":
        raise CoatOfArmsResourceCatalogError("render support asset is not DDS")
    if int.from_bytes(data[4:8], "little") != 124:
        raise CoatOfArmsResourceCatalogError("render support DDS header is invalid")
    try:
        four_cc = data[84:88].decode("ascii")
    except UnicodeDecodeError as error:
        raise CoatOfArmsResourceCatalogError(
            "render support DDS FourCC is not ASCII"
        ) from error
    dds_format = four_cc
    if (
        four_cc == "\0\0\0\0"
        and int.from_bytes(data[88:92], "little") == 32
        and int.from_bytes(data[92:96], "little") == 0x00FF0000
        and int.from_bytes(data[96:100], "little") == 0x0000FF00
        and int.from_bytes(data[100:104], "little") == 0x000000FF
        and int.from_bytes(data[104:108], "little") == 0xFF000000
    ):
        dds_format = "BGRA8"
    return {
        "width": int.from_bytes(data[16:20], "little"),
        "height": int.from_bytes(data[12:16], "little"),
        "mipmap_count": max(1, int.from_bytes(data[28:32], "little")),
        "four_cc": four_cc,
        "format": dds_format,
    }


def _named_colors(path: Path) -> list[dict[str, object]]:
    if not path.is_file() or not 0 < path.stat().st_size <= _MAX_MANIFEST_BYTES:
        raise CoatOfArmsResourceCatalogError(
            "default named-color source is missing or outside the size contract"
        )
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeError as error:
        raise CoatOfArmsResourceCatalogError(
            "default named-color source is not UTF-8"
        ) from error
    result: list[dict[str, object]] = []
    for line in text.splitlines():
        match = _NAMED_COLOR_LINE.match(line)
        if not match:
            continue
        name, model, first, second, third = match.groups()
        components = tuple(float(value) for value in (first, second, third))
        if model == "hsv360":
            hue, saturation, value = (
                components[0] / 360.0,
                components[1] / 100.0,
                components[2] / 100.0,
            )
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        elif model == "hsv":
            rgb = colorsys.hsv_to_rgb(*components)
        else:
            divisor = 255.0 if any(value > 1.0 for value in components) else 1.0
            rgb = tuple(value / divisor for value in components)
        if any(value < 0.0 or value > 1.0 for value in rgb):
            raise CoatOfArmsResourceCatalogError(
                f"named color {name} resolves outside RGB 0..1"
            )
        result.append(
            {
                "name": name,
                "model": model or "rgb",
                "components": list(components),
                "rgb": [round(value, 9) for value in rgb],
                "rgb_255": [round(value * 255) for value in rgb],
            }
        )
    if not result:
        raise CoatOfArmsResourceCatalogError(
            "default named-color source contains no supported definitions"
        )
    return result


def _tokenize(text: str) -> tuple[_Token, ...]:
    result: list[_Token] = []
    index = 0
    line = 1
    column = 1
    while index < len(text):
        character = text[index]
        if character in " \t\r":
            index += 1
            column += 1
            continue
        if character == "\n":
            index += 1
            line += 1
            column = 1
            continue
        if character == "#":
            while index < len(text) and text[index] != "\n":
                index += 1
                column += 1
            continue
        if character in "{}=":
            result.append(_Token(character, line, column))
            index += 1
            column += 1
            continue
        start_line = line
        start_column = column
        if character == '"':
            index += 1
            column += 1
            value: list[str] = []
            while index < len(text) and text[index] != '"':
                if text[index] in "\r\n":
                    raise CoatOfArmsResourceCatalogError(
                        f"unterminated string at {start_line}:{start_column}"
                    )
                if text[index] == "\\" and index + 1 < len(text):
                    index += 1
                    column += 1
                value.append(text[index])
                index += 1
                column += 1
            if index >= len(text):
                raise CoatOfArmsResourceCatalogError(
                    f"unterminated string at {start_line}:{start_column}"
                )
            index += 1
            column += 1
            result.append(_Token("".join(value), start_line, start_column))
            continue
        start = index
        while index < len(text) and text[index] not in " \t\r\n#{}=\"":
            index += 1
            column += 1
        if start == index:
            raise CoatOfArmsResourceCatalogError(
                f"unexpected character at {line}:{column}"
            )
        result.append(_Token(text[start:index], start_line, start_column))
    return tuple(result)


class _Parser:
    def __init__(self, tokens: tuple[_Token, ...]) -> None:
        self.tokens = tokens
        self.index = 0

    def document(self) -> tuple[tuple[str, _Value], ...]:
        entries = self._entries(stop_at_brace=False)
        if self.index != len(self.tokens):
            token = self.tokens[self.index]
            raise CoatOfArmsResourceCatalogError(
                f"unexpected token at {token.line}:{token.column}"
            )
        return entries

    def _entries(self, *, stop_at_brace: bool) -> tuple[tuple[str, _Value], ...]:
        result: list[tuple[str, _Value]] = []
        while self.index < len(self.tokens):
            if self.tokens[self.index].value == "}":
                if not stop_at_brace:
                    token = self.tokens[self.index]
                    raise CoatOfArmsResourceCatalogError(
                        f"unexpected closing brace at {token.line}:{token.column}"
                    )
                self.index += 1
                return tuple(result)
            key = self._take().value
            if self._take().value != "=":
                token = self.tokens[self.index - 1]
                raise CoatOfArmsResourceCatalogError(
                    f"expected '=' at {token.line}:{token.column}"
                )
            token = self._take()
            if token.value == "{":
                value: _Value = _Block(self._entries(stop_at_brace=True))
            elif token.value in "}=":
                raise CoatOfArmsResourceCatalogError(
                    f"expected value at {token.line}:{token.column}"
                )
            else:
                value = _Scalar(token.value)
            result.append((key, value))
        if stop_at_brace:
            raise CoatOfArmsResourceCatalogError("unterminated block")
        return tuple(result)

    def _take(self) -> _Token:
        if self.index >= len(self.tokens):
            raise CoatOfArmsResourceCatalogError("unexpected end of manifest")
        token = self.tokens[self.index]
        self.index += 1
        return token


def _property(block: _Block, name: str) -> str | None:
    values = [
        value.value
        for key, value in block.entries
        if key == name and isinstance(value, _Scalar)
    ]
    if len(values) > 1:
        raise CoatOfArmsResourceCatalogError(
            f"designer manifest repeats scalar property {name}"
        )
    return values[0] if values else None


def _designer_entries_text(kind: str, text: str) -> list[dict[str, object]]:
    entries = _Parser(_tokenize(text)).document()
    if kind == "color":
        palettes = [
            value
            for key, value in entries
            if key == "coa_designer_background_colors"
            and isinstance(value, _Block)
        ]
        if len(palettes) != 1:
            raise CoatOfArmsResourceCatalogError(
                "background color palette must occur exactly once"
            )
        return [
            {
                "name": name,
                "colors": None,
                "visible": True,
                "category": "background",
            }
            for name, value in palettes[0].entries
            if isinstance(value, _Block)
        ]

    result: list[dict[str, object]] = []
    for name, value in entries:
        if not isinstance(value, _Block):
            raise CoatOfArmsResourceCatalogError(
                f"designer resource {name} must be a block"
            )
        colors_text = _property(value, "colors")
        try:
            colors = 3 if colors_text is None else int(colors_text)
        except ValueError as error:
            raise CoatOfArmsResourceCatalogError(
                f"designer resource {name} has invalid colors"
            ) from error
        if not 0 <= colors <= 3:
            raise CoatOfArmsResourceCatalogError(
                f"designer resource {name} has colors outside 0..3"
            )
        visible_text = _property(value, "visible")
        if visible_text not in {None, "yes", "no"}:
            raise CoatOfArmsResourceCatalogError(
                f"designer resource {name} has invalid visibility"
            )
        category = _property(value, "category")
        result.append(
            {
                "name": name,
                "colors": colors,
                "visible": visible_text != "no",
                "category": category,
            }
        )
    return result


def _designer_entries(kind: str, manifest: Path) -> list[dict[str, object]]:
    size = manifest.stat().st_size
    if size <= 0 or size > _MAX_MANIFEST_BYTES:
        raise CoatOfArmsResourceCatalogError(
            "designer manifest size is outside the v1 contract"
        )
    try:
        text = manifest.read_text(encoding="utf-8-sig")
    except UnicodeError as error:
        raise CoatOfArmsResourceCatalogError(
            "designer manifest is not UTF-8"
        ) from error
    return _designer_entries_text(kind, text)


def query_coat_of_arms_resource_catalog_v1(
    game_directory: str,
    kind: str,
    *,
    query: str | None = None,
    visible_only: bool = True,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, object]:
    """Return one bounded page from the exact base-game designer manifest."""

    if not isinstance(game_directory, str) or not game_directory.strip():
        raise ValueError("game_directory must be a non-empty string")
    if kind not in CK3_COAT_OF_ARMS_RESOURCE_KINDS:
        raise ValueError(
            "kind must be pattern, colored_emblem, or color"
        )
    if query is not None and (not isinstance(query, str) or len(query) > 128):
        raise ValueError("query must be null or a string of at most 128 characters")
    if not isinstance(visible_only, bool):
        raise ValueError("visible_only must be boolean")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or not 1 <= limit <= _MAX_PAGE_SIZE
    ):
        raise ValueError(f"limit must be between 1 and {_MAX_PAGE_SIZE}")

    game_root = Path(game_directory).expanduser().resolve()
    executable = game_root / "binaries" / "ck3.exe"
    manifest_relative = _MANIFESTS[kind]
    manifest = game_root / manifest_relative
    if not executable.is_file() or not manifest.is_file():
        raise CoatOfArmsResourceCatalogError(
            "game_directory lacks the CK3 executable or designer manifest"
        )
    executable_sha256 = _sha256(executable)
    if executable_sha256 != CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256:
        raise CoatOfArmsResourceCatalogError(
            "CK3 executable does not match the frozen 1.19.0.6 catalog build"
        )

    resources = _designer_entries(kind, manifest)
    needle = (query or "").casefold().strip()
    filtered = [
        resource
        for resource in resources
        if (not visible_only or resource["visible"] is True)
        and (
            not needle
            or needle in str(resource["name"]).casefold()
            or needle in str(resource["category"] or "").casefold()
        )
    ]
    page = filtered[offset : offset + limit]
    items: list[dict[str, object]] = []
    asset_directory = _ASSET_DIRECTORIES.get(kind)
    for source_index, resource in enumerate(page, start=offset):
        if asset_directory is None:
            relative_path = None
            asset_exists = None
            asset_bytes = None
            asset_sha256 = None
        else:
            asset_relative = asset_directory / str(resource["name"])
            asset = game_root / asset_relative
            relative_path = asset_relative.as_posix()
            asset_exists = asset.is_file()
            asset_bytes = asset.stat().st_size if asset_exists else None
            asset_sha256 = _sha256(asset) if asset_exists else None
        items.append(
            {
                "index": source_index,
                **resource,
                "relative_path": relative_path,
                "asset_exists": asset_exists,
                "asset_bytes": asset_bytes,
                "asset_sha256": asset_sha256,
            }
        )

    next_offset = offset + len(page)
    has_more = next_offset < len(filtered)
    return {
        "schema": "ck3-coat-of-arms-resource-catalog-v1",
        "schema_version": 1,
        "status": "indexed",
        "ck3_build": CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_BUILD,
        "kind": kind,
        "query": query,
        "visible_only": visible_only,
        "offset": offset,
        "limit": limit,
        "total": len(filtered),
        "returned": len(items),
        "has_more": has_more,
        "next_offset": next_offset if has_more else None,
        "items": items,
        "provenance": {
            "mode": "base-game-designer-manifest-static",
            "executable_sha256": executable_sha256,
            "manifest_relative_path": manifest_relative.as_posix(),
            "manifest_bytes": manifest.stat().st_size,
            "manifest_sha256": _sha256(manifest),
            "engine_registration_observed": False,
            "dlc_and_mod_overrides_included": False,
        },
    }


def read_coat_of_arms_resource_asset_v1(
    game_directory: str,
    kind: str,
    name: str,
) -> dict[str, object]:
    """Return one manifest-owned base-game DDS asset as bounded base64."""

    if not isinstance(game_directory, str) or not game_directory.strip():
        raise ValueError("game_directory must be a non-empty string")
    if kind not in _ASSET_DIRECTORIES:
        raise ValueError("kind must be pattern or colored_emblem")
    if not isinstance(name, str) or not name or len(name) > 128:
        raise ValueError("name must be a non-empty string of at most 128 characters")

    game_root = Path(game_directory).expanduser().resolve()
    executable = game_root / "binaries" / "ck3.exe"
    manifest_relative = _MANIFESTS[kind]
    manifest = game_root / manifest_relative
    if not executable.is_file() or not manifest.is_file():
        raise CoatOfArmsResourceCatalogError(
            "game_directory lacks the CK3 executable or designer manifest"
        )
    executable_sha256 = _sha256(executable)
    if executable_sha256 != CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256:
        raise CoatOfArmsResourceCatalogError(
            "CK3 executable does not match the frozen 1.19.0.6 catalog build"
        )

    matches = [
        resource
        for resource in _designer_entries(kind, manifest)
        if resource["name"] == name
    ]
    if len(matches) != 1:
        raise CoatOfArmsResourceCatalogError(
            "asset name is not uniquely owned by the designer manifest"
        )
    resource = matches[0]
    asset_relative = _ASSET_DIRECTORIES[kind] / name
    asset = game_root / asset_relative
    if not asset.is_file():
        raise CoatOfArmsResourceCatalogError(
            "designer manifest asset is missing"
        )
    size = asset.stat().st_size
    if size < 128 or size > _MAX_ASSET_BYTES:
        raise CoatOfArmsResourceCatalogError(
            "designer DDS size is outside the v1 asset contract"
        )
    data = asset.read_bytes()
    if data[:4] != b"DDS " or int.from_bytes(data[4:8], "little") != 124:
        raise CoatOfArmsResourceCatalogError(
            "designer asset is not a supported DDS container"
        )
    four_cc_bytes = data[84:88]
    try:
        four_cc = four_cc_bytes.decode("ascii")
    except UnicodeDecodeError as error:
        raise CoatOfArmsResourceCatalogError(
            "designer DDS FourCC is not ASCII"
        ) from error

    return {
        "schema": "ck3-coat-of-arms-resource-asset-v1",
        "schema_version": 1,
        "status": "read",
        "ck3_build": CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_BUILD,
        "kind": kind,
        "name": name,
        "colors": resource["colors"],
        "visible": resource["visible"],
        "category": resource["category"],
        "relative_path": asset_relative.as_posix(),
        "content_type": "application/octet-stream",
        "asset_bytes": size,
        "asset_sha256": hashlib.sha256(data).hexdigest().upper(),
        "asset_base64": base64.b64encode(data).decode("ascii"),
        "dds": {
            "width": int.from_bytes(data[16:20], "little"),
            "height": int.from_bytes(data[12:16], "little"),
            "mipmap_count": max(1, int.from_bytes(data[28:32], "little")),
            "four_cc": four_cc,
            "format": four_cc,
        },
        "provenance": {
            "mode": "base-game-designer-manifest-static",
            "executable_sha256": executable_sha256,
            "manifest_relative_path": manifest_relative.as_posix(),
            "manifest_sha256": _sha256(manifest),
            "engine_registration_observed": False,
            "dlc_and_mod_overrides_included": False,
        },
    }


def read_coat_of_arms_render_support_v1(
    game_directory: str,
) -> dict[str, object]:
    """Return exact-build shader provenance and bounded offline render inputs."""

    if not isinstance(game_directory, str) or not game_directory.strip():
        raise ValueError("game_directory must be a non-empty string")
    game_root = Path(game_directory).expanduser().resolve()
    executable = game_root / "binaries" / "ck3.exe"
    if not executable.is_file():
        raise CoatOfArmsResourceCatalogError(
            "game_directory lacks the CK3 executable"
        )
    executable_sha256 = _sha256(executable)
    if executable_sha256 != CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256:
        raise CoatOfArmsResourceCatalogError(
            "CK3 executable does not match the frozen 1.19.0.6 render build"
        )

    required = (
        _RENDER_MASK,
        _TEXTURED_EMBLEM_DEFAULT,
        _NAMED_COLORS,
        *_RENDER_SHADER_SOURCES,
    )
    missing = [
        path.as_posix()
        for path in required
        if not (game_root / path).is_file()
    ]
    if missing:
        raise CoatOfArmsResourceCatalogError(
            "game_directory lacks render support files: " + ", ".join(missing)
        )
    mask_path = game_root / _RENDER_MASK
    if not 128 <= mask_path.stat().st_size <= _MAX_ASSET_BYTES:
        raise CoatOfArmsResourceCatalogError(
            "coat-of-arms mask is outside the v1 size contract"
        )
    mask_data = mask_path.read_bytes()
    textured_default_path = game_root / _TEXTURED_EMBLEM_DEFAULT
    if not 128 <= textured_default_path.stat().st_size <= _MAX_ASSET_BYTES:
        raise CoatOfArmsResourceCatalogError(
            "default textured emblem is outside the v1 size contract"
        )
    textured_default_data = textured_default_path.read_bytes()
    named_colors_path = game_root / _NAMED_COLORS
    shader_sources = [
        {
            "relative_path": path.as_posix(),
            "bytes": (game_root / path).stat().st_size,
            "sha256": _sha256(game_root / path),
        }
        for path in _RENDER_SHADER_SOURCES
    ]
    return {
        "schema": "ck3-coat-of-arms-render-support-v1",
        "schema_version": 1,
        "status": "read",
        "ck3_build": CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_BUILD,
        "named_colors": _named_colors(named_colors_path),
        "surface_mask": {
            "relative_path": _RENDER_MASK.as_posix(),
            "content_type": "application/octet-stream",
            "asset_bytes": len(mask_data),
            "asset_sha256": hashlib.sha256(mask_data).hexdigest().upper(),
            "asset_base64": base64.b64encode(mask_data).decode("ascii"),
            "dds": _dds_metadata(mask_data),
        },
        "textured_emblem_default": {
            "relative_path": _TEXTURED_EMBLEM_DEFAULT.as_posix(),
            "content_type": "application/octet-stream",
            "asset_bytes": len(textured_default_data),
            "asset_sha256": hashlib.sha256(
                textured_default_data
            ).hexdigest().upper(),
            "asset_base64": base64.b64encode(textured_default_data).decode("ascii"),
            "dds": _dds_metadata(textured_default_data),
        },
        "render_contract": {
            "pattern_color_steps": [
                {"mask_channel": "r", "target": "color1"},
                {"mask_channel": "g", "target": "color2"},
                {"mask_channel": "b", "target": "color3"},
            ],
            "colored_emblem_color_steps": [
                {"initial": "color1"},
                {"mask_channel": "g", "target": "color2"},
                {"mask_channel": "r", "target": "color3"},
                {"overlay_channel": "b", "strength": 1.0},
            ],
            "pattern_mask_channel_isolation": [
                "r=clamp(r-g-b,0,1)",
                "g=clamp(g-b,0,1)",
                "b=b",
            ],
            "surface_detail": {
                "overlay_channel": "surface_mask.b",
                "overlay_strength": 0.2,
                "emblem_alpha_multiplier": "surface_mask.g*2",
                "portrait_effects_skip_surface_detail": True,
            },
            "transform_order": ["flip", "rotate", "scale", "translate"],
            "blend": {
                "source": "src_alpha",
                "destination": "inv_src_alpha",
                "write_mask": ["red", "green", "blue"],
            },
            "overlay": {
                "formula": "lerp(color,Overlay(overlay_color,color),strength)",
                "branch": "base<0.5 ? 2*base*blend : 1-2*(1-base)*(1-blend)",
                "legacy_parameter_flip": True,
            },
            "overlay_function_body_available": True,
            "fallback_color_binding_available": False,
        },
        "provenance": {
            "mode": "base-game-clausewitz-jomini-shader-source-static",
            "executable_sha256": executable_sha256,
            "named_colors_relative_path": _NAMED_COLORS.as_posix(),
            "named_colors_sha256": _sha256(named_colors_path),
            "shader_sources": shader_sources,
            "engine_registration_observed": False,
            "dlc_and_mod_overrides_included": False,
            "limits": [
                "the engine-side FallbackColor binding is not exposed by shipped shader source",
                "GPU sampling and color-space identity require later native pixel comparison",
            ],
        },
    }
