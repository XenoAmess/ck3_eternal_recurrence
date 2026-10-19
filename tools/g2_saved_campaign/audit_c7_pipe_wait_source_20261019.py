"""Qualify only the kernel32 binding cache against the exact C7 source leaf."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import statistics
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[2]
BASE = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
FREEZE = BASE / "robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37C7.json"
RELATIVE = "xar_autoplayer/bridge/native_driver.py"
OUTPUT = REPO / "docs/ck3-native-ai/evidence/c7-pipe-kernel32-cache-2026-10-19.json"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_exact(path, size, digest):
    before = path.stat()
    if before.st_size != size:
        raise ValueError("exact source size changed")
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or sha(raw) != digest:
        raise ValueError("exact source changed")
    return raw


freeze_raw = read_exact(FREEZE, 403018, "4c9de700f1572ad81627fe6c92cd5fec4b05cb4e02b0c4e6449bda48b32cb4d9")
freeze = json.loads(freeze_raw)
entry, = [row for row in freeze["files"] if row["relative"] == RELATIVE]
frozen_path = Path(freeze["source_root"]) / RELATIVE
old = read_exact(frozen_path, entry["bytes"], entry["sha256"])
candidate_path = REPO / "ck3_autonomous_player/src" / RELATIVE
candidate = candidate_path.read_bytes()
expected = old.replace(b"import ctypes\n", b"import ctypes\nfrom functools import lru_cache\n", 1)
expected = expected.replace(b"\ndef _kernel32():\n", b"\n@lru_cache(maxsize=1)\ndef _kernel32():\n", 1)
if candidate != expected:
    raise ValueError("candidate exceeds the exact two-line cache delta")
command = [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q",
    "-o", "pythonpath=" + (REPO / "ck3_autonomous_player/src").as_posix(),
    "ck3_autonomous_player/tests/unit/test_native_kernel32_cache.py",
    "ck3_autonomous_player/tests/unit/test_current_actor_stress_adjustment.py::ContractTests",
    "ck3_autonomous_player/tests/unit/test_current_actor_stress_adjustment.py::GetterTests"]
started = datetime.now(timezone.utc).isoformat()
tests = subprocess.run(command, cwd=REPO, capture_output=True, text=True, check=False)
finished = datetime.now(timezone.utc).isoformat()
if len(tests.stdout) + len(tests.stderr) > 8192:
    raise ValueError("unexpected test output extent; inspect without expanding this report")
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.bridge import native_driver as driver

bench = None
if tests.returncode == 0:
    driver._kernel32.cache_clear()
    cold_start = time.perf_counter_ns()
    driver._kernel32()
    cold_ns = time.perf_counter_ns() - cold_start
    loops, repeats = 1000, 5
    samples = {"original_body_uncached": [], "cached_warm": []}
    methods = {"original_body_uncached": driver._kernel32.__wrapped__, "cached_warm": driver._kernel32}
    for repeat in range(repeats):
        order = list(methods) if repeat % 2 == 0 else list(reversed(methods))
        for name in order:
            method = methods[name]
            start = time.perf_counter_ns()
            for _ in range(loops):
                method()
            samples[name].append(time.perf_counter_ns() - start)
    bench = {"calls_per_sample": loops, "repeats": repeats, "cold_initialization_ns": cold_ns,
        "sample_elapsed_ns": samples,
        "median_ns_per_call": {name: statistics.median(values) / loops for name, values in samples.items()},
        "cache_info_after": driver._kernel32.cache_info()._asdict(),
        "limit": "Only same-body DLL-wrapper initialization versus warm lookup, no pipe/handles/Game. Elapsed, not CPU. No live-RPC or seconds-per-game-day benefit measured."}
    driver._kernel32.cache_clear()
test_path = REPO / "ck3_autonomous_player/tests/unit/test_native_kernel32_cache.py"
producer_path = Path(__file__).resolve()
result = {
    "schema": "xar.ck3.kernel32-binding-cache-source-qualification/v1",
    "machine_id": freeze["machine_id"], "observed_at_utc": datetime.now(timezone.utc).isoformat(),
    "status": "OFFLINE_PASS_NOT_ADOPTED" if tests.returncode == 0 else "OFFLINE_RED",
    "freeze": {"path": str(FREEZE), "bytes": len(freeze_raw), "sha256": sha(freeze_raw),
               "observed_at_utc": freeze["at_utc"], "business_source_commit": freeze["business_source_commit"]},
    "frozen_driver": {"path": str(frozen_path), "bytes": len(old), "sha256": sha(old)},
    "candidate_driver": {"path": str(candidate_path), "bytes": len(candidate), "sha256": sha(candidate),
                         "net_added_bytes": len(candidate) - len(old), "exact_import_and_decorator_delta": True},
    "source_audit_C7_1based": {
        "1490,1623-1654": "Default10ms poll only when header/body incomplete; ready frames have no unconditional sleep. Actual poll setting/arrival time and added detection delay not measured.",
        "1545-1564,36227-36250": "One JSON encode/packet send; final I/O uses buffer copies. Reader consumes complete packet once then decodes/parses once; no finished-result file polling.",
        "1192-1225,1386-1394,2189-2190": "Command result shallow-stored, condition notified; waiter wakes and pops once. No sleep or file reread in result publication path.",
        "1377-1384,25804-25844": "Public snapshot wait is condition-based; existing revision/predicate/timeout guards retained.",
        "12417-12425,14989-14995,15081-15085": "Route uses internal semantic snapshot, already omits transcript; separate post-result frame read enforces freshness and is retained.",
        "36150-36192": "Old helper creates WinDLL and binds8 API signatures on every call. Added maxsize1 cache retains only the wrapper/function bindings; all I/O calls remain outside it."},
    "source_change_boundary": "No cache of handles, process IDs, payloads, results, timestamps, errors or qualifications; use_last_error=True and every get/set_last_error call unchanged. LRU may initialize twice under a simultaneous cold miss; no global once-only/concurrency claim.",
    "tests": {"command": command, "started_at_utc": started, "finished_at_utc": finished,
              "returncode": tests.returncode, "stdout": tests.stdout, "stderr": tests.stderr,
              "coverage": "4 cache cases plus existing transport-mocked ContractTests/GetterTests; binding signatures/call values, failure not cached, isolated mock caches, fresh read/write/errno."},
    "earlier_broader_attempt": {"source": "exec tool chunk a0996a,2026-10-19; actual output retained in task transcript",
        "command_scope": "new cache test plus entire test_current_actor_stress_adjustment.py",
        "passed": 22, "failed": 5, "exit_code": 1,
        "failures": "3ProfileTests: fixture NativeProfileService lacks driver;2SchemaTests: tool count189!=158 and same missing driver. Not repaired; baseline full-file rerun not performed, not labelled verified pre-existing failures."},
    "earlier_launcher_failure": {"sources": ["exec tool chunk a03fa1", "exec tool chunk 8d2679", "exec tool chunk 4d2822"], "exit_code_each": 4,
        "reason": "Narrow node-ID collection lacked source import path; relative and Windows-backslash pytest overrides did not resolve it. Use exact absolute forward-slash path via pytest local configuration; no business source change."},
    "helper_microbench": bench,
    "closed_wartime_reference": {"path": "docs/ck3-native-ai/evidence/c7-first-war-native-timing-2026-10-19.json",
        "sha256": "fecd4f9710fbcf4d7ac47e577d409d3ff9f63870cd9d0ff1ccfd7e8546bdbb2f",
        "limit": "Route whole RPC4.2767402s versus14preview pipe spans0.3235843s and Army RPC0.3919289s versuspipe0.2488295s/read+serialize0.0909801s. These do not measure initialization share or prove Native CPU/world-scan bottlenecks."},
    "publication_copy_or_sleep_cost_elsewhere_ns": None,
    "actions": {"game": 0, "live_rpc": 0, "native_compile": 0, "new_exe": 0, "runtime_or_C7_changes": 0,
                "environment_changes": 0, "raw_body_or_live_driver_reads": 0, "speed_or_horizon_changes": 0},
    "storage": {"admitted_repo_micro_bytes": 49152, "new_leaves": [
        {"path": str(path.relative_to(REPO)), "bytes": path.stat().st_size, "sha256": sha(path.read_bytes())}
        for path in (test_path, producer_path)],
        "allocated_bytes": None, "physical_credit_bytes": 0, "future_writes_after_close": 0,
        "review_at_utc": "2026-10-20T01:48:56.993837+00:00"},
}
raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
if len(raw) > 12 * 1024:
    raise ValueError("source report exceeds bound")
OUTPUT.write_bytes(raw)
print(json.dumps({"path": str(OUTPUT), "bytes": len(raw), "sha256": sha(raw),
                  "tests_exit": tests.returncode, "tests_stdout": tests.stdout,
                  "helper_bench": bench, "candidate_sha256": sha(candidate),
                  "repo_package_new_logical_bytes": len(raw) + test_path.stat().st_size + producer_path.stat().st_size,
                  "driver_net_added_bytes": len(candidate) - len(old)}, ensure_ascii=True))
raise SystemExit(tests.returncode)
