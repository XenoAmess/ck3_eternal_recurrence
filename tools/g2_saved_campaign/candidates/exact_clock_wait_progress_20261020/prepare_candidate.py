"""RAM-only bounded wait diagnostic over the exact immutable Source24 tree."""
from __future__ import annotations
import hashlib
import subprocess
import ast
import difflib
from pathlib import Path

COMMIT = "6b55531b1d3a44ee73ab13ea40132556030f682e"
PREFIX = "ck3_autonomous_player/src/xar_autoplayer/bridge/"
PINS = {
    "native_driver.py": (1642169, "2d3fe6a71d8ee15e924446986fae4e27fe00ea59cc86baa31d1c79b11da2acc8"),
    "exact_clock_failure_diagnostic_v1.py": (6624, "8bf4dc3413fae7634999e3bd1b3509c2b9f2b9a58e0a13ee1abb7a477c52276f"),
    "clock_observation_timing_v1.py": (11099, "34ffbd45381675db60faeb0e36146508cd6234465690d48d7a507ef40e29bda0"),
}


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def read_inputs():
    result = {}
    for name, (size, digest) in PINS.items():
        raw = subprocess.run(["git", "show", COMMIT + ":" + PREFIX + name],
                             check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError("exact Source24 input differs: " + name)
        result[name] = raw
    return result


DRIVER_HUNKS = (
    ('''        frame_type = self.state.ingest(frame)
        if frame_type == "hello":
''', '''        frame_type = self.state.ingest(frame)
        progress = getattr(self, "_exact_clock_wait_progress_v1", None)
        if progress is not None and frame_type in {"heartbeat", "hello"}:
            try:
                # ingest() returned outside its Condition. Copy only this token;
                # never hold the transport Condition while taking collector.lock.
                with self.state._condition:
                    token = (self.state._connected, self.state._connection_generation,
                             (self.state._hello or {}).get("pid"))
                progress.received(frame_type, frame, token)
            except Exception:
                try:
                    progress.note_callback_error()
                except Exception:
                    pass
        if frame_type == "hello":
'''),
    ('''            self.state.mark_disconnected()
        finally:
''', '''            self.state.mark_disconnected()
            progress = getattr(self, "_exact_clock_wait_progress_v1", None)
            if progress is not None:
                try:
                    progress.boundary()
                except Exception:
                    pass
        finally:
'''),
    ('''            changed = self.take_internal_semantic_snapshot()
            if getattr(self, "_exact_clock_observation_v1", None) is not None:
''', '''            changed = self.take_internal_semantic_snapshot()
            progress = getattr(self, "_exact_clock_wait_progress_v1", None)
            if progress is not None:
                try:
                    progress.observe_candidate(changed)
                except Exception:
                    try:
                        progress.note_callback_error()
                    except Exception:
                        pass
            if getattr(self, "_exact_clock_observation_v1", None) is not None:
'''),
    ('''            clock_observation = start_clock_observation_v1(self, current)
''', '''            wait_progress = wait_progress_summary = None
            try:
                from .exact_clock_wait_progress_v1 import (
                    start_wait_progress_v1, finish_wait_progress_v1,
                )
                wait_progress = start_wait_progress_v1(self, current, arm_status["generation"])
            except Exception:
                pass
            clock_observation = start_clock_observation_v1(self, current)
'''),
    ('''                finish_clock_observation_v1(self, clock_observation, current)
''', '''                try:
                    wait_progress_summary = finish_wait_progress_v1(self, wait_progress, current) if wait_progress is not None else None
                except Exception:
                    pass
                finish_clock_observation_v1(self, clock_observation, current)
'''),
    ('''                        cleanup_start=diagnostic_cleanup_start,
''', '''                        cleanup_start=diagnostic_cleanup_start,
                        wait_progress=wait_progress_summary,
'''),
)
DTO_HUNKS = (
    ('import json\n', 'import json\nfrom .exact_clock_wait_progress_v1 import project_wait_progress_v1\n'),
    ('SCHEMA = "xar.exact-day-clock-failure.v1"', 'SCHEMA = "xar.exact-day-clock-failure.v2"'),
    ('"cleanup_before_pause_frame", "before_cleanup_actions", "cleanup_actions", "truncated")',
     '"cleanup_before_pause_frame", "before_cleanup_actions", "cleanup_actions", "truncated", "wait_progress")'),
    ('actions, action_start, cleanup_start):', 'actions, action_start, cleanup_start, wait_progress=None):'),
    ('"truncated": False,\n', '"truncated": False, "wait_progress": project_wait_progress_v1(wait_progress),\n'),
    ('        encoded = _encode({key: value[key] for key in _DIAGNOSTIC})\n',
     '        result = {key: value[key] for key in _DIAGNOSTIC}\n'
     '        result["wait_progress"] = project_wait_progress_v1(value["wait_progress"])\n'
     '        encoded = _encode(result)\n'),
)


def transfer(raw, hunks, *, inverse=False):
    for before, after in reversed(hunks) if inverse else hunks:
        before, after = (after, before) if inverse else (before, after)
        before, after = before.encode(), after.encode()
        if raw.count(before) != 1:
            raise ValueError("exact unique patch anchor differs")
        raw = raw.replace(before, after, 1)
    return raw


def functions(raw):
    result = {}
    def visit(nodes, prefix=""):
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                visit(node.body, prefix + node.name + ".")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                result[prefix + node.name] = ast.dump(node, include_attributes=False)
    visit(ast.parse(raw).body)
    return result


def compose(inputs):
    for name, (size, digest) in PINS.items():
        if len(inputs[name]) != size or hashlib.sha256(inputs[name]).hexdigest() != digest:
            raise ValueError("immutable Source24 preimage differs: " + name)
    driver = transfer(inputs["native_driver.py"], DRIVER_HUNKS)
    dto = transfer(inputs["exact_clock_failure_diagnostic_v1.py"], DTO_HUNKS)
    for name, value, hunks in (("native_driver.py", driver, DRIVER_HUNKS),
                               ("exact_clock_failure_diagnostic_v1.py", dto, DTO_HUNKS)):
        if transfer(value, hunks, inverse=True) != inputs[name]:
            raise ValueError("whole immutable input inverse differs")
    before, after = functions(inputs["native_driver.py"]), functions(driver)
    changed = {k for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
    expected = {"NativeHeadlessGameplayDriver." + n for n in (
        "_ingest", "_mark_bridge_disconnected_v1", "_wait_for_life_advance_change", "_advance_exact_day_with_sentinel")}
    if changed != expected:
        raise ValueError("unowned Driver function AST changed: " + repr(changed))
    # Full state-cache/Condition implementation and wait predicate/deadline are identical.
    for name in before:
        if name.startswith("NativeProtocolState.") or name.endswith("._wait_for_life_advance_snapshot"):
            if before[name] != after[name]:
                raise ValueError("original state/wait contract changed")
    helper = Path(__file__).with_name("exact_clock_wait_progress_v1.py").read_bytes()
    outputs = {"native_driver.py": driver, "exact_clock_failure_diagnostic_v1.py": dto,
               "exact_clock_wait_progress_v1.py": helper}
    for name, value in outputs.items():
        compile(value, name, "exec", dont_inherit=True)
    diffs = []
    for name in ("native_driver.py", "exact_clock_failure_diagnostic_v1.py"):
        diffs.extend(difflib.unified_diff(inputs[name].decode().splitlines(True), outputs[name].decode().splitlines(True),
                                       fromfile="Source24/" + name, tofile="candidate/" + name, n=3))
    return outputs, "".join(diffs).encode(), sorted(changed)
