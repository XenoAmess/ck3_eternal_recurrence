"""Apply only common continuity accounting to a new, not-running feeder."""
from pathlib import Path
import argparse
import ast
import hashlib


SUPPORT = '''
CONTINUITY_WINDOW = N / "ROOT-CONTINUITY-WINDOW.json"


def continuity_attach(verified):
    ledger = WindowLedger(CONTINUITY_WINDOW)
    prior = ledger.load()
    if prior is None:
        raise ValueError("Root must initialize the prepared continuity window from the blocking failure")
    return ledger.apply("attach_verified", {
        "evidence_id": "verified-bootstrap:" + str(MARKER), "source": pin(MARKER),
        "game": read(N / "ROOT-ACTUAL-GAME-LAUNCH.json"),
        "frame": verified["actual_baseline_frame"], "completed_cycles": BASELINE_CYCLES})


def continuity_settled(kind, sequence, result=None, response=None):
    if result is None:
        state_path = Q / "ROOT-CUMULATIVE-LOOP-STATE.json"
        settled = read(state_path)
        details = {"evidence_id": kind + ":" + str(Q) + ":" + str(sequence),
            "source": pin(state_path), "date_raw": settled["before"]["date_raw"],
            "completed_cycles": settled["completed_cycles"], "frame": settled["before"]}
    else:
        details = {"evidence_id": "settled-batch:" + str(response), "source": pin(response),
            "date_raw": result["actual_end_date_raw"], "completed_cycles": result["cumulative_cycles"]}
    return continuity_summary(WindowLedger(CONTINUITY_WINDOW).apply(kind, details))


def continuity_interrupted(reason, source):
    state_path = Q / "ROOT-CUMULATIVE-LOOP-STATE.json"
    settled = read(state_path)
    return continuity_summary(WindowLedger(CONTINUITY_WINDOW).apply("repair_required", {
        "evidence_id": "manual-repair:" + str(source),
        "source": {"settled_state": pin(state_path), "failure": pin(source) if Path(source).is_file() else str(source)},
        "frame": settled["before"], "completed_cycles": settled["completed_cycles"],
        "reason": str(reason)[:2048]}))


'''


def adapt(text):
    if "from root_continuity_window import" in text:
        raise ValueError("continuity already adapted; do not apply twice")
    def replace(before, after, expected=1):
        nonlocal text
        if text.count(before) != expected:
            raise ValueError("exact feeder span missing: " + before[:120])
        text = text.replace(before, after)
    replace("START_RAW = 53144328\nTARGET_DAYS = 30 * 365.25", "from root_continuity_window import WindowLedger, summary as continuity_summary, pin")
    replace('        "campaign_start_raw": START_RAW,\n        "campaign_target_days": TARGET_DAYS,',
        '        "continuity_window": continuity_summary(WindowLedger(CONTINUITY_WINDOW).load()) if CONTINUITY_WINDOW.exists() else None,')
    replace("def main(first_control: int) -> None:\n    admitted()", SUPPORT + "def main(first_control: int) -> None:\n    continuity_attach(admitted())")
    replace('        elapsed_days = (date_raw - START_RAW) / 24\n        if elapsed_days >= TARGET_DAYS:\n            status("thirty_year_date_reached_review_required", control_sequence=sequence,',
        '        stable = continuity_settled("settled_batch", sequence, result, response)\n        elapsed_days = stable["elapsed_days"]\n        if stable["target_reached"]:\n            status("thirty_year_stability_window_completed", continuity_window=stable, control_sequence=sequence,')
    replace('            status("halted_review_required", control_sequence=sequence,',
        '            interrupted = continuity_interrupted(str(error), response)\n            status("halted_review_required", continuity_window=interrupted, control_sequence=sequence,')
    replace('            status("campaign_terminal_review_required", control_sequence=sequence,',
        '            interrupted = continuity_interrupted(result.get("reason", "campaign terminal requires intervention"), response)\n            status("campaign_terminal_review_required", continuity_window=interrupted, control_sequence=sequence,')
    # A batch ending in a new intervention must invalidate the window before
    # any success check, including a date landing exactly on the goal.
    terminal_start = text.index('        if result.get("same_SDK_continuation_available") is not True:', text.index('        stable = continuity_settled'))
    terminal_end = text.index('        following = result["next_sequence"]', terminal_start)
    terminal = text[terminal_start:terminal_end].replace("elapsed_days=elapsed_days", 'elapsed_days=interrupted["elapsed_days"]')
    text = text[:terminal_start] + text[terminal_end:]
    text = text.replace('        stable = continuity_settled', terminal + '        stable = continuity_settled', 1)
    # Each existing automatic recovery path remains unchanged. Only append its
    # settled observation; no reset, action, retry, or successful FULL claim.
    replace('                following, settled = recovered_readonly\n',
        '                following, settled = recovered_readonly\n                continuity_settled("automatic_recovery", sequence)\n', expected=2)
    replace('                following, settled = recovered\n',
        '                following, settled = recovered\n                continuity_settled("automatic_recovery", sequence)\n', expected=2)
    replace('                following, settled = recovered_construction\n',
        '                following, settled = recovered_construction\n                continuity_settled("automatic_recovery", sequence)\n')
    replace('        status("following_actual_control", control_sequence=following,',
        '        status("following_actual_control", continuity_window=stable, control_sequence=following,')
    # Failed wrapper or Python feeder errors requiring human repair invalidate
    # the window. Normal Root STOP/SDK close branches are untouched.
    replace('    except Exception as error:\n        status("feeder_error_review_required",',
        '    except Exception as error:\n        if CONTINUITY_WINDOW.exists():\n            continuity_interrupted(str(error), Q / "ROOT-CUMULATIVE-LOOP-STATE.json")\n        status("feeder_error_review_required",')
    tree = ast.parse(text)
    if any(isinstance(node, ast.Name) and node.id in ("START_RAW", "TARGET_DAYS") for node in ast.walk(tree)):
        raise ValueError("obsolete campaign age variable remains")
    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = adapt(args.source.read_text(encoding="utf-8-sig")).encode("utf-8")
    with args.output.open("xb") as stream:
        stream.write(result)
    print(str(args.output), hashlib.sha256(result).hexdigest())
