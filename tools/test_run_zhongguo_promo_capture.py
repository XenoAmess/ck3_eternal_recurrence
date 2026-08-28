#!/usr/bin/env python3
"""Static contracts for the append-only ZhongGuo promo capture mode."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tools" / "run_zhongguo_acceptance.py"
FIXTURE = ROOT / "tools" / "fixtures" / "zg361_acceptance"
IDS = (1, 7, 20, 22, 26, 361)


def bom_text(path: Path) -> str:
    data = path.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf"), path
    return data.decode("utf-8-sig")


def main() -> int:
    runner = RUNNER.read_text(encoding="utf-8")
    scenario = re.search(
        r"def run_scenario\(.*?(?=^def )", runner, re.M | re.S
    )
    assert scenario is not None
    body = scenario.group(0)
    assert body.index("initialize_fixture") < body.index("recorder.start()")
    for token in (
        '"-f",\n            "gdigrab"',
        '"zg361-promo-live-full-take-01.mkv"',
        '"exclude_ck3_loading": True',
        '"--promo-capture"',
        "capture_received_scoreboard",
        "capture_policy_cards",
    ):
        assert token in runner, token

    received = re.search(
        r"def capture_received_scoreboard\(.*?(?=^def )", runner, re.M | re.S
    )
    assert received is not None
    received_body = received.group(0)
    assert '"\u8ba4\u547d"' in received_body
    assert '"\u4e0a\u53f8\u8003\u5b9a"' in received_body
    assert (
        'result_option = acceptance.wait_for_ocr_text(\n        "\u77e5\u9053\u4e86"'
        not in received_body
    )
    assert "real 3.25 result response was not accepted" in received_body

    decisions = bom_text(FIXTURE / "common" / "decisions" / "zga_decisions.txt")
    found = tuple(
        int(value)
        for value in re.findall(r"^zga_promo_policy_(\d{3})_decision\s*=", decisions, re.M)
    )
    assert found == IDS, found
    for identifier in IDS:
        assert decisions.count(f"trigger_event = zg361m.{identifier}") == 1

    for language in ("english", "simp_chinese"):
        loc = bom_text(
            FIXTURE / "localization" / language / f"zga_l_{language}.yml"
        )
        for identifier in IDS:
            assert f" zga_promo_policy_{identifier:03d}_decision:0 " in loc
            assert f" zga_promo_policy_{identifier:03d}_decision_confirm:0 " in loc
    print("GREEN: ZhongGuo post-loading promo capture contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
