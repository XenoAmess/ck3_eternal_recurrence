#!/usr/bin/env python3
"""Non-selecting live fixture for current-event character scopes.

This runner reuses the managed seed/checkpoint/fresh-cold machinery from
``run_current_event_window_context_live_acceptance.py`` through a bounded
context-manager profile.  The disposable generic, nonreligious
``character_event`` saves its root as ``xar_scope_root_control`` in
``immediate`` and exposes one enabled option with no gameplay effect.  No
stage selects the option.

Qualification requires the exact played CharacterID in the root and in the
single named scope, truthful root/saved readiness, false full-effect and
semantic-decision readiness, adjacent same-revision cold frames, stable
character identities across checkpoint/fresh-cold reload, immutable source
save bytes and the base runner's managed cleanup gates.  A script-identifier
number is a full signed-int32, process-local datum and is validated
independently in each process; it is not compared as a cross-process identity.

The implementation source commit and bridge DLL hash below pin the reviewed
static implementation.  They make an older bridge or a dirty source tree
ineligible; live readiness still requires this runner's artifact to qualify.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Iterator


RESEARCH_ROOT = Path(__file__).resolve().parent
if str(RESEARCH_ROOT) not in sys.path:
    sys.path.insert(0, str(RESEARCH_ROOT))

import run_current_event_window_context_live_acceptance as BASE  # noqa: E402


FROZEN_SCOPE_SOURCE_COMMIT = "a860702cb76bb3b5c9972bc8d22bc2a61dffbd65"
FROZEN_SCOPE_BRIDGE_DLL_SHA256 = (
    "A2B78F371A16A87B2A911E1E832C07A5701E2E7B3C42FA046006A41C233702DF"
)

EXPECTED_EVENT_KEY = "xar_event_scopes_live_fixture.1"
FIXTURE_NAMESPACE = "xar_event_scopes_live_fixture"
EXPECTED_SAVED_SCOPE_NAME = "xar_scope_root_control"
FIXTURE_MOD_TARGET_NAME = "xar-event-scopes-live-fixture"
FIXTURE_MOD_OUTER_NAME = "xar_event_scopes_live_fixture.mod"
FIXTURE_MOD_OUTER_REF = f"mod/{FIXTURE_MOD_OUTER_NAME}"
FIXTURE_EVENT_RELATIVE = Path("events/zz_xar_event_scopes_live_fixture.txt")
FIXTURE_EVENT_SOURCE = """namespace = xar_event_scopes_live_fixture

xar_event_scopes_live_fixture.1 = {
	type = character_event
	title = XAR_EVENT_SCOPES_LIVE_FIXTURE_TITLE
	desc = XAR_EVENT_SCOPES_LIVE_FIXTURE_DESC
	theme = default
	left_portrait = root

	immediate = {
		save_scope_as = xar_scope_root_control
	}

	option = {
		name = XAR_EVENT_SCOPES_LIVE_FIXTURE_CONTINUE
	}
}
"""

# Literal review pins.  Do not calculate expectations at acceptance time.
FIXTURE_EVENT_SHA256 = (
    "58A33AD64209BB814BB5D126E43428D28296D4805BDFB0E7FCE868ADD1CF417C"
)
FIXTURE_CONTENT_MANIFEST_SHA256 = (
    "B21597CE319DA733F5B5E60DE067E5F4215C0407C3857D0651769875EEC7CC9B"
)

EXPECTED_OPTION_NAMES = ("XAR continue without effects",)
_LOCALIZATION_ROWS = (
    ("XAR_EVENT_SCOPES_LIVE_FIXTURE_TITLE", "XAR event-scope fixture"),
    (
        "XAR_EVENT_SCOPES_LIVE_FIXTURE_DESC",
        "A deterministic character root and named-scope observation fixture.",
    ),
    (
        "XAR_EVENT_SCOPES_LIVE_FIXTURE_CONTINUE",
        EXPECTED_OPTION_NAMES[0],
    ),
)

GENERATE_GUARD = "xar_event_scopes_live_fixture_generated"
GENERATE_MARKER = (
    "XAR_FIXTURE:EVENT_SCOPES_GENERATE|"
    f"event={EXPECTED_EVENT_KEY}|saved={EXPECTED_SAVED_SCOPE_NAME}"
)
_ROOT_MARKER_NAME = ".xar-current-event-scopes-live.json"
_ROOT_KIND = "xar_current_event_scopes_live_acceptance"
_ROOT_PREFIX = "xes-"
_SEED_STAGE_NAME = "seed-trigger-query-save-scopes"
_COLD_STAGE_NAME = "fresh-scope-cold-double-query"
_SIGNED_INT32_MIN = -(2**31)
_SIGNED_INT32_MAX = 2**31 - 1

_BASE_CONTEXT_PROOF = BASE._context_proof
_BASE_CROSS_STAGE_PROOF = BASE._cross_stage_proof


def _localization_source(header: str) -> str:
    rows = "".join(f' {key}:0 "{value}"\n' for key, value in _LOCALIZATION_ROWS)
    return f"{header}:\n{rows}"


def _fixture_content() -> dict[Path, bytes]:
    files = {FIXTURE_EVENT_RELATIVE: BASE._bom(FIXTURE_EVENT_SOURCE)}
    for directory, header in BASE._LOCALES.items():
        relative = Path(
            f"localization/{directory}/"
            f"xar_event_scopes_live_fixture_l_{directory}.yml"
        )
        files[relative] = BASE._bom(_localization_source(header))
    return files


def _fixture_descriptor(*, outer: bool, target: Path) -> str:
    path = f'path="{target.resolve().as_posix()}"\n' if outer else ""
    return (
        '\ufeffversion="0.1.0"\n'
        'tags={\n\t"Utilities"\n}\n'
        'name="XAR Current Event Scopes Live Fixture"\n'
        'supported_version="1.19.0.6"\n'
        f"{path}"
    )


def _fixture_definition_contract() -> dict[str, object]:
    files = _fixture_content()
    event_raw = files[FIXTURE_EVENT_RELATIVE]
    event_text = FIXTURE_EVENT_SOURCE
    folded = "\n".join(
        raw.decode("utf-8-sig") for raw in files.values()
    ).casefold()
    manifest = BASE._content_manifest(files)
    immediate_block = (
        "\timmediate = {\n"
        f"\t\tsave_scope_as = {EXPECTED_SAVED_SCOPE_NAME}\n"
        "\t}"
    )
    option_block = (
        "\toption = {\n"
        "\t\tname = XAR_EVENT_SCOPES_LIVE_FIXTURE_CONTINUE\n"
        "\t}"
    )
    forbidden_event_effects = (
        "\tafter =",
        "trigger_event =",
        "add_",
        "remove_",
        "set_",
        "change_",
        "death =",
    )
    checks = {
        "utf8_bom_every_file": all(
            raw.startswith(b"\xef\xbb\xbf") for raw in files.values()
        ),
        "exact_event_sha256": hashlib.sha256(event_raw).hexdigest().upper()
        == FIXTURE_EVENT_SHA256,
        "exact_content_manifest_sha256": manifest["sha256"]
        == FIXTURE_CONTENT_MANIFEST_SHA256,
        "canonical_character_event": (
            event_text.startswith(f"namespace = {FIXTURE_NAMESPACE}\n")
            and f"{EXPECTED_EVENT_KEY} = {{" in event_text
            and "\ttype = character_event\n" in event_text
        ),
        "single_exact_root_save": (
            immediate_block in event_text
            and event_text.count("\timmediate = {\n") == 1
            and event_text.count("save_scope_as =") == 1
            and event_text.count(EXPECTED_SAVED_SCOPE_NAME) == 1
        ),
        "single_effectless_option": (
            option_block in event_text
            and event_text.count("\toption = {\n") == 1
        ),
        "no_other_event_gameplay_effects": all(
            token not in event_text for token in forbidden_event_effects
        ),
        "all_locales_have_exact_keys": all(
            raw.decode("utf-8-sig").count(":0 ") == len(_LOCALIZATION_ROWS)
            for path, raw in files.items()
            if path != FIXTURE_EVENT_RELATIVE
        ),
        "no_religion_semantics": all(
            token not in folded for token in BASE._RELIGION_TOKENS
        ),
    }
    return {
        "classification": "generic-nonreligious-character-event-scope-fixture",
        "canonical_key": EXPECTED_EVENT_KEY,
        "saved_scope_name": EXPECTED_SAVED_SCOPE_NAME,
        "event_definition_relative_path": FIXTURE_EVENT_RELATIVE.as_posix(),
        "event_definition_size": len(event_raw),
        "event_definition_sha256": hashlib.sha256(event_raw).hexdigest().upper(),
        "expected_event_definition_sha256": FIXTURE_EVENT_SHA256,
        "content_manifest": manifest,
        "expected_content_manifest_sha256": FIXTURE_CONTENT_MANIFEST_SHA256,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _expected_option_shape(options: object) -> bool:
    if not isinstance(options, list) or len(options) != 1:
        return False
    row = options[0]
    if not isinstance(row, dict) or set(row) != {
        "rendered_index",
        "native_option_index",
        "shown",
        "enabled",
        "fallback",
        "cancel",
        "resolved_name",
        "unavailable_reason",
        "effect_indicators",
        "effect_preview",
        "resource_deltas",
        "relationship_deltas",
    }:
        return False
    return bool(
        row.get("rendered_index") == 0
        and row.get("native_option_index") == 0
        and row.get("shown") is True
        and row.get("enabled") is True
        and row.get("fallback") is False
        and row.get("cancel") is False
        and row.get("resolved_name") == EXPECTED_OPTION_NAMES[0]
        and row.get("unavailable_reason") == ""
        and row.get("effect_indicators")
        == {
            "status": "available",
            "coverage": BASE.EXPECTED_EFFECT_INDICATOR_COVERAGE,
            "complete_effect_set": False,
            "rows": [],
        }
        and row.get("effect_preview")
        == {
            "status": "unavailable",
            "reason": "indicator_subset_has_no_completeness_signal",
        }
        and row.get("resource_deltas") == {"status": "unavailable"}
        and row.get("relationship_deltas") == {"status": "unavailable"}
    )


def _character_scope(value: object, character_id: int) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "status",
        "raw_type_index",
        "type_key",
        "subtype",
        "typed_identity",
    }:
        return False
    identity = value.get("typed_identity")
    return bool(
        value.get("status") == "available"
        and value.get("raw_type_index") == 4
        and value.get("type_key") == "character"
        and value.get("subtype") == 0
        and isinstance(identity, dict)
        and set(identity) == {"status", "kind", "character_id"}
        and identity.get("status") == "available"
        and identity.get("kind") == "character"
        and identity.get("character_id") == character_id
    )


def _saved_scopes(value: object, character_id: int) -> bool:
    if not isinstance(value, list) or len(value) != 1:
        return False
    row = value[0]
    if not isinstance(row, dict) or set(row) != {
        "name",
        "name_identifier",
        "scope",
    }:
        return False
    name_identifier = row.get("name_identifier")
    return bool(
        row.get("name") == EXPECTED_SAVED_SCOPE_NAME
        and isinstance(name_identifier, int)
        and not isinstance(name_identifier, bool)
        and _SIGNED_INT32_MIN <= name_identifier <= _SIGNED_INT32_MAX
        and _character_scope(row.get("scope"), character_id)
    )


def _readiness_exact(value: object) -> bool:
    return value == {
        "event_definition_identity_ready": True,
        "root_scope_ready": True,
        "saved_scopes_ready": True,
        "option_presentation_ready": True,
        "effect_indicators_ready": True,
        "effect_preview_ready": False,
        "semantic_decision_ready": False,
    }


def _stable_scope_projection(frame: object) -> object:
    value = BASE._mapping(frame)
    root = value.get("root_scope")
    saved = value.get("saved_scopes")
    if not (
        _character_scope(root, BASE.PLAYER_CHARACTER_ID)
        and _saved_scopes(saved, BASE.PLAYER_CHARACTER_ID)
    ):
        return None
    assert isinstance(saved, list)
    row = saved[0]
    assert isinstance(row, dict)
    return {
        "root_scope": copy.deepcopy(root),
        "saved_scopes": [
            {
                "name": row["name"],
                "scope": copy.deepcopy(row["scope"]),
            }
        ],
    }


def _context_proof(
    result: object,
    *,
    event_id: int,
    snapshot_id: str,
    public_revision: int,
    native_revision: int,
    date_raw: int,
) -> dict[str, object]:
    proof = copy.deepcopy(
        _BASE_CONTEXT_PROOF(
            result,
            event_id=event_id,
            snapshot_id=snapshot_id,
            public_revision=public_revision,
            native_revision=native_revision,
            date_raw=date_raw,
        )
    )
    envelope = BASE._mapping(result)
    frame = BASE._mapping(envelope.get("current_event_window_context"))
    readiness = frame.get("readiness")
    checks = BASE._mapping(proof.get("checks"))
    checks.pop("root_and_saved_scopes_unavailable", None)
    checks["root_scope_exact_played_character"] = _character_scope(
        frame.get("root_scope"), BASE.PLAYER_CHARACTER_ID
    )
    checks["single_named_scope_exact_played_character"] = _saved_scopes(
        frame.get("saved_scopes"), BASE.PLAYER_CHARACTER_ID
    )
    checks["readiness_truthful"] = bool(
        _readiness_exact(readiness)
        and envelope.get("current_event_window_context_ready") is True
        and envelope.get("current_event_effect_indicators_ready") is True
    )
    checks["effect_and_semantic_readiness_false"] = bool(
        isinstance(readiness, dict)
        and readiness.get("effect_preview_ready") is False
        and readiness.get("semantic_decision_ready") is False
    )
    proof["root_scope"] = copy.deepcopy(frame.get("root_scope"))
    proof["saved_scopes"] = copy.deepcopy(frame.get("saved_scopes"))
    proof["checks"] = checks
    proof["ok"] = all(checks.values())
    return proof


def _cross_stage_proof(
    seed_stage: object,
    cold_stage: object,
    transfer: object,
) -> dict[str, object]:
    proof = copy.deepcopy(
        _BASE_CROSS_STAGE_PROOF(seed_stage, cold_stage, transfer)
    )
    seed = BASE._mapping(seed_stage)
    cold = BASE._mapping(cold_stage)
    sequence = BASE._mapping(cold.get("sequence"))
    seed_frame = BASE._mapping(
        BASE._mapping(seed.get("seed_query")).get(
            "current_event_window_context"
        )
    )
    cold_frame = BASE._mapping(
        BASE._mapping(sequence.get("first_query")).get(
            "current_event_window_context"
        )
    )
    seed_projection = _stable_scope_projection(seed_frame)
    cold_projection = _stable_scope_projection(cold_frame)
    checks = BASE._mapping(proof.get("checks"))
    checks.pop("unclosed_semantics_stay_false", None)
    checks["root_scope_exact_in_both_stages"] = bool(
        _character_scope(
            seed_frame.get("root_scope"), BASE.PLAYER_CHARACTER_ID
        )
        and _character_scope(
            cold_frame.get("root_scope"), BASE.PLAYER_CHARACTER_ID
        )
    )
    checks["saved_scope_exact_in_both_stages"] = bool(
        _saved_scopes(
            seed_frame.get("saved_scopes"), BASE.PLAYER_CHARACTER_ID
        )
        and _saved_scopes(
            cold_frame.get("saved_scopes"), BASE.PLAYER_CHARACTER_ID
        )
    )
    checks["same_stable_scope_identities"] = bool(
        seed_projection is not None and seed_projection == cold_projection
    )
    checks["scope_readiness_stays_true"] = bool(
        _readiness_exact(seed_frame.get("readiness"))
        and _readiness_exact(cold_frame.get("readiness"))
    )
    checks["effect_and_semantic_readiness_stay_false"] = bool(
        isinstance(seed_frame.get("readiness"), dict)
        and isinstance(cold_frame.get("readiness"), dict)
        and seed_frame["readiness"].get("effect_preview_ready") is False
        and seed_frame["readiness"].get("semantic_decision_ready") is False
        and cold_frame["readiness"].get("effect_preview_ready") is False
        and cold_frame["readiness"].get("semantic_decision_ready") is False
    )
    proof["root_scope"] = copy.deepcopy(cold_frame.get("root_scope"))
    proof["saved_scopes"] = copy.deepcopy(cold_frame.get("saved_scopes"))
    proof["checks"] = checks
    proof["ok"] = all(checks.values())
    return proof


_PROFILE_PATCHES = {
    "FROZEN_SOURCE_COMMIT": FROZEN_SCOPE_SOURCE_COMMIT,
    "FROZEN_BRIDGE_DLL_SHA256": FROZEN_SCOPE_BRIDGE_DLL_SHA256,
    "EXPECTED_EVENT_KEY": EXPECTED_EVENT_KEY,
    "FIXTURE_NAMESPACE": FIXTURE_NAMESPACE,
    "FIXTURE_MOD_TARGET_NAME": FIXTURE_MOD_TARGET_NAME,
    "FIXTURE_MOD_OUTER_NAME": FIXTURE_MOD_OUTER_NAME,
    "FIXTURE_MOD_OUTER_REF": FIXTURE_MOD_OUTER_REF,
    "FIXTURE_EVENT_RELATIVE": FIXTURE_EVENT_RELATIVE,
    "FIXTURE_EVENT_SOURCE": FIXTURE_EVENT_SOURCE,
    "FIXTURE_EVENT_SHA256": FIXTURE_EVENT_SHA256,
    "FIXTURE_CONTENT_MANIFEST_SHA256": FIXTURE_CONTENT_MANIFEST_SHA256,
    "EXPECTED_OPTION_NAMES": EXPECTED_OPTION_NAMES,
    "GENERATE_GUARD": GENERATE_GUARD,
    "GENERATE_MARKER": GENERATE_MARKER,
    "_ROOT_MARKER_NAME": _ROOT_MARKER_NAME,
    "_ROOT_KIND": _ROOT_KIND,
    "_ROOT_PREFIX": _ROOT_PREFIX,
    "_SEED_STAGE_NAME": _SEED_STAGE_NAME,
    "_COLD_STAGE_NAME": _COLD_STAGE_NAME,
    "_fixture_content": _fixture_content,
    "_fixture_descriptor": _fixture_descriptor,
    "_fixture_definition_contract": _fixture_definition_contract,
    "_expected_option_shape": _expected_option_shape,
    "_context_proof": _context_proof,
    "_cross_stage_proof": _cross_stage_proof,
}


@contextmanager
def _installed_fixture_profile() -> Iterator[None]:
    """Install this fixture only around one base-runner operation."""

    original = {name: getattr(BASE, name) for name in _PROFILE_PATCHES}
    try:
        for name, value in _PROFILE_PATCHES.items():
            setattr(BASE, name, value)
        yield
    finally:
        for name, value in original.items():
            setattr(BASE, name, value)


def _parser() -> argparse.ArgumentParser:
    parser = BASE._parser()
    parser.description = __doc__
    return parser


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    with _installed_fixture_profile():
        payload, exit_code = BASE._run(args)
    payload = copy.deepcopy(payload)
    payload["kind"] = "ck3_current_event_scopes_live_acceptance"

    scenario = payload.get("fixed_scenario")
    if isinstance(scenario, dict):
        for key in (
            "expected_hidden_native_index",
            "expected_unmaterialized_fallback_native_index",
        ):
            scenario.pop(key, None)
        scenario.update(
            {
                "authored_option_count": 1,
                "expected_rendered_native_indices": [0],
                "saved_scope_name": EXPECTED_SAVED_SCOPE_NAME,
                "expected_scope_character_id": BASE.PLAYER_CHARACTER_ID,
            }
        )

    policy = payload.get("policy")
    if isinstance(policy, dict):
        policy.update(
            {
                "root_scope_ready_expected": True,
                "saved_scopes_ready_expected": True,
                "named_scope_count_expected": 1,
                "named_scope_identifier_is_cross_process_identity": False,
                "event_option_selection_allowed": False,
                "event_option_selection_invoked": False,
                "full_effect_preview_ready_expected": False,
                "semantic_decision_ready_expected": False,
            }
        )

    sequence = BASE._mapping(
        BASE._mapping(payload.get("cold_stage")).get("sequence")
    )
    context_checks = BASE._mapping(
        BASE._mapping(sequence.get("first_context_proof")).get("checks")
    )
    cross_checks = BASE._mapping(
        BASE._mapping(payload.get("cross_stage_proof")).get("checks")
    )
    gates = payload.get("readiness_gates")
    if isinstance(gates, dict):
        gates.pop("effect_scopes_and_semantic_readiness_remain_unclosed", None)
        gates["root_and_named_character_scopes_exact"] = all(
            context_checks.get(key) is True
            for key in (
                "root_scope_exact_played_character",
                "single_named_scope_exact_played_character",
                "readiness_truthful",
                "effect_and_semantic_readiness_false",
            )
        ) and all(
            cross_checks.get(key) is True
            for key in (
                "root_scope_exact_in_both_stages",
                "saved_scope_exact_in_both_stages",
                "same_stable_scope_identities",
                "scope_readiness_stays_true",
                "effect_and_semantic_readiness_stay_false",
            )
        )

    frozen = payload.get("frozen_source_contract")
    if isinstance(frozen, dict):
        frozen.update(
            {
                "commit": FROZEN_SCOPE_SOURCE_COMMIT,
                "bridge_dll_sha256": FROZEN_SCOPE_BRIDGE_DLL_SHA256,
            }
        )

    payload["ok"] = bool(
        payload.get("error") is None
        and isinstance(gates, dict)
        and all(value is True for value in gates.values())
    )
    payload["evidence_classification"] = (
        "fixture-scoped-live-confirmed"
        if payload["ok"]
        else "not-qualified"
    )
    return payload, 0 if payload["ok"] else max(1, exit_code)


def main() -> int:
    args = _parser().parse_args()
    payload, exit_code = _run(args)
    cross = BASE._mapping(payload.get("cross_stage_proof"))
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "event_instance_id": cross.get("current_event_instance_id"),
                "event_definition_key": cross.get("event_definition_key"),
                "saved_scope_name": EXPECTED_SAVED_SCOPE_NAME,
                "output": str(output),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
