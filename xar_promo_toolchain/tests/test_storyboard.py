from __future__ import annotations

import unittest
from dataclasses import replace
from decimal import Decimal

from xar_promo.model import ProjectConfig
from xar_promo.storyboard import (
    ResolvedNarrationDuration,
    StoryboardError,
    TimelineSpacing,
    plan_storyboard,
    validate_storyboard_timeline,
)


def make_project(
    *,
    duration_limit_seconds: int | None = 30,
    first_artifacts: list[str] | None = None,
) -> ProjectConfig:
    return ProjectConfig.from_mapping(
        {
            "format_version": 1,
            "kind": "xar_promo_project_config",
            "project": {"id": "storyboard-test", "title": "Storyboard Test"},
            "pipeline": {"adapter": "generic", "preset": "caller-owned"},
            "locales": {"narration": "locale-a", "subtitles": ["locale-a", "locale-b"]},
            "constraints": {"duration_limit_seconds": duration_limit_seconds},
            "chapters": [
                {
                    "id": "chapter-a",
                    "type": "video",
                    "state": "planned",
                    "title": {"locale-a": "A"},
                    "cues": [
                        {
                            "id": "cue-a1",
                            "narration": {"locale-a": "alpha", "locale-b": "一"},
                            "subtitles": {"locale-a": "alpha", "locale-b": "一"},
                        },
                        {
                            "id": "cue-a2",
                            "narration": {"locale-a": "beta", "locale-b": "二二二"},
                            "subtitles": {"locale-a": "beta", "locale-b": "二二二"},
                        },
                    ],
                    "artifact_ids": first_artifacts or [],
                },
                {
                    "id": "chapter-b",
                    "type": "still",
                    "state": "planned",
                    "title": {"locale-a": "B"},
                    "cues": [
                        {
                            "id": "cue-b1",
                            "narration": {"locale-a": "gamma", "locale-b": "三"},
                            "subtitles": {"locale-a": "gamma", "locale-b": "三"},
                        }
                    ],
                    "artifact_ids": [],
                },
            ],
        }
    )


class MappingEstimator:
    def __init__(self, durations: dict[str, object]) -> None:
        self.durations = durations
        self.calls: list[str] = []

    def __call__(self, project, chapter, cue):
        self.calls.append(cue.cue_id)
        return self.durations[cue.cue_id]


class MappingResolver:
    def __init__(self, durations: dict[str, ResolvedNarrationDuration]) -> None:
        self.durations = durations
        self.calls: list[str] = []

    def __call__(self, project, chapter, cue):
        self.calls.append(cue.cue_id)
        return self.durations.get(cue.cue_id)


class StoryboardPlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spacing = TimelineSpacing(
            cue_gap_seconds="0.25",
            chapter_gap_seconds="1.0",
        )

    def test_real_duration_wins_then_falls_back_and_timeline_is_deterministic(self) -> None:
        project = make_project(first_artifacts=["audio-a1"])
        resolver = MappingResolver(
            {"cue-a1": ResolvedNarrationDuration("2.5", "audio-a1")}
        )
        estimator = MappingEstimator(
            {"cue-a1": "99", "cue-a2": "1.25", "cue-b1": "3.0"}
        )
        first = plan_storyboard(
            project,
            narration_duration_resolver=resolver,
            draft_estimator=estimator,
            spacing=self.spacing,
            available_artifact_ids=["audio-a1"],
        )
        second = plan_storyboard(
            project,
            narration_duration_resolver=MappingResolver(
                {"cue-a1": ResolvedNarrationDuration("2.5", "audio-a1")}
            ),
            draft_estimator=MappingEstimator(
                {"cue-a1": "99", "cue-a2": "1.25", "cue-b1": "3.0"}
            ),
            spacing=self.spacing,
            available_artifact_ids=["audio-a1"],
        )

        self.assertEqual(first, second)
        self.assertEqual(["cue-a1", "cue-a2", "cue-b1"], resolver.calls)
        self.assertEqual(["cue-a2", "cue-b1"], estimator.calls)
        self.assertEqual(Decimal("8.000000"), first.duration_seconds)
        self.assertEqual(
            [
                (Decimal("0.000000"), Decimal("2.500000")),
                (Decimal("2.750000"), Decimal("4.000000")),
                (Decimal("5.000000"), Decimal("8.000000")),
            ],
            [(cue.start_seconds, cue.end_seconds) for cue in first.cues],
        )
        self.assertEqual("resolved-narration", first.cues[0].duration_source)
        self.assertEqual("draft-estimate", first.cues[1].duration_source)
        self.assertEqual("8.000000", first.to_dict()["duration_seconds"])

    def test_validate_only_never_calls_real_audio_resolver(self) -> None:
        class ForbiddenResolver:
            def __call__(self, project, chapter, cue):
                raise AssertionError("validate-only called the audio resolver")

        estimator = MappingEstimator(
            {"cue-a1": "1", "cue-a2": "2", "cue-b1": "3"}
        )
        timeline = plan_storyboard(
            make_project(),
            narration_duration_resolver=ForbiddenResolver(),
            draft_estimator=estimator,
            spacing=self.spacing,
            validate_only=True,
        )
        self.assertEqual(["cue-a1", "cue-a2", "cue-b1"], estimator.calls)
        self.assertTrue(
            all(cue.duration_source == "draft-estimate" for cue in timeline.cues)
        )

    def test_estimation_is_entirely_caller_owned_not_character_based(self) -> None:
        estimator = MappingEstimator(
            {"cue-a1": "4.5", "cue-a2": "1.0", "cue-b1": "2.25"}
        )
        timeline = plan_storyboard(
            make_project(),
            narration_duration_resolver=None,
            draft_estimator=estimator,
            spacing=TimelineSpacing(
                cue_gap_seconds=0,
                chapter_gap_seconds=0,
            ),
            validate_only=True,
        )
        self.assertEqual(
            [Decimal("4.500000"), Decimal("1.000000"), Decimal("2.250000")],
            [cue.duration_seconds for cue in timeline.cues],
        )

    def test_artifact_references_and_resolved_audio_binding_are_checked(self) -> None:
        project = make_project(first_artifacts=["audio-a1"])
        estimator = MappingEstimator(
            {"cue-a1": "1", "cue-a2": "1", "cue-b1": "1"}
        )
        with self.assertRaisesRegex(StoryboardError, "unavailable artifacts"):
            plan_storyboard(
                project,
                narration_duration_resolver=None,
                draft_estimator=estimator,
                spacing=self.spacing,
            )

        with self.assertRaisesRegex(StoryboardError, "not declared"):
            plan_storyboard(
                project,
                narration_duration_resolver=MappingResolver(
                    {"cue-a1": ResolvedNarrationDuration(1, "audio-other")}
                ),
                draft_estimator=MappingEstimator(
                    {"cue-a1": "1", "cue-a2": "1", "cue-b1": "1"}
                ),
                spacing=self.spacing,
                available_artifact_ids=["audio-a1", "audio-other"],
            )

    def test_non_positive_duration_and_negative_spacing_are_rejected(self) -> None:
        with self.assertRaisesRegex(StoryboardError, "cue gap"):
            TimelineSpacing(cue_gap_seconds="-0.1", chapter_gap_seconds=0)
        with self.assertRaisesRegex(StoryboardError, "greater than zero"):
            plan_storyboard(
                make_project(),
                narration_duration_resolver=None,
                draft_estimator=MappingEstimator(
                    {"cue-a1": "0", "cue-a2": "1", "cue-b1": "1"}
                ),
                spacing=self.spacing,
                validate_only=True,
            )

    def test_validator_distinguishes_overlap_from_unexpected_gap(self) -> None:
        timeline = plan_storyboard(
            make_project(),
            narration_duration_resolver=None,
            draft_estimator=MappingEstimator(
                {"cue-a1": "1", "cue-a2": "1", "cue-b1": "1"}
            ),
            spacing=self.spacing,
            validate_only=True,
        )
        second = timeline.cues[1]
        overlap = replace(
            second,
            start_seconds=second.start_seconds - Decimal("0.500000"),
        )
        with self.assertRaisesRegex(StoryboardError, "overlaps"):
            validate_storyboard_timeline(
                replace(timeline, cues=(timeline.cues[0], overlap, timeline.cues[2])),
                spacing=self.spacing,
                duration_limit_seconds=30,
            )

        gap = replace(
            second,
            start_seconds=second.start_seconds + Decimal("0.500000"),
        )
        with self.assertRaisesRegex(StoryboardError, "unexpected gap"):
            validate_storyboard_timeline(
                replace(timeline, cues=(timeline.cues[0], gap, timeline.cues[2])),
                spacing=self.spacing,
                duration_limit_seconds=30,
            )

    def test_total_duration_must_be_strictly_below_limit(self) -> None:
        exact_limit = ProjectConfig.from_mapping(
            {
                "format_version": 1,
                "kind": "xar_promo_project_config",
                "project": {"id": "limit", "title": "Limit"},
                "pipeline": {"adapter": "generic", "preset": "caller-owned"},
                "locales": {"narration": "x", "subtitles": ["x"]},
                "constraints": {"duration_limit_seconds": 10},
                "chapters": [
                    {
                        "id": "only",
                        "type": "still",
                        "state": "planned",
                        "title": {"x": "Only"},
                        "cues": [
                            {
                                "id": "only-cue",
                                "narration": {"x": "text"},
                                "subtitles": {"x": "text"},
                            }
                        ],
                        "artifact_ids": [],
                    }
                ],
            }
        )
        spacing = TimelineSpacing(cue_gap_seconds=0, chapter_gap_seconds=0)
        with self.assertRaisesRegex(StoryboardError, "strictly below"):
            plan_storyboard(
                exact_limit,
                narration_duration_resolver=None,
                draft_estimator=lambda project, chapter, cue: "10",
                spacing=spacing,
                validate_only=True,
            )
        below = plan_storyboard(
            exact_limit,
            narration_duration_resolver=None,
            draft_estimator=lambda project, chapter, cue: "9.999999",
            spacing=spacing,
            validate_only=True,
        )
        self.assertEqual(Decimal("9.999999"), below.duration_seconds)


if __name__ == "__main__":
    unittest.main()
