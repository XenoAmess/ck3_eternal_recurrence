"""Build a narrow Native25 successor from preserved actual recipes only.

Requires the exact admitted child and pinned consumer plan. Never deploys,
injects, starts Game, runs a project EXE or changes system settings.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_native_msvc as msvc
from plan_native25_successor_20261019 import Recipes, norm, tokens

MIB = 1024 * 1024
NATIVE = "ck3_autonomous_player/native_bridge/"
OLD_JSON = "652e873ab164cfb78b654854c0dc2ca35ef816b3"
NEW_JSON = "d90d5e79ac7d22b3376ca70f3fccebd3faef516f"
NEW_ACTOR = "d761b3ce"
HEADERS = ("ck3_12002_declarations.hpp", "ck3_12004_person_six_stage_capture.hpp", "person_callback_entry_inputs_12004.hpp")
LOW_FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)


def now(): return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(MIB), b""): h.update(chunk)
    return h.hexdigest()


def pin(path):
    path = Path(path)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": sha(path)}


def canonical(value): return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def write(path, value):
    path = Path(path)
    if path.exists(): raise ValueError("create-only output already exists: " + str(path))
    path.write_bytes(json.dumps(value, ensure_ascii=True, indent=2).encode() + b"\n")


def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def normalized(raw): return raw.decode("utf-8-sig").replace("\r\n", "\n")


def git(commit, relative):
    return subprocess.check_output(["git", "show", commit + ":" + NATIVE + relative], cwd=ROOT)


def system_times():
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    values = [wintypes.FILETIME() for _ in range(3)]
    if not kernel.GetSystemTimes(*(ctypes.byref(value) for value in values)):
        raise ctypes.WinError(ctypes.get_last_error())
    return [value.dwLowDateTime | value.dwHighDateTime << 32 for value in values]


def occupied(root): return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def check_space(root, phase, limit):
    total = occupied(root)
    if total > limit: raise RuntimeError(f"{phase} child phase bound exceeded: {total}>{limit}")
    return total


def archive_payloads(path):
    """COFF archive member payload SHA/order, excluding linker/name tables."""
    rows, long_names = [], b""
    with Path(path).open("rb") as stream:
        if stream.read(8) != b"!<arch>\n": raise ValueError("invalid COFF archive")
        while True:
            header = stream.read(60)
            if not header: break
            if len(header) != 60 or header[58:] != b"`\n": raise ValueError("invalid archive member header")
            name, size = header[:16].decode("ascii").strip(), int(header[48:58])
            h, remaining, name_table_parts = hashlib.sha256(), size, []
            while remaining:
                block = stream.read(min(remaining, MIB))
                if not block: raise ValueError("truncated archive member")
                h.update(block); remaining -= len(block)
                if name == "//": name_table_parts.append(block)
            if name == "//": long_names = b"".join(name_table_parts)
            if name not in {"/", "//", "/SYM64/"}:
                if name.startswith("/") and name[1:].isdigit():
                    tail = long_names[int(name[1:]):]
                    payload_name = tail.split(b"\0", 1)[0].split(b"/\n", 1)[0].decode("utf-8")
                else: payload_name = name.rstrip("/")
                rows.append({"header_name": name, "payload_name": payload_name, "bytes": size, "sha256": h.hexdigest()})
            if size % 2 and stream.read(1) != b"\n": raise ValueError("invalid archive padding")
    return rows


def original_argv(row, recipes):
    actual = recipes.get(row["object"], row["origin"])
    if actual["argv_sha256"] != row["argv_sha256"]: raise ValueError("original recipe changed")
    data = recipes.read(row["recipe"])
    if row["recipe_pointer"]:
        for part in row["recipe_pointer"].strip("/").split("/"):
            data = data[int(part)] if isinstance(data, list) else data[part]
    argv = data.get("argv", data.get("compiler_argv", data.get("compile_argv")))
    return list(argv), actual


def header_fingerprint(plan, recipes):
    seen = {}
    for row in plan["objects"]:
        _, actual = original_argv(row, recipes)
        for name in actual["includes"] or []:
            low = norm(name)
            if ("xar_bridge" in low or "ck3_autonomous_player" in low or "frozen" in low) and low not in seen:
                seen[low] = pin(name)
    pins = sorted(seen.values(), key=lambda item: item["path"].lower())
    actual = hashlib.sha256(canonical(pins)).hexdigest()
    if actual != plan["frozen_project_header_pin_digest"]: raise ValueError("old frozen header bytes changed")
    return actual


def prepare(args, plan, admission):
    root = args.output_root
    resume = args.stage == "prepare-resume"
    if root.exists() and not (resume and (root / "PREPARATION-FAILED01.json").exists() and not (root / "PREPARED.json").exists()):
        raise ValueError("Native26 output root must be fresh or exact diagnosed preparation resume")
    root.mkdir(exist_ok=resume)
    (root / "source/include/xar_bridge").mkdir(parents=True, exist_ok=resume)
    (root / "source/src").mkdir(exist_ok=resume)
    (root / ("producer-used-resume02.py" if resume else "producer-used.py")).write_bytes(Path(__file__).read_bytes())
    def put(path, raw):
        if path.exists():
            if path.read_bytes() != raw: raise ValueError("preserved prepare output changed: " + str(path))
        else: path.write_bytes(raw)
    put(root / "INPUT-PLAN.json", args.plan.read_bytes())
    recipes = Recipes(Path(plan["legacy_recipe_index"]["path"]))
    fingerprint = header_fingerprint(plan, recipes)
    deltas = []
    mappings = {}
    for name, old_commit, new_commit in [
        ("ck3_12002_declarations.hpp", NEW_ACTOR + "^", NEW_ACTOR),
        ("ck3_12004_person_six_stage_capture.hpp", OLD_JSON, NEW_JSON),
        ("person_callback_entry_inputs_12004.hpp", OLD_JSON, NEW_JSON),
    ]:
        relative = "include/xar_bridge/" + name
        old, new = git(old_commit, relative), git(new_commit, relative)
        versions = [item for item in plan["frozen_project_header_versions"] if Path(item["path"]).name == name]
        canonical_version = [item for item in versions if normalized(Path(item["path"]).read_bytes()) == normalized(old)]
        if not canonical_version: raise ValueError("reviewed old header missing: " + name)
        # Two older actual consumers used the pre-Native18 private header. All
        # layout consumers now converge on the canonical successor header.
        if name != HEADERS[0] and len(canonical_version) != len(versions):
            raise ValueError("unreviewed additive header version: " + name)
        out = root / "source" / relative
        put(out, new)
        deltas.append({"relative": relative, "old_commit": old_commit, "new_commit": new_commit,
                       "old_header_versions": versions, "new": pin(out)})
    relative = "include/xar_bridge/ck3_12004_declaration_actor_candidate.hpp"
    out = root / "source" / relative; put(out, git(NEW_ACTOR, relative))
    deltas.append({"relative": relative, "new_commit": NEW_ACTOR, "new": pin(out)})
    source_commits = {
        "ck3_12002_declarations.cpp": (NEW_ACTOR + "^", NEW_ACTOR),
        "ck3_12004_war_declarations.cpp": (NEW_ACTOR + "^", NEW_ACTOR),
        "ck3_12004_person_six_stage_capture.cpp": (OLD_JSON, NEW_JSON),
        "person_callback_entry_inputs_12004.cpp": (OLD_JSON, NEW_JSON),
        "ck3_12004_knight_stat_consumption_serializer.cpp": (OLD_JSON, NEW_JSON),
    }
    for name, (before, after) in source_commits.items():
        old, new = git(before, "src/" + name), git(after, "src/" + name)
        matching = [row for row in plan["objects"] if Path(row["source"]).name == name]
        if not matching: raise ValueError("reviewed source has no actual Native25 object: " + name)
        for row in matching:
            if normalized(Path(row["source"]).read_bytes()) != normalized(old):
                raise ValueError("actual source is not the audited delta baseline: " + row["source"])
            mappings[norm(row["source"])] = str(root / "source/src" / name)
        out = root / "source/src" / name; put(out, new)
        deltas.append({"relative": "src/" + name, "old_commit": before, "new_commit": after, "new": pin(out)})
    m6 = read(args.m6_receipt)["candidate"]
    for row in plan["objects"]:
        if Path(row["source"]).name != "ck3_12002_nonwar_router.cpp": continue
        raw = Path(row["source"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != m6["baseline_sha256"]: raise ValueError("M6 old router source mismatch")
        text = normalized(raw); start = text.index("bool IsNonwarPrivateStep12004(")
        anchor = "  if (step == kSwayCompletionStepV1) return true;\n"
        end = text.index(anchor, start) + len(anchor)
        candidate = (text[:end] + m6["added_source"] + text[end:]).encode()
        if hashlib.sha256(candidate).hexdigest() != m6["candidate_sha256"]: raise ValueError("M6 single-line candidate hash mismatch")
        out = root / "source/src/ck3_12002_nonwar_router.cpp"
        put(out, candidate)
        mappings[norm(row["source"])] = str(out)
    deltas.append({"relative": "src/ck3_12002_nonwar_router.cpp", "qualification": pin(args.m6_receipt),
                   "new": pin(root / "source/src/ck3_12002_nonwar_router.cpp")})
    # Pin the preserved input archive as actually retained by Native25's chain.
    prior = read(args.prior_link_plan)
    expected = {norm(item["path"]): item["sha256"] for item in prior["retained_inputs"]}
    direct = [item for item in tokens(Path(plan["baseline_response"]["path"])) if item.lower().endswith(".obj")]
    member_paths = [item for item in tokens(Path(plan["archive_response"]["path"])) if item.lower().endswith(".obj")]
    direct_pins = []
    for obj in direct:
        actual = recipes.get(obj, "direct"); result = pin(obj)
        wanted = actual.get("expected_object_sha256") or expected.get(norm(obj))
        if not wanted or result["sha256"] != wanted: raise ValueError("unbound/changed original direct object: " + obj)
        direct_pins.append(result)
    libraries = [item for item in tokens(Path(plan["baseline_response"]["path"])) if item.lower().endswith("runtime-native18.lib")]
    if len(libraries) != 1: raise ValueError("ambiguous original runtime archive")
    library = pin(libraries[0])
    if library["sha256"] != expected.get(norm(libraries[0])): raise ValueError("old runtime archive changed")
    payloads = archive_payloads(libraries[0])
    member_pins = [pin(path) for path in member_paths]
    payload_key = lambda row: (Path(row.get("payload_name", row.get("path"))).name.lower(), row["bytes"], row["sha256"])
    if Counter(map(payload_key, payloads)) != Counter(map(payload_key, member_pins)):
        raise ValueError("original archive response/member name+payload identity mismatch")
    write(root / "SOURCE-DELTA.json", {"machine_id": admission["machine_id"], "at_utc": now(),
          "deltas": deltas, "source_mappings": mappings, "original_header_fingerprint": fingerprint,
          "current_master_tree_used": False, "old_source_and_header_inputs_read_only": True})
    write(root / "RETAINED-INPUTS.json", {"machine_id": admission["machine_id"], "at_utc": now(),
          "direct": direct_pins, "old_archive": library, "members_in_exact_response_order": member_pins,
          "original_archive_payload_name_and_multiset_verified": True,
          "original_librarian_payload_order_equals_response": list(map(payload_key, payloads)) == list(map(payload_key, member_pins)),
          "prior_link_plan": pin(args.prior_link_plan)})
    write(root / "PREPARED.json", {"machine_id": admission["machine_id"], "at_utc": now(),
          "admission": pin(args.admission), "plan": pin(args.plan), "producer": pin(Path(__file__)),
          "delta": pin(root / "SOURCE-DELTA.json"), "retained_inputs": pin(root / "RETAINED-INPUTS.json"),
          "occupied_bytes": check_space(root, "prepare", 8 * MIB), "compile_or_Game_calls": 0})
    print(json.dumps({"stage": "prepared", "objects_to_compile": len(plan["objects"]), "occupied_bytes": occupied(root)}), flush=True)


def environment(root):
    build = root / "build"; build.mkdir(exist_ok=True)
    child = msvc.child_environment(build)
    install = msvc.visual_studio_installation(None, child)
    return msvc.initialize_msvc(install, build, child)


def execute(argv, cwd, env, log, timeout=600):
    started = now(); tick = time.perf_counter()
    with Path(log).open("wb") as stream:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT, creationflags=LOW_FLAGS)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=30)
            raise
    return {"argv": argv, "started_at_utc": started, "ended_at_utc": now(), "exit_code": code,
            "wall_seconds": time.perf_counter() - tick, "priority": "BELOW_NORMAL", "log": pin(log)}


def compile_all(args, plan, admission):
    root = args.output_root; check_space(root, "precompile", 256 * MIB)
    env, tools = environment(root)
    recipes = Recipes(Path(plan["legacy_recipe_index"]["path"]))
    fingerprint = header_fingerprint(plan, recipes)
    mappings = read(root / "SOURCE-DELTA.json")["source_mappings"]
    source_pins = {norm(item["path"]): item["sha256"] for item in plan["frozen_sources"]}
    stop = threading.Event(); results = []
    phase_start, cpu_start = now(), system_times()
    print(json.dumps({"stage": "compile_started", "at_utc": phase_start, "workers": 2, "priority": "BELOW_NORMAL"}), flush=True)
    def one(row):
        if stop.is_set(): return {"old_object": row["object"], "status": "NOTRUN_AFTER_FAILURE"}
        tag = hashlib.sha256(norm(row["object"]).encode()).hexdigest()[:12]
        base = root / "build/jobs" / tag
        base.mkdir(parents=True, exist_ok=True)
        attempt = base / "attempt01"
        if attempt.exists(): raise ValueError("compile attempt already exists: " + str(attempt))
        attempt.mkdir(); (attempt / "temp").mkdir()
        argv, original = original_argv(row, recipes)
        if sha(row["source"]) != source_pins[norm(row["source"])]: raise ValueError("old source changed")
        source = mappings.get(norm(row["source"]), row["source"])
        target, deps = attempt / (tag + ".obj"), attempt / "dependencies.json"
        for i, value in enumerate(argv):
            low = value.lower()
            if norm(value) == norm(row["source"]): argv[i] = source
            elif low.startswith("/fo"): argv[i] = "/Fo" + str(target)
            elif low.startswith("/fd"): argv[i] = "/Fd" + str(attempt / "compiler.pdb")
            elif low == "/sourcedependencies": argv[i + 1] = str(deps)
        if "/sourcedependencies" not in [value.lower() for value in argv]: argv += ["/sourceDependencies", str(deps)]
        argv.insert(1, "/I" + str(root / "source/include"))
        child = env.copy(); child["TEMP"] = child["TMP"] = str(attempt / "temp")
        result = execute(argv, attempt, child, attempt / "compile.log")
        result.update({"old_object": row["object"], "old_source": row["source"], "source": pin(source),
                       "object": str(target), "origin": row["origin"], "rebuild_reasons": row["rebuild_reasons"]})
        if result["exit_code"] == 0:
            includes = read(deps)["Data"]["Includes"]
            overrides = {}
            for name in HEADERS:
                found = [item for item in includes if Path(item).name.lower() == name]
                expected = norm(root / "source/include/xar_bridge" / name)
                if any(norm(item) != expected for item in found): raise ValueError("old override header remained: " + repr(found))
                if name == HEADERS[0] and row["layout_consumer"] and len(found) != 1:
                    raise ValueError("new declarations header not uniquely consumed")
                if name in row["additive_header_consumers"] and len(found) != 1:
                    raise ValueError("new additive header not uniquely consumed")
                overrides[name] = found
            allowed_new = norm(root / "source/include/xar_bridge/ck3_12004_declaration_actor_candidate.hpp")
            old_includes = {norm(item) for item in original["includes"]}
            for item in includes:
                low = norm(item)
                if "xar_bridge" in low and Path(item).name not in HEADERS and low != allowed_new and low not in old_includes:
                    raise ValueError("unreviewed project header introduced: " + item)
            result.update({"object_pin": pin(target), "dependencies": pin(deps), "unique_override_includes": overrides,
                           "source_after_sha256": sha(source), "status": "PASS"})
            if result["source_after_sha256"] != result["source"]["sha256"]: raise ValueError("source drift during compilation")
        else:
            result["status"] = "COMPILE_RED"; stop.set()
        write(attempt / "COMPILE-RESULT.json", result)
        return result
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(one, row) for row in plan["objects"]]
            for future in as_completed(futures):
                try: result = future.result()
                except Exception as error:
                    stop.set(); result = {"status": "QUALIFICATION_RED", "error": repr(error)}
                results.append(result)
                if len(results) % 8 == 0 or result["status"] not in {"PASS", "NOTRUN_AFTER_FAILURE"}:
                    print(json.dumps({"stage": "compile_progress", "completed": len(results), "status": result["status"],
                                      "occupied_bytes": check_space(root, "compile", 256 * MIB)}), flush=True)
    finally:
        cpu_end = system_times(); idle, kernel, user = [b - a for a, b in zip(cpu_start, cpu_end)]
        report = {"machine_id": admission["machine_id"], "started_at_utc": phase_start, "ended_at_utc": now(),
                  "workers": 2, "priority": "BELOW_NORMAL", "system_cpu_logical_processors": os.cpu_count(),
                  "system_cpu_busy_fraction_during_phase": (kernel + user - idle) / (kernel + user) if kernel + user else None,
                  "compiler": pin(Path(tools["cl"])), "original_header_fingerprint": fingerprint,
                  "counts": dict(Counter(result["status"] for result in results)), "results": results,
                  "occupied_bytes": check_space(root, "compile", 256 * MIB), "Game_calls": 0}
        write(root / "COMPILE-RESULT.json", report)
    if len(results) != len(plan["objects"]) or any(item["status"] != "PASS" for item in results):
        raise RuntimeError("Native26 compile/Includes qualification failed; preserve attempts")
    print(json.dumps({"stage": "compile_pass", "objects": len(results), "occupied_bytes": occupied(root)}), flush=True)


def replace_lines(original, replacements):
    result, seen = [], set()
    for line in Path(original).read_text(encoding="utf-8-sig").splitlines():
        key = norm(line.strip('"'))
        if key in replacements: result.append(replacements[key]); seen.add(key)
        else: result.append(line)
    if seen != set(replacements): raise ValueError("some replacement tokens were not exact original inputs")
    return result


def archive(args, plan, admission):
    root = args.output_root; check_space(root, "prearchive", 640 * MIB)
    env, tools = environment(root); compiled = read(root / "COMPILE-RESULT.json")
    replacements = {norm(row["old_object"]): row["object"] for row in compiled["results"] if row["origin"] == "archive"}
    if len(replacements) != 100: raise ValueError("expected exact100 archive replacements")
    target = root / "build/native26-runtime.lib"
    lines = replace_lines(plan["archive_response"]["path"], replacements)
    out_flags = [i for i, line in enumerate(lines) if line.upper().startswith("/OUT:")]
    if len(out_flags) != 1 or target.exists(): raise ValueError("archive must be a fresh output")
    lines[out_flags[0]] = "/OUT:" + str(target)
    response = root / "build/native26-archive.rsp"; response.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = execute([str(Path(tools["cl"]).parent / "lib.exe"), "@" + str(response)], root / "build", env, root / "build/archive.log")
    result.update({"machine_id": admission["machine_id"], "response": pin(response), "replaced_old_members": list(replacements),
                   "members": len([line for line in lines if line.lower().endswith(".obj")])})
    if result["exit_code"] == 0:
        expected = [pin(path) for path in tokens(response) if path.lower().endswith(".obj")]
        actual = archive_payloads(target)
        payload_key = lambda row: (Path(row.get("payload_name", row.get("path"))).name.lower(), row["bytes"], row["sha256"])
        equal = len(actual) == 612 and Counter(map(payload_key, actual)) == Counter(map(payload_key, expected))
        result.update({"archive": pin(target), "payload_names_and_multiset_equal_expected612": equal,
                       "librarian_payload_order_equals_response": list(map(payload_key, actual)) == list(map(payload_key, expected)),
                       "old_replaced_paths_absent": not set(replacements).intersection(norm(path) for path in tokens(response)),
                       "retained_member_order_unchanged": True})
        if not equal: result["exit_code"] = 91
    result["occupied_bytes"] = check_space(root, "archive", 640 * MIB)
    write(root / "ARCHIVE-RESULT.json", result)
    if result["exit_code"]: raise RuntimeError("Native26 archive failed")
    print(json.dumps({"stage": "archive_pass", "archive_bytes": target.stat().st_size, "occupied_bytes": occupied(root)}), flush=True)


def link(args, plan, admission):
    root = args.output_root; check_space(root, "prelink", 768 * MIB)
    env, tools = environment(root); compiled = read(root / "COMPILE-RESULT.json")
    archive_result = read(root / "ARCHIVE-RESULT.json")
    if archive_result["exit_code"] or not archive_result["payload_names_and_multiset_equal_expected612"]: raise ValueError("archive qualification missing")
    replacements = {norm(row["old_object"]): row["object"] for row in compiled["results"] if row["origin"] == "direct"}
    retained = read(root / "RETAINED-INPUTS.json")
    replacements[norm(retained["old_archive"]["path"])] = str(root / "build/native26-runtime.lib")
    if len(replacements) != 22: raise ValueError("expected21 direct replacements and one fresh runtime archive")
    lines = replace_lines(plan["baseline_response"]["path"], replacements)
    for prefix, filename, count in (("/OUT:", "native26.dll", 1), ("/PDB:", "native26.pdb", 1),
                                    ("/IMPLIB:", "native26.lib", 1), ("/MAP:", "native26.map", 2)):
        found = [i for i, line in enumerate(lines) if line.upper().startswith(prefix)]
        if len(found) != count: raise ValueError("unexpected preserved link output switches")
        for index in found: lines[index] = prefix + str(root / "build" / filename)
    response = root / "build/native26-link.rsp"; response.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = execute([str(Path(tools["cl"]).parent / "link.exe"), "@" + str(response)], root / "build", env, root / "build/link.log")
    result.update({"machine_id": admission["machine_id"], "response": pin(response), "direct_replacements": 21,
                   "runtime_archive_replacements": 1, "other_response_tokens_and_order_unchanged": True,
                   "current_Native25_or_Game_changed": False})
    if result["exit_code"] == 0:
        result.update({"DLL": pin(root / "build/native26.dll"), "map": pin(root / "build/native26.map")})
    result["occupied_bytes"] = check_space(root, "link", 768 * MIB)
    write(root / "LINK-RESULT.json", result)
    if result["exit_code"]: raise RuntimeError("Native26 link failed")
    print(json.dumps({"stage": "link_pass", "DLL": result["DLL"], "occupied_bytes": occupied(root)}), flush=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--m6-receipt", type=Path, required=True)
    parser.add_argument("--prior-link-plan", type=Path, required=True)
    parser.add_argument("--stage", choices=("prepare", "prepare-resume", "compile", "archive", "link"), required=True)
    args = parser.parse_args()
    admission, plan = read(args.admission), read(args.plan)
    actual_machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True).strip()
    if admission["machine_id"] != actual_machine or plan["machine_id"] != actual_machine: raise ValueError("wrong machine")
    if norm(args.output_root.resolve()) != norm(admission["approved_output_root"]): raise ValueError("child root mismatch")
    if sha(args.plan) != admission["exact_consumer_plan"]["sha256"]: raise ValueError("consumer plan differs from admission")
    if datetime.now(timezone.utc) >= datetime.fromisoformat(admission["parent_review_at_utc"]): raise ValueError("storage admission expired")
    if admission["hard_total_child_peak_bytes"] != 768 * MIB: raise ValueError("unexpected child limit")
    {"prepare": prepare, "prepare-resume": prepare, "compile": compile_all, "archive": archive, "link": link}[args.stage](args, plan, admission)


if __name__ == "__main__":
    main()
