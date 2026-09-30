"""Validate the fixed capture adapter's actual disk binding; never start CK3."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
OUT = Path("C:/Users/1/ck3-a04-mechanism-evidence-20261001/knights-attempt-02")
CAPTURE = Path("C:/w/ep2a04/promo/ck3_native_war_ai/integration/capture_session.py")
NEW = Path("C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-nextday-live-20261001-a01")
OLD = Path("C:/Users/1/ck3-a04-mechanism-evidence-20261001/knights-nextday-live-attempt-01")
RAW = Path("D:/workspace/ck3_native_war_ai_promo_work")
SOURCE = RAW / "episode01-paired-counter-trace-attempt-010/d26-immutable.ck3"
RECEIPT = RAW / "episode01-paired-counter-trace-attempt-010/ck3-output/interactive-requests-responses/d26-save.json"
GUI = RAW / "episode02-e2-04-d05-screen-lease-20260928-a04/native-ui-saved-settings-a01.pdx.txt"
GUI_RECEIPT = RAW / "episode02-e2-04-d05-screen-lease-20260928-a04/native-ui-saved-settings-a01.json"

def ident(path):
    code = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(code), "sha256": hashlib.sha256(code).hexdigest().upper()}

def write_new(path, val):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(val, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

sys.path.insert(0, str(CAPTURE.parent))
spec = importlib.util.spec_from_file_location("fixed_a04_capture_binding", CAPTURE)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)
checkpoint = capture.checkpoint_source(SOURCE, RECEIPT)

def namespace(root, state_name="ck3-state", output_name="ck3-output", output_parent=None):
    return argparse.Namespace(
        state_dir=root / state_name, output_dir=(output_parent or root) / output_name,
        checkpoint_save=SOURCE, checkpoint_receipt=RECEIPT,
        import_a04_ui_gui_100=True, gui_scale="1.0", record_debug_desktop=False,
        a04_ui_settings_snapshot=GUI, a04_ui_preservation_receipt=GUI_RECEIPT)

cases = [
    ("actual_new_source_state_output", namespace(NEW), checkpoint, True),
    ("previous_invalid_parent_and_prefix", namespace(OLD), checkpoint, False),
    ("wrong_state_name", namespace(NEW, state_name="profile-state"), checkpoint, False),
    ("foreign_output_parent", namespace(NEW, output_parent=OUT), checkpoint, False),
    ("wrong_source_actor", namespace(NEW), {**checkpoint, "actor": 33437}, False),
]
results = []
for name, args, source, expected in cases:
    try:
        binding = capture.bind_a04_ui_target(args, source)
        accepted, error = True, None
    except RuntimeError as exc:
        binding, accepted, error = None, False, str(exc)
    results.append({"name": name, "state_dir": str(args.state_dir), "output_dir": str(args.output_dir),
                    "expected_accepted": expected, "accepted": accepted, "error": error,
                    "binding": binding, "passed": accepted == expected})
gui_binding = capture.validate_a04_ui_gui_source_binding(namespace(NEW), checkpoint)
help_argv = [sys.executable, str(CAPTURE), "--help"]
with (OUT / "capture-root-binding-help.stdout.log").open("xb") as stdout, (OUT / "capture-root-binding-help.stderr.log").open("xb") as stderr:
    result = subprocess.run(help_argv, stdout=stdout, stderr=stderr, check=False)
if result.returncode != 0:
    raise RuntimeError("Actual capture --help failed")
report = {"schema": "ck3.a04.knights.capture-root-binding-offline.v1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
          "disk_binding_only": True, "ck3_launches": 0, "desktop_inputs": 0, "not_run": True,
          "capture_source": ident(CAPTURE), "exact_checkpoint": checkpoint, "new_run_root": str(NEW),
          "new_root_created": False, "cases": results, "gui_source_binding": gui_binding,
          "actual_help": {"argv": help_argv, "returncode": result.returncode,
                          "stdout": ident(OUT / "capture-root-binding-help.stdout.log"),
                          "stderr": ident(OUT / "capture-root-binding-help.stderr.log")},
          "passed": all(row["passed"] for row in results),
          "limits": ["No native/desktop freshness or runtime GUI acceptance was tested", "No new live run ID exists"]}
REPORT_PATH = OUT / "capture-root-binding-offline.json"
write_new(REPORT_PATH, report)
if not report["passed"]:
    raise RuntimeError("Offline capture binding case failed")

plan_path = HERE / "capture-nextday-plan.json"
old_bytes = plan_path.read_bytes()
with (OUT / "capture-nextday-plan-before-root-binding-fix.json").open("xb") as stream:
    stream.write(old_bytes)
plan = json.loads(old_bytes)
def migrate(value):
    if isinstance(value, str):
        return value.replace(str(OLD), str(NEW)).replace(OLD.as_posix(), NEW.as_posix())
    if isinstance(value, dict):
        return {key: migrate(val) for key, val in value.items()}
    if isinstance(value, list):
        return [migrate(val) for val in value]
    return value
plan = migrate(plan)
plan["corrected_at_utc"] = datetime.now(timezone.utc).isoformat()
plan["capture_root_admission"] = {"actual_callable": "capture_session.bind_a04_ui_target(args, checkpoint)",
    "parent": str(NEW.parent), "checker_prefix": "episode02-e2-05-d26-nextday-live-",
    "adapter_track_prefix": "episode02-e2-05-d26-", "state_dir": str(NEW / "ck3-state"),
    "output_dir": str(NEW / "ck3-output"), "userdir": str(NEW / "ck3-state/profile"),
    "offline_validation": ident(REPORT_PATH), "no_gui_contract_bypass": True}
plan["source_reuse"]["checker"] = ident(HERE / "check_nextday_saved_status.py")
plan["source_reuse"]["gui_settings_snapshot"] = ident(GUI)
plan["source_reuse"]["gui_preservation_receipt"] = ident(GUI_RECEIPT)
plan["source_reuse"]["root_binding_validation"] = ident(REPORT_PATH)
plan["source_reuse"]["checker_validation"] += "; root admission aligned with actual capture adapter; 5 disk binding cases and full frozen GUI source binding passed offline"
args = plan["sequence"][1]["capture_cli_argv_template"]
insert = args.index("--enable-private-phase-trace")
args[insert:insert] = ["--import-a04-ui-gui-100", "--a04-ui-settings-snapshot", str(GUI),
                     "--a04-ui-preservation-receipt", str(GUI_RECEIPT), "--interactive-seconds", "3600"]
insert = args.index("--capture")
args[insert:insert] = ["--screen-task-id", "<actual-new-screen-task-id>",
                     "--screen-expected-sequence", "<fresh-task-last-sequence>",
                     "--screen-cli-sha256", "<identical-source-installed-CAS-CLI-SHA256>"]
plan["sequence"][1]["action"] += " Import only the exact reviewed 54-byte GUI block using actual supported flags and actual source files; retain the independent screen-task lease parameters required by --capture."
plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"passed": report["passed"], "binding_cases": len(results), "gui_source_binding": "PASSED_DISK_ONLY",
                  "new_run_root": str(NEW), "new_live_run_id": None, "ck3_launches": 0}))
