"""Config-driven Pillow compositions for reusable promotional visuals.

Pillow is an optional runtime dependency and is imported lazily.  Projects
inject already-resolved Pillow font handles and decoded image assets; this
module never searches the host for a fallback font or substitutes a missing
asset.  Every text block is wrapped through :mod:`xar_promo.layout` using the
same font handle that will draw it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .errors import PromoToolchainError
from .layout import FontSpec, LayoutError, SafeArea, WrapPolicy, wrap_text


RGBA = tuple[int, int, int, int]
_FIT_MODES = frozenset({"fill", "contain", "crop"})
_RESAMPLING = frozenset({"nearest", "bilinear", "bicubic", "lanczos"})
_ALIGNMENTS = frozenset({"left", "center", "right"})
_VERTICAL_ALIGNMENTS = frozenset({"top", "center", "bottom"})


class VisualError(PromoToolchainError):
    """A visual cannot be composed without violating its contract."""


class VisualDependencyError(VisualError):
    """The optional Pillow runtime is unavailable."""


class VisualResourceError(VisualError):
    """A configured font, image, or palette role is unavailable or invalid."""


class VisualLayoutError(VisualError):
    """A layer escapes its configured box or canvas safe area."""


@dataclass(frozen=True)
class Box:
    left: int
    top: int
    right: int
    bottom: int

    def __post_init__(self) -> None:
        for label, value in (
            ("left", self.left),
            ("top", self.top),
            ("right", self.right),
            ("bottom", self.bottom),
        ):
            _nonnegative_integer(value, f"box {label}")
        if self.left >= self.right or self.top >= self.bottom:
            raise VisualLayoutError("box must have positive width and height")

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass(frozen=True)
class Palette:
    """Named RGBA roles selected entirely by the caller."""

    colors: Mapping[str, RGBA]

    def __post_init__(self) -> None:
        if not isinstance(self.colors, Mapping) or not self.colors:
            raise VisualResourceError("palette must contain at least one color role")
        snapshot: dict[str, RGBA] = {}
        for role, color in self.colors.items():
            key = _identifier(role, "palette role")
            if key in snapshot:
                raise VisualResourceError(f"duplicate palette role {key!r}")
            snapshot[key] = _rgba(color, f"palette role {key!r}")
        object.__setattr__(self, "colors", MappingProxyType(snapshot))

    def resolve(self, role: str) -> RGBA:
        key = _identifier(role, "color role")
        try:
            return self.colors[key]
        except KeyError as exc:
            raise VisualResourceError(f"palette color role {key!r} is missing") from exc


@dataclass(frozen=True)
class BackgroundSpec:
    """Canvas background: a role, vertical gradient, or injected image."""

    kind: str
    color_role: str | None = None
    end_color_role: str | None = None
    asset_key: str | None = None
    fit_mode: str = "crop"
    resampling: str = "lanczos"

    def __post_init__(self) -> None:
        if self.kind not in {"solid", "gradient", "asset"}:
            raise VisualError("background kind must be solid, gradient, or asset")
        _fit_mode(self.fit_mode)
        _resampling(self.resampling)
        if self.kind == "solid":
            _required_identifier(self.color_role, "solid background color_role")
            if self.end_color_role is not None or self.asset_key is not None:
                raise VisualError("solid background accepts only color_role")
        elif self.kind == "gradient":
            _required_identifier(self.color_role, "gradient color_role")
            _required_identifier(self.end_color_role, "gradient end_color_role")
            if self.asset_key is not None:
                raise VisualError("gradient background must not declare an asset")
        else:
            _required_identifier(self.asset_key, "background asset_key")
            if self.end_color_role is not None:
                raise VisualError("asset background must not declare end_color_role")
            if self.fit_mode == "contain":
                _required_identifier(
                    self.color_role,
                    "contained asset background color_role",
                )
            elif self.color_role is not None:
                raise VisualError(
                    "asset background color_role is only valid with contain fitting"
                )


@dataclass(frozen=True)
class CanvasSpec:
    width: int
    height: int
    safe_area: SafeArea
    palette: Palette
    background: BackgroundSpec

    def __post_init__(self) -> None:
        _positive_integer(self.width, "canvas width")
        _positive_integer(self.height, "canvas height")
        if not isinstance(self.safe_area, SafeArea):
            raise VisualLayoutError("canvas safe_area must be a SafeArea")
        if (
            self.safe_area.frame_width != self.width
            or self.safe_area.frame_height != self.height
        ):
            raise VisualLayoutError(
                "safe-area frame dimensions must exactly match the canvas"
            )
        if not isinstance(self.palette, Palette):
            raise VisualResourceError("canvas palette must be a Palette")
        if not isinstance(self.background, BackgroundSpec):
            raise VisualError("canvas background must be a BackgroundSpec")


@dataclass(frozen=True)
class PillowFont:
    """Caller-resolved FontSpec and its exact Pillow font handle."""

    spec: FontSpec
    handle: object

    def __post_init__(self) -> None:
        if not isinstance(self.spec, FontSpec):
            raise VisualResourceError("font binding spec must be a FontSpec")
        if self.handle is None:
            raise VisualResourceError(
                f"font binding {self.spec.key!r} has no Pillow font handle"
            )


@dataclass(frozen=True)
class TextStyle:
    font_key: str
    color_role: str
    line_height_px: int
    max_lines: int
    alignment: str = "left"
    vertical_alignment: str = "top"
    wrap_policy: WrapPolicy = field(default_factory=WrapPolicy)

    def __post_init__(self) -> None:
        _identifier(self.font_key, "text font_key")
        _identifier(self.color_role, "text color_role")
        _positive_integer(self.line_height_px, "text line_height_px")
        _positive_integer(self.max_lines, "text max_lines")
        if self.alignment not in _ALIGNMENTS:
            raise VisualLayoutError(
                "text alignment must be one of: " + ", ".join(sorted(_ALIGNMENTS))
            )
        if self.vertical_alignment not in _VERTICAL_ALIGNMENTS:
            raise VisualLayoutError(
                "text vertical_alignment must be one of: "
                + ", ".join(sorted(_VERTICAL_ALIGNMENTS))
            )
        if not isinstance(self.wrap_policy, WrapPolicy):
            raise VisualLayoutError("text wrap_policy must be a WrapPolicy")


@dataclass(frozen=True)
class TextElement:
    text: str
    box: Box
    style: TextStyle

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise VisualLayoutError("text element must contain renderable text")
        if not isinstance(self.box, Box):
            raise VisualLayoutError("text element box must be a Box")
        if not isinstance(self.style, TextStyle):
            raise VisualLayoutError("text element style must be a TextStyle")


@dataclass(frozen=True)
class PanelElement:
    box: Box
    fill_role: str
    outline_role: str | None = None
    outline_width: int = 0
    radius: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.box, Box):
            raise VisualLayoutError("panel box must be a Box")
        _identifier(self.fill_role, "panel fill_role")
        _nonnegative_integer(self.outline_width, "panel outline_width")
        _nonnegative_integer(self.radius, "panel radius")
        if self.outline_role is None:
            if self.outline_width != 0:
                raise VisualLayoutError(
                    "panel outline_width requires an outline_role"
                )
        else:
            _identifier(self.outline_role, "panel outline_role")
            if self.outline_width == 0:
                raise VisualLayoutError(
                    "panel outline_role requires a positive outline_width"
                )
        if self.radius * 2 > min(self.box.width, self.box.height):
            raise VisualLayoutError("panel radius exceeds half its shortest side")
        if self.outline_width * 2 >= min(self.box.width, self.box.height):
            raise VisualLayoutError("panel outline is too wide for its box")


@dataclass(frozen=True)
class ImageElement:
    asset_key: str
    box: Box
    fit_mode: str = "contain"
    resampling: str = "lanczos"
    opacity: int = 255
    contain_color_role: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.asset_key, "image asset_key")
        if not isinstance(self.box, Box):
            raise VisualLayoutError("image box must be a Box")
        _fit_mode(self.fit_mode)
        _resampling(self.resampling)
        _integer_in_range(self.opacity, "image opacity", 0, 255)
        if self.fit_mode == "contain":
            _required_identifier(
                self.contain_color_role,
                "contained image color role",
            )
        elif self.contain_color_role is not None:
            raise VisualError(
                "contain_color_role is only valid for contain image fitting"
            )


@dataclass(frozen=True)
class LayerGroup:
    panels: tuple[PanelElement, ...] = ()
    images: tuple[ImageElement, ...] = ()
    texts: tuple[TextElement, ...] = ()

    def __post_init__(self) -> None:
        panels = _typed_tuple(self.panels, PanelElement, "layer panels")
        images = _typed_tuple(self.images, ImageElement, "layer images")
        texts = _typed_tuple(self.texts, TextElement, "layer texts")
        object.__setattr__(self, "panels", panels)
        object.__setattr__(self, "images", images)
        object.__setattr__(self, "texts", texts)


@dataclass(frozen=True)
class BrandingSpec(LayerGroup):
    """Caller-defined text/image branding layers; no brand is built in."""


@dataclass(frozen=True)
class LowerThirdSpec(LayerGroup):
    """Caller-positioned lower-third layers."""


@dataclass(frozen=True)
class StatusBadgeSpec(LayerGroup):
    """Caller-positioned status badge layers."""


@dataclass(frozen=True)
class OverlaySpec:
    layers: LayerGroup = field(default_factory=LayerGroup)
    lower_third: LowerThirdSpec | None = None
    branding: BrandingSpec | None = None
    status_badge: StatusBadgeSpec | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.layers, LayerGroup):
            raise VisualError("overlay layers must be a LayerGroup")
        _optional_component(self.lower_third, LowerThirdSpec, "lower_third")
        _optional_component(self.branding, BrandingSpec, "branding")
        _optional_component(self.status_badge, StatusBadgeSpec, "status_badge")


@dataclass(frozen=True)
class CardSpec:
    canvas: CanvasSpec
    layers: LayerGroup = field(default_factory=LayerGroup)
    branding: BrandingSpec | None = None
    status_badge: StatusBadgeSpec | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.canvas, CanvasSpec):
            raise VisualError("card canvas must be a CanvasSpec")
        if not isinstance(self.layers, LayerGroup):
            raise VisualError("card layers must be a LayerGroup")
        _optional_component(self.branding, BrandingSpec, "branding")
        _optional_component(self.status_badge, StatusBadgeSpec, "status_badge")


@dataclass(frozen=True)
class TitleCardSpec(CardSpec):
    """A title-card composition with caller-supplied text and geometry."""


@dataclass(frozen=True)
class EvidenceCardSpec(CardSpec):
    """An evidence-card composition with caller-supplied evidence layers."""


@dataclass(frozen=True)
class StillSpec:
    canvas: CanvasSpec
    asset_key: str
    fit_mode: str
    resampling: str = "lanczos"
    overlay: OverlaySpec | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.canvas, CanvasSpec):
            raise VisualError("still canvas must be a CanvasSpec")
        _identifier(self.asset_key, "still asset_key")
        _fit_mode(self.fit_mode)
        _resampling(self.resampling)
        if self.overlay is not None and not isinstance(self.overlay, OverlaySpec):
            raise VisualError("still overlay must be an OverlaySpec")


@dataclass(frozen=True)
class _PillowRuntime:
    Image: Any
    ImageDraw: Any
    ImageOps: Any


def render_title_card(
    spec: TitleCardSpec,
    *,
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
) -> bytes:
    """Render a deterministic, opaque-or-alpha title-card PNG."""

    if not isinstance(spec, TitleCardSpec):
        raise VisualError("spec must be a TitleCardSpec")
    return _render_card(spec, fonts=fonts, assets=assets)


def render_evidence_card(
    spec: EvidenceCardSpec,
    *,
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
) -> bytes:
    """Render a deterministic evidence-card PNG."""

    if not isinstance(spec, EvidenceCardSpec):
        raise VisualError("spec must be an EvidenceCardSpec")
    return _render_card(spec, fonts=fonts, assets=assets)


def render_still(
    spec: StillSpec,
    *,
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
) -> bytes:
    """Fit an injected still as fill/contain/crop and apply an optional overlay."""

    if not isinstance(spec, StillSpec):
        raise VisualError("spec must be a StillSpec")
    runtime = _load_pillow()
    font_map, asset_map = _resources(fonts, assets)
    source = _resolve_image(spec.asset_key, asset_map, runtime)
    fitted = fit_image(
        source,
        width=spec.canvas.width,
        height=spec.canvas.height,
        mode=spec.fit_mode,
        background=(0, 0, 0, 0),
        resampling=spec.resampling,
        runtime=runtime,
    )
    if spec.fit_mode == "contain":
        image = _background_image(spec.canvas, asset_map, runtime)
        image.alpha_composite(fitted)
    else:
        image = fitted
    if spec.overlay is not None:
        _draw_overlay_spec(
            image,
            spec.canvas,
            spec.overlay,
            font_map,
            asset_map,
            runtime,
        )
    return _png_bytes(image, runtime)


def render_overlay(
    canvas: CanvasSpec,
    spec: OverlaySpec,
    *,
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
) -> bytes:
    """Render a full-canvas transparent overlay PNG."""

    if not isinstance(canvas, CanvasSpec):
        raise VisualError("canvas must be a CanvasSpec")
    if not isinstance(spec, OverlaySpec):
        raise VisualError("spec must be an OverlaySpec")
    runtime = _load_pillow()
    font_map, asset_map = _resources(fonts, assets)
    image = runtime.Image.new("RGBA", (canvas.width, canvas.height), (0, 0, 0, 0))
    _draw_overlay_spec(image, canvas, spec, font_map, asset_map, runtime)
    return _png_bytes(image, runtime)


def render_lower_third(
    canvas: CanvasSpec,
    spec: LowerThirdSpec,
    *,
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
) -> bytes:
    """Render only one lower-third on a transparent full-size canvas."""

    if not isinstance(canvas, CanvasSpec):
        raise VisualError("canvas must be a CanvasSpec")
    if not isinstance(spec, LowerThirdSpec):
        raise VisualError("spec must be a LowerThirdSpec")
    return _render_component(canvas, spec, fonts=fonts, assets=assets)


def render_status_badge(
    canvas: CanvasSpec,
    spec: StatusBadgeSpec,
    *,
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
) -> bytes:
    """Render only one status badge on a transparent full-size canvas."""

    if not isinstance(canvas, CanvasSpec):
        raise VisualError("canvas must be a CanvasSpec")
    if not isinstance(spec, StatusBadgeSpec):
        raise VisualError("spec must be a StatusBadgeSpec")
    return _render_component(canvas, spec, fonts=fonts, assets=assets)


def fit_image(
    source: object,
    *,
    width: int,
    height: int,
    mode: str,
    background: RGBA,
    resampling: str = "lanczos",
    runtime: _PillowRuntime | None = None,
) -> object:
    """Return a new RGBA Pillow image with deterministic fit semantics."""

    selected_runtime = _load_pillow() if runtime is None else runtime
    _positive_integer(width, "fit width")
    _positive_integer(height, "fit height")
    selected_mode = _fit_mode(mode)
    background_color = _rgba(background, "fit background")
    method = _resample_filter(selected_runtime, _resampling(resampling))
    if not isinstance(source, selected_runtime.Image.Image):
        raise VisualResourceError("fit source must be a decoded Pillow image")
    try:
        normalized = selected_runtime.ImageOps.exif_transpose(source).convert("RGBA")
    except (OSError, ValueError) as exc:
        raise VisualResourceError(f"could not normalize image asset: {exc}") from exc
    if normalized.width <= 0 or normalized.height <= 0:
        raise VisualResourceError("image asset has invalid dimensions")
    size = (width, height)
    if selected_mode == "fill":
        return normalized.resize(size, resample=method)
    if selected_mode == "crop":
        return selected_runtime.ImageOps.fit(
            normalized,
            size,
            method=method,
            centering=(0.5, 0.5),
        )
    contained = selected_runtime.ImageOps.contain(normalized, size, method=method)
    result = selected_runtime.Image.new("RGBA", size, background_color)
    left = (width - contained.width) // 2
    top = (height - contained.height) // 2
    result.alpha_composite(contained, (left, top))
    return result


def _render_card(
    spec: CardSpec,
    *,
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
) -> bytes:
    runtime = _load_pillow()
    font_map, asset_map = _resources(fonts, assets)
    image = _background_image(spec.canvas, asset_map, runtime)
    _draw_group(image, spec.canvas, spec.layers, font_map, asset_map, runtime)
    if spec.branding is not None:
        _draw_group(image, spec.canvas, spec.branding, font_map, asset_map, runtime)
    if spec.status_badge is not None:
        _draw_group(image, spec.canvas, spec.status_badge, font_map, asset_map, runtime)
    return _png_bytes(image, runtime)


def _render_component(
    canvas: CanvasSpec,
    spec: LayerGroup,
    *,
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
) -> bytes:
    runtime = _load_pillow()
    font_map, asset_map = _resources(fonts, assets)
    image = runtime.Image.new("RGBA", (canvas.width, canvas.height), (0, 0, 0, 0))
    _draw_group(image, canvas, spec, font_map, asset_map, runtime)
    return _png_bytes(image, runtime)


def _draw_overlay_spec(
    image: object,
    canvas: CanvasSpec,
    spec: OverlaySpec,
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
    runtime: _PillowRuntime,
) -> None:
    _draw_group(image, canvas, spec.layers, fonts, assets, runtime)
    if spec.lower_third is not None:
        _draw_group(image, canvas, spec.lower_third, fonts, assets, runtime)
    if spec.branding is not None:
        _draw_group(image, canvas, spec.branding, fonts, assets, runtime)
    if spec.status_badge is not None:
        _draw_group(image, canvas, spec.status_badge, fonts, assets, runtime)


def _background_image(
    canvas: CanvasSpec,
    assets: Mapping[str, object],
    runtime: _PillowRuntime,
) -> object:
    background = canvas.background
    if background.kind == "solid":
        color = canvas.palette.resolve(
            _required_identifier(background.color_role, "background color_role")
        )
        return runtime.Image.new("RGBA", (canvas.width, canvas.height), color)
    if background.kind == "gradient":
        start = canvas.palette.resolve(
            _required_identifier(background.color_role, "gradient color_role")
        )
        end = canvas.palette.resolve(
            _required_identifier(background.end_color_role, "gradient end_color_role")
        )
        image = runtime.Image.new("RGBA", (canvas.width, canvas.height), start)
        draw = runtime.ImageDraw.Draw(image, "RGBA")
        denominator = max(1, canvas.height - 1)
        for y in range(canvas.height):
            color = tuple(
                ((start[channel] * (denominator - y)) + (end[channel] * y) + denominator // 2)
                // denominator
                for channel in range(4)
            )
            draw.line((0, y, canvas.width - 1, y), fill=color)
        return image
    asset_key = _required_identifier(background.asset_key, "background asset_key")
    source = _resolve_image(asset_key, assets, runtime)
    contain_color = (
        (0, 0, 0, 0)
        if background.color_role is None
        else canvas.palette.resolve(background.color_role)
    )
    return fit_image(
        source,
        width=canvas.width,
        height=canvas.height,
        mode=background.fit_mode,
        background=contain_color,
        resampling=background.resampling,
        runtime=runtime,
    )


def _draw_group(
    image: object,
    canvas: CanvasSpec,
    group: LayerGroup,
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
    runtime: _PillowRuntime,
) -> None:
    for panel in group.panels:
        _draw_panel(image, canvas, panel, runtime)
    for element in group.images:
        _draw_image(image, canvas, element, assets, runtime)
    for element in group.texts:
        _draw_text(image, canvas, element, fonts, runtime)


def _draw_panel(
    image: object,
    canvas: CanvasSpec,
    panel: PanelElement,
    runtime: _PillowRuntime,
) -> None:
    _require_safe_box(panel.box, canvas, "panel")
    fill = canvas.palette.resolve(panel.fill_role)
    outline = (
        None
        if panel.outline_role is None
        else canvas.palette.resolve(panel.outline_role)
    )
    draw = runtime.ImageDraw.Draw(image, "RGBA")
    coordinates = (panel.box.left, panel.box.top, panel.box.right - 1, panel.box.bottom - 1)
    if panel.radius:
        draw.rounded_rectangle(
            coordinates,
            radius=panel.radius,
            fill=fill,
            outline=outline,
            width=panel.outline_width,
        )
    else:
        draw.rectangle(
            coordinates,
            fill=fill,
            outline=outline,
            width=panel.outline_width,
        )


def _draw_image(
    image: object,
    canvas: CanvasSpec,
    element: ImageElement,
    assets: Mapping[str, object],
    runtime: _PillowRuntime,
) -> None:
    _require_safe_box(element.box, canvas, f"image {element.asset_key!r}")
    source = _resolve_image(element.asset_key, assets, runtime)
    background = (
        (0, 0, 0, 0)
        if element.contain_color_role is None
        else canvas.palette.resolve(element.contain_color_role)
    )
    fitted = fit_image(
        source,
        width=element.box.width,
        height=element.box.height,
        mode=element.fit_mode,
        background=background,
        resampling=element.resampling,
        runtime=runtime,
    )
    if element.opacity != 255:
        alpha = fitted.getchannel("A")
        lookup = tuple((value * element.opacity) // 255 for value in range(256))
        fitted.putalpha(alpha.point(lookup))
    image.alpha_composite(fitted, (element.box.left, element.box.top))


def _draw_text(
    image: object,
    canvas: CanvasSpec,
    element: TextElement,
    fonts: Mapping[str, PillowFont],
    runtime: _PillowRuntime,
) -> None:
    _require_safe_box(element.box, canvas, "text")
    binding = _resolve_font(element.style.font_key, fonts)
    color = canvas.palette.resolve(element.style.color_role)
    draw = runtime.ImageDraw.Draw(image, "RGBA")

    def measure(text: str, spec: FontSpec) -> float:
        if spec != binding.spec:
            raise VisualResourceError("layout requested a different resolved font")
        try:
            return float(draw.textlength(text, font=binding.handle))
        except (AttributeError, OSError, TypeError, ValueError) as exc:
            raise VisualResourceError(
                f"Pillow rejected font {binding.spec.key!r}: {exc}"
            ) from exc

    try:
        layout = wrap_text(
            element.text,
            font=binding.spec,
            measure=measure,
            max_width=element.box.width,
            max_lines=element.style.max_lines,
            policy=element.style.wrap_policy,
        )
    except LayoutError as exc:
        raise VisualLayoutError(f"text cannot fit its declared box: {exc}") from exc

    total_height = len(layout.lines) * element.style.line_height_px
    if total_height > element.box.height:
        raise VisualLayoutError(
            f"text needs {total_height}px vertical space; box has {element.box.height}px"
        )
    if element.style.vertical_alignment == "top":
        first_y = element.box.top
    elif element.style.vertical_alignment == "bottom":
        first_y = element.box.bottom - total_height
    else:
        first_y = element.box.top + ((element.box.height - total_height) // 2)

    planned: list[tuple[str, int, int, tuple[int, int, int, int]]] = []
    for index, (line, width) in enumerate(zip(layout.lines, layout.widths)):
        if element.style.alignment == "left":
            x = element.box.left
        elif element.style.alignment == "right":
            x = element.box.right - math.ceil(width)
        else:
            x = element.box.left + round((element.box.width - width) / 2)
        y = first_y + (index * element.style.line_height_px)
        try:
            bounds = draw.textbbox(
                (x, y),
                line,
                font=binding.handle,
                anchor="lt",
            )
        except (AttributeError, OSError, TypeError, ValueError) as exc:
            raise VisualResourceError(
                f"Pillow could not bound font {binding.spec.key!r}: {exc}"
            ) from exc
        if (
            bounds[0] < element.box.left
            or bounds[1] < element.box.top
            or bounds[2] > element.box.right
            or bounds[3] > element.box.bottom
        ):
            raise VisualLayoutError(
                f"rendered glyph bounds escape the text box on line {index}"
            )
        planned.append((line, x, y, bounds))

    for line, x, y, _ in planned:
        draw.text((x, y), line, font=binding.handle, fill=color, anchor="lt")


def _resources(
    fonts: Mapping[str, PillowFont],
    assets: Mapping[str, object],
) -> tuple[dict[str, PillowFont], dict[str, object]]:
    if not isinstance(fonts, Mapping):
        raise VisualResourceError("fonts must be a mapping")
    if not isinstance(assets, Mapping):
        raise VisualResourceError("assets must be a mapping")
    font_map = dict(fonts)
    asset_map = dict(assets)
    if any(not isinstance(key, str) for key in font_map):
        raise VisualResourceError("font registry keys must be strings")
    if any(not isinstance(key, str) for key in asset_map):
        raise VisualResourceError("asset registry keys must be strings")
    return font_map, asset_map


def _resolve_font(key: str, fonts: Mapping[str, PillowFont]) -> PillowFont:
    binding = fonts.get(key)
    if binding is None:
        raise VisualResourceError(f"required font {key!r} is missing")
    if not isinstance(binding, PillowFont):
        raise VisualResourceError(f"font registry entry {key!r} is not a PillowFont")
    if binding.spec.key != key:
        raise VisualResourceError(
            f"font registry key {key!r} does not match FontSpec.key {binding.spec.key!r}"
        )
    return binding


def _resolve_image(
    key: str,
    assets: Mapping[str, object],
    runtime: _PillowRuntime,
) -> object:
    source = assets.get(key)
    if source is None:
        raise VisualResourceError(f"required image asset {key!r} is missing")
    if not isinstance(source, runtime.Image.Image):
        raise VisualResourceError(
            f"image registry entry {key!r} is not a decoded Pillow image"
        )
    return source


def _require_safe_box(box: Box, canvas: CanvasSpec, label: str) -> None:
    safe = canvas.safe_area
    if (
        box.left < safe.left
        or box.top < safe.top
        or box.right > safe.right
        or box.bottom > safe.bottom
    ):
        raise VisualLayoutError(f"{label} box escapes the canvas safe area")


def _png_bytes(image: object, runtime: _PillowRuntime) -> bytes:
    if not isinstance(image, runtime.Image.Image):
        raise VisualResourceError("PNG source is not a Pillow image")
    # Recompose into a fresh image so source EXIF/ICC/DPI/text chunks never leak
    # into the generated artifact.  Only the caller-visible pixels are inputs.
    normalized = runtime.Image.new("RGBA", image.size, (0, 0, 0, 0))
    normalized.alpha_composite(image.convert("RGBA"))
    output = BytesIO()
    try:
        normalized.save(
            output,
            format="PNG",
            optimize=False,
            compress_level=9,
        )
    except (OSError, ValueError) as exc:
        raise VisualResourceError(f"could not encode deterministic PNG: {exc}") from exc
    payload = output.getvalue()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise VisualResourceError("Pillow did not produce a PNG payload")
    return payload


def _load_pillow() -> _PillowRuntime:
    try:
        from PIL import Image, ImageDraw, ImageOps
    except ImportError as exc:
        raise VisualDependencyError(
            "Pillow is required for visual composition; install the project's "
            "visual runtime before rendering"
        ) from exc
    return _PillowRuntime(Image=Image, ImageDraw=ImageDraw, ImageOps=ImageOps)


def _resample_filter(runtime: _PillowRuntime, name: str) -> object:
    try:
        values = runtime.Image.Resampling
    except AttributeError as exc:
        raise VisualDependencyError(
            "the installed Pillow version does not provide Image.Resampling"
        ) from exc
    return {
        "nearest": values.NEAREST,
        "bilinear": values.BILINEAR,
        "bicubic": values.BICUBIC,
        "lanczos": values.LANCZOS,
    }[name]


def _typed_tuple(values: Sequence[object], expected: type, label: str) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise VisualError(f"{label} must be a sequence")
    try:
        materialized = tuple(values)
    except TypeError as exc:
        raise VisualError(f"{label} must be a sequence") from exc
    if any(not isinstance(value, expected) for value in materialized):
        raise VisualError(f"{label} contains an invalid element")
    return materialized


def _optional_component(value: object, expected: type, label: str) -> None:
    if value is not None and not isinstance(value, expected):
        raise VisualError(f"{label} must be a {expected.__name__}")


def _rgba(value: object, label: str) -> RGBA:
    if not isinstance(value, tuple) or len(value) != 4:
        raise VisualResourceError(f"{label} must be an RGBA tuple")
    channels: list[int] = []
    for channel in value:
        if isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel <= 255:
            raise VisualResourceError(f"{label} channels must be integers in [0, 255]")
        channels.append(channel)
    return channels[0], channels[1], channels[2], channels[3]


def _fit_mode(value: object) -> str:
    if not isinstance(value, str) or value not in _FIT_MODES:
        raise VisualError("fit mode must be fill, contain, or crop")
    return value


def _resampling(value: object) -> str:
    if not isinstance(value, str) or value not in _RESAMPLING:
        raise VisualError(
            "resampling must be nearest, bilinear, bicubic, or lanczos"
        )
    return value


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise VisualError(f"{label} must be a non-empty trimmed string")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise VisualError(f"{label} must not contain control characters")
    return value


def _required_identifier(value: object, label: str) -> str:
    if value is None:
        raise VisualError(f"{label} is required")
    return _identifier(value, label)


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise VisualError(f"{label} must be a positive integer")
    return value


def _nonnegative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise VisualError(f"{label} must be a non-negative integer")
    return value


def _integer_in_range(value: object, label: str, minimum: int, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise VisualError(f"{label} must be an integer in [{minimum}, {maximum}]")
    return value


__all__ = [
    "BackgroundSpec",
    "Box",
    "BrandingSpec",
    "CanvasSpec",
    "EvidenceCardSpec",
    "ImageElement",
    "LayerGroup",
    "LowerThirdSpec",
    "OverlaySpec",
    "Palette",
    "PanelElement",
    "PillowFont",
    "StatusBadgeSpec",
    "StillSpec",
    "TextElement",
    "TextStyle",
    "TitleCardSpec",
    "VisualDependencyError",
    "VisualError",
    "VisualLayoutError",
    "VisualResourceError",
    "fit_image",
    "render_evidence_card",
    "render_lower_third",
    "render_overlay",
    "render_status_badge",
    "render_still",
    "render_title_card",
]
