"""Compile the private receipt in Debug/Release and parse its actual JSON."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from run_domain_construction_cost_legality_live_observer_v1_tests import (
    _visual_studio_environment,
)


HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent


def main() -> int:
    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("cl.exe missing from Visual Studio environment")
    with tempfile.TemporaryDirectory(prefix="xar-m4-defidentity-json-") as name:
        build = Path(name)
        for mode, flags in (
            ("Debug", ["/Od", "/MDd", "/Zi"]),
            ("Release", ["/O2", "/MD"]),
        ):
            output = build / f"m4-defidentity-{mode}.exe"
            command = [
                compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", "/permissive-",
                "/EHsc", "/Gy", *flags,
                f"/I{HERE}",
                f"/I{NATIVE / 'src'}", f"/I{NATIVE / 'include'}",
                str(NATIVE / "src/player_construction_view_probe_v1_mailbox.cpp"),
                str(NATIVE / "src/player_world_definition_identity_diagnostic_serializer_test.cpp"),
                f"/Fe:{output}", "/link", "/OPT:REF",
            ]
            subprocess.run(command, cwd=build, env=environment, check=True)
            raw_receipt = subprocess.run(
                [str(output)], cwd=build, env=environment, check=True,
                text=True, capture_output=True,
            ).stdout
            try:
                receipts = [json.loads(line) for line in raw_receipt.splitlines()]
            except json.JSONDecodeError as error:
                raise AssertionError(raw_receipt[max(0, error.pos - 100):
                                                 error.pos + 100]) from error
            assert len(receipts) == 3
            source = receipts[0]["player_world_building_sources"]
            diagnostic = source["definition_identity_diagnostic"]
            assert source["status"] == "unavailable"
            assert source["failure"] == "definition_identity"
            assert source["definition_source_count"] is None
            assert diagnostic == {
                "registry_count": 47,
                "failed_index": 9,
                "stage": "vtable_mismatch",
                "observed_vtable_rva": 0x44046D0,
                "observed_building_type_id": None,
            }
            assert source["cost_ready"] is False
            assert source["construction_action_ready"] is False
            assert source["advertised"] is False
            assert source["completed_buildings_observed"] is False
            assert source["completed_buildings"] is None
            legal = receipts[1]["player_world_building_sources"]
            assert legal["status"] == "source_available"
            assert legal["snapshot_revision"] == 3
            assert legal["legal_samples"][0]["building_type_id"] == 24
            assert legal["legal_samples"][0]["slot_index"] == 1
            assert legal["legal_samples"][0]["building_key"] == "common_tradeport_01"
            assert legal["completed_buildings_observed"] is False
            assert legal["completed_buildings"] is None
            completed = receipts[2]["player_world_building_sources"]
            assert completed["completed_buildings_observed"] is True
            assert completed["completed_buildings"] == [{
                "barony_title_id": 2103, "province_id": 2635,
                "building_type_id": 24, "slot_index": 1,
            }]
            print(f"m4-definition-identity-receipt-{mode}: GREEN_W4WX_JSON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
