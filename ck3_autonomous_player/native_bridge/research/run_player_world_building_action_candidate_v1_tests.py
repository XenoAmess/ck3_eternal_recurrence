"""Focus only the R746 stock-cost selection/material contract in both MSVC modes."""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from run_domain_construction_cost_legality_live_observer_v1_tests import (
    _visual_studio_environment,
)


NATIVE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(NATIVE.parent / "src"))
from xar_autoplayer.bridge.domain_construction_private_transport_v1 import _candidate
from xar_autoplayer.bridge.construction_economic_value_v1 import (
    _AUTHOR_MONTHLY_INCOME_HUNDREDTHS,
)


def _python_same_frame_choice() -> tuple[int, int, int, int, int]:
    samples = []
    for building, key, cost in ((12, "farm_estates_01", 20_000_000),
                                (24, "common_tradeport_01", 15_000_000)):
        for slot in (1, 2, 3):
            samples.append({"barony_title_id": 2103, "province_id": 2635,
                            "building_type_id": building, "slot_index": slot,
                            "building_key": key, "native_cost_observed": True,
                            "cost_raw_native": [cost] + [0] * 9})
    choice = _candidate({"player_gold_raw": 50_035_659,
                         "active_constructions": [
                             {"barony_title_id": 2103, "province_id": 2635,
                              "active": False}],
                         "legal_samples": samples})
    assert choice is not None
    return tuple(choice[field] for field in (
        "barony_title_id", "province_id", "building_type_id", "slot_index",
        "stock_gold_cost_raw"))


def main() -> int:
    environment = _visual_studio_environment()
    compiler = shutil.which("cl.exe", path=environment.get("PATH"))
    if compiler is None:
        raise RuntimeError("cl.exe missing from Visual Studio environment")
    source = NATIVE / "src"
    native_values = dict((key, int(value)) for key, value in re.findall(
        r'\{"([a-z0-9_]+)", ([0-9]+)\}',
        (source / "player_world_building_authored_income_v1.hpp").read_text(
            encoding="utf-8")))
    assert native_values == _AUTHOR_MONTHLY_INCOME_HUNDREDTHS
    with tempfile.TemporaryDirectory(prefix="xar-m4-cost-to-action-") as name:
        build = Path(name)
        for mode, flags in (("normal-Debug", ["/Od", "/MDd", "/Zi"]),
                            ("optimized-Release", ["/O2", "/MD"])):
            output = build / f"m4-cost-to-action-{mode}.exe"
            command = [
                compiler, "/nologo", "/std:c++20", "/W4", "/WX",
                "/DNOMINMAX", "/DWIN32_LEAN_AND_MEAN", "/permissive-",
                "/EHsc", "/UNDEBUG", *flags,
                f"/I{source}", f"/I{NATIVE / 'include'}",
                str(source / "player_world_building_action_candidate_v1.cpp"),
                str(source / "player_world_building_action_candidate_v1_test.cpp"),
                f"/Fe:{output}",
            ]
            subprocess.run(command, cwd=build, env=environment, check=True)
            native = subprocess.run([str(output)], cwd=build, env=environment,
                                    check=True, capture_output=True, text=True)
            line = next(line for line in native.stdout.splitlines()
                        if line.startswith("VALUE_CHOICE "))
            native_choice = tuple(int(value) for value in line.split()[1:])
            assert native_choice == _python_same_frame_choice(), (
                native_choice, _python_same_frame_choice())
            print(f"m4-cost-to-action-{mode}: GREEN_W4WX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
