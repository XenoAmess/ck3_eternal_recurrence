from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import math
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_promo.layout import (  # noqa: E402
    FontSpec,
    LayoutError,
    SafeArea,
    TrackLayoutConfig,
    WrapPolicy,
    balance_lines,
    layout_tracks,
    wrap_text,
)
from xar_promo.subtitles import (  # noqa: E402
    AssCue,
    AssDocumentConfig,
    AssStyleConfig,
    SubtitleError,
    SubtitleTrackConfig,
    ass_escape,
    ass_timestamp,
    render_ass_document,
)


def _monospace_width(text: str, font: FontSpec) -> float:
    return len(text) * font.size_px


class LayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.font = FontSpec(
            key="body-face",
            family="Example Sans",
            size_px=10,
            weight=600,
        )

    def test_safe_area_from_margins_is_exact_and_rejects_escape(self) -> None:
        area = SafeArea.from_margins(
            frame_width=1920,
            frame_height=1080,
            left=120,
            top=80,
            right=140,
            bottom=100,
        )
        self.assertEqual((120, 80, 1780, 980), (area.left, area.top, area.right, area.bottom))
        self.assertEqual(1660, area.width)
        self.assertEqual(900, area.height)

        with self.assertRaises(LayoutError):
            SafeArea(1920, 1080, 0, 0, 1921, 1080)
        with self.assertRaises(LayoutError):
            SafeArea.from_margins(
                frame_width=100,
                frame_height=100,
                left=60,
                top=0,
                right=60,
                bottom=0,
            )

    def test_wrap_uses_injected_metrics_and_word_boundaries(self) -> None:
        layout = wrap_text(
            "alpha beta gamma",
            font=self.font,
            measure=_monospace_width,
            max_width=60,
            max_lines=3,
        )
        self.assertEqual(("alpha", "beta", "gamma"), layout.lines)
        self.assertEqual((50, 40, 50), layout.widths)

    def test_semantic_breaks_and_decimal_exceptions_are_configuration(self) -> None:
        policy = WrapPolicy(
            force_break_after=frozenset({"."}),
            decimal_separators=frozenset({"."}),
        )
        layout = wrap_text(
            "1.2. final.",
            font=self.font,
            measure=_monospace_width,
            max_width=200,
            max_lines=3,
            policy=policy,
        )
        self.assertEqual(("1.2.", "final."), layout.lines)

        alternate = wrap_text(
            "first|second",
            font=self.font,
            measure=_monospace_width,
            max_width=200,
            max_lines=2,
            policy=WrapPolicy(force_break_after=frozenset({"|"})),
        )
        self.assertEqual(("first|", "second"), alternate.lines)

    def test_wrap_never_truncates_or_accepts_invalid_metrics(self) -> None:
        with self.assertRaises(LayoutError):
            wrap_text(
                "one two three",
                font=self.font,
                measure=_monospace_width,
                max_width=40,
                max_lines=2,
            )
        with self.assertRaises(LayoutError):
            wrap_text(
                "x",
                font=self.font,
                measure=_monospace_width,
                max_width=5,
                max_lines=1,
            )
        for invalid_width in (-1.0, math.nan, math.inf):
            with self.subTest(width=invalid_width), self.assertRaises(LayoutError):
                wrap_text(
                    "x",
                    font=self.font,
                    measure=lambda _text, _font, value=invalid_width: value,
                    max_width=100,
                    max_lines=1,
                )
        with self.assertRaisesRegex(LayoutError, "measurement failed"):
            wrap_text(
                "x",
                font=self.font,
                measure=lambda _text, _font: (_ for _ in ()).throw(RuntimeError("boom")),
                max_width=100,
                max_lines=1,
            )

    def test_balanced_blocks_are_deterministic_and_bounded(self) -> None:
        blocks = balance_lines(
            ("a", "b", "c", "d", "e"), max_lines_per_block=2
        )
        self.assertEqual((("a", "b"), ("c", "d"), ("e",)), blocks)
        with self.assertRaises(LayoutError):
            balance_lines((), max_lines_per_block=2)

    def test_track_hierarchy_and_alignment_come_only_from_configuration(self) -> None:
        area = SafeArea(400, 300, 20, 20, 380, 280)
        tracks = (
            TrackLayoutConfig(
                track_id="track-a",
                font_key="body-face",
                layer=9,
                stack_order=0,
                max_lines=1,
                line_height_px=20,
                horizontal_inset_px=10,
                gap_above_px=10,
                alignment="center",
            ),
            TrackLayoutConfig(
                track_id="track-b",
                font_key="body-face",
                layer=3,
                stack_order=1,
                max_lines=1,
                line_height_px=20,
                alignment="right",
            ),
        )
        result = layout_tracks(
            {"track-b": "bb", "track-a": "aaaa"},
            tracks=tracks,
            fonts={"body-face": self.font},
            safe_area=area,
            measure=_monospace_width,
        )

        self.assertEqual(("track-a", "track-b"), tuple(row.track_id for row in result))
        self.assertEqual((9, 3), tuple(row.layer for row in result))
        self.assertEqual((260, 230), tuple(row.top for row in result))
        self.assertEqual(180, result[0].lines[0].x)
        self.assertEqual(360, result[1].lines[0].x)

    def test_track_layout_fails_closed_for_missing_fonts_or_text(self) -> None:
        area = SafeArea(400, 300, 20, 20, 380, 280)
        track = TrackLayoutConfig(
            track_id="track-a",
            font_key="body-face",
            layer=0,
            stack_order=0,
            max_lines=2,
            line_height_px=20,
        )
        with self.assertRaisesRegex(LayoutError, "is missing"):
            layout_tracks(
                {"track-a": "text"},
                tracks=(track,),
                fonts={},
                safe_area=area,
                measure=_monospace_width,
            )
        with self.assertRaisesRegex(LayoutError, "unexpected"):
            layout_tracks(
                {"track-a": "text", "track-b": "extra"},
                tracks=(track,),
                fonts={"body-face": self.font},
                safe_area=area,
                measure=_monospace_width,
            )

    def test_track_layout_rejects_vertical_and_horizontal_overflow(self) -> None:
        small_area = SafeArea(100, 40, 0, 0, 100, 40)
        tall = TrackLayoutConfig(
            track_id="track-a",
            font_key="body-face",
            layer=0,
            stack_order=0,
            max_lines=2,
            line_height_px=30,
        )
        with self.assertRaisesRegex(LayoutError, "vertical safe area"):
            layout_tracks(
                {"track-a": "one two three"},
                tracks=(tall,),
                fonts={"body-face": self.font},
                safe_area=small_area,
                measure=_monospace_width,
            )

        inset = replace(tall, line_height_px=10, horizontal_inset_px=50)
        with self.assertRaisesRegex(LayoutError, "consumes its safe width"):
            layout_tracks(
                {"track-a": "one"},
                tracks=(inset,),
                fonts={"body-face": self.font},
                safe_area=small_area,
                measure=_monospace_width,
            )

    def test_track_layout_rejects_ambiguous_stack_order(self) -> None:
        base = TrackLayoutConfig(
            track_id="track-a",
            font_key="body-face",
            layer=0,
            stack_order=0,
            max_lines=1,
            line_height_px=10,
        )
        duplicate = replace(base, track_id="track-b", layer=1)
        with self.assertRaisesRegex(LayoutError, "stack_order"):
            layout_tracks(
                {"track-a": "a", "track-b": "b"},
                tracks=(base, duplicate),
                fonts={"body-face": self.font},
                safe_area=SafeArea(100, 100, 0, 0, 100, 100),
                measure=_monospace_width,
            )


class SubtitleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.primary_style = AssStyleConfig(
            name="PrimaryStyle",
            font_name="Resolved Font A",
            font_size=52,
            outline=3,
            shadow=1,
            margin_left=180,
            margin_right=180,
            margin_vertical=90,
        )
        self.secondary_style = AssStyleConfig(
            name="SecondaryStyle",
            font_name="Resolved Font B",
            font_size=34,
            primary_colour="&H00DDEEFF",
            outline=2,
            shadow=0,
            margin_left=200,
            margin_right=200,
            margin_vertical=165,
        )
        self.tracks = (
            SubtitleTrackConfig(
                track_id="track-a",
                locale="locale-a",
                layer=4,
                style=self.primary_style,
            ),
            SubtitleTrackConfig(
                track_id="track-b",
                locale="locale-b",
                layer=8,
                style=self.secondary_style,
            ),
        )
        self.config = AssDocumentConfig(
            title="Config-driven subtitle fixture",
            play_res_x=1920,
            play_res_y=1080,
            duration_seconds=10,
            cue_wrap_style=2,
        )
        self.fonts = {"Resolved Font A", "Resolved Font B"}

    def test_timestamp_uses_strict_decimal_half_up_rounding(self) -> None:
        self.assertEqual("0:00:00.00", ass_timestamp(0))
        self.assertEqual("0:01:05.68", ass_timestamp(Decimal("65.675")))
        self.assertEqual("1:00:00.00", ass_timestamp(3600))

    def test_timestamp_rejects_invalid_or_out_of_range_values(self) -> None:
        for value in (-0.01, True, "1", math.nan, math.inf, Decimal("Infinity")):
            with self.subTest(value=value), self.assertRaises(SubtitleError):
                ass_timestamp(value)  # type: ignore[arg-type]
        with self.assertRaises(SubtitleError):
            ass_timestamp(Decimal("359999.995"))

    def test_ass_escape_handles_markup_newlines_and_tabs(self) -> None:
        self.assertEqual(
            r"a\\b\{c\}\Nx\hy",
            ass_escape("a\\b{c}\r\nx\ty"),
        )
        with self.assertRaises(SubtitleError):
            ass_escape("bad\x00text")

    def test_document_is_deterministic_and_tracks_are_config_driven(self) -> None:
        cues = (
            AssCue("cue-b", "track-b", 1, 2, "brace {x}\nnext"),
            AssCue("cue-a", "track-a", Decimal("0.5"), Decimal("2.5"), "plain, text"),
        )
        first = render_ass_document(
            self.config,
            self.tracks,
            cues,
            available_font_names=self.fonts,
        )
        second = render_ass_document(
            self.config,
            tuple(reversed(self.tracks)),
            tuple(reversed(cues)),
            available_font_names=tuple(reversed(sorted(self.fonts))),
        )
        self.assertEqual(first, second)
        self.assertIn("Title: Config-driven subtitle fixture", first)
        self.assertIn("Style: PrimaryStyle,Resolved Font A,52", first)
        self.assertIn("Style: SecondaryStyle,Resolved Font B,34", first)
        self.assertIn(
            r"Dialogue: 4,0:00:00.50,0:00:02.50,PrimaryStyle,cue-a,0,0,0,,{\q2}plain, text",
            first,
        )
        self.assertIn(
            r"Dialogue: 8,0:00:01.00,0:00:02.00,SecondaryStyle,cue-b,0,0,0,,{\q2}brace \{x\}\Nnext",
            first,
        )
        self.assertNotIn("Chinese", first)
        self.assertNotIn("English", first)

    def test_document_requires_explicitly_resolved_fonts(self) -> None:
        cue = AssCue("cue-a", "track-a", 0, 1, "text")
        with self.assertRaisesRegex(SubtitleError, "required font"):
            render_ass_document(
                self.config,
                self.tracks,
                (cue,),
                available_font_names={"Resolved Font A"},
            )
        with self.assertRaises(SubtitleError):
            render_ass_document(
                self.config,
                self.tracks,
                (cue,),
                available_font_names=set(),
            )

    def test_document_rejects_unknown_track_duplicate_ids_and_overlap(self) -> None:
        unknown = AssCue("cue-x", "track-x", 0, 1, "text")
        with self.assertRaisesRegex(SubtitleError, "unknown track"):
            render_ass_document(
                self.config,
                self.tracks,
                (unknown,),
                available_font_names=self.fonts,
            )

        duplicate = (
            AssCue("same", "track-a", 0, 1, "first"),
            AssCue("same", "track-b", 1, 2, "second"),
        )
        with self.assertRaisesRegex(SubtitleError, "duplicate cue id"):
            render_ass_document(
                self.config,
                self.tracks,
                duplicate,
                available_font_names=self.fonts,
            )

        overlapping = (
            AssCue("cue-1", "track-a", 0, 2, "first"),
            AssCue("cue-2", "track-a", 1, 3, "second"),
        )
        with self.assertRaisesRegex(SubtitleError, "overlaps"):
            render_ass_document(
                self.config,
                self.tracks,
                overlapping,
                available_font_names=self.fonts,
            )

    def test_document_rejects_time_and_style_bounds(self) -> None:
        with self.assertRaisesRegex(SubtitleError, "positive after centisecond"):
            AssCue("cue-short", "track-a", 1, Decimal("1.004"), "text")

        beyond = AssCue("cue-late", "track-a", 9, Decimal("10.01"), "text")
        with self.assertRaisesRegex(SubtitleError, "outside"):
            render_ass_document(
                self.config,
                self.tracks,
                (beyond,),
                available_font_names=self.fonts,
            )

        invalid_style = replace(
            self.primary_style,
            margin_left=1000,
            margin_right=920,
        )
        invalid_track = replace(self.tracks[0], style=invalid_style)
        with self.assertRaisesRegex(SubtitleError, "consume the render width"):
            render_ass_document(
                self.config,
                (invalid_track,),
                (AssCue("cue-a", "track-a", 0, 1, "text"),),
                available_font_names={"Resolved Font A"},
            )

    def test_conflicting_style_definitions_fail_closed(self) -> None:
        conflicting = SubtitleTrackConfig(
            track_id="track-c",
            locale="locale-c",
            layer=9,
            style=replace(self.primary_style, font_size=60),
        )
        with self.assertRaisesRegex(SubtitleError, "conflicting definitions"):
            render_ass_document(
                self.config,
                (self.tracks[0], conflicting),
                (AssCue("cue-a", "track-a", 0, 1, "text"),),
                available_font_names=self.fonts,
            )


if __name__ == "__main__":
    unittest.main()
