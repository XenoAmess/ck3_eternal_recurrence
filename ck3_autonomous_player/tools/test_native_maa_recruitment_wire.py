"""Two NEW true-regular MAA publisher frames through the actual war normalizer."""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys
import types


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wire", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--projection-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    projection = args.projection_root or Path(__file__).resolve().parents[1]
    baseline = args.source_root / "ck3_autonomous_player"
    for name, suffix in (("xar_autoplayer", "src/xar_autoplayer"),
                         ("xar_autoplayer.bridge", "src/xar_autoplayer/bridge")):
        package = types.ModuleType(name)
        package.__path__ = [str(projection / suffix), str(baseline / suffix)]
        sys.modules[name] = package
    war = importlib.import_module("xar_autoplayer.bridge.war_contract")
    leaf = importlib.import_module("xar_autoplayer.bridge.native_maa_recruitment_inputs_contract")
    require(Path(war.__file__).resolve() ==
            (projection / "src/xar_autoplayer/bridge/war_contract.py").resolve(),
            "projected production war_contract required")
    wire = json.loads(args.wire.read_text(encoding="utf-8"))
    require(wire["bounded_cases"] == 2 and len(wire["cases"]) == 2, "exactly two NEW regular cases")
    passed = []
    for index, case in enumerate(wire["cases"]):
        rows = war.normalize_army_strengths(case["rows"])
        require([r["army_id"] for r in rows] == [301989997, 184549452], "row identity/order")
        require(case["validator_calls"] == 2 and case["quote_calls"] == 2,
                "same-owner native query is reused")
        blocks = [r["native_maa_recruitment_inputs_v1"] for r in rows]
        require(blocks[0] == blocks[1], "identical same-owner cached result")
        block = blocks[0]
        require(block["command_class"] == "CCreateMAARegimentCommand" and
                block["creation_scope"] == "regular_personal" and block["creation_kind"] == 1,
                "RTTI-closed true regular domain")
        require(block["title_id"] == -1 and block["requested_quantity"] == -1 and
                block["pay_cost"] is True and block["owner_character_id"] == 29829,
                "personal constructor defaults")
        denied = index == 1
        require(block["status"] == ("partial" if denied else "available") and
                block["catalog_observed"] is True, "actual aggregate availability")
        types_in_order = block["types_in_native_order"]
        require([r["type_key"] for r in types_in_order] == ["mangonel", "onager"] and
                [r["type_index"] for r in types_in_order] == [7, 4] and
                [r["effective_quantity"] for r in types_in_order] == [10, 20],
                "native Type order/index/default quantity")
        require(block["missing_type_keys"] == ["trebuchet", "bombard", "torch_bearers",
                "ballista", "cloud_ladder", "siege_tower", "cannon"], "observed catalog absences")
        for type_index, row in enumerate(types_in_order):
            require(row["can_create"] is (not denied), "native false must remain observed false")
            quote = row["regular_personal_quote"]
            require(quote["context"] == "regular_personal_create" and quote["resource_scale"] == 100000,
                    "true regular personal quote context")
            unread = denied and type_index == 1
            require(row["inputs_ready"] is (not unread), "readiness independent of native false")
            if unread:
                require(quote["status"] == "unavailable" and quote["resources_raw"] is None,
                        "failed native output remains null")
            else:
                expected = ([125000, 0, 750000, 0, 0, 0, 0, 910000, -25000, 0]
                            if type_index == 0 else
                            [350000, 0, 900000, 0, 0, 0, 0, 1200000, -10000, 0])
                require(quote["status"] == "available" and quote["resources_raw"] == expected,
                        "observed ten signed raw resource slots including zero")
        passed.append({"name": case["name"], "status": "GREEN", "rows": len(rows)})
    report = {"status": "GREEN", "bounded_cases": 2, "production_normalizer_frames": 2,
              "production_row_frames": 4, "old_cases_executed": 0, "Create_actions": 0,
              "registered_MCP_ingress_executed": False, "actual_baseline_health_getter_executed": False,
              "cases": passed, "actual_war_normalizer": pin(Path(war.__file__)),
              "actual_leaf_normalizer": pin(Path(leaf.__file__))}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "GREEN", "bounded_cases": 2, "output": str(args.output)}))


if __name__ == "__main__":
    main()
