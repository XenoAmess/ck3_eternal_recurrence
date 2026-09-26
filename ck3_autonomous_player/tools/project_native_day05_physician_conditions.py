#!/usr/bin/env python3
"""Read-only source/save projection for attempt-066 treatment weights.

The picker captured [40, 50], but did not capture scope:physician. This tool
checks a possible static explanation against exact source bytes and the
immutable pre-event save; it deliberately does not assert live physician
identity or live effective skill at the selector.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


SOURCE_SAVE_SHA = "695F1FDE17457004EB8D060C1F21146C3605374806DABACF6FB5FAB386882885"
MELTED_SAVE_SHA = "3EA734AECA5992CA8DDAD87564C1B7090A7AC677DF23C1069764A5C93F42C4CA"
RAKALY_SHA = "E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D"
TRACE_SHA = "069584BF9134BA8949D5AB47ED36C925ADFD774DF10C5DA0055B1703BFB27AFF"
WEIGHT_PROJECTION_SHA = "CC792DF04804FD160C83AFCDFF2F2284C02791B0DE79492E49AAFAE99E73593E"
SCRIPT_SHAS = {
    "health_effects": ("common/scripted_effects/20_health_effects.txt", "6D7DEF1245D899DE4DEBC42136815BC7F4D14F6A467A8320355507AD03528F12"),
    "health_triggers": ("common/scripted_triggers/20_health_triggers.txt", "7A40670167D8073B34F73AAA53387FC05DB4543D5BF1C10C5296967A4DE8F8F8"),
    "basic_values": ("common/script_values/00_basic_values.txt", "9268A54F0E425D409D9D0F20D884E0A3D0A89DF85A0B6644D56133C0C4CB0096"),
    "traits": ("common/traits/00_traits.txt", "079F0AB5C4224C505AB9F25BCA80D8DF296E5899BFAB26049CE5FE794DC0B042"),
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def single(pattern: str, text: str, *, flags: int = 0) -> re.Match[str]:
    matches = list(re.finditer(pattern, text, flags))
    if len(matches) != 1:
        raise ValueError(f"expected one match, found {len(matches)}: {pattern}")
    return matches[0]


def character_record(melted: str, character_id: int) -> dict:
    match = single(rf"(?ms)^\t{character_id}=\{{\n(.*?)^\t\}}", melted)
    body = match.group(1)
    skills = [int(value) for value in single(r"(?s)\bskill=\{\s*([0-9\s]+?)\s*\}", body).group(1).split()]
    traits = [int(value) for value in single(r"(?s)\btraits=\{\s*([0-9\s]+?)\s*\}", body).group(1).split()]
    if len(skills) != 6:
        raise ValueError("save skill vector must have six slots")
    employer = int(single(r"(?m)^\t\t\temployer=(\d+)$", body).group(1))
    position_ids = [int(value) for value in single(r"(?s)\bcourt_positions=\{\s*([0-9\s]+?)\s*\}", body).group(1).split()]
    return {"character_id": character_id, "skills": skills, "trait_ids": traits,
            "court_employer_id": employer, "court_position_ids": position_ids}


def trait_learning_bonus(traits_source: str, key: str) -> int:
    body = single(rf"(?ms)^{re.escape(key)}\s*=\s*\{{\n(.*?)^\}}", traits_source).group(1)
    rows = re.findall(r"(?m)^\tlearning\s*=\s*(-?\d+)\s*$", body)
    if len(rows) > 1:
        raise ValueError(f"multiple top-level learning modifiers for {key}")
    return int(rows[0]) if rows else 0


def project(attempt: Path, source_save: Path, rakaly_exe: Path, game_root: Path,
            weight_projection: Path) -> dict:
    melted_path = attempt / "d05-source-melted.ck3"
    trace_path = attempt / "ck3-output/interactive-requests-responses/007-finish.json"
    assert digest(source_save) == SOURCE_SAVE_SHA
    assert digest(melted_path) == MELTED_SAVE_SHA
    assert digest(rakaly_exe) == RAKALY_SHA
    assert digest(trace_path) == TRACE_SHA
    assert digest(weight_projection) == WEIGHT_PROJECTION_SHA
    scripts: dict[str, str] = {}
    for name, (relative, expected_sha) in SCRIPT_SHAS.items():
        path = game_root / "game" / relative
        assert digest(path) == expected_sha
        scripts[name] = path.read_text(encoding="utf-8-sig")

    trace = json.loads(trace_path.read_text(encoding="utf-8"))["body"]["managed_trace"]["trace"]
    before = trace["records"][0]["battle_events"]
    after = trace["records"][-1]["battle_events"]
    assert after[:len(before)] == before
    assert [(e["stable_key"], e["left_character_id"], e["right_character_id"])
            for e in after[len(before):]] == [("knight_maimed_by_enemy", 34333, 47032)]
    runtime = json.loads(weight_projection.read_text(encoding="utf-8"))
    treatment = next(row for row in runtime["choices"] if row["call_index"] == 49)
    assert treatment["weights_native_int32"] == [40, 50]
    assert treatment["selected_source_order_index"] == 1

    melted = melted_path.read_text(encoding="utf-8-sig")
    lookup = single(r"(?ms)^traits_lookup=\{\n(.*?)^\}", melted).group(1).split()
    assert lookup.index("lifestyle_physician") == 44
    position = single(
        r'(?m)^\t\t(\d+)=\{\n\t\t\tcourt_position="court_physician_court_position"\n'
        r'\t\t\temployee=(\d+)\n\t\t\temployer=34333$', melted
    )
    position_id, doctor_id = int(position.group(1)), int(position.group(2))
    assert (position_id, doctor_id) == (834, 57392)
    doctor = character_record(melted, doctor_id)
    assert doctor["court_employer_id"] == 34333
    assert doctor["court_position_ids"] == [position_id]
    assert doctor["skills"] == [1, 3, 2, 7, 2, 1]
    trait_keys = [lookup[index] for index in doctor["trait_ids"]]
    assert trait_keys == ["just", "gluttonous", "ambitious", "education_learning_3"]
    assert "lifestyle_physician" not in trait_keys
    bonuses = {key: trait_learning_bonus(scripts["traits"], key) for key in trait_keys}
    assert bonuses == {"just": 1, "gluttonous": 0, "ambitious": 1,
                       "education_learning_3": 6}
    baseline_learning = doctor["skills"][4] + sum(bonuses.values())
    assert baseline_learning == 10
    thresholds = {
        key: int(single(rf"(?m)^{key}\s*=\s*(\d+)\s*$", scripts["basic_values"]).group(1))
        for key in ("mediocre_skill_rating", "medium_skill_rating", "decent_skill_rating", "high_skill_rating")
    }
    assert thresholds == {"mediocre_skill_rating": 8, "medium_skill_rating": 10,
                          "decent_skill_rating": 12, "high_skill_rating": 15}
    effects = scripts["health_effects"]
    assert re.search(r"court_owner\s*=\s*\{\s*random_court_position_holder\s*=", effects)
    assert "type = court_physician_court_position" in effects
    assert "save_scope_as = $SCOPE_NAME$" in effects
    assert "physician_level_up_chance_effect = { CHANCE = 10 }" in effects
    assert re.search(r"learning >= medium_skill_rating\s+learning < decent_skill_rating", effects)
    assert "factor = 4" in effects
    assert "50 = { #Failure" in effects
    assert "court_physician_available_when_traveling_trigger = yes" in scripts["health_triggers"]
    projected_success = 10 * 4
    assert projected_success == treatment["weights_native_int32"][0]

    return {
        "schema": "ck3.native_day05_physician_condition_projection.v1",
        "evidence_sha256": {
            "source_save": SOURCE_SAVE_SHA,
            "melted_save": MELTED_SAVE_SHA,
            "rakaly_exe": RAKALY_SHA,
            "raw_trace": TRACE_SHA,
            "runtime_weight_projection": WEIGHT_PROJECTION_SHA,
            **{key: sha for key, (_, sha) in SCRIPT_SHAS.items()},
        },
        "maimed_patient_character_id": 34333,
        "candidate_court_owner_character_id": 34333,
        "pre_event_court_physician_position_id": position_id,
        "pre_event_court_physician_character_id": doctor_id,
        "pre_event_physician_name": "Guy",
        "pre_event_physician_base_skill_vector": doctor["skills"],
        "pre_event_physician_trait_keys": trait_keys,
        "pre_event_physician_learning_components": {
            "base_learning": doctor["skills"][4], "trait_bonuses": bonuses,
            "base_plus_frozen_trait_modifiers": baseline_learning,
        },
        "source_skill_thresholds": thresholds,
        "source_success_base_weight": 10,
        "source_matching_learning_factor": 4,
        "static_projected_weights": [projected_success, 50],
        "runtime_picker_weights_direct": treatment["weights_native_int32"],
        "runtime_picker_selected_index_direct": treatment["selected_source_order_index"],
        "physician_id_at_picker_directly_observed": False,
        "physician_effective_learning_at_picker_directly_observed": False,
        "pre_list_physician_rank_up_outcome_observed": False,
        "static_projection_matches_runtime_weights": True,
        "full_treatment_feedback_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", required=True, type=Path)
    parser.add_argument("--source-save", required=True, type=Path)
    parser.add_argument("--rakaly-exe", required=True, type=Path)
    parser.add_argument("--game-root", required=True, type=Path)
    parser.add_argument("--weight-projection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists(), f"refusing to overwrite {args.output}"
    result = project(args.attempt_root, args.source_save, args.rakaly_exe,
                     args.game_root, args.weight_projection)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
