"""Prepare R191 source recipe using only small files + raw stat. Never decode."""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
from r03_pipeline import (DEADLINE, EXPECTED_ARGV, FFMPEG, FONT, MACHINE, RAW, RETAINED_STAT,
                          ROOT, encoded, source_stat, stamp, validate_stat, write_new)

SMALL_INPUTS: list[tuple[str, int, str]] = [
 ("D:/workspace/ck3_native_war_ai_promo_work/e04-r191-media-audit-bounded-a01/audit.actual-a01.json",19453,"52ca8dc34420a5912235f28c714fd5a6540d9362f710542556a2218583849dfb"),
 ("D:/workspace/ck3_eternal_recurrence/docs/ck3-native-ai/evidence/episode04-r0191-20261017/facts.derived-a01.json",7487,"2790bec7b583f1f90b01ade1fde2e41b7cc6df5261284db6ecf1eed9de1f0b79"),
 ("D:/workspace/ck3_native_war_ai_promo_work/e04-r191-window-capture-a01/runtime-actor-identity.actual-a01.json",7920,"154c8f84c8211f57c4ba3baa6f7570ee2bc71fc9db2bcb4855e1ffc01f39950b"),
 ("C:/ck3-e04-resume-20261015-a01/review02-experiment-cards-a01/EXPERIMENT-CARDS.md",27122,"dc1f06132109032d9ddef9316faacdb04bd2c1759a96ea38ec99c2d5f27bddab"),
 ("C:/ck3-e04-resume-20261015-a01/r191-portable-candidate-a01/reader-derived-a03/STRICT-SOURCE-FACTS.actual.json",9964,"f3ade075421681ce83031ed49bb49a27ff328dc4233908ad1c6b6ad580f5ff98"),
]
def pin(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def main() -> None:
    validate_stat(source_stat(RAW))
    small: list[dict[str, object]] = []
    for name, size, sha in SMALL_INPUTS:
        entry = pin(Path(name))
        if entry["bytes"] != size or entry["sha256"] != sha:
            raise ValueError("Small retained input differs: " + name)
        small.append(entry)
    source_files = ["r03_pipeline.py", "r03_once.py", "prepare_r03_recipe.py", "test_r03_pipeline.py", "run_source_checks.py"]
    for name in source_files:
        small.append(pin(ROOT/"source"/name))
    document: dict[str, object] = {
        "schema": "xar.R191.JPEG-pipe.prepared.v1", "machine_id": MACHINE,
        "prepared_at_utc": stamp(), "root": str(ROOT), "deadline_utc": DEADLINE,
        "raw": str(RAW), "raw_retained_sha256": "7234e5b34c05ed47a4022864485b2c89e1229be33008dbb06177c7edc0d4d872",
        "raw_body_hashed_during_preparation": False, "retained_source_stat": dict(RETAINED_STAT),
        "financial_admission": {"path":str(ROOT/"capacity"/"FINITE-FINANCIAL-SOURCE-ADMISSION.actual-a01.json"),
                                "bytes":2452,"sha256":"3654de572257d61e793c400334724ae195d77fc1675cecbe189875845ee41865",
                                "decoder_admitted_at_financial_stage":False},
        "historical_process_birth_filetime": "134366591050798809", "historical_pid": 32028,
        "historical_machine_identity_source": SMALL_INPUTS[2][0],
        "historical_episode": "native-31254-03602e8dc25a",
        "run_id": "desktop-3fevhd2-1c74096080--vanilla--R0191",
        "argv": EXPECTED_ARGV, "entry": [str(ROOT/"source"/"r03_once.py"), "--execute-once", str(ROOT/"R03-RECIPE.prepared-a01.json")],
        "frame_window": {"start":0,"end_exclusive":1200,"expected_count":1200,"seconds":"[0,40)","expected_last_pts_ms":39967,
                         "ordinal_basis":"Decoded source starts at actual frame0; no fps/drop/dup filter; actual n/PTS validated"},
        "pipe_contract": {"JPEG_geometry":[1280,720],"stdout_FFmpeg_qscale":4,"fullres_JPEG_disk_frames":[0,1199],
                          "other_source_JPEGs_disk":0,"JPEG_RAM_limit_bytes":2097152,"stderr_RAM_limit_bytes":4194304,
                          "stderr_reader":"Concurrent continuous drain; log compressed losslessly only after original wait",
                          "JPEG_boundary":"Marker aware; APP/COM payload EOI bytes are not a frame terminator",
                          "PTS":"Actual showinfo input timebase/n/pts/pts_time joined by exact output order; no UTC interpolation"},
        "contacts": {"count":75,"grid":[4,4],"cell_source":[320,180],"label_height":18,"geometry":[1280,792],
                     "valid_cells_each":16,"padding_cells":0,"Pillow_quality":60,"subsampling":2,
                     "equivalent_to_FFmpeg_q12_claim":False},
        "limits": {"aggregate":9437184,"contacts":7340032,"endpoints":524288,"metadata":786432,
                   "spare_reserved":262144,"source_checks":524288,
                   "author_planning_max":524288,"independent_review_max":131072,
                   "Root_max":65536,"capacity_max":65536},
        "tools": {"ffmpeg":str(FFMPEG),"ffmpeg_bytes":222229504,
                  "ffmpeg_retained_sha256":"57c56e369d5b4873b4d93fc1a1d833cb7cd8bc9325c14b05c34ce60b22842d8a",
                  "ffmpeg_body_rehash":False,"Pillow":"12.3.0","Python":"3.14.7","font":str(FONT),
                  "mypy_readonly_Lib":"C:/ck3-e04-resume-20261020-a01/r08-mypy1201-tools-2115-a01/Lib",
                  "downloads_or_installs":False,"latest_release_query":"fresh gh release view before actual FFmpeg; expected v0.3.0"},
        "small_source_pins":small,
        "existing_QA_reuse":{"decoded_frames":3359,"encoded_end":"111.966","missing_timestamps":0,"PTS_regressions":0,
                            "max_gap_ms":34,"full_AV_decode_exit":0,"repeated":False},
        "native_claim":{"Army":18,"callback_sequence":8,"positive_writers":7,"actual_physical_debit":11,
                        "stock_and_capacity":"300/300","source_supply_budget":0,"source_raid_budget":0,
                        "physical_count":[1174,1163],"cached_count":[1184,1173],
                        "event_exact_PTS":None,"scope":"These source-bound siege-only positive events; no allworld/wholeinterval total"},
        "acceptance_pending":{"continuous_clean":True,"actual_inclip_date_and1184_to1173_readable":True,
                              "AI_all75_and_Root_key_fullres_review":True,
                              "formal_credit":0,"human1x_required_or_claimed":False},
        "guards":{"single_Popen":True,"WAL_before_start":True,"no_retry":True,"original_wait_and_gzip_CRC":True,
                  "on_limit_or_missing_visual":"Preserve actual partial/failure; no automatic tail/quality reduction/retry",
                  "FFmpeg_execution_admitted_by_this_recipe":False},
    }
    data = encoded(document)
    consumed: object = json.loads(data)
    if not isinstance(consumed, dict):
        raise ValueError("Producer roundtrip must remain object")
    validate_stat(consumed["retained_source_stat"])
    result = write_new(ROOT, "R03-RECIPE.prepared-a01.json", data)
    print(json.dumps(result))
if __name__ == "__main__":
    main()
