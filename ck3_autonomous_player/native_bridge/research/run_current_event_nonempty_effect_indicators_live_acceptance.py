#!/usr/bin/env python3
"""Non-selecting live fixture for nonempty current-event effect indicators.

This runner deliberately reuses the managed seed/checkpoint/fresh-cold
machinery from ``run_current_event_window_context_live_acceptance.py``.  It
changes only the disposable event-definition/localization projection and the
expected materialized option shape:

* authored option 0 is an enabled empty-row control;
* authored option 1 uses ``add_trait_force_tooltip = brave``;
* authored option 2 is hidden;
* authored option 3 contains stress gain plus played-character death and is
  also the cancel option;
* authored option 4 is an unmaterialized fallback control.

Neither stage selects an option.  The seed process queries the paused event
and saves it; a distinct fresh-cold process performs exactly two adjacent
same-revision queries.  GREEN requires byte-exact checkpoint transfer and the
empty control plus the exact ``trait/add brave``, ``stress/increase`` and
played-character death rows to rematerialize as structurally equal frames
across the two processes.  Full effect preview and semantic-decision readiness
remain false.

The fixture is generic and nonreligious.  It is definition-only evidence, not
stock-event or production-only-playset evidence.
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


EXPECTED_EVENT_KEY = "xar_event_indicator_live_fixture.1"
FIXTURE_NAMESPACE = "xar_event_indicator_live_fixture"
FIXTURE_MOD_TARGET_NAME = "xar-event-indicator-live-fixture"
FIXTURE_MOD_OUTER_NAME = "xar_event_indicator_live_fixture.mod"
FIXTURE_MOD_OUTER_REF = f"mod/{FIXTURE_MOD_OUTER_NAME}"
FIXTURE_EVENT_RELATIVE = Path(
    "events/zz_xar_event_indicator_live_fixture.txt"
)
FIXTURE_EVENT_SOURCE = """namespace = xar_event_indicator_live_fixture

xar_event_indicator_live_fixture.1 = {
	type = character_event
	title = XAR_EVENT_INDICATOR_LIVE_FIXTURE_TITLE
	desc = XAR_EVENT_INDICATOR_LIVE_FIXTURE_DESC
	theme = default
	left_portrait = root

	option = {
		name = XAR_EVENT_INDICATOR_LIVE_FIXTURE_EMPTY
	}
	option = {
		name = XAR_EVENT_INDICATOR_LIVE_FIXTURE_TRAIT
		add_trait_force_tooltip = brave
	}
	option = {
		name = XAR_EVENT_INDICATOR_LIVE_FIXTURE_HIDDEN
		trigger = { always = no }
	}
	option = {
		name = XAR_EVENT_INDICATOR_LIVE_FIXTURE_STRESS_DEATH
		add_stress = minor_stress_gain
		death = { death_reason = death_accident }
		is_cancel_option = yes
	}
	option = {
		name = XAR_EVENT_INDICATOR_LIVE_FIXTURE_FALLBACK
		trigger = { always = no }
		fallback = yes
	}
}
"""

# Filled with literal, independently checked values rather than calculated
# expectations so a fixture edit fails before CK3 can launch.
FIXTURE_EVENT_SHA256 = (
    "4E532E372932276A26B549B0B3A8A67C3943EC5762B7773940E03BA3E04329C3"
)
FIXTURE_CONTENT_MANIFEST_SHA256 = (
    "8110439FBCBCD3DB8FE0AED0B2B040339940E344485B92BC8A626AF0B7C317DE"
)

EXPECTED_OPTION_NAMES = (
    "XAR empty indicator control",
    "XAR trait indicator",
    "XAR stress and death indicators",
)
_LOCALIZATION_ROWS = (
    ("XAR_EVENT_INDICATOR_LIVE_FIXTURE_TITLE", "XAR indicator fixture"),
    (
        "XAR_EVENT_INDICATOR_LIVE_FIXTURE_DESC",
        "A deterministic nonempty effect-indicator observation fixture.",
    ),
    (
        "XAR_EVENT_INDICATOR_LIVE_FIXTURE_EMPTY",
        EXPECTED_OPTION_NAMES[0],
    ),
    (
        "XAR_EVENT_INDICATOR_LIVE_FIXTURE_TRAIT",
        EXPECTED_OPTION_NAMES[1],
    ),
    (
        "XAR_EVENT_INDICATOR_LIVE_FIXTURE_HIDDEN",
        "XAR hidden indicator fixture option",
    ),
    (
        "XAR_EVENT_INDICATOR_LIVE_FIXTURE_STRESS_DEATH",
        EXPECTED_OPTION_NAMES[2],
    ),
    (
        "XAR_EVENT_INDICATOR_LIVE_FIXTURE_FALLBACK",
        "XAR fallback indicator fixture option",
    ),
)

GENERATE_GUARD = "xar_event_indicator_live_fixture_generated"
GENERATE_MARKER = (
    "XAR_FIXTURE:EVENT_INDICATOR_NONEMPTY_GENERATE|"
    f"event={EXPECTED_EVENT_KEY}"
)
_ROOT_MARKER_NAME = ".xar-current-event-nonempty-indicators-live.json"
_ROOT_KIND = "xar_current_event_nonempty_indicators_live_acceptance"
_ROOT_PREFIX = "xei-"
_SEED_STAGE_NAME = "seed-trigger-query-save-indicators"
_COLD_STAGE_NAME = "fresh-indicator-cold-double-query"


def _localization_source(header: str) -> str:
    rows = "".join(f' {key}:0 "{value}"\n' for key, value in _LOCALIZATION_ROWS)
    return f"{header}:\n{rows}"


def _fixture_content() -> dict[Path, bytes]:
    files = {FIXTURE_EVENT_RELATIVE: BASE._bom(FIXTURE_EVENT_SOURCE)}
    for directory, header in BASE._LOCALES.items():
        relative = Path(
            f"localization/{directory}/"
            f"xar_event_indicator_live_fixture_l_{directory}.yml"
        )
        files[relative] = BASE._bom(_localization_source(header))
    return files


def _fixture_descriptor(*, outer: bool, target: Path) -> str:
    path = f'path="{target.resolve().as_posix()}"\n' if outer else ""
    return (
        '\ufeffversion="0.1.0"\n'
        'tags={\n\t"Utilities"\n}\n'
        'name="XAR Current Event Nonempty Indicator Live Fixture"\n'
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
    empty_block = (
        "\toption = {\n"
        "\t\tname = XAR_EVENT_INDICATOR_LIVE_FIXTURE_EMPTY\n"
        "\t}"
    )
    trait_block = (
        "\toption = {\n"
        "\t\tname = XAR_EVENT_INDICATOR_LIVE_FIXTURE_TRAIT\n"
        "\t\tadd_trait_force_tooltip = brave\n"
        "\t}"
    )
    stress_death_block = (
        "\toption = {\n"
        "\t\tname = XAR_EVENT_INDICATOR_LIVE_FIXTURE_STRESS_DEATH\n"
        "\t\tadd_stress = minor_stress_gain\n"
        "\t\tdeath = { death_reason = death_accident }\n"
        "\t\tis_cancel_option = yes\n"
        "\t}"
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
        "five_authored_options": event_text.count("\toption = {\n") == 5,
        "empty_row_control_has_no_effect": empty_block in event_text,
        "forced_trait_indicator_is_brave": (
            trait_block in event_text
            and event_text.count("add_trait_force_tooltip = brave") == 1
        ),
        "stress_and_death_indicator_option": (
            stress_death_block in event_text
            and event_text.count("add_stress = minor_stress_gain") == 1
            and event_text.count(
                "death = { death_reason = death_accident }"
            )
            == 1
        ),
        "hidden_control": (
            "name = XAR_EVENT_INDICATOR_LIVE_FIXTURE_HIDDEN\n"
            "\t\ttrigger = { always = no }" in event_text
        ),
        "one_cancel_option": event_text.count("is_cancel_option = yes") == 1,
        "fallback_control": (
            event_text.count("fallback = yes") == 1
            and "name = XAR_EVENT_INDICATOR_LIVE_FIXTURE_FALLBACK\n"
            "\t\ttrigger = { always = no }\n"
            "\t\tfallback = yes" in event_text
        ),
        "no_event_level_immediate_after_or_chained_event": (
            "\timmediate =" not in event_text
            and "\tafter =" not in event_text
            and "trigger_event =" not in event_text
        ),
        "all_locales_have_exact_keys": all(
            raw.decode("utf-8-sig").count(":0 ")
            == len(_LOCALIZATION_ROWS)
            for path, raw in files.items()
            if path != FIXTURE_EVENT_RELATIVE
        ),
        "no_religion_semantics": all(
            token not in folded for token in BASE._RELIGION_TOKENS
        ),
    }
    return {
        "classification": (
            "generic-nonreligious-nonempty-effect-indicator-fixture"
        ),
        "canonical_key": EXPECTED_EVENT_KEY,
        "event_definition_relative_path": FIXTURE_EVENT_RELATIVE.as_posix(),
        "event_definition_size": len(event_raw),
        "event_definition_sha256": hashlib.sha256(event_raw).hexdigest().upper(),
        "expected_event_definition_sha256": FIXTURE_EVENT_SHA256,
        "content_manifest": manifest,
        "expected_content_manifest_sha256": FIXTURE_CONTENT_MANIFEST_SHA256,
        "expected_indicator_kinds": ["trait", "stress", "death"],
        "empty_row_control_native_index": 0,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _common_effect_surface(row: object) -> bool:
    return bool(
        isinstance(row, dict)
        and row.get("effect_preview")
        == {
            "status": "unavailable",
            "reason": "indicator_subset_has_no_completeness_signal",
        }
        and row.get("resource_deltas") == {"status": "unavailable"}
        and row.get("relationship_deltas") == {"status": "unavailable"}
    )


def _trait_indicator(row: object) -> bool:
    if not isinstance(row, dict):
        return False
    trait = row.get("trait")
    native_id = trait.get("native_id") if isinstance(trait, dict) else None
    return bool(
        row.get("kind") == "trait"
        and row.get("operation") == "add"
        and isinstance(trait, dict)
        and trait.get("status") == "available"
        and trait.get("key") == "brave"
        and isinstance(native_id, int)
        and not isinstance(native_id, bool)
        and 0 <= native_id <= 2**31 - 1
    )


def _stress_indicator(row: object) -> bool:
    return bool(
        isinstance(row, dict)
        and row.get("kind") == "stress"
        and row.get("direction") == "increase"
        and row.get("magnitude") == {"status": "unavailable"}
        and row.get("affected_by_trait") is False
        and isinstance(row.get("critical"), bool)
    )


def _death_indicator(row: object) -> bool:
    return bool(
        isinstance(row, dict)
        and row
        == {
            "kind": "death",
            "subject": "played_character",
            "direction": "not_applicable",
        }
    )


def _indicator_surface(row: object, expected_rows: int) -> list[object] | None:
    if not isinstance(row, dict):
        return None
    indicators = row.get("effect_indicators")
    if not isinstance(indicators, dict):
        return None
    rows = indicators.get("rows")
    if not (
        indicators.get("status") == "available"
        and indicators.get("coverage")
        == BASE.EXPECTED_EFFECT_INDICATOR_COVERAGE
        and indicators.get("complete_effect_set") is False
        and isinstance(rows, list)
        and len(rows) == expected_rows
        and _common_effect_surface(row)
    ):
        return None
    return rows


def _expected_option_shape(options: object) -> bool:
    if not isinstance(options, list) or len(options) != 3:
        return False
    expected_presentation = (
        (0, 0, False, EXPECTED_OPTION_NAMES[0]),
        (1, 1, False, EXPECTED_OPTION_NAMES[1]),
        (2, 3, True, EXPECTED_OPTION_NAMES[2]),
    )
    for row, expected in zip(options, expected_presentation, strict=True):
        if not isinstance(row, dict):
            return False
        rendered, native, cancel, name = expected
        if not (
            row.get("rendered_index") == rendered
            and row.get("native_option_index") == native
            and row.get("shown") is True
            and row.get("enabled") is True
            and row.get("fallback") is False
            and row.get("cancel") is cancel
            and row.get("resolved_name") == name
            and row.get("unavailable_reason") == ""
        ):
            return False
    empty_rows = _indicator_surface(options[0], 0)
    trait_rows = _indicator_surface(options[1], 1)
    stress_death_rows = _indicator_surface(options[2], 2)
    return bool(
        empty_rows == []
        and isinstance(trait_rows, list)
        and _trait_indicator(trait_rows[0])
        and isinstance(stress_death_rows, list)
        and _stress_indicator(stress_death_rows[0])
        and _death_indicator(stress_death_rows[1])
    )


_PROFILE_PATCHES = {
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
}


@contextmanager
def _installed_fixture_profile() -> Iterator[None]:
    """Install the bounded fixture profile only for one base-runner call."""

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
    payload["kind"] = (
        "ck3_current_event_nonempty_effect_indicators_live_acceptance"
    )
    scenario = payload.get("fixed_scenario")
    if isinstance(scenario, dict):
        scenario.update(
            {
                "empty_row_control_native_index": 0,
                "trait_indicator_native_index": 1,
                "stress_death_indicator_native_index": 3,
                "expected_indicator_kinds": ["trait", "stress", "death"],
            }
        )
    policy = payload.get("policy")
    if isinstance(policy, dict):
        policy.update(
            {
                "nonempty_indicator_fixture": True,
                "empty_row_control_required": True,
                "trait_stress_and_death_rows_required": True,
                "indicator_rows_are_complete_effect_preview": False,
                "visual_gui_icon_render_verified": False,
            }
        )
    gates = payload.get("readiness_gates")
    indicator_gate = False
    if isinstance(gates, dict):
        indicator_gate = bool(
            gates.get("rendered_native_presentation_exact") is True
            and BASE._mapping(
                BASE._mapping(payload.get("cross_stage_proof")).get("checks")
            ).get("same_materialized_options")
            is True
        )
        gates["empty_control_trait_stress_death_rows_exact"] = indicator_gate
    payload["ok"] = bool(payload.get("ok") is True and indicator_gate)
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
                "expected_indicator_kinds": ["trait", "stress", "death"],
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
