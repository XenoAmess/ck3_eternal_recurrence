from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from xar_promo.sources import (
    EVIDENCE_CARD,
    GENERATED_CARD,
    STILL,
    VIDEO,
    PreparedVisual,
    SourceKind,
    VisualBindingError,
    VisualProbeResult,
    VisualResolutionError,
    VisualSource,
    VisualSourceValidationError,
    prepare_visual,
    validate_visual_source,
    verify_prepared_visual,
)


class FakeProbe:
    def __init__(self, result: VisualProbeResult) -> None:
        self.result = result
        self.calls: list[Path] = []

    def __call__(self, path: Path) -> VisualProbeResult:
        self.calls.append(path)
        return self.result


class SourcesTests(unittest.TestCase):
    def test_builtin_kinds_are_stable_and_custom_kinds_are_extensible(self) -> None:
        self.assertEqual(("video", "video"), (VIDEO.id, VIDEO.media_family))
        self.assertEqual(("still", "image"), (STILL.id, STILL.media_family))
        self.assertEqual(
            ("generated-card", "image"),
            (GENERATED_CARD.id, GENERATED_CARD.media_family),
        )
        self.assertEqual(
            ("evidence-card", "image"),
            (EVIDENCE_CARD.id, EVIDENCE_CARD.media_family),
        )
        self.assertEqual(SourceKind("animated-map", "video").id, "animated-map")

    def test_validate_only_plans_missing_generated_visual_without_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "attempt-that-does-not-exist"
            source = VisualSource(
                "opening-card",
                GENERATED_CARD,
                Path("visuals/opening.png"),
                "title-renderer",
                requires_resolution=True,
            )

            planned = validate_visual_source(
                source,
                workdir=root,
                validate_only=True,
            )

            self.assertEqual((root / "visuals/opening.png").resolve(), planned)
            self.assertFalse(root.exists())
            with self.assertRaises(VisualBindingError):
                validate_visual_source(source, workdir=root, validate_only=False)

    def test_prepared_source_must_exist_even_during_validate_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = VisualSource(
                "missing-capture",
                VIDEO,
                root / "missing.mkv",
                "capture",
            )
            with self.assertRaises(VisualBindingError):
                validate_visual_source(source, workdir=root / "attempt", validate_only=True)

    def test_generated_output_must_be_planned_beneath_workdir(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = VisualSource(
                "escape",
                GENERATED_CARD,
                root / "elsewhere" / "card.png",
                "renderer",
                requires_resolution=True,
            )
            with self.assertRaisesRegex(VisualSourceValidationError, "beneath workdir"):
                validate_visual_source(
                    source,
                    workdir=root / "attempt",
                    validate_only=True,
                )

    def test_generated_build_binds_actual_bytes_type_and_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            metadata = {"layout": "caller-owned"}
            source = VisualSource(
                "chapter-card",
                GENERATED_CARD,
                Path("visuals/chapter.png"),
                "injected-renderer",
                requires_resolution=True,
                metadata=metadata,
            )
            resolver_calls: list[tuple[VisualSource, Path]] = []

            def resolver(item: VisualSource, *, workdir: Path) -> Path:
                resolver_calls.append((item, workdir))
                output = workdir / item.path
                output.parent.mkdir(parents=True)
                output.write_bytes(b"FAKE-PNG-VISUAL-BYTES")
                return output

            probe = FakeProbe(VisualProbeResult("image/png", 1920, 1080))
            prepared = prepare_visual(
                source,
                workdir=root / "attempt",
                resolver=resolver,
                probe=probe,
            )

            expected_path = (root / "attempt/visuals/chapter.png").resolve()
            self.assertEqual(expected_path, prepared.path)
            self.assertEqual("image/png", prepared.media_type)
            self.assertEqual((1920, 1080), (prepared.width, prepared.height))
            self.assertEqual(len(b"FAKE-PNG-VISUAL-BYTES"), prepared.bytes)
            self.assertEqual(
                hashlib.sha256(b"FAKE-PNG-VISUAL-BYTES").hexdigest().upper(),
                prepared.sha256,
            )
            self.assertEqual([(source, (root / "attempt").resolve())], resolver_calls)
            self.assertEqual([expected_path], probe.calls)
            metadata["layout"] = "mutated-after-authoring"
            self.assertEqual("caller-owned", prepared.metadata["layout"])
            with self.assertRaises(TypeError):
                prepared.metadata["new"] = "forbidden"  # type: ignore[index]

    def test_existing_prepared_visual_bypasses_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            capture = root / "capture.mkv"
            capture.write_bytes(b"FAKE-MATROSKA-BYTES")
            source = VisualSource("capture", VIDEO, capture, "capture-bundle")

            def forbidden_resolver(source: VisualSource, *, workdir: Path) -> Path:
                raise AssertionError("prepared sources must bypass the resolver")

            prepared = prepare_visual(
                source,
                workdir=root / "attempt",
                resolver=forbidden_resolver,
                probe=FakeProbe(VisualProbeResult("video/x-matroska", 1280, 720)),
            )
            self.assertEqual(capture.resolve(), prepared.path)
            self.assertEqual(VIDEO, prepared.kind)

    def test_resolver_must_return_exact_declared_path_and_real_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = VisualSource(
                "card",
                GENERATED_CARD,
                Path("card.png"),
                "renderer",
                requires_resolution=True,
            )
            probe = FakeProbe(VisualProbeResult("image/png", 640, 360))

            with self.assertRaisesRegex(VisualResolutionError, "requires a VisualResolver"):
                prepare_visual(source, workdir=root, resolver=None, probe=probe)

            def string_resolver(source: VisualSource, *, workdir: Path) -> Path:
                return str(workdir / source.path)  # type: ignore[return-value]

            with self.assertRaisesRegex(VisualResolutionError, "pathlib.Path"):
                prepare_visual(source, workdir=root, resolver=string_resolver, probe=probe)

            def wrong_path(source: VisualSource, *, workdir: Path) -> Path:
                output = workdir / "different.png"
                output.write_bytes(b"wrong target")
                return output

            with self.assertRaisesRegex(VisualResolutionError, "planned"):
                prepare_visual(source, workdir=root, resolver=wrong_path, probe=probe)

            def missing_file(source: VisualSource, *, workdir: Path) -> Path:
                return workdir / source.path

            with self.assertRaises(VisualBindingError):
                prepare_visual(source, workdir=root, resolver=missing_file, probe=probe)

    def test_probe_must_observe_visual_media_with_matching_family(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            still = root / "still.png"
            still.write_bytes(b"fake image")
            source = VisualSource("still", STILL, still, "photographer")

            with self.assertRaisesRegex(VisualBindingError, "requires image"):
                prepare_visual(
                    source,
                    workdir=root / "attempt",
                    resolver=None,
                    probe=FakeProbe(VisualProbeResult("video/mp4", 1920, 1080)),
                )

            def bad_probe(path: Path) -> object:
                return {"media_type": "image/png", "width": 1, "height": 1}

            with self.assertRaisesRegex(VisualBindingError, "VisualProbeResult"):
                prepare_visual(
                    source,
                    workdir=root / "attempt",
                    resolver=None,
                    probe=bad_probe,  # type: ignore[arg-type]
                )

    def test_manifest_cannot_masquerade_as_visual_input(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest = root / "capture-manifest.json"
            manifest.write_text('{"artifact": "capture.mp4"}', encoding="utf-8")
            declared = VisualSource("manifest", VIDEO, manifest, "evidence-index")

            with self.assertRaisesRegex(VisualBindingError, "manifest path"):
                prepare_visual(
                    declared,
                    workdir=root / "attempt",
                    resolver=None,
                    probe=FakeProbe(VisualProbeResult("video/mp4", 1920, 1080)),
                )

            renamed = root / "manifest-disguised-as-video.mp4"
            renamed.write_bytes(manifest.read_bytes())
            disguised = VisualSource("disguised", VIDEO, renamed, "evidence-index")

            def byte_inspecting_probe(path: Path) -> VisualProbeResult:
                if path.read_bytes().lstrip().startswith(b"{"):
                    raise ValueError("actual bytes are JSON, not visual media")
                return VisualProbeResult("video/mp4", 1920, 1080)

            with self.assertRaisesRegex(VisualBindingError, "actual bytes are JSON"):
                prepare_visual(
                    disguised,
                    workdir=root / "attempt",
                    resolver=None,
                    probe=byte_inspecting_probe,
                )

    def test_probe_dimensions_are_strictly_positive(self) -> None:
        for width, height in ((0, 1), (1, 0), (True, 1), (1, -2)):
            with self.subTest(width=width, height=height), self.assertRaises(
                VisualSourceValidationError
            ):
                VisualProbeResult("image/png", width, height)  # type: ignore[arg-type]

    def test_verify_detects_byte_or_dimension_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            still = root / "still.png"
            still.write_bytes(b"first image bytes")
            source = VisualSource("still", STILL, still, "photographer")
            original_probe = FakeProbe(VisualProbeResult("image/png", 800, 600))
            prepared = prepare_visual(
                source,
                workdir=root / "attempt",
                resolver=None,
                probe=original_probe,
            )
            self.assertIs(prepared, verify_prepared_visual(prepared, probe=original_probe))

            with self.assertRaisesRegex(VisualBindingError, "dimension binding"):
                verify_prepared_visual(
                    prepared,
                    probe=FakeProbe(VisualProbeResult("image/png", 801, 600)),
                )

            still.write_bytes(b"changed image bytes")
            with self.assertRaisesRegex(VisualBindingError, "byte binding"):
                verify_prepared_visual(prepared, probe=original_probe)

    def test_prepared_visual_rejects_shape_only_records_without_valid_binding_fields(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = (Path(raw) / "visual.png").resolve()
            path.write_bytes(b"bytes")
            with self.assertRaises(VisualBindingError):
                PreparedVisual(
                    source_id="visual",
                    kind=STILL,
                    path=path,
                    media_type="application/json",
                    origin="resolver",
                    bytes=5,
                    sha256="0" * 64,
                    width=1,
                    height=1,
                )


if __name__ == "__main__":
    unittest.main()
