from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from PIL import Image, ImageFont
except ImportError:
    Image = None
    ImageFont = None

from xar_promo.layout import FontSpec, SafeArea  # noqa: E402
from xar_promo import visuals  # noqa: E402
from xar_promo.visuals import (  # noqa: E402
    BackgroundSpec,
    Box,
    BrandingSpec,
    CanvasSpec,
    EvidenceCardSpec,
    ImageElement,
    LayerGroup,
    LowerThirdSpec,
    OverlaySpec,
    Palette,
    PanelElement,
    PillowFont,
    StatusBadgeSpec,
    StillSpec,
    TextElement,
    TextStyle,
    TitleCardSpec,
    VisualDependencyError,
    VisualError,
    VisualLayoutError,
    VisualResourceError,
    fit_image,
    render_evidence_card,
    render_lower_third,
    render_overlay,
    render_status_badge,
    render_still,
    render_title_card,
)


def _palette() -> Palette:
    return Palette(
        {
            "background": (8, 12, 20, 255),
            "background-end": (24, 30, 44, 255),
            "primary": (245, 247, 250, 255),
            "secondary": (170, 190, 220, 255),
            "accent": (45, 180, 150, 255),
            "panel": (4, 8, 16, 210),
            "outline": (80, 110, 145, 255),
            "transparent": (0, 0, 0, 0),
            "contain": (20, 90, 40, 255),
        }
    )


def _canvas(*, width: int = 320, height: int = 180) -> CanvasSpec:
    return CanvasSpec(
        width=width,
        height=height,
        safe_area=SafeArea(width, height, 8, 8, width - 8, height - 8),
        palette=_palette(),
        background=BackgroundSpec(
            kind="gradient",
            color_role="background",
            end_color_role="background-end",
        ),
    )


def _style(
    *,
    max_lines: int = 2,
    alignment: str = "left",
    vertical_alignment: str = "top",
) -> TextStyle:
    return TextStyle(
        font_key="body",
        color_role="primary",
        line_height_px=16,
        max_lines=max_lines,
        alignment=alignment,
        vertical_alignment=vertical_alignment,
    )


class VisualContractTests(unittest.TestCase):
    def test_palette_is_snapshotted_and_missing_roles_fail_closed(self) -> None:
        source = {"role": (1, 2, 3, 4)}
        palette = Palette(source)
        source["role"] = (9, 9, 9, 9)
        self.assertEqual((1, 2, 3, 4), palette.resolve("role"))
        with self.assertRaises(VisualResourceError):
            palette.resolve("missing")
        with self.assertRaises(VisualResourceError):
            Palette({"bad": (1, 2, 3)})  # type: ignore[dict-item]

    def test_canvas_requires_an_exact_safe_area(self) -> None:
        with self.assertRaisesRegex(VisualLayoutError, "exactly match"):
            CanvasSpec(
                width=320,
                height=180,
                safe_area=SafeArea(321, 180, 8, 8, 313, 172),
                palette=_palette(),
                background=BackgroundSpec(
                    kind="solid",
                    color_role="background",
                ),
            )
        with self.assertRaises(VisualError):
            BackgroundSpec(kind="asset", asset_key="image", fit_mode="contain")
        with self.assertRaises(VisualError):
            BackgroundSpec(
                kind="asset",
                asset_key="image",
                fit_mode="crop",
                color_role="background",
            )

    def test_panels_and_image_fit_contracts_reject_ambiguous_values(self) -> None:
        with self.assertRaises(VisualLayoutError):
            PanelElement(Box(0, 0, 20, 20), "panel", outline_width=1)
        with self.assertRaises(VisualLayoutError):
            PanelElement(Box(0, 0, 20, 20), "panel", radius=11)
        with self.assertRaises(VisualError):
            ImageElement("asset", Box(0, 0, 20, 20), fit_mode="unknown")
        with self.assertRaises(VisualError):
            ImageElement("asset", Box(0, 0, 20, 20), fit_mode="crop", contain_color_role="contain")

    def test_layer_groups_materialize_input_sequences(self) -> None:
        panels = [PanelElement(Box(10, 10, 40, 40), "panel")]
        group = LayerGroup(panels=panels)  # type: ignore[arg-type]
        panels.clear()
        self.assertEqual(1, len(group.panels))
        self.assertIsInstance(group.panels, tuple)

    def test_missing_pillow_dependency_is_actionable(self) -> None:
        spec = TitleCardSpec(canvas=_canvas())
        with mock.patch.object(
            visuals,
            "_load_pillow",
            side_effect=VisualDependencyError("Pillow unavailable"),
        ):
            with self.assertRaisesRegex(VisualDependencyError, "Pillow unavailable"):
                render_title_card(spec, fonts={}, assets={})


@unittest.skipUnless(Image is not None and ImageFont is not None, "Pillow is optional")
class PillowVisualTests(unittest.TestCase):
    def setUp(self) -> None:
        assert Image is not None
        assert ImageFont is not None
        self.fonts = {
            "body": PillowFont(
                FontSpec("body", "Injected Test Face", 10),
                ImageFont.load_default(),
            )
        }
        self.logo = Image.new("RGBA", (8, 8), (220, 60, 50, 255))
        self.assets = {"logo": self.logo}

    def _branding(self) -> BrandingSpec:
        return BrandingSpec(
            images=(
                ImageElement(
                    "logo",
                    Box(280, 12, 304, 36),
                    fit_mode="contain",
                    resampling="nearest",
                    contain_color_role="transparent",
                ),
            ),
            texts=(
                TextElement(
                    "Caller brand",
                    Box(16, 12, 200, 32),
                    _style(max_lines=1),
                ),
            ),
        )

    def _badge(self) -> StatusBadgeSpec:
        return StatusBadgeSpec(
            panels=(
                PanelElement(
                    Box(204, 132, 304, 166),
                    "panel",
                    outline_role="accent",
                    outline_width=2,
                    radius=8,
                ),
            ),
            texts=(
                TextElement(
                    "Ready",
                    Box(214, 140, 294, 160),
                    _style(max_lines=1, alignment="center"),
                ),
            ),
        )

    def _title_spec(self) -> TitleCardSpec:
        return TitleCardSpec(
            canvas=_canvas(),
            layers=LayerGroup(
                panels=(
                    PanelElement(
                        Box(16, 42, 304, 122),
                        "panel",
                        outline_role="outline",
                        outline_width=1,
                        radius=10,
                    ),
                ),
                texts=(
                    TextElement(
                        "A reusable title card",
                        Box(26, 50, 294, 78),
                        _style(max_lines=1, alignment="center"),
                    ),
                    TextElement(
                        "Layout uses the exact injected font metrics.",
                        Box(26, 84, 294, 114),
                        TextStyle(
                            font_key="body",
                            color_role="secondary",
                            line_height_px=14,
                            max_lines=2,
                            alignment="center",
                        ),
                    ),
                ),
            ),
            branding=self._branding(),
            status_badge=self._badge(),
        )

    def test_title_and_evidence_cards_are_deterministic_pngs(self) -> None:
        title = self._title_spec()
        first = render_title_card(title, fonts=self.fonts, assets=self.assets)
        second = render_title_card(title, fonts=self.fonts, assets=self.assets)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith(b"\x89PNG\r\n\x1a\n"))

        with Image.open(BytesIO(first)) as rendered:
            self.assertEqual((320, 180), rendered.size)
            self.assertEqual("RGBA", rendered.mode)
            self.assertEqual(255, rendered.getpixel((0, 0))[3])
            self.assertEqual((220, 60, 50, 255), rendered.getpixel((290, 22)))

        evidence = EvidenceCardSpec(
            canvas=title.canvas,
            layers=LayerGroup(
                panels=title.layers.panels,
                texts=(
                    TextElement(
                        "Evidence item with a retained digest",
                        Box(26, 50, 294, 100),
                        _style(max_lines=2, alignment="center"),
                    ),
                ),
            ),
            branding=title.branding,
            status_badge=title.status_badge,
        )
        evidence_png = render_evidence_card(
            evidence,
            fonts=self.fonts,
            assets=self.assets,
        )
        self.assertTrue(evidence_png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertNotEqual(first, evidence_png)

    def test_missing_font_or_palette_role_fails_without_fallback(self) -> None:
        title = self._title_spec()
        with self.assertRaisesRegex(VisualResourceError, "required font"):
            render_title_card(title, fonts={}, assets=self.assets)

        missing_role = TitleCardSpec(
            canvas=title.canvas,
            layers=LayerGroup(
                texts=(
                    TextElement(
                        "text",
                        Box(20, 50, 200, 80),
                        TextStyle("body", "not-defined", 16, 1),
                    ),
                ),
            ),
        )
        with self.assertRaisesRegex(VisualResourceError, "not-defined"):
            render_title_card(missing_role, fonts=self.fonts, assets=self.assets)

    def test_text_and_component_safe_area_overflow_fail_closed(self) -> None:
        narrow = TitleCardSpec(
            canvas=_canvas(),
            layers=LayerGroup(
                texts=(
                    TextElement(
                        "This text cannot fit on one tiny line",
                        Box(16, 40, 36, 60),
                        _style(max_lines=1),
                    ),
                ),
            ),
        )
        with self.assertRaisesRegex(VisualLayoutError, "cannot fit"):
            render_title_card(narrow, fonts=self.fonts, assets=self.assets)

        escaped = TitleCardSpec(
            canvas=_canvas(),
            layers=LayerGroup(
                panels=(PanelElement(Box(0, 20, 100, 60), "panel"),),
            ),
        )
        with self.assertRaisesRegex(VisualLayoutError, "safe area"):
            render_title_card(escaped, fonts=self.fonts, assets=self.assets)

    def test_fit_image_has_distinct_fill_contain_and_crop_contracts(self) -> None:
        source = Image.new("RGBA", (4, 2), (220, 20, 20, 255))
        for x in range(2, 4):
            for y in range(2):
                source.putpixel((x, y), (20, 40, 220, 255))

        contained = fit_image(
            source,
            width=8,
            height=8,
            mode="contain",
            background=(20, 90, 40, 255),
            resampling="nearest",
        )
        filled = fit_image(
            source,
            width=8,
            height=8,
            mode="fill",
            background=(0, 0, 0, 0),
            resampling="nearest",
        )
        cropped = fit_image(
            source,
            width=8,
            height=8,
            mode="crop",
            background=(0, 0, 0, 0),
            resampling="nearest",
        )
        self.assertEqual((20, 90, 40, 255), contained.getpixel((0, 0)))
        self.assertEqual((220, 20, 20, 255), contained.getpixel((0, 2)))
        self.assertNotEqual((20, 90, 40, 255), filled.getpixel((0, 0)))
        self.assertNotEqual((20, 90, 40, 255), cropped.getpixel((0, 0)))
        self.assertEqual((8, 8), filled.size)
        self.assertEqual((8, 8), cropped.size)
        with self.assertRaises(VisualResourceError):
            fit_image(
                object(),
                width=8,
                height=8,
                mode="fill",
                background=(0, 0, 0, 0),
            )

    def test_still_uses_injected_asset_background_and_optional_overlay(self) -> None:
        canvas = CanvasSpec(
            width=80,
            height=80,
            safe_area=SafeArea(80, 80, 4, 4, 76, 76),
            palette=_palette(),
            background=BackgroundSpec(kind="solid", color_role="contain"),
        )
        source = Image.new("RGBA", (4, 2), (220, 20, 20, 255))
        overlay = OverlaySpec(
            layers=LayerGroup(
                panels=(PanelElement(Box(8, 56, 72, 72), "panel"),),
            )
        )
        spec = StillSpec(
            canvas=canvas,
            asset_key="still",
            fit_mode="contain",
            resampling="nearest",
            overlay=overlay,
        )
        payload = render_still(
            spec,
            fonts={},
            assets={"still": source},
        )
        with Image.open(BytesIO(payload)) as rendered:
            self.assertEqual((20, 90, 40, 255), rendered.getpixel((0, 0)))
            self.assertEqual((220, 20, 20, 255), rendered.getpixel((40, 40)))
            self.assertEqual((4, 8, 16, 210), rendered.getpixel((12, 60)))

        with self.assertRaisesRegex(VisualResourceError, "missing"):
            render_still(spec, fonts={}, assets={})

    def test_lower_third_status_badge_and_overlay_remain_transparent_elsewhere(self) -> None:
        canvas = _canvas()
        lower = LowerThirdSpec(
            panels=(PanelElement(Box(16, 108, 190, 166), "panel", radius=8),),
            texts=(
                TextElement(
                    "Lower third",
                    Box(26, 118, 180, 150),
                    _style(max_lines=1),
                ),
            ),
        )
        lower_png = render_lower_third(
            canvas,
            lower,
            fonts=self.fonts,
            assets=self.assets,
        )
        badge_png = render_status_badge(
            canvas,
            self._badge(),
            fonts=self.fonts,
            assets=self.assets,
        )
        overlay_png = render_overlay(
            canvas,
            OverlaySpec(
                lower_third=lower,
                branding=self._branding(),
                status_badge=self._badge(),
            ),
            fonts=self.fonts,
            assets=self.assets,
        )
        for payload in (lower_png, badge_png, overlay_png):
            with Image.open(BytesIO(payload)) as rendered:
                self.assertEqual((0, 0, 0, 0), rendered.getpixel((0, 0)))
        with Image.open(BytesIO(lower_png)) as rendered:
            self.assertEqual((4, 8, 16, 210), rendered.getpixel((20, 112)))
        with Image.open(BytesIO(badge_png)) as rendered:
            self.assertNotEqual((0, 0, 0, 0), rendered.getpixel((206, 140)))
        with Image.open(BytesIO(overlay_png)) as rendered:
            self.assertNotEqual((0, 0, 0, 0), rendered.getpixel((290, 22)))


if __name__ == "__main__":
    unittest.main()
