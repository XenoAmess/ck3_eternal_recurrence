from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from xar_promo.adapters.ck3 import CK3CaptureError, load_capture_bundle  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _record(path: Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _indexed_row(root: Path, path: Path) -> dict[str, object]:
    return {
        "path": path.resolve().relative_to(root.resolve()).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _make_frame(root: Path, span_id: str, phase: str) -> dict[str, object]:
    evidence_root = root / "cell" / "promo" / "proof"
    image = evidence_root / f"{span_id}-{phase}.png"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(f"lossless-frame:{span_id}:{phase}".encode("ascii"))
    frame: dict[str, object] = {
        "schema_version": 1,
        "result": "GREEN",
        "span": span_id,
        "phase": phase,
        "image": _record(image),
        "producer_assertions": {"hud_visible": True, "fixture_ui_absent": True},
    }
    gate = evidence_root / f"{span_id}-{phase}-gate.json"
    _write_json(gate, frame)
    frame["gate"] = _record(gate)
    return frame


def _build_bundle(root: Path) -> None:
    raw = root / "cell" / "promo" / "raw" / "take-01.mkv"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(b"synthetic lossless-ish CK3 capture\x00\x01")

    span_id = "feature_demo"
    timeline = {
        "schema": 2,
        "exclude_ck3_loading": True,
        "source_kind": "real CK3 desktop capture after gameplay HUD",
        "raw_path": str(raw.resolve()),
        "raw_bytes": raw.stat().st_size,
        "raw_sha256": _sha256(raw),
        "marks": [
            {"label": "recording_started_after_gameplay_hud", "seconds": 1.0},
            {"label": "feature_demo_clean_begin", "seconds": 2.0},
            {"label": "feature_demo_clean_end", "seconds": 5.5},
            {"label": "recording_stop_requested", "seconds": 7.0},
        ],
        "clean_frame_gates": [
            {
                "span_id": span_id,
                "result": "GREEN",
                "begin_mark": "feature_demo_clean_begin",
                "end_mark": "feature_demo_clean_end",
                "frames": [
                    _make_frame(root, span_id, "begin"),
                    _make_frame(root, span_id, "end"),
                ],
            }
        ],
        "clean_capture_complete": True,
        "missing_clean_spans": [],
    }
    timeline_path = root / "cell" / "promo" / "capture-timeline.json"
    _write_json(timeline_path, timeline)
    report = {
        "schema_version": 1,
        "result": "GREEN",
        "cell": {
            "schema_version": 1,
            "result": "GREEN",
            "promo_capture": copy.deepcopy(timeline),
        },
    }
    report_path = root / "report.json"
    _write_json(report_path, report)

    indexed_paths = [
        report_path,
        timeline_path,
        raw,
        *sorted((root / "cell" / "promo" / "proof").iterdir()),
    ]
    index = {
        "schema_version": 1,
        "result": "GREEN",
        "artifact_root": str(root.resolve()),
        "files": [_indexed_row(root, path) for path in indexed_paths],
    }
    _write_json(root / "evidence-index.json", index)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _refresh_index(root: Path, relative_path: str) -> None:
    index_path = root / "evidence-index.json"
    index = _load_json(index_path)
    target = root / Path(relative_path)
    for row in index["files"]:  # type: ignore[index]
        if row["path"] == relative_path:  # type: ignore[index]
            row.update(_indexed_row(root, target))  # type: ignore[union-attr]
            break
    else:
        raise AssertionError(f"missing fixture index row: {relative_path}")
    _write_json(index_path, index)


class CK3CaptureAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        _build_bundle(self.root)

    def _rewrite_timeline_and_report(self, mutator) -> None:
        timeline_path = self.root / "cell" / "promo" / "capture-timeline.json"
        report_path = self.root / "report.json"
        timeline = _load_json(timeline_path)
        mutator(timeline)
        _write_json(timeline_path, timeline)
        report = _load_json(report_path)
        report["cell"]["promo_capture"] = copy.deepcopy(timeline)  # type: ignore[index]
        _write_json(report_path, report)
        _refresh_index(self.root, "cell/promo/capture-timeline.json")
        _refresh_index(self.root, "report.json")

    def test_loads_hash_bound_files_marks_and_clean_spans(self) -> None:
        bundle = load_capture_bundle(
            self.root,
            required_span_ids=("feature_demo",),
            required_mark_labels=("feature_demo_clean_begin",),
        )

        self.assertEqual(bundle.timeline_schema, 2)
        self.assertEqual(bundle.recording_start_seconds, 1.0)
        self.assertEqual(bundle.recording_stop_seconds, 7.0)
        self.assertEqual(bundle.mark("feature_demo_clean_end").seconds, 5.5)
        span = bundle.clean_span("feature_demo")
        self.assertEqual((span.begin_seconds, span.end_seconds), (2.0, 5.5))
        self.assertEqual(span.duration_seconds, 3.5)
        self.assertEqual(len(span.evidence), 4)
        self.assertEqual(bundle.report.sha256, _sha256(self.root / "report.json").upper())
        self.assertEqual(
            bundle.evidence_index.sha256,
            _sha256(self.root / "evidence-index.json").upper(),
        )

    def test_verify_unchanged_accepts_untouched_sources(self) -> None:
        bundle = load_capture_bundle(self.root)
        bundle.verify_unchanged()

    def test_verify_unchanged_rejects_raw_capture_tampering_after_load(self) -> None:
        bundle = load_capture_bundle(self.root)
        raw = self.root / "cell" / "promo" / "raw" / "take-01.mkv"
        raw.write_bytes(raw.read_bytes() + b"tampered-after-load")

        with self.assertRaisesRegex(
            CK3CaptureError,
            "capture source changed after bundle load: cell/promo/raw/take-01.mkv",
        ):
            bundle.verify_unchanged()

    def test_verify_unchanged_rejects_clean_frame_evidence_tampering_after_load(self) -> None:
        bundle = load_capture_bundle(self.root)
        image = self.root / "cell" / "promo" / "proof" / "feature_demo-begin.png"
        image.write_bytes(image.read_bytes() + b"tampered-after-load")

        with self.assertRaisesRegex(
            CK3CaptureError,
            "capture source changed after bundle load: cell/promo/proof/feature_demo-begin.png",
        ):
            bundle.verify_unchanged()

    def test_rejects_raw_capture_tampering(self) -> None:
        raw = self.root / "cell" / "promo" / "raw" / "take-01.mkv"
        raw.write_bytes(raw.read_bytes() + b"tampered")

        with self.assertRaisesRegex(CK3CaptureError, "byte count mismatch"):
            load_capture_bundle(self.root)

    def test_rejects_capture_that_did_not_start_after_gameplay_hud(self) -> None:
        def mutate(timeline: dict[str, object]) -> None:
            timeline["marks"][0]["label"] = "recording_started_during_loading"  # type: ignore[index]

        self._rewrite_timeline_and_report(mutate)
        with self.assertRaisesRegex(CK3CaptureError, "first capture mark"):
            load_capture_bundle(self.root)

    def test_rejects_missing_clean_frame_evidence(self) -> None:
        image = self.root / "cell" / "promo" / "proof" / "feature_demo-begin.png"
        image.unlink()

        with self.assertRaisesRegex(CK3CaptureError, "missing"):
            load_capture_bundle(self.root)

    def test_rejects_unbound_required_projection(self) -> None:
        with self.assertRaisesRegex(CK3CaptureError, "missing required clean spans"):
            load_capture_bundle(self.root, required_span_ids=("unrecorded_feature",))

    def test_rejects_report_that_does_not_exactly_bind_timeline(self) -> None:
        report_path = self.root / "report.json"
        report = _load_json(report_path)
        report["cell"]["promo_capture"]["source_kind"] = "different capture"  # type: ignore[index]
        _write_json(report_path, report)
        _refresh_index(self.root, "report.json")

        with self.assertRaisesRegex(CK3CaptureError, "does not exactly bind"):
            load_capture_bundle(self.root)

    def test_rejects_gate_json_that_does_not_bind_timeline_frame(self) -> None:
        gate_path = (
            self.root
            / "cell"
            / "promo"
            / "proof"
            / "feature_demo-begin-gate.json"
        )
        gate = _load_json(gate_path)
        gate["producer_assertions"]["hud_visible"] = False  # type: ignore[index]
        _write_json(gate_path, gate)

        timeline_path = self.root / "cell" / "promo" / "capture-timeline.json"
        timeline = _load_json(timeline_path)
        timeline["clean_frame_gates"][0]["frames"][0]["gate"] = _record(gate_path)  # type: ignore[index]
        _write_json(timeline_path, timeline)
        report_path = self.root / "report.json"
        report = _load_json(report_path)
        report["cell"]["promo_capture"] = copy.deepcopy(timeline)  # type: ignore[index]
        _write_json(report_path, report)
        _refresh_index(self.root, "cell/promo/proof/feature_demo-begin-gate.json")
        _refresh_index(self.root, "cell/promo/capture-timeline.json")
        _refresh_index(self.root, "report.json")

        with self.assertRaisesRegex(CK3CaptureError, "does not exactly bind"):
            load_capture_bundle(self.root)

    def test_failed_attempt_is_rejected_without_mutating_or_deleting_it(self) -> None:
        report_path = self.root / "report.json"
        report = _load_json(report_path)
        report["result"] = "RED"
        _write_json(report_path, report)
        _refresh_index(self.root, "report.json")
        before = {
            path.relative_to(self.root).as_posix(): (path.stat().st_size, _sha256(path))
            for path in self.root.rglob("*")
            if path.is_file()
        }

        with self.assertRaisesRegex(CK3CaptureError, "must be GREEN"):
            load_capture_bundle(self.root)

        after = {
            path.relative_to(self.root).as_posix(): (path.stat().st_size, _sha256(path))
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
