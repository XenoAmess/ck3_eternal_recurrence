"""Offline authoring/producer contract checks; no TTS, FFmpeg, run or screen."""
from copy import deepcopy
from pathlib import Path
import hashlib
import inspect
import json
import math
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "src"))
from faith_power_promo.context_composer import compose, font_render_planner
from faith_power_promo.production import cue_duration, pin, project, select_context
from xar_promo.model import ProjectConfig
from xar_promo.pipeline import PipelineDependencies
from xar_promo.render import RenderOptions
from xar_promo.tts.cache import tts_fingerprint
from xar_promo.tts.provider import ProviderIdentity, TtsRequest


def rejects(call, text):
    try:
        call()
    except (ValueError, TypeError, KeyError) as error:
        if text and text not in str(error):
            raise AssertionError(str(error)) from error
    else:
        raise AssertionError("Expected refusal")


def main():
    source = HERE.parent / "episode01"
    script = json.loads((source / "script.json").read_text("utf-8"))
    recipe = json.loads((source / "tts-recipe.json").read_text("utf-8"))
    config = ProjectConfig.from_mapping(json.loads((source / "authoring-project.json").read_text("utf-8")))
    projected = project(script)
    assert len(script["cues"]) == 158
    assert all(not chapter.artifact_ids for chapter in config.chapters)
    assert projected["chapters"][0]["artifact_ids"] == []
    assert all(slot[key] is None for slot in script["live_result_slots"] for key in ("zh", "en", "outcome"))
    identity = ProviderIdentity(**recipe["provider_identity_for_frozen_fingerprints"])
    entries = {r["cue_id"]: r for r in recipe["entries"]}
    sources = {r["id"] for r in script["source_catalog"]}
    for row in script["cues"]:
        assert row["claim_ids"] and row["shot_ids"] and set(row["source_ref_ids"]) <= sources
        assert row["raw_binding"] is None and row["final_interval_seconds"] is None
        request = TtsRequest(row["zh"], **recipe["request_defaults"])
        assert entries[row["id"]]["text_utf8_sha256"] == hashlib.sha256(row["zh"].encode()).hexdigest()
        assert entries[row["id"]]["tts_fingerprint"] == tts_fingerprint(request, identity)
    assert abs(cue_duration(14.448) - 14.933333333333334) < 1e-9
    assert all(math.isclose(cue_duration(t) * 30 / 16, round(cue_duration(t) * 30 / 16))
               for t in (0.001, 1, 10.752, 11.568, 14.448))
    for invalid in (0, -1, float("nan"), float("inf")):
        rejects(lambda: cue_duration(invalid), "positive")
    rejects(lambda: compose(None, None, config_path=None, run_path=None, workdir=Path("unused"),
                            adapter_factory=None, preset_factory=None, validate_only=True), "preserved native run")
    assert "render_planner" in inspect.signature(PipelineDependencies).parameters
    # Plan the public fontsdir extension without creating files or subprocesses.
    plan = font_render_planner(Path("font-input"))(
        ffmpeg="ffmpeg", video_input=Path("v.mp4"), audio_input=Path("a.mp3"),
        partial_output=Path("partial.mp4"), final_output=Path("final.mp4"),
        audit_directory=Path("unused-audit"), options=RenderOptions(2560, 1440, 30, 1),
        ass_path=Path("subtitle.ass"), start_seconds=0, working_directory=Path("unused-work"))
    graph = plan.commands[0].spec.argv[plan.commands[0].spec.argv.index("-filter_complex") + 1]
    assert ":fontsdir='font-input'" in graph
    # Source bindings are opaque temporary bytes for validation only. They are
    # never submitted to a media probe or represented as playable captures.
    with tempfile.TemporaryDirectory(prefix="faith-context-contract-") as temporary:
        root = Path(temporary)
        for name in ("raw", "audio"):
            (root / name).write_text("contract-only, not media", encoding="utf-8")
        terminal = root / "terminal.json"
        terminal.write_text(json.dumps({"machine_id": "contract-machine",
            "job": {"state": "ABORT_TREE_EMPTY", "job_active_processes": 0}}), "utf-8")
        (root / "audit").write_text(json.dumps({"schema": "ck3-faith-power-raw-media-read-audit-v1",
            "machine_id": "contract-machine", "raw": pin(root / "raw"), "terminal": pin(terminal)}), "utf-8")
        small = {"cues": []}
        measured = {"cues": []}
        chosen = {"machine_id": "contract-machine", "scope": "context-only-first-opening", "business_result_verified": False, "segments": []}
        for index in range(3):
            row = {"id": f"c{index}", "zh": "机制解释", "en": "Mechanism", "claim_ids": ["claim"],
                   "shot_ids": ["shot"], "live_result_asserted": False}
            small["cues"].append(row)
            request = root / f"request{index}.json"
            request.write_text(json.dumps({"request": {"text": row["zh"]}}), "utf-8")
            measured["cues"].append({"id": row["id"], "speech_duration_seconds": 10,
                                      "request": pin(request), "audio": pin(root / "audio")})
            chosen["segments"].append({"cue_id": row["id"], "raw": pin(root / "raw"),
                "source_machine_id": "contract-machine",
                "raw_audit": pin(root / "audit"), "raw_start_seconds": index * 11,
                "approved_raw_end_seconds": index * 11 + 11, "decoded_last_pts_seconds": 40,
                "raw_terminal_status": "ABORT_TREE_EMPTY"})
        assert len(select_context(small, measured, chosen)) == 3
        overlapping = deepcopy(chosen)
        overlapping["segments"][1]["raw_start_seconds"] = 1
        rejects(lambda: select_context(small, measured, overlapping), "repeated")
        short = deepcopy(chosen)
        short["segments"][0]["decoded_last_pts_seconds"] = 1
        rejects(lambda: select_context(small, measured, short), "decoded source")
        claimed = deepcopy(chosen)
        claimed["business_result_verified"] = True
        rejects(lambda: select_context(small, measured, claimed), "context-only")
    print(json.dumps({"status": "OFFLINE_CONTRACT_PASS", "cues": 158, "unwritten_results": 3,
                      "rendered": False, "tts_invoked": False, "native_run_created": False}))


if __name__ == "__main__":
    main()
