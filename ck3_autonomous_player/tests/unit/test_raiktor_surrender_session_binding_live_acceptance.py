"""Pure checks for the paused Raiktor session-binding live harness."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "native_bridge"
    / "research"
    / "run_raiktor_surrender_session_binding_live_acceptance.py"
)
SPEC = importlib.util.spec_from_file_location(
    "run_raiktor_surrender_session_binding_live_acceptance", SCRIPT
)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError(f"cannot load harness: {SCRIPT}")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

from test_war_termination_terms_contract import (  # noqa: E402
    WAR_ID,
    _available_raiktor_observed_terms,
)
from xar_autoplayer.bridge.raiktor_surrender_public_aggregate import (  # noqa: E402
    project_raiktor_surrender_six_domain,
)
from xar_autoplayer.bridge import (  # noqa: E402
    raiktor_surrender_session_binding_contract as session_contract,
)
from xar_autoplayer.bridge.war_contract import (  # noqa: E402
    normalize_war_termination_terms,
)


ATTACKER_ID = 29_829
DEFENDER_ID = 41_002
DATE_RAW = 53_175_816


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:7",
        "revision": 91,
        "native_revision": 7,
        "date_raw": DATE_RAW,
        "paused": True,
        "episode_run_id": "native-29829-fixture",
        "episode_character_id": ATTACKER_ID,
        "played_character": {"character_id": ATTACKER_ID, "alive": True},
        "diagnostics": {
            "connection_generation": 12,
            "bridge_pid": 51_268,
        },
        "active_wars": [
            {
                "war_id": WAR_ID,
                "player_side": "attacker",
                "player_is_primary_war_leader": True,
                "primary_opponent_character_id": DEFENDER_ID,
            }
        ],
    }


def _query_and_cache() -> tuple[dict[str, object], dict[str, object]]:
    before = _snapshot()
    terms = normalize_war_termination_terms(
        _available_raiktor_observed_terms(), expected_war_id=WAR_ID
    )
    receipt = {
        "queried_snapshot_id": before["snapshot_id"],
        "queried_revision": before["revision"],
        "queried_native_revision": before["native_revision"],
        "queried_connection_generation": 12,
        "episode_run_id": before["episode_run_id"],
    }
    aggregate = project_raiktor_surrender_six_domain(before, terms)
    wrapper = session_contract.bind_raiktor_surrender_aggregate_session(
        before, receipt, aggregate
    )
    query = {
        "query_sequence": 14,
        "war_termination_terms": terms,
        **receipt,
        "raiktor_surrender_aggregate_session": wrapper,
    }
    cached = {
        **before,
        "war_termination_terms": [
            {
                **terms,
                "query_sequence": 14,
                **receipt,
                "raiktor_surrender_aggregate_session": wrapper,
            }
        ],
    }
    return query, cached


class RaiktorSurrenderSessionBindingLiveAcceptanceTests(unittest.TestCase):
    def test_session_checks_bind_query_and_exact_frame_cache(self) -> None:
        before = _snapshot()
        query, cached = _query_and_cache()

        result = HARNESS._session_binding_checks(
            before=before,
            query=query,
            cached_snapshot=cached,
            war_id=WAR_ID,
            expected_character_id=ATTACKER_ID,
        )

        self.assertTrue(result["ok"])
        self.assertTrue(all(result["checks"].values()))
        self.assertIsNone(result["normalization_error"])

    def test_missing_pid_and_promoted_truce_are_separate_red_checks(self) -> None:
        before = _snapshot()
        query, cached = _query_and_cache()
        before["diagnostics"]["bridge_pid"] = None

        missing_pid = HARNESS._session_binding_checks(
            before=before,
            query=query,
            cached_snapshot=cached,
            war_id=WAR_ID,
            expected_character_id=ATTACKER_ID,
        )

        self.assertFalse(missing_pid["ok"])
        self.assertFalse(
            missing_pid["checks"]["wrapper_strictly_normalized"]
        )
        query, cached = _query_and_cache()
        query["raiktor_surrender_aggregate_session"]["aggregate"]["domains"][
            "truce"
        ] = {"available": True}
        promoted = HARNESS._session_binding_checks(
            before=_snapshot(),
            query=query,
            cached_snapshot=cached,
            war_id=WAR_ID,
            expected_character_id=ATTACKER_ID,
        )
        self.assertFalse(promoted["checks"]["truce_typed_unavailable"])

    def test_no_launch_preflight_never_enters_session_or_prepares_profile(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source_checkpoint = root / "source.ck3"
            source_driver = root / "driver-state.json"
            game_dir = root / "game"
            game_exe = game_dir / "binaries" / "ck3.exe"
            bridge_dll = root / "bridge.dll"
            bridge_injector = root / "injector.exe"
            for path in (
                source_checkpoint,
                source_driver,
                game_exe,
                bridge_dll,
                bridge_injector,
            ):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fixture")
            checkpoint_sha = "A" * 64
            driver_sha = "B" * 64
            hashes = {
                source_checkpoint.resolve(): checkpoint_sha,
                source_driver.resolve(): driver_sha,
                game_exe.resolve(): HARNESS.terms_live.EXPECTED_EXECUTABLE_SHA256,
                bridge_dll.resolve(): "C" * 64,
                bridge_injector.resolve(): "D" * 64,
            }
            args = argparse.Namespace(
                attempt_dir=root / "future-live-attempt",
                preflight_report=root / "preflight.json",
                source_checkpoint=source_checkpoint,
                source_driver_state=source_driver,
                expected_checkpoint_sha256=checkpoint_sha,
                expected_driver_state_sha256=driver_sha,
                game_dir=game_dir,
                bridge_dll=bridge_dll,
                bridge_injector=bridge_injector,
                war_id=WAR_ID,
                expected_character_id=ATTACKER_ID,
                expected_date_raw=DATE_RAW,
            )
            anchor = {
                "pipe_name": r"\\.\pipe\fixture",
                "episode_character_id": ATTACKER_ID,
                "episode_run_id": "native-29829-fixture",
                "last_checkpoint": {
                    "sha256": checkpoint_sha,
                    "date_raw": DATE_RAW,
                },
            }
            with (
                mock.patch.object(
                    HARNESS.terms_live,
                    "_sha256_file",
                    side_effect=lambda path: hashes[Path(path).resolve()],
                ),
                mock.patch.object(
                    HARNESS.terms_live,
                    "_driver_anchor",
                    return_value=anchor,
                ),
                mock.patch.object(
                    HARNESS.terms_live, "native_session"
                ) as native_session,
                mock.patch.object(
                    HARNESS.terms_live, "prepare_profile"
                ) as prepare_profile,
            ):
                payload, exit_code = HARNESS._no_launch_preflight(args)

        self.assertEqual(exit_code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "ready-to-run")
        self.assertFalse(payload["ck3_started"])
        self.assertFalse(payload["profile_prepared"])
        native_session.assert_not_called()
        prepare_profile.assert_not_called()

    def test_runner_source_has_no_termination_mutation_call(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("ck3_surrender_war", source)
        self.assertNotIn("ck3_offer_white_peace", source)
        self.assertNotIn("ck3_enforce_demands", source)


class RaiktorSurrenderSessionBindingSequenceTests(
    unittest.IsolatedAsyncioTestCase
):
    async def test_sequence_extends_base_double_query_without_new_command(
        self,
    ) -> None:
        before = _snapshot()
        first, between = _query_and_cache()
        second, after = _query_and_cache()
        second["query_sequence"] = 15
        after["war_termination_terms"][0]["query_sequence"] = 15
        base = {
            "ok": True,
            "allowed_gameplay_commands": [
                f"query-war-termination-terms-v1-{WAR_ID}",
                f"query-war-termination-terms-v1-{WAR_ID}",
            ],
            "mutation_commands": [],
            "before_snapshot": {"structured_content": before},
            "first_query": {"structured_content": first},
            "between_snapshot": {"structured_content": between},
            "second_query": {"structured_content": second},
            "after_snapshot": {"structured_content": after},
        }
        with mock.patch.object(
            HARNESS.terms_live,
            "_run_mcp_sequence",
            new=mock.AsyncMock(return_value=base),
        ):
            result = await HARNESS._run_session_binding_mcp_sequence(
                object(),
                war_id=WAR_ID,
                expected_character_id=ATTACKER_ID,
                expected_date_raw=DATE_RAW,
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["session_binding"]["ok"])
        self.assertEqual(result["mutation_commands"], [])


if __name__ == "__main__":
    unittest.main()
