"""Validate a real header-layout stdout artifact; never start an EXE or Game."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

TYPES = (
    "xar::game::Snapshot", "xar::game::PlayerFactionAlertsV1",
    "xar::ck3_11906::PlayerFactionAlertsSourceSampleV1",
    "xar::ck3_11906::MainThreadQueryMailboxV1",
    "xar::ck3_11906::PlayerFactionAlertsMailboxContextV1",
    "xar::ck3_12002::QueryMailboxEnvelope",
    "xar::ck3_12002::PlayerFactionAlertsMailboxContext12002",
    "xar::ck3_12004::PlayerFactionAlertsMailboxContext12004",
)


def validate(report: dict) -> None:
    if not __debug__:
        raise RuntimeError("layout validation requires normal Python assertion checks")
    assert report["schema"] == "xar.ck3.native-header-layout/v1"
    assert report["scope"] == "header_layout_only_not_Game_qualification"
    assert report["machine_id"] and report["machine_id"] != "unknown"
    assert report["observed_at_utc"].endswith(("Z", "+00:00"))
    assert report["pointer_bytes"] == 8
    assert report["current_pragma_pack"] is None
    assert set(report["types"]) == set(TYPES)
    for value in report["types"].values():
        size, alignment = value["sizeof"], value["alignof"]
        assert type(size) is int and size > 0
        assert type(alignment) is int and alignment > 0
        assert alignment & (alignment - 1) == 0 and size % alignment == 0
        assert type(value["standard_layout"]) is bool
    macros = report["preprocessor"]
    for key in ("_MSC_VER", "_MSC_FULL_VER", "_MSVC_STL_VERSION",
                "_ITERATOR_DEBUG_LEVEL", "_CRT_PACKING", "_MT", "_DLL", "_DEBUG"):
        assert key in macros
    assert macros["_MSC_VER"] and macros["_MSVC_STL_VERSION"]
    assert macros["_ITERATOR_DEBUG_LEVEL"] == "0", "Release STL ABI expected"
    for key in ("configuration=Release", "compiler=", "global_flags=",
                "release_flags=", "bridge_definitions=", "bridge_options="):
        assert key in report["source_flags"], key


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    data = json.loads(args.report.read_text(encoding="utf-8-sig"))
    validate(data)
    print(json.dumps({"schema": "xar.ck3.native-header-layout-check/v1",
        "machine_id": data["machine_id"], "observed_at_utc": data["observed_at_utc"],
        "status": "SHAPE_AND_RELEASE_ABI_METADATA_PASS",
        "input": str(args.report), "Game_qualification": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

