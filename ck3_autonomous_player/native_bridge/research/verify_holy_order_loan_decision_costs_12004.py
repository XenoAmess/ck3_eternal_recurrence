"""Check the bounded source contract; this does not compile or execute C++."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[3]
LEAF = Path("ck3_autonomous_player/native_bridge/research")
CPP = LEAF / "holy_order_loan_decision_costs_12004.cpp"
HPP = LEAF / "holy_order_loan_decision_costs_12004.hpp"
PINS = {
    "ck3_autonomous_player/native_bridge/src/ck3_12004_religion_context_addons.cpp":
        "e0ba99a34214b07efb832136af60f75cd80c3f9a9f24a2856a5735ca99bb6dc4",
    "ck3_autonomous_player/native_bridge/src/ck3_12004_holy_site_decision_cooldown.cpp":
        "e502cc469de98d25c29c1f5c25314192d1af485a0f24299b5dcf5af14c818573",
    "ck3_autonomous_player/native_bridge/src/ck3_12003_mystical_communion_decision_terms.cpp":
        "2195e69beff24ef3645a9d6d39e311b1f631eeeced5bf47178724b24943f4870",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "tools"))
    from ck3_live_run_id import current_machine_id

    files: dict[str, dict[str, object]] = {}
    texts: dict[str, str] = {}
    for relative in (*PINS, CPP.as_posix(), HPP.as_posix()):
        data = (ROOT / relative).read_bytes()
        if len(data) > 256 * 1024:
            raise ValueError(f"source exceeds this validator's bounded input: {relative}")
        files[relative] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        texts[relative] = data.decode("utf-8-sig")
    cpp, hpp = texts[CPP.as_posix()], texts[HPP.as_posix()]
    # Remove comments so explanatory promises cannot satisfy executable checks.
    code = re.sub(r"//[^\n]*|/\*.*?\*/", "", cpp, flags=re.S)
    header = re.sub(r"//[^\n]*|/\*.*?\*/", "", hpp, flags=re.S)
    checks = {
        "reused_source_pins_match": all(files[k]["sha256"] == v for k, v in PINS.items()),
        "exact_12004_admission": "sha != ck3_12004::kExecutableSha256" in code,
        "factory_reuses_existing_12004_decision_bindings":
            "BindReligionContextAddonsImage12004(base, sha).mystical_communion_bindings" in code,
        "no_new_native_function_pointer_addresses":
            re.search(r"reinterpret_cast<[^>]+>\s*\(\s*base\s*\+", code) is None,
        "no_12003_image_factory": re.search(r"Bind\w*12003\s*\(", code) is None,
        "ten_slot_dto_and_evaluator":
            "kResourceSlotCount = 10" in header
            and "std::array<std::int64_t, kResourceSlotCount>" in header
            and "d.cost_evaluate(cost, scope, costs.data())" in code
            and "out.costs_raw_by_native_index = costs" in code,
        "all_slots_serialized_without_four_resource_projection":
            "i < kResourceSlotCount" in code
            and "(*d.costs_raw_by_native_index)[i]" in code
            and not re.search(r"costs\[\d+\]", code),
        "unknown_read_has_null_costs":
            'if (!available || !d.costs_raw_by_native_index) json << "null"' in code,
        "paused_actor_frame_checked_before_and_after":
            "PausedPlayer(b, before)" in code and "PausedPlayer(b, after)" in code
            and "before.clock.date_raw != after.clock.date_raw" in code
            and "before.played_character_id != after.played_character_id" in code,
        "definition_stability_checked":
            "ExactDefinition(b.image_base, out.definition, key)" in code
            and "before != after" in code,
        "principal_debt_unknown_and_no_funding_credit": all(
            token in code for token in (
                r'\"complete_loan_terms\":false', r'\"principal_quote_raw\":null',
                r'\"typed_debt\":null', r'\"funding_credit_raw\":0',
                r'\"submit_planned\":false',
            )
        ),
        "no_native_mutation_entrypoints": not re.search(
            r"\b(?:Submit|Dispatch|Confirm|SelectEventOption|CancelConstruction|AddGold|SetGold)\w*\s*\(", code
        ),
    }
    result = {
        "schema": "xar.g2-m4-loan-decision-costs-source-contract.v1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "machine_id": current_machine_id(),
        "identity_source": "tools/ck3_live_run_id.py:current_machine_id",
        "status": "SOURCE_CONTRACT_PASS" if all(checks.values()) else "SOURCE_CONTRACT_FAIL",
        "checks": checks,
        "sources": files,
        "qualification": {
            "validation": "bounded_source_contract_only",
            "cpp_compiled": False, "cpp_executed": False,
            "native_or_game_access": False, "registered_public_route": False,
            "loan_or_cancellation_executed": False,
            "g2_m4_status_change": False,
        },
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        target = args.output.resolve()
        target.relative_to(ROOT / "docs" / "ck3-native-ai" / "evidence")
        if target.exists():
            raise FileExistsError("source proof is append-only; use a fresh result path")
        target.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
