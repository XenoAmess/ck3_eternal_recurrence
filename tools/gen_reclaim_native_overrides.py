#!/usr/bin/env python3
"""Generate RMTM's three narrow native projections for exact CK3 1.20.0.2."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import reclaim_the_motherland_vanilla_contract as native

MOD = native.ROOT / "mod_reclaim_the_motherland"
CHAOS = "tgp_chaos_shattering_effect"
PRIVATE_CHAOS = "rmtm_vanilla_chaos_shattering_effect"
MINISTRY = "tgp_has_access_to_ministry_trigger"
MANDATE = "situation_dynastic_cycle_claim_mandate_decision"
GUARD = "\t\tNOT = { rmtm_holds_restoration_hegemony_trigger = yes }\n"
MINISTRY_NATIVE = "\thas_title = title:h_china\n"
MINISTRY_PRIVATE = """\
\tOR = {
\t\thas_title = title:h_china
\t\tAND = {
\t\t\ttitle:h_china = { NOT = { exists = holder } }
\t\t\texists = global_var:rmtm_ministry_entitlement_title
\t\t\ttrigger_if = {
\t\t\t\tlimit = { exists = global_var:rmtm_ministry_entitlement_title }
\t\t\t\tprimary_title = global_var:rmtm_ministry_entitlement_title
\t\t\t\tglobal_var:rmtm_ministry_entitlement_title = {
\t\t\t\t\thas_variable = rmtm_restoration_hegemony
\t\t\t\t}
\t\t\t}
\t\t}
\t}
"""
MANDATE_ANCHORS = (
    ("\t\thas_tgp_dlc_trigger = yes\n", "shown guard"),
    ("\t\tis_independent_ruler = yes\n", "valid guard"),
    ("\tai_potential = {\n\t\tsituation:dynastic_cycle ?= { situation_current_phase = situation_dynastic_cycle_phase_chaos }\n", "AI guard"),
)
OUTPUTS = {
    CHAOS: MOD / "common/scripted_effects/rmtm_vanilla_compat_effects.txt",
    MINISTRY: MOD / "common/scripted_triggers/zz_rmtm_ministry_override.txt",
    MANDATE: MOD / "common/decisions/dlc_decisions/tgp/zz_rmtm_mandate_override.txt",
}


def project(name: str, body: str) -> str:
    native.assert_definition(body, name)
    if name == CHAOS:
        return native.replace_once(body, f"{CHAOS} = {{", f"{PRIVATE_CHAOS} = {{", "private vanilla shattering name")
    if name == MINISTRY:
        return native.replace_once(body, MINISTRY_NATIVE, MINISTRY_PRIVATE, "unique Later Dynasty ministry access")
    if name == MANDATE:
        for anchor, label in MANDATE_ANCHORS:
            body = native.replace_once(body, anchor, anchor + GUARD, label)
        return body
    raise ValueError(name)


def generated_payloads(game: Path = native.GAME) -> dict[Path, bytes]:
    native.assert_source_files(game)
    notes = {
        CHAOS: "Native shattering body copied exactly; only its definition is renamed.",
        MINISTRY: "Native celestial and ministry-budget flags retained; only title access gains the existing unique Later Dynasty branch.",
        MANDATE: "Native mandate decision retained; only the three existing restoration locks are inserted.",
    }
    payloads = {}
    for name in OUTPUTS:
        header = native.header((name,), notes[name])
        if name == MANDATE:
            values_path = native.CONTRACT["paths"]["values"]
            header += f"# Native threshold values SHA-256: {native.CONTRACT['files'][values_path]}\n"
        payloads[OUTPUTS[name]] = b"\xef\xbb\xbf" + (header + project(name, native.definition(name, game))).encode("utf-8")
    return payloads


def validate_committed_projections() -> list[str]:
    errors = []
    for name, path in OUTPUTS.items():
        try:
            raw = path.read_bytes()
            if not raw.startswith(b"\xef\xbb\xbf"):
                raise ValueError("UTF-8 BOM missing")
            body = native.extract_definition(raw.decode("utf-8-sig"), PRIVATE_CHAOS if name == CHAOS else name)
            if name == CHAOS:
                body = native.replace_once(body, f"{PRIVATE_CHAOS} = {{", f"{CHAOS} = {{", "restore shattering name")
            elif name == MINISTRY:
                body = native.replace_once(body, MINISTRY_PRIVATE, MINISTRY_NATIVE, "restore native title access")
            else:
                for anchor, label in reversed(MANDATE_ANCHORS):
                    body = native.replace_once(body, anchor + GUARD, anchor, "restore " + label)
            native.assert_definition(body, name)
        except (OSError, ValueError) as error:
            errors.append(f"{path.name}: {error}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=native.GAME)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    for path, expected in generated_payloads(args.game_root).items():
        if args.check:
            if not path.is_file() or path.read_bytes() != expected:
                print(f"stale generated RMTM native projection: {path}", file=sys.stderr)
                return 1
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    print("RMTM NATIVE PROJECTIONS OK" if args.check else "Wrote three RMTM native projections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
