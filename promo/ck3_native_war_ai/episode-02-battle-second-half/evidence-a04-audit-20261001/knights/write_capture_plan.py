from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = Path("C:/w/ep2a04")
RAW = Path("D:/workspace/ck3_native_war_ai_promo_work")
NEXT = Path("C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-nextday-live-20261001-a01")
def identity(p):
    p=Path(p)
    with p.open("rb") as stream:
        sha=hashlib.file_digest(stream,"sha256").hexdigest().upper()
    return {"path":str(p).replace("\\","/"),"bytes":p.stat().st_size,"sha256":sha}
save=RAW/"episode01-paired-counter-trace-attempt-010/d26-immutable.ck3"
source_receipt=RAW/"episode01-paired-counter-trace-attempt-010/ck3-output/interactive-requests-responses/d26-save.json"
reader=FROZEN/"ck3_autonomous_player/tools/project_native_phase_event_save_feedback.py"
capture=FROZEN/"promo/ck3_native_war_ai/integration/capture_session.py"
step=FROZEN/"promo/ck3_native_war_ai/episode-02-battle-second-half/remaining_live_step.py"
transport=FROZEN/"promo/ck3_native_war_ai/episode-02-battle-second-half/pursuit_live_step.py"
checker=HERE/"check_nextday_saved_status.py"
gui=RAW/"episode02-e2-04-d05-screen-lease-20260928-a04/native-ui-saved-settings-a01.pdx.txt"
gui_receipt=RAW/"episode02-e2-04-d05-screen-lease-20260928-a04/native-ui-saved-settings-a01.json"
plan={
 "schema":"ck3.a04.knights.capture-nextday-plan.v1","created_at_utc":datetime.now(timezone.utc).isoformat(),
 "status":"NOT_RUN_ENVIRONMENT_RED","not_run":True,"ck3_launches":0,"new_live_run_id":None,
 "environment":"Root reported black/stale Steam desktop and failed recovery; no fresh offline proof. Root released its screen lease. This plan performs no desktop/game action.",
 "branch":"codex/war-series-brown-gold-20261001","master_intake_allowed":False,
 "new_run_root":str(NEXT),"isolation":"Create a new workdir/profile/pipe/recording/run ID; never reuse old a02 profile or replace historical assets.",
 "exact_input":{"save":identity(save),"receipt":identity(source_receipt),"actor_character_id":29829,
                "combat_id":16777218,"war_id":4,"player_army_id":18,"date_raw":53146848,"ui_date":"1066.12.30","source_day_index":26,
                "game_version":"1.19.0.6","exe_sha256":"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"},
 "target":{"character_id":33437,"expected_before":"ALIVE must be read from this new run's native d26 checkpoint", "next_date_raw":53146872,"next_ui_date":"1066.12.31","next_day_index":27,
           "after_status":"Observe ALIVE or DEAD; do not prefill the historical020 result or killer34120."},
 "source_reuse":{"capture_script":identity(capture),"remaining_step":identity(step),"request_transport":identity(transport),
                 "transport_callable":"pursuit_live_step.call(output: Path, name: str, tool: str, arguments: dict, timeout: float)",
                 "strict_reader_source":identity(reader),"strict_reader_callable":"project_native_phase_event_save_feedback._character_snapshot(melted_text: str, character_id: int)",
                  "checker":identity(checker),"gui_settings_snapshot":identity(gui),"gui_preservation_receipt":identity(gui_receipt),
                  "checker_validation":"5 synthetic lifecycle checks; 5 actual capture disk binding cases and full GUI source binding passed offline only; no new live input was supplied"},
 "ABI_provider":{"current_native_pair":{"dll_sha256":"EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7","injector_sha256":"CE8A20C7B25A697058AB69B03629D6B7655BB2935AD147DF1E84895A826BF247"},
                 "save_route_available":True,"targeted_paused_character_query_available":False,
                 "status_route":"Use existing MCP save-checkpoint and pinned strict save reader; saved state, not same-frame live CharacterID query.",
                 "selector_admission":"Old currenta02 has no selector rows. Selector-capable newer candidate still requires its exact admission/review; not required merely to read saved d27 target status.",
                 "native_patch_needed_for_saved_route":False,
                 "minimum_if_live_query_required":["full CharacterID native storage resolution and equality","native_valid/death_marker_present/alive/regiment_id","paused date_raw/revision and before/after frame identity","explicit missing/fault/stale result; no alive inference from combat roster"]},
 "sequence":[
  {"step":1,"not_run":True,"action":"Root acquires exclusive CK3/screen slot, resolves desktop environment and directly reviews fresh Steam offline image; allocate live run ID only at actual admitted launch."},
  {"step":2,"not_run":True,"action":"Run capture_session in new isolated state/output/pipe with exact input pair. Retain preflight.json and native-start-readback.json that bind actor/date/save/receipt and exact binary pair.",
    "capture_cli_argv_template":["<verified-python>",str(capture),"--game-dir","<exact-build-game-dir>","--bridge-dll","<verified-DLL>","--bridge-injector","<verified-injector>","--state-dir",str(NEXT/"ck3-state"),"--output-dir",str(NEXT/"ck3-output"),"--pipe-name","<new-local-pipe>","--checkpoint-save",str(save),"--checkpoint-receipt",str(source_receipt),"--gui-scale","1.0","--import-a04-ui-gui-100","--a04-ui-settings-snapshot",str(gui),"--a04-ui-preservation-receipt",str(gui_receipt),"--interactive-seconds","3600","--enable-private-phase-trace","--steam-offline-receipt","<fresh-reviewed-offline-receipt>","--screen-task-id","<actual-new-screen-task-id>","--screen-expected-sequence","<fresh-task-last-sequence>","--screen-cli-sha256","<identical-source-installed-CAS-CLI-SHA256>","--capture"]},
  {"step":3,"not_run":True,"native_calls":[{"tool":"ck3_take_snapshot","arguments":{}},{"tool":"ck3_query_battle_control_snapshot_v1","arguments":{"subject_army_id":18,"expected_revision":"<current-paused-d26-revision>"}}],
   "accept":"53146848/paused=true/actor29829/Combat16777218; snapshot/control same revision. Actual UI12/30 and targetID/name need their own same-run binding."},
  {"step":4,"not_run":True,"action":"Reuse remaining_live_step observe/advance only after recorder intent and native marked source frame match. Its advance saves d26 once, then one private begin→one life-advance→one finish. Preserve the d26 save bytes BEFORE any d27 save overwrites xar_checkpoint.",
   "existing_cli_examples":[["<verified-python>",str(step),"observe","--track","e2-05-d26","--session-output",str(NEXT/"ck3-output")],["<verified-python>",str(step),"advance","--track","e2-05-d26","--session-output",str(NEXT/"ck3-output"),"--recorder-workdir","<new-running-recorder-workdir>","--sequence-token","<new-positive-token>"]],
   "do_not_retry":"An ambiguous or timed-out life-advance is never resubmitted; inspect and preserve the run."},
  {"step":5,"not_run":True,"action":"After actual53146872, acquire new paused snapshot/control same revision, retain actualUI12/31, then only once ck3_save_checkpoint(expected_revision=that snapshot revision). Copy exact native saved path into this new root's exclusive evidence/d27-immutable.ck3 and bind bytes/SHA/date/actor/episode_run_id.",
   "native_calls":[{"tool":"ck3_take_snapshot","arguments":{}},{"tool":"ck3_query_battle_control_snapshot_v1","arguments":{"subject_army_id":18,"expected_revision":"<paused-d27-revision>"}},{"tool":"ck3_save_checkpoint","arguments":{"expected_revision":"<paused-d27-revision>"}}]},
  {"step":6,"not_run":True,"action":"Run saved-status checker below. It validates newroot input/run/connection/native save/date/revision/SHA and invokes pinned Rakaly0.8.19 on newly supplied d26+d27 byte copies, then calls existing strict character parser for33437.",
   "accept":"Unique alive_data XOR dead_data, beforeALIVE, after observedALIVE/DEAD; ifDEAD retain death_date/reason/killer. Missing or ambiguous staysUNKNOWN. Neither old020 nor a02 assets are accepted as new run evidence."}
 ],
 "rakaly":{"version":"0.8.19","exe_sha256":"E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D","actual_cli_argv":["<pinned-rakaly>","melt","<new-immutable.ck3>","--unknown-key","stringify","--format","ck3","--out","<new-exclusive-melted.ck3>"]},
 "checker_cli_argv_template":["<verified-python>",str(checker),"--new-run-root",str(NEXT),"--source-save",str(save),"--source-receipt",str(source_receipt),"--preflight",str(NEXT/"ck3-output/preflight.json"),"--readback",str(NEXT/"ck3-output/native-start-readback.json"),"--before-save",str(NEXT/"evidence/d26-immutable.ck3"),"--before-save-receipt",str(NEXT/"ck3-output/interactive-requests-responses/e2-05-d26-before-save.json"),"--before-snapshot",str(NEXT/"ck3-output/interactive-requests-responses/e2-05-d26-pre-advance-snapshot.json"),"--after-save",str(NEXT/"evidence/d27-immutable.ck3"),"--after-save-receipt",str(NEXT/"ck3-output/interactive-requests-responses/new-d27-save.json"),"--after-snapshot",str(NEXT/"ck3-output/interactive-requests-responses/new-d27-snapshot.json"),"--rakaly-exe","<pinned-rakaly-exe>","--parser-source",str(reader),"--parser-sha256",identity(reader)["sha256"],"--expected-episode-run-id","<actual-new-run-id-from-native-checkpoint>","--output",str(NEXT/"strict-save-check-attempt-01")],
 "completion_boundaries":{"old_a02_postframe_status":"UNKNOWN remains permanently","newrun_status":"NOT_RUN","selector_choice":"not supplied by saved status checker","live_targeted_death_query":"not supplied","human_clean_span":"not supplied","historical_UI":"new coldload/replay cannot be renamed original020/039/036 footage"}
}
with (HERE/"capture-nextday-plan.json").open("x",encoding="utf-8",newline="\n") as f:
    json.dump(plan,f,ensure_ascii=False,indent=2);f.write("\n")
print(HERE/"capture-nextday-plan.json")
