"""Create a new comparator for saved second versus recovered third prefixes."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
original = (ROOT / "compare_callback_prefixes.py").read_text(encoding="utf-8")
updated = original.replace('FIRST = ROOT / "first-prefix-001"', 'FIRST = ROOT / "after-callback-prefix-002"', 1)
updated = updated.replace('SECOND = ROOT / "after-callback-prefix-002"', 'SECOND = ROOT / "after-sign-and-first-join-prefix-recovery-004"', 1)
updated = updated.replace('OUTPUT = ROOT / "compare-first-to-after-callback-001"', 'OUTPUT = ROOT / "compare-second-to-recovered-third-001"', 1)
start = updated.index('              "parent_reported_callbacks": [')
end = updated.index('              "callback_execution_independently_inspected_by_this_log_reader"', start)
updated = updated[:start] + '''              "parent_reported_callbacks": [
                  {"request": "0027", "reported_behavior": "First ordinary JOIN commit; exact time not supplied to this reader"},
                  {"request": "0050", "reported_behavior": "DETACH source signing in lyd.220; exact time not supplied to this reader"}],
''' + updated[end:]
# The complete JSONL line ledger retains every new E. Avoid duplicating 99k E
# rows into the summary report, which still counts all actual E separately.
updated = updated.replace('if tokens or row["e_header"]:', 'if tokens:', 1)
target = ROOT / "compare_second_to_recovered_third.py"
with target.open("x", encoding="utf-8") as stream:
    stream.write(updated)
completed = subprocess.run([sys.executable, "-B", str(target)], cwd=ROOT, capture_output=True, check=False)
for suffix, payload in (("stdout.log", completed.stdout), ("stderr.log", completed.stderr)):
    with (ROOT / ("third-comparison-command." + suffix)).open("xb") as stream:
        stream.write(payload)
print(completed.stdout.decode("utf-8", errors="replace"))
if completed.returncode:
    print(completed.stderr.decode("utf-8", errors="replace"))
raise SystemExit(completed.returncode)
