"""Exact f198 RAM patch and inverse; creates only the two candidate leaves."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
BASE = "f19864de1cc073eed62617faad2307c57ad45a97"
PINS = {
    "native_driver.py": (1637048, "cc60c9af670c37ef2085f66d07db17a2bd309660fcb60c05a5340df7720874ab"),
    "mcp_server.py": (264359, "8b1c260f779dbd3e25770af75ed87de0cfd39200454c7662f611accfce92688f"),
}
PREFIX = "ck3_autonomous_player/src/xar_autoplayer/bridge/"
DRIVER_EDITS = [
    ("        cancel_attempted = False\n        try:\n            from .exact_day_speed_configuration_v1",
     "        cancel_attempted = False\n        clock_stop_not_observed = False\n        diagnostic_action_start = len(actions)\n        try:\n            from .exact_day_speed_configuration_v1"),
    ('            if current.get("paused") is not True:\n                raise BridgeUnavailableError("exact-day native clock did not stop the map")',
     '            if current.get("paused") is not True:\n                clock_stop_not_observed = True\n                raise BridgeUnavailableError("exact-day native clock did not stop the map")'),
    ("        except Exception as original_error:\n            try:\n                cleanup_frame = self.take_internal_semantic_snapshot()",
     "        except Exception as original_error:\n            cleanup_frame = None\n            diagnostic_cleanup_start = len(actions)\n            try:\n                cleanup_frame = self.take_internal_semantic_snapshot()"),
    ('                    }) from original_error\n            raise\n\n    def _resume_life_advance(',
     '                    }) from original_error\n            if clock_stop_not_observed:\n                from .exact_clock_failure_diagnostic_v1 import build_exact_clock_failure_v1\n\n                diagnostic = build_exact_clock_failure_v1(\n                    original_error=original_error, starting_date_raw=starting_date_raw,\n                    target_date_raw=target_date_raw, speed=speed, arm_status=arm_status,\n                    starting=starting, last_frame=current, cleanup_before_frame=cleanup_frame,\n                    actions=actions, action_start=diagnostic_action_start,\n                    cleanup_start=diagnostic_cleanup_start,\n                )\n                raise StepPostconditionError(\n                    str(original_error), selected_step="life-advance-one-day",\n                    step_result=diagnostic,\n                ) from original_error\n            raise\n\n    def _resume_life_advance('),
]
_old_diagnostic_block = '''                from .exact_clock_failure_diagnostic_v1 import build_exact_clock_failure_v1

                diagnostic = build_exact_clock_failure_v1(
                    original_error=original_error, starting_date_raw=starting_date_raw,
                    target_date_raw=target_date_raw, speed=speed, arm_status=arm_status,
                    starting=starting, last_frame=current, cleanup_before_frame=cleanup_frame,
                    actions=actions, action_start=diagnostic_action_start,
                    cleanup_start=diagnostic_cleanup_start,
                )
'''
_safe_diagnostic_block = '''                try:
                    from .exact_clock_failure_diagnostic_v1 import build_exact_clock_failure_v1

                    diagnostic = build_exact_clock_failure_v1(
                        original_error=original_error, starting_date_raw=starting_date_raw,
                        target_date_raw=target_date_raw, speed=speed, arm_status=arm_status,
                        starting=starting, last_frame=current, cleanup_before_frame=cleanup_frame,
                        actions=actions, action_start=diagnostic_action_start,
                        cleanup_start=diagnostic_cleanup_start,
                    )
                except Exception:
                    raise original_error
'''
_old, _new = DRIVER_EDITS[-1]
if _new.count(_old_diagnostic_block) != 1:
    raise ValueError("diagnostic patch declaration is inconsistent")
DRIVER_EDITS[-1] = (_old, _new.replace(_old_diagnostic_block, _safe_diagnostic_block))
MCP_EDITS = [
    ('            diagnostic = construction_transport_diagnostic(error)\n            diagnostic_key = "construction_transport_v1"\n            if diagnostic is None:\n                diagnostic = _native_command_rejection_diagnostic(error)',
     '            from .exact_clock_failure_diagnostic_v1 import exact_clock_failure_diagnostic_v1\n\n            diagnostic = exact_clock_failure_diagnostic_v1(error)\n            diagnostic_key = "exact_day_clock_failure_v1"\n            if diagnostic is None:\n                diagnostic = construction_transport_diagnostic(error)\n                diagnostic_key = "construction_transport_v1"\n            if diagnostic is None:\n                diagnostic = _native_command_rejection_diagnostic(error)'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def original(name):
    data = subprocess.check_output(["git", "show", f"{BASE}:{PREFIX}{name}"], cwd=REPO)
    size, digest = PINS[name]
    if len(data) != size or sha(data) != digest:
        raise ValueError(f"wrong f198 blob: {name}")
    return data


def transform(data, edits, reverse=False):
    text = data.decode("utf-8")
    for old, new in (reversed(edits) if reverse else edits):
        old, new = (new, old) if reverse else (old, new)
        if text.count(old) != 1:
            raise ValueError("exact hunk occurrence is not one")
        text = text.replace(old, new, 1)
    return text.encode("utf-8")


def function_node(data, name):
    found = [n for n in ast.walk(ast.parse(data)) if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(found) != 1:
        raise ValueError(f"nonunique function {name}")
    return found[0]


def prepare():
    result = {}
    pending = []
    for name, edits in (("native_driver.py", DRIVER_EDITS), ("mcp_server.py", MCP_EDITS)):
        before = original(name)
        after = transform(before, edits)
        if transform(after, edits, reverse=True) != before:
            raise ValueError("inverse differs from full original blob")
        compile(after, name, "exec")
        # Exact string inverse protects the full Source20/sharedbudget/MCP blob;
        # the AST name identifies the sole changed behavior span for composition.
        owner = "_advance_exact_day_with_sentinel" if name == "native_driver.py" else "ck3_auto_turn"
        function_node(before, owner)
        function_node(after, owner)
        path = ROOT / "xar_autoplayer" / "bridge" / name
        result[name] = {"path": str(path), "before_bytes": len(before), "before_sha256": sha(before),
                        "after_bytes": len(after), "after_sha256": sha(after),
                        "inverse_full_blob_equal": True, "owner_function": owner}
        if path.exists():
            raise FileExistsError(path)
        pending.append((path, after))
    existing = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
    if existing + sum(len(data) for _, data in pending) + 65536 > 2097152:
        raise ValueError("full candidate plus 64KiB tests/proof reserve exceeds cap")
    for path, after in pending:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(after)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    prepare()
