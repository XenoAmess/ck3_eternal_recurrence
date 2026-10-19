"""Pure source hooks and an opt-in normal-Queue binder; no SDK/Game loader.

Qualification is software only. The owner supplies already-read admission,
exact source digests and its existing create-only atomic writer. No artifact
enumeration, Native observation or business retry is added by this module.
"""
from __future__ import annotations

import ast
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys

from queue_control_timing_v1 import QueueControlTimingV1


_ACTIVE = ContextVar("queue_control_timing_v1", default=None)
ADMISSION_SCHEMA = "xar.ck3.queue-control-timing-admission/v1"


def _note(probe, error):
    notes = getattr(probe, "_adapter_diagnostics", None)
    if notes is None:
        notes = probe._adapter_diagnostics = []
    if len(notes) < 16:
        notes.append((type(error).__name__ + ": " + str(error))[:256])


@contextmanager
def control_span_v1(phase):
    probe = _ACTIVE.get()
    if probe is None or not probe.active:
        yield
        return
    try:
        cm = probe.span(phase)
        cm.__enter__()
    except Exception as error:
        _note(probe, error)
        yield
        return
    original = None
    try:
        yield
    except BaseException as error:
        original = error
        raise
    finally:
        try:
            cm.__exit__(type(original) if original is not None else None,
                        original, original.__traceback__ if original is not None else None)
        except Exception as error:
            _note(probe, error)
            if original is not None:
                original.add_note("control timing failure: " + str(error)[:256])


def control_call_v1(phase, operation, *args, **kwargs):
    with control_span_v1(phase):
        return operation(*args, **kwargs)


def _boundary(probe, sequence, point, *, at_utc=None, monotonic_ns=None):
    if probe is None or not probe.active:
        return
    try:
        probe.boundary(sequence, point,
            at_utc=at_utc or datetime.now(timezone.utc).isoformat(), monotonic_ns=monotonic_ns)
    except Exception as error:
        _note(probe, error)


@contextmanager
def control_call_scope_v1(request):
    probe = _ACTIVE.get()
    sequence = request.get("sequence") if isinstance(request, dict) else None
    _boundary(probe, sequence, "call_enter")
    try:
        with control_span_v1("call_total"):
            yield
    finally:
        _boundary(probe, sequence, "call_return")


def control_rpc_boundary_v1(sequence, point, value, mono):
    probe = _ACTIVE.get()
    if probe is None or not probe.active:
        return
    try:
        if point == "rpc_start":
            stamp, endpoint = value, mono
        else:
            stamp, endpoint = value["ended_at_utc"], mono + value["elapsed_seconds"]
        _boundary(probe, sequence, point, at_utc=stamp, monotonic_ns=int(endpoint * 1e9))
    except Exception as error:
        _note(probe, error)


def _checked_source(source, expected_sha256):
    if not isinstance(source, str) or "\r" in source or len(source.encode()) > 524288:
        raise ValueError("bounded LF source string required")
    if hashlib.sha256(source.encode()).hexdigest() != expected_sha256:
        raise ValueError("exact caller source digest differs")
    return ast.parse(source)


def _replace_calls(source, tree, selection):
    lines = source.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    def offset(line, column):
        return starts[line - 1] + len(lines[line - 1].encode()[:column].decode())
    edits, counts = [], {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        phase = selection(node)
        if phase is None:
            continue
        first = offset(node.lineno, node.col_offset)
        func_end = offset(node.func.end_lineno, node.func.end_col_offset)
        opening = source.find("(", func_end)
        if opening < 0 or source[func_end:opening].strip():
            raise ValueError("unexpected selected call syntax")
        edits.extend([(first, first, '_control_call_v1("' + phase + '", '),
                      (opening, opening + 1, ",")])
        counts[phase] = counts.get(phase, 0) + 1
    for first, last, value in sorted(edits, reverse=True):
        source = source[:first] + value + source[last:]
    return source, counts


def _wrap_bodies(source, ranges):
    lines = source.splitlines(keepends=True)
    for first, last, context in sorted(ranges, reverse=True):
        indent = len(lines[first - 1]) - len(lines[first - 1].lstrip(" "))
        body = ["    " + line if line.strip() else line for line in lines[first - 1:last]]
        lines[first - 1:last] = [" " * indent + "with " + context + ":\n"] + body
    return "".join(lines)


def transform_queue_source_v1(source, *, expected_sha256):
    """Transform the exact normal Queue shape; return text only, never write it."""
    tree = _checked_source(source, expected_sha256)
    owners = [n for n in tree.body if isinstance(n, ast.ClassDef)
        and {"call", "full_loop", "generated", "persist_loop_state"}.issubset(
            {x.name for x in n.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))})]
    if len(owners) != 1:
        raise ValueError("one original normal Queue owner required")
    owner_name = owners[0].name
    def select(node):
        if isinstance(node.func, ast.Name):
            return {"pending_request_paths": "pending_paths", "relay_compact": "relay_total",
                "decoded": "result_decode", "display_projection": "display_projection",
                "_owner_response_success_row_once_v1": "response_prepare"}.get(node.func.id)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "self":
            return {"guard": "consume_guard", "check_after": "classifier"}.get(node.func.attr)
        return None
    source, counts = _replace_calls(source, tree, select)
    for phase in ("pending_paths", "relay_total", "response_prepare", "consume_guard", "classifier"):
        if counts.get(phase, 0) < 1:
            raise ValueError("missing original control call: " + phase)
    tree = ast.parse(source)
    owner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == owner_name)
    methods = {n.name: n for n in owner.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    call, full = methods["call"], methods["full_loop"]
    starts = [n for n in ast.walk(call) if isinstance(n, ast.Assign)
        and any(isinstance(x, ast.Tuple) and [getattr(y, "id", None) for y in x.elts] == ["started", "mono"] for x in n.targets)]
    tries = [n for n in ast.walk(call) if isinstance(n, ast.Try)
        and any(isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                and x.func.attr == "call_tool" for x in ast.walk(n))]
    loops = [n for n in ast.walk(full) if isinstance(n, ast.While)
             and ast.dump(n.test) == ast.dump(ast.parse("settled < maximum", mode="eval").body)]
    atomics = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "atomic_payload_v1"]
    if not (len(starts) == len(tries) == len(loops) == len(atomics) == 1):
        raise ValueError("original RPC boundary/loop/atomic shape differs")
    # Insert boundaries before wrapping: source positions are still original AST positions.
    lines = source.splitlines(keepends=True)
    insertions = [(starts[0].end_lineno, '        _control_rpc_boundary_v1(sequence, "rpc_start", started, mono)\n'),
                  (tries[0].end_lineno, '        _control_rpc_boundary_v1(sequence, "rpc_end", row, mono)\n')]
    for after, text in sorted(insertions, reverse=True):
        lines[after:after] = [text]
    source = "".join(lines)
    tree = ast.parse(source)
    owner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == owner_name)
    methods = {n.name: n for n in owner.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    ranges = []
    for node, scope in [(methods["call"], "_control_call_scope_v1(request)"),
                        (methods["persist_loop_state"], '_control_span_v1("loop_state_persist")'),
                        (next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "atomic_payload_v1"), '_control_span_v1("atomic_write")')]:
        ranges.append((node.body[0].lineno, node.end_lineno, scope))
    loop = next(n for n in ast.walk(methods["full_loop"]) if isinstance(n, ast.While)
        and ast.dump(n.test) == ast.dump(ast.parse("settled < maximum", mode="eval").body))
    ranges.append((loop.body[0].lineno, loop.end_lineno, '_control_span_v1("loop_step")'))
    source = _wrap_bodies(source, ranges)
    tree = ast.parse(source)
    after = max((n.end_lineno for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == "__future__"), default=0)
    lines = source.splitlines(keepends=True)
    lines[after:after] = ["from queue_control_timing_adapter_v1 import (control_call_v1 as _control_call_v1, control_span_v1 as _control_span_v1, control_call_scope_v1 as _control_call_scope_v1, control_rpc_boundary_v1 as _control_rpc_boundary_v1)\n"]
    result = "".join(lines)
    compile(result, "normal-queue-control-timing", "exec")
    return {"source": result, "owner_class": owner_name, "call_hook_counts": counts,
            "source_sha256": expected_sha256, "target_sha256": hashlib.sha256(result.encode()).hexdigest()}


def transform_relay_source_v1(source, *, expected_sha256):
    tree = _checked_source(source, expected_sha256)
    def select(node):
        return "relay_ack_wait" if isinstance(node.func, ast.Attribute) and node.func.attr == "wait_text_published" else None
    result, counts = _replace_calls(source, tree, select)
    if counts != {"relay_ack_wait": 1}:
        raise ValueError("one exact parent relay ACK wait required")
    lines = result.splitlines(keepends=True)
    first = tree.body[0]
    after = first.end_lineno if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str) else 0
    lines[after:after] = ["from queue_control_timing_adapter_v1 import control_call_v1 as _control_call_v1\n"]
    result = "".join(lines)
    compile(result, "normal-relay-control-timing", "exec")
    return {"source": result, "source_sha256": expected_sha256,
            "target_sha256": hashlib.sha256(result.encode()).hexdigest()}


def _admission(admission):
    if admission is None or isinstance(admission, dict) and admission.get("enabled", False) is False:
        return None
    if (not isinstance(admission, dict) or admission.get("enabled") is not True
            or admission.get("schema") != ADMISSION_SCHEMA
            or type(admission.get("control_sequence")) is not int or admission["control_sequence"] < 1
            or type(admission.get("cycle_budget")) is not int or not 1 <= admission["cycle_budget"] <= 30
            or type(admission.get("machine_id")) is not str or not admission["machine_id"]):
        raise ValueError("explicit bounded control timing admission required")
    return dict(admission)


def bind_queue_control_timing_v1(Base, env, *, admission=None, admission_getter=None):
    """Compose outside the cold factory; optional getter reads only owned state.

    Normal-cold getter: lambda queue: queue._normal_cold['admission'].get('control_timing').
    It runs at FULL entry after the original preflight has read that admission.
    No registry/file/metadata read is introduced by this binder.
    """
    fixed = _admission(admission)
    if admission_getter is None and fixed is None:
        return Base
    if admission_getter is not None and not callable(admission_getter):
        raise ValueError("owned in-memory admission getter required")
    class TimedQueue(Base):
        async def full_loop(self, session, request, path):
            admitted = _admission(admission_getter(self)) if admission_getter is not None else fixed
            if admitted is None:
                return await super().full_loop(session, request, path)
            args = request.get("arguments", {})
            maximum = args.get("max_turns", 30) if isinstance(args, dict) else None
            if (getattr(self, "_control_timing_used_v1", False)
                    or request.get("sequence") != admitted["control_sequence"]
                    or type(maximum) is not int or not 1 <= maximum <= admitted["cycle_budget"]):
                return await super().full_loop(session, request, path)
            self._control_timing_used_v1 = True
            probe = self.control_timing_v1 = QueueControlTimingV1(machine_id=admitted["machine_id"], enabled=True)
            probe.arm_batch(admitted["control_sequence"], cycle_budget=admitted["cycle_budget"])
            state = getattr(self, "full_loop_state", None)
            before = state.get("completed_cycles") if isinstance(state, dict) else None
            token = _ACTIVE.set(probe)
            original = None
            try:
                return await super().full_loop(session, request, path)
            except BaseException as error:
                original = error
                raise
            finally:
                _ACTIVE.reset(token)
                try:
                    state = getattr(self, "full_loop_state", None)
                    after = state.get("completed_cycles") if isinstance(state, dict) else None
                    delta = after - before if type(before) is type(after) is int else None
                    if type(delta) is int and 0 <= delta <= admitted["cycle_budget"]:
                        for _ in range(delta):
                            probe.settled_cycle()
                    snapshot = probe.finish_batch(at_utc=datetime.now(timezone.utc).isoformat(),
                        reason="original_full_error" if original is not None else "original_full_returned")
                    snapshot["actual_cycle_delta"] = delta
                    snapshot["instrumentation_diagnostics"] = list(getattr(probe, "_adapter_diagnostics", []))
                    destination = Path(env["Q"]) / ("CONTROL-TIMING-" + str(admitted["control_sequence"]).zfill(4) + ".json")
                    env["atomic"](destination, snapshot, limit=65536)
                except Exception as error:
                    diagnostic = type(error).__name__ + ": " + str(error)[:512]
                    self.timing_write_diagnostic = diagnostic
                    if original is not None:
                        original.add_note("control timing snapshot unavailable: " + diagnostic)
                    try:
                        print("CONTROL_TIMING_SNAPSHOT_UNAVAILABLE; original FULL is not replayable: " + diagnostic, file=sys.stderr, flush=True)
                    except Exception:
                        pass
    return TimedQueue
