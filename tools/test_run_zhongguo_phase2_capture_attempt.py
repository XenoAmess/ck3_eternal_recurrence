from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from run_zhongguo_phase2_capture_attempt import prepare_plan  # noqa: E402


NOW = dt.datetime(2026, 9, 2, 12, 0, tzinfo=dt.timezone.utc)


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _media() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "zhongguo-361-phase2-media-environment-preflight",
        "result": "GREEN",
        "expires_at_utc": "2026-09-03T12:00:00+00:00",
        "promo_toolchain": {
            # A fresh origin/main may legitimately advance beyond the version
            # that existed when this wrapper was first written.
            "version": "0.3.0",
            "clean": True,
            "head": "a" * 40,
            "origin_main": "a" * 40,
        },
        "media": {
            "ffmpeg": {"bytes": 10, "sha256": "b" * 64},
            "ffprobe": {"bytes": 11, "sha256": "c" * 64},
        },
    }


def _seed(*, ready: bool) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "ready" if ready else "blocked_seed_generation_required",
        "ready": ready,
        "source": {"sha256": "d" * 64},
        "domain_query_matrix": {
            "schema_version": 1,
            "b2_pip_owner_character_id": 2 if ready else None,
            "incident_owner_character_id": 3 if ready else None,
            "workforce_owner_character_id": 4 if ready else None,
            "ai_owned_case_owner_character_id": 5 if ready else None,
            "ai_owned_case_subject_character_id": 6 if ready else None,
        },
    }


def _source_registry(root: Path) -> Path:
    seed_sha = "d" * 64
    lineage = f"zg361-phase2-seed-{seed_sha}"
    specs = (
        ("phase2_promotion_compensation", "capture_promotion_compensation", "zg361pp.147", 2, 1),
        ("phase2_projects_metrics", "capture_projects_metrics", "zg361cp.26", 2, 1),
        ("phase2_incidents_operations", "capture_incidents_operations", "zg361.50", 2, 1),
        ("phase2_cross_cycle_endgame", "capture_cross_cycle_endgame", "zg361we.356", 2, 1),
    )
    entries = []
    for index, (span, handler, event, owner, player) in enumerate(specs):
        checkpoint = _write(root / f"source-{index}.ck3", f"checkpoint-{index}")
        digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest().upper()
        date_raw = 100 + index
        entries.append(
            {
                "span_id": span,
                "handler": handler,
                "source_event_definition_key": event,
                "owner_character_id": owner,
                "player_character_id": player,
                "date_raw": date_raw,
                "checkpoint": {
                    "path": str(checkpoint.resolve()),
                    "bytes": checkpoint.stat().st_size,
                    "sha256": digest,
                    "save_lineage_id": lineage,
                },
                "source_receipt": {
                    "result": "GREEN",
                    "evidence_class": "real_ck3",
                    "provider_observed": True,
                    "ui_state_verified": True,
                    "fixture_used": False,
                    "console_used": False,
                    "span_id": span,
                    "event_definition_key": event,
                    "owner_character_id": owner,
                    "player_character_id": player,
                    "date_raw": date_raw,
                    "checkpoint_sha256": digest,
                    "save_lineage_id": lineage,
                },
            }
        )
    return _write(
        root / "source-checkpoints.json",
        {
            "schema_version": 1,
            "registry_kind": "zg361_phase2_canonical_source_checkpoint_registry",
            "result": "GREEN",
            "evidence_class": "real_ck3",
            "fixture_used": False,
            "console_used": False,
            "seed_lineage_id": lineage,
            "capture_lineage": {"seed_lineage_id": lineage},
            "entries": entries,
        },
    )


class CaptureAttemptPlanTests(unittest.TestCase):
    def test_pending_observer_and_seed_stay_typed_waiting_without_capture_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "tools").mkdir(parents=True)
            python = _write(root / "python.exe", "")
            runner = _write(source / "tools" / "run_zhongguo_acceptance.py", "")
            self.assertTrue(runner.is_file())
            bridge = _write(root / "bridge.dll", "")
            injector = _write(root / "injector.exe", "")
            seed = _write(root / "seed.json", _seed(ready=False))
            media = _write(root / "media.json", _media())
            import hashlib

            media_sha = hashlib.sha256(media.read_bytes()).hexdigest()
            manifest, path = prepare_plan(
                attempt_dir=root / "attempt",
                source_root=source,
                source_git_commit="a" * 40,
                python=python,
                observer_artifact=None,
                seed_contract=seed,
                media_preflight_report=media,
                expected_media_preflight_sha256=media_sha,
                bridge_dll=bridge,
                bridge_injector=injector,
                now=NOW,
            )
            self.assertEqual(manifest["result"], "RED")
            self.assertEqual(
                manifest["reason_code"], "completion_observer_artifact_pending"
            )
            self.assertIn("seed_contract_not_ready", manifest["blockers"])
            self.assertFalse((root / "attempt" / "capture").exists())
            self.assertTrue(path.is_file())
            self.assertFalse(manifest["no_launch_attestation"]["ck3_started"])

    def test_all_bound_inputs_emit_eight_span_ready_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "tools").mkdir(parents=True)
            python = _write(root / "python.exe", "")
            _write(source / "tools" / "run_zhongguo_acceptance.py", "")
            bridge = _write(root / "bridge.dll", "")
            injector = _write(root / "injector.exe", "")
            observer = _write(
                root / "observer.json",
                {
                    "schema": "xar.phase2.completion_observer_ready_to_live.v1",
                    "result": "GREEN",
                    "status": "ready-to-live",
                },
            )
            seed = _write(root / "seed.json", _seed(ready=True))
            registry = _source_registry(root)
            product = root / "product"
            product.mkdir()
            projection = _write(root / "projection.json", {"result": "GREEN"})
            media = _write(root / "media.json", _media())

            media_sha = hashlib.sha256(media.read_bytes()).hexdigest()
            manifest, _ = prepare_plan(
                attempt_dir=root / "attempt",
                source_root=source,
                source_git_commit="a" * 40,
                python=python,
                observer_artifact=observer,
                seed_contract=seed,
                media_preflight_report=media,
                expected_media_preflight_sha256=media_sha,
                bridge_dll=bridge,
                bridge_injector=injector,
                source_checkpoint_registry=registry,
                product_source=product,
                product_projection="phase2-final-product",
                product_projection_manifest=projection,
                frontend_first_load_save_name="phase2_seed",
                now=NOW,
            )
            self.assertEqual(manifest["result"], "GREEN")
            self.assertEqual(manifest["status"], "ready-to-run")
            self.assertEqual(
                manifest["capture_contract"]["default_handlers"], "8/8"
            )
            spans = manifest["capture_contract"]["spans"]
            self.assertEqual(len(spans), 8)
            self.assertEqual(
                manifest["recorder_contract"]["clean_frame_gate_count"], 8
            )
            self.assertIn(
                "04_phase2_seed_loaded.json schema_version=2 GREEN",
                manifest["pre_recorder_gates"],
            )
            self.assertEqual(
                manifest["single_capture_command"]["argv"][2],
                "--phase2-promo-capture",
            )
            self.assertEqual(
                manifest["single_capture_command"]["argv"][3:5],
                ["--phase2-seed-contract", str(seed.resolve())],
            )
            self.assertEqual(
                manifest["managed_session_handoff"]["same_session_boundary"],
                "per-span-pre-action-post-only",
            )
            self.assertTrue(
                manifest["managed_session_handoff"]["cross_span_restart_allowed"]
            )
            self.assertEqual(
                manifest["managed_session_handoff"]["seed_generation_continuity"],
                "save-hash-and-source-provenance",
            )
            self.assertFalse(
                manifest["managed_session_handoff"][
                    "seed_generation_session_reused"
                ]
            )
            self.assertFalse((root / "attempt" / "capture").exists())
            command = manifest["single_capture_command"]["argv"]
            self.assertIn("--phase2-source-checkpoint-registry", command)
            self.assertIn("--phase2-product-source", command)
            self.assertIn("--phase2-product-projection-manifest", command)
            self.assertIn("--phase2-frontend-first-load-save-name", command)
            self.assertEqual(
                manifest["recorder_contract"]["timeline_artifact"],
                "cell/promo/capture-timeline.json",
            )
            self.assertEqual(manifest["recorder_contract"]["report_artifact"], "report.json")
            self.assertEqual(
                manifest["recorder_contract"]["evidence_index_artifact"],
                "evidence-index.json",
            )


if __name__ == "__main__":
    unittest.main()
