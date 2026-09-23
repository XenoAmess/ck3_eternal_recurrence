"""One real-frame and one paper-frame smoke check for the V3 visual gate."""

import hashlib
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE / "src"))

from war_ai_promo.v3_visuals import COPY, make_v3_frame  # noqa: E402


def main():
    ledger = REPO / "promo/ck3_native_war_ai/longform/v3/evidence-visual-ledger.json"
    import json
    cues = json.loads(ledger.read_text(encoding="utf-8-sig"))["cues"]
    assert {r["id"] for r in cues if r["state"] != "unbound"} == set(COPY)
    original = Path("D:/workspace/ck3_war_film_research_20260923/robert-case-r-frames-pts-fix-r1/begin.png")
    root = Path("D:/workspace/ck3_war_film_research_20260923")
    for index in range(1, 1000):
        output = root / f"v3-visual-preview-r{index}"
        try:
            output.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            continue
    else:
        raise RuntimeError("No unused V3 visual preview attempt directory")
    asset = {"CASE-R": {"case_id": "CASE-R", "path": original.as_posix(),
                        "sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
                        "evidence_role": "context-only-original-frame"}}
    live = make_v3_frame({"id": "V3-06", "shot_id": "S3-06"}, output / "case-r.png",
                         1, ledger_path=ledger, assets=asset)
    paper = make_v3_frame({"id": "V3-30", "shot_id": "S3-30"}, output / "battle-rule.png",
                          2, ledger_path=ledger)
    assert live["context_frame"]["case_id"] == "CASE-R"
    assert paper["context_frame"] is None
    for cue in ("V3-99",):
        try:
            make_v3_frame({"id": cue, "shot_id": "S3-" + cue[-2:]},
                          output / (cue + ".png"), 0, ledger_path=ledger)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Unbound/unknown cue rendered: {cue}")
    assert sorted(p.name for p in output.glob("*.png")) == ["battle-rule.png", "case-r.png"]
    print(f"V3 visual sample PASS: {output.as_posix()}")


if __name__ == "__main__":
    main()
