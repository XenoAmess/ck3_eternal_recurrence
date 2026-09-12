from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.simulation.raiktor_owner_budget_profile_provider import (
    DEFAULT_PROFILE_PATH,
    OwnerBudgetProfileError,
    PROVIDER_SCHEMA,
    SOURCE_CONTRACT,
    VERSIONED_SOURCE_CONTRACT,
    provide_raiktor_owner_budget_profile,
    render_raiktor_owner_budget_profile,
)
from xar_autoplayer.simulation.raiktor_three_way_exit_policy import (
    OWNER_BUDGET_PROFILE_CONTRACT,
    OWNER_BUDGET_PROVIDER,
)


def _source(*, approved: bool = True) -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract": SOURCE_CONTRACT,
        "approval": {
            "status": "approved" if approved else "draft",
            "approved_by": "project-owner" if approved else None,
            "approved_at_utc": (
                "2026-09-06T03:20:00Z" if approved else None
            ),
        },
        "profile_id": "owner-authored-raiktor-budget-2026-09-06",
        "profile_provenance": (
            "explicit project-owner budget artifact; not inferred from play"
        ),
        "pairwise_limits": {
            "maximum_surrender_gold_transfer_raw": 30_000_000,
            "maximum_surrender_prestige_loss_raw": 100_000_000,
            "maximum_surrender_claims_removed": 1,
            "allow_surrender_favor_hook": True,
            "maximum_surrender_truce_days": 1_825,
            "maximum_continue_tail_loss_raw": 100,
            "minimum_switch_margin_raw": 10,
        },
        "white_peace_limits": {
            "maximum_gold_transfer_raw": 0,
            "maximum_prestige_loss_raw": 10_000_000,
            "maximum_claims_removed": 0,
            "allow_favor_hook": False,
            "maximum_truce_days": 1_825,
        },
    }


class RaiktorOwnerBudgetProfileProviderTests(unittest.TestCase):
    def test_missing_source_selects_versioned_repository_default(self) -> None:
        result = provide_raiktor_owner_budget_profile(None)

        self.assertEqual(result["schema"], PROVIDER_SCHEMA)
        self.assertEqual(result["provider"], OWNER_BUDGET_PROVIDER)
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["profile_available"])
        self.assertTrue(result["profile_production_eligible"])
        self.assertTrue(result["default_source_used"])
        self.assertEqual(result["source_kind"], "repository_default")
        self.assertEqual(result["source_profile_version"], "1.0.0")
        self.assertEqual(result["source"]["path"], str(DEFAULT_PROFILE_PATH))
        self.assertEqual(result["blockers"], [])
        self.assertEqual(
            result["owner_budget_profile"]["profile_id"],
            "raiktor-exit-balanced-v1",
        )

    def test_approved_source_renders_existing_policy_contract(self) -> None:
        source = _source()
        payload = json.dumps(
            source, ensure_ascii=False, sort_keys=True, indent=2
        ).encode("utf-8")
        expected_sha = hashlib.sha256(payload).hexdigest().upper()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "owner-budget.json"
            path.write_bytes(payload)

            result = provide_raiktor_owner_budget_profile(path)

        profile = result["owner_budget_profile"]
        self.assertIsInstance(profile, dict)
        assert isinstance(profile, dict)
        self.assertEqual(result["status"], "available")
        self.assertTrue(result["profile_available"])
        self.assertTrue(result["profile_production_eligible"])
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["source"]["sha256"], expected_sha)
        self.assertEqual(profile["contract"], OWNER_BUDGET_PROFILE_CONTRACT)
        self.assertEqual(profile["status"], "complete")
        self.assertEqual(profile["profile_source_sha256"], expected_sha)
        self.assertTrue(profile["profile_production_eligible"])
        self.assertEqual(
            profile["pairwise_limits"]["profile_id"],
            profile["profile_id"],
        )
        self.assertTrue(
            profile["pairwise_limits"]["profile_production_eligible"]
        )

    def test_draft_source_stays_incomplete_and_ineligible(self) -> None:
        source = _source(approved=False)
        profile = render_raiktor_owner_budget_profile(
            source, source_sha256="A" * 64
        )

        self.assertEqual(profile["status"], "incomplete")
        self.assertFalse(profile["profile_production_eligible"])
        self.assertFalse(
            profile["pairwise_limits"]["profile_production_eligible"]
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            result = provide_raiktor_owner_budget_profile(path)

        self.assertEqual(result["status"], "incomplete")
        self.assertTrue(result["profile_available"])
        self.assertFalse(result["profile_production_eligible"])
        self.assertEqual(
            result["blockers"],
            ["owner_budget_profile_not_owner_approved"],
        )

    def test_source_hash_binds_exact_bytes(self) -> None:
        source = _source()
        compact = json.dumps(source, separators=(",", ":")).encode("utf-8")
        indented = json.dumps(source, indent=2).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            compact_path = Path(directory) / "compact.json"
            indented_path = Path(directory) / "indented.json"
            compact_path.write_bytes(compact)
            indented_path.write_bytes(indented)

            compact_result = provide_raiktor_owner_budget_profile(
                compact_path
            )
            indented_result = provide_raiktor_owner_budget_profile(
                indented_path
            )

        self.assertNotEqual(
            compact_result["source"]["sha256"],
            indented_result["source"]["sha256"],
        )
        self.assertNotEqual(
            compact_result["owner_budget_profile"][
                "profile_source_sha256"
            ],
            indented_result["owner_budget_profile"][
                "profile_source_sha256"
            ],
        )

    def test_versioned_operator_override_must_bind_repository_default(
        self,
    ) -> None:
        source = json.loads(DEFAULT_PROFILE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(source["contract"], VERSIONED_SOURCE_CONTRACT)
        source["activation"] = {
            "kind": "operator_override",
            "source": "focused GEN-034 scenario override",
            "base_profile_id": "raiktor-exit-balanced-v1",
            "base_profile_version": "1.0.0",
        }
        source["profile_id"] = "raiktor-exit-focused-override-v1"
        source["profile_version"] = "1.0.1"
        source["pairwise_limits"]["minimum_switch_margin_raw"] = 20

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "override.json"
            path.write_text(json.dumps(source), encoding="utf-8")
            result = provide_raiktor_owner_budget_profile(path)

            drifted = deepcopy(source)
            drifted["activation"]["base_profile_version"] = "2.0.0"
            drifted_path = Path(directory) / "drifted.json"
            drifted_path.write_text(json.dumps(drifted), encoding="utf-8")
            with self.assertRaisesRegex(
                OwnerBudgetProfileError, "base profile identity drifted"
            ):
                provide_raiktor_owner_budget_profile(drifted_path)

        self.assertFalse(result["default_source_used"])
        self.assertEqual(result["source_kind"], "operator_override")
        self.assertEqual(result["source_profile_version"], "1.0.1")
        self.assertEqual(
            result["owner_budget_profile"]["pairwise_limits"][
                "minimum_switch_margin_raw"
            ],
            20,
        )
    def test_malformed_approval_never_promotes(self) -> None:
        cases = {
            "unknown-status": ("status", "ready"),
            "approved-without-author": ("approved_by", None),
            "approved-without-time": ("approved_at_utc", None),
            "bad-time": ("approved_at_utc", "2026-09-06"),
        }
        for name, (key, value) in cases.items():
            with self.subTest(name=name):
                source = _source()
                source["approval"][key] = value
                with self.assertRaises(OwnerBudgetProfileError):
                    render_raiktor_owner_budget_profile(
                        source, source_sha256="A" * 64
                    )

        draft = _source(approved=False)
        draft["approval"]["approved_by"] = "stale-author"
        with self.assertRaises(OwnerBudgetProfileError):
            render_raiktor_owner_budget_profile(
                draft, source_sha256="A" * 64
            )

    def test_missing_or_invalid_threshold_is_rejected_not_defaulted(
        self,
    ) -> None:
        cases: list[tuple[str, dict[str, object]]] = []
        missing = _source()
        del missing["pairwise_limits"]["minimum_switch_margin_raw"]
        cases.append(("missing", missing))
        boolean_count = _source()
        boolean_count["pairwise_limits"][
            "maximum_surrender_claims_removed"
        ] = True
        cases.append(("boolean-count", boolean_count))
        zero_margin = _source()
        zero_margin["pairwise_limits"]["minimum_switch_margin_raw"] = 0
        cases.append(("zero-margin", zero_margin))
        negative_white_limit = _source()
        negative_white_limit["white_peace_limits"][
            "maximum_gold_transfer_raw"
        ] = -1
        cases.append(("negative-white-limit", negative_white_limit))

        for name, source in cases:
            with self.subTest(name=name):
                with self.assertRaises(OwnerBudgetProfileError):
                    render_raiktor_owner_budget_profile(
                        source, source_sha256="A" * 64
                    )

    def test_invalid_file_and_explicit_missing_path_are_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            with self.assertRaises(OwnerBudgetProfileError):
                provide_raiktor_owner_budget_profile(missing)

            invalid = Path(directory) / "invalid.json"
            invalid.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(OwnerBudgetProfileError):
                provide_raiktor_owner_budget_profile(invalid)

    def test_render_does_not_mutate_source(self) -> None:
        source = _source()
        before = deepcopy(source)

        render_raiktor_owner_budget_profile(
            source, source_sha256="A" * 64
        )

        self.assertEqual(source, before)


if __name__ == "__main__":
    unittest.main()
