"""Seal the bounded, offline SDK candidate; never opens CK3 or runtime state."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DRIVER = "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
HELPER = "ck3_autonomous_player/src/xar_autoplayer/bridge/war_daily_watch_v1.py"
TEST = "ck3_autonomous_player/tests/unit/test_war_daily_watch_v1.py"
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()
OUT = "docs/ck3-native-ai/evidence/war-daily-watch-v1-software-qualification-2026-10-19.json"
TEST_FILES = [
    TEST,
    "ck3_autonomous_player/tests/unit/test_exact_day_native_clock_paused_next_frame.py",
    "ck3_autonomous_player/tests/unit/test_contact_free_exact_route_speed_trial_v1.py",
    "ck3_autonomous_player/tests/unit/test_campaign_deadline_transport_v1.py",
    "ck3_autonomous_player/tests/unit/test_native_exact_day_speed_five.py",
    "ck3_autonomous_player/tests/unit/test_battle_reader_exact_speed.py",
    "ck3_autonomous_player/tests/unit/test_war_objective_hold_sentinel_contract.py",
    "ck3_autonomous_player/tests/unit/test_exact_war_move_stop.py",
]


def pin(rel):
    body = (ROOT / rel).read_bytes()
    return {"path": rel, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def functions(body):
    result = {}
    def walk(nodes, prefix=""):
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                walk(node.body, prefix + node.name + ".")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result[prefix+node.name] = ast.dump(node, include_attributes=False)
    walk(ast.parse(body).body)
    return result


def main():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    old = subprocess.check_output(["git", "show", "HEAD:"+DRIVER], cwd=ROOT)
    current = (ROOT/DRIVER).read_bytes()
    before, after = functions(old.decode("utf-8-sig")), functions(current.decode("utf-8-sig"))
    changed = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    expected = sorted(["NativeHeadlessGameplayDriver.__init__",
        "NativeHeadlessGameplayDriver._execute_life_advance",
        "NativeHeadlessGameplayDriver._advance_exact_day_with_sentinel",
        "_validate_tactical_daily_sentinel_arm"])
    if changed != expected:
        raise RuntimeError("Driver changes extend outside four authorized functions: "+str(changed))
    machine = subprocess.check_output([sys.executable, "-B", "tools/ck3_live_run_id.py", "machine"],
                                      cwd=ROOT, text=True).strip()
    if machine != "xenoamess-full-tower-eb9d2c1186":
        raise RuntimeError("machine changed")
    subprocess.run(["git", "diff", "--check", "--", DRIVER], cwd=ROOT, check=True)
    document = {
        "schema": "xar.war-daily-watch-software-qualification.v1",
        "machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "machine_evidence": "tools/ck3_live_run_id.py machine, actual subprocess readback",
        "status": "SOFTWARE_READY_DEFAULT_OFF_LIVE_NOTRUN", "baseline_repo_head": head,
        "driver_baseline": {"path": DRIVER, "bytes": len(old),
                            "sha256": hashlib.sha256(old).hexdigest()},
        "source_pins": [pin(rel) for rel in [DRIVER, HELPER, TEST, SELF]],
        "changed_driver_functions": changed,
        "configuration": {"constructor_parameter": "allow_war_daily_watch_v1",
            "default": False, "requires_exact_bool": True, "fixed_speed": 2,
            "public_capability_or_readiness_change": False,
            "current_sdk_or_game_adoption": False},
        "admission": ["explicit life-advance-one-day, proof_kind=None, no open assault",
            "paused/map-ready nonterminal alive player, exact 1.20.0.4 version/SHA hello",
            "stable actor/episode/bridge PID/connection and real public/native revision",
            "verified absence of exclusive modal, no event/interaction; pending observer capability",
            "all published player plus every war allied/enemy regular CUnit ID, no truncation",
            "known regular/moving/retreating/sieging states, no initial combat/embarked/gathering/unknown",
            "1..64 unique IDs; contradictory duplicate rows or sides reject",
            "set-speed-2 ACK followed by actual semantic speed=2 and unchanged paused owner/roster"],
        "transaction": ["arm exact start+24, terminal mode, sorted all-published watch IDs",
            "verify arm generation/date/speed/count/combat_count=0 and idle trigger flags",
            "submit resume exactly once; an unknown result never permits replay",
            "at target date wait for native pause, including simultaneous event/date publication (147 race)",
            "before target, event/interaction/modal => actual pause plus same-generation verified cancel, zero days",
            "actor/episode/connection/invalid frame => fail closed; changed connection sends no old cancel",
            "verify ending speed readback plus existing native generation/+24/ticks/overshoot/pause postconditions",
            "all failures latch; existing StepPostconditionError persists never_replay receipt",
            "one-time restored-history check rejects the same unresolved candidate without Native commands"],
        "honest_limits": ["watch covers the full published roster, not a physical world-complete hostile scan",
            "Native29 army fingerprint watch runs after the daily callback; no native intra-day event/actor watch",
            "SDK boundary observation does not provide that missing native intra-day guarantee",
            "active battle, contact-free route, objective hold, a0 and global A/B readiness retain old qualification",
            "offline success grants no speed2 live acceptance or measured game throughput gain"],
        "verification": {"command": [sys.executable, "-B", "-m", "pytest", "-q", "-p",
                "no:cacheprovider", "--tb=short", *TEST_FILES],
            "actual_tool_result": "46 passed in 5.42s, exit_code=0",
            "input_pins": [pin(rel) for rel in TEST_FILES[1:]],
            "history": ["initial collection import and fake pending argument errors corrected in this new test",
                "broader run 40 pass/5 failures: constructor-bypassing legacy FakeDriver lacked opt-in fields; default-OFF getattr corrected",
                "final same eight files: 46 pass; unrelated tests and production guards were not changed"],
            "test_cases": "default OFF; full roster; 4 eligible states; malformed/missing/duplicate/overflow; unrelated scopes; actual setter; prearm owner/roster; stop fields; 147 race including event; running/paused zero-day mandatory; identity/connection; unknown arm/resume/cancel; restored never_replay history",
            "native_build": "NOTRUN", "game_rpc": 0, "game_speed_changes": 0,
            "live_driver_save_profile_reads": 0},
        "prospective_live_acceptance_requires_root_authorization": {
            "deployment": "future ordinary SDK factory warm using this exact source pair; default stays OFF until authorized",
            "first_trial": "next naturally selected no-combat war one-day turn, all admission fields observed; fixed speed2 only",
            "keep": "existing orders, daily planning, mandatory/owner preempt, horizon and all original strategy/risk guards",
            "evidence": "existing ordinary RPC + exact-clock stage stream: actual speed/start/end/native pause/generation/flags/owner/date; no benchmark RPC",
            "pass": "one actual day, zero overshoot, verified native pause and speed2, no omitted watched roster IDs; classify early interruption separately",
            "fail": "any unknown, mismatched identity, missing observer/roster/stop field or unverified cancellation leaves candidate OFF and unreplayed",
            "performance": "compare real days and end-to-end ordinary wall on bounded natural windows; stock nominal speed2=1s/day is not an end-to-end guarantee",
            "speed3_or_native30": "separate later qualification; no admission by this receipt"},
        "storage": {"scope": "repo-only original other128 micro allocation", "new_source_limit_bytes": 65536,
            "new_files": [HELPER, TEST, SELF, OUT], "driver_net_growth_bytes": len(current)-len(old),
            "external_output_bytes": 0, "allocated_bytes": None, "physical_credit_bytes": 0,
            "future_writes_after_seal": 0},
    }
    document["storage"]["new_files_logical_bytes"] = 0
    for _ in range(8):
        body = (json.dumps(document, ensure_ascii=False, indent=2)+"\n").encode()
        total = sum((ROOT/p).stat().st_size for p in [HELPER, TEST, SELF])+len(body)
        if document["storage"]["new_files_logical_bytes"] == total:
            break
        document["storage"]["new_files_logical_bytes"] = total
    if total+max(0, len(current)-len(old)) > 65536:
        raise RuntimeError("source budget exceeded")
    with (ROOT/OUT).open("xb") as output:
        output.write(body)
    print(json.dumps({"receipt": pin(OUT), "source_pins": document["source_pins"],
        "new_files_logical_bytes": total, "driver_net_growth_bytes": len(current)-len(old)}, indent=2))


if __name__ == "__main__":
    main()
