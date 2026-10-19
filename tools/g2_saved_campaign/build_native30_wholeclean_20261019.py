"""Finite Native30 wrapper: ADMITTED contract, owned root/Job; no Game/DLL load."""
from __future__ import annotations
import argparse
import ctypes as c
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
NATIVE = "ck3_autonomous_player/native_bridge"
EXACT_ROOT = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-native30-camera01")
MIB = 1024 * 1024
HARD = 1536 * MIB
TOOLS = ("tools/run_native_msvc.py", "tools/register_project_exe_exclusions.py",
         "tools/project_exe_exclusion_broker_client.py", "tools/check_native_layout_report_v1.py")
PRODUCTION = ["xar_ck3_bridge", "xar_ck3_12002_runtime", "xar_bridge_protocol"]
BAD_FLAGS = re.compile(r"(?i)(?:^|\s)[/-](?:MP\d*|Zi|ZI|Z7|GL|Yu\S*|DEBUG\S*|LTCG\S*)(?:\s|$)")

def utc(): return datetime.now(timezone.utc).isoformat()
def require(value, message):
    if not value: raise RuntimeError(message)
def digest(path):
    with Path(path).open("rb") as stream: return hashlib.file_digest(stream, "sha256").hexdigest()
def pin(path):
    path = Path(path)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}
def load(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
def write(path, value):
    with Path(path).open("x", encoding="utf-8") as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.write("\n")
def inside(path, root): return Path(path).resolve().is_relative_to(Path(root).resolve())
def machine():
    return subprocess.check_output([sys.executable, "-B", str(REPO / "tools/ck3_live_run_id.py"),
                                    "machine"], text=True, timeout=15).strip()
def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args], timeout=60)

class FileAPI:
    """Actual FileStandardInfo EOF/AllocationSize, never st_size as allocation."""
    class Standard(c.Structure):
        _fields_ = [("allocation", c.c_longlong), ("eof", c.c_longlong),
                    ("links", c.c_ulong), ("deleted", c.c_ubyte), ("directory", c.c_ubyte)]
    def __init__(self):
        require(os.name == "nt", "Windows FileStandardInfo required")
        from ctypes import wintypes as w
        self.k = c.WinDLL("kernel32", use_last_error=True)
        self.k.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID,
                                      w.DWORD, w.DWORD, w.HANDLE]
        self.k.CreateFileW.restype = w.HANDLE
        self.k.GetFileInformationByHandleEx.argtypes = [w.HANDLE, c.c_int, w.LPVOID, w.DWORD]
        self.k.GetFileInformationByHandleEx.restype = w.BOOL
        self.k.CloseHandle.argtypes = [w.HANDLE]
        self.k.CloseHandle.restype = w.BOOL
    def sizes(self, path):
        handle = self.k.CreateFileW(str(path), 0x80, 7, None, 3, 0x02200000, None)
        if handle in (None, c.c_void_p(-1).value):
            raise c.WinError(c.get_last_error())
        try:
            out = self.Standard()
            if not self.k.GetFileInformationByHandleEx(handle, 1, c.byref(out), c.sizeof(out)):
                raise c.WinError(c.get_last_error())
            require(out.eof >= 0 and out.allocation >= 0 and not out.directory,
                    "invalid FileStandardInfo")
            return out.eof, out.allocation
        finally: self.k.CloseHandle(handle)

def inventory(root, api, cap=30000):
    rows, eof, allocation, raced = [], 0, 0, 0
    if not root.exists(): return {"eof": 0, "allocation": 0, "files": [], "raced": 0}
    for parent, directories, names in os.walk(root, followlinks=False):
        for name in directories + names:
            path = Path(parent) / name
            try: attributes = path.lstat().st_file_attributes
            except FileNotFoundError:
                raced += 1
                continue
            require(not (attributes & 0x400), "reparse point in owned root")
        for name in names:
            path = Path(parent) / name
            require(len(rows) < cap, "owned inventory file cap")
            try: logical, allocated = api.sizes(path)
            except FileNotFoundError:
                raced += 1
                continue
            eof += logical
            allocation += allocated
            rows.append({"path": str(path.relative_to(root)), "eof": logical,
                         "allocation": allocated})
    return {"eof": eof, "allocation": allocation, "files": rows, "raced": raced}

class Guard:
    def __init__(self, root, contract, api):
        self.root, self.contract, self.api = root, contract, api
        self.peak_eof = self.peak_allocation = self.samples = 0
        self.last = None
    def __call__(self, reserve=0):
        require(datetime.now(timezone.utc) < datetime.fromisoformat(
            self.contract["deadline_utc"].replace("Z", "+00:00")), "admission expired")
        data = inventory(self.root, self.api)
        self.samples += 1
        self.peak_eof = max(self.peak_eof, data["eof"])
        self.peak_allocation = max(self.peak_allocation, data["allocation"])
        charged = max(data["eof"], data["allocation"])
        require(charged + reserve <= self.contract["hard_bytes"], "child cumulative cap/reserve")
        require(shutil.disk_usage(self.root).free >= self.contract["minimum_free_bytes"] + reserve,
                "actual global free floor")
        source = metadata = temporary = 0
        for row in data["files"]:
            p = row["path"].replace("\\", "/")
            charge = max(row["eof"], row["allocation"])
            if p.startswith("source/"): source += charge
            elif "/.msvc-temp/" in p or p.startswith("environment-temp/"): temporary += charge
            elif p.startswith("evidence/") or Path(p).suffix.lower() in {
                    ".json", ".log", ".ninja", ".cmake", ".txt", ".pyc"} or ".ninja_" in p:
                metadata += charge
        require(source <= self.contract.get("source_charge_cap_bytes", 96*MIB) and
                metadata <= 80*MIB and temporary <= 384*MIB,
                "source/metadata/TEMP component cap")
        self.last = {"utc": utc(), "eof": data["eof"], "allocation": data["allocation"],
                     "source": source, "metadata": metadata, "temporary": temporary,
                     "raced": data["raced"]}
        return data

class OwnedJob:
    """Suspended launch -> exact new Job -> resume. Never discovers other PIDs."""
    def __init__(self, argv, cwd, environment, log):
        import win32api, win32con, win32event, win32job, win32process
        import msvcrt
        self.api, self.event, self.jobapi, self.processapi = win32api, win32event, win32job, win32process
        self.job = self.process = self.thread = None
        self.output = self.null = None
        flags = win32con.CREATE_SUSPENDED | subprocess.BELOW_NORMAL_PRIORITY_CLASS | subprocess.CREATE_NO_WINDOW
        try:
            win32api.SetLastError(0)
            self.job = win32job.CreateJobObject(None, "Local\\XAR-Native30-" + uuid.uuid4().hex)
            require(win32api.GetLastError() != 183, "private Job unexpectedly preexists")
            limits = win32job.QueryInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation)
            limits["BasicLimitInformation"]["LimitFlags"] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            win32job.SetInformationJobObject(self.job, win32job.JobObjectExtendedLimitInformation, limits)
            self.output, self.null = open(log, "xb"), open(os.devnull, "rb")
            si = win32process.STARTUPINFO()
            si.dwFlags = win32con.STARTF_USESTDHANDLES
            for stream in (self.output, self.null): os.set_inheritable(stream.fileno(), True)
            si.hStdInput = msvcrt.get_osfhandle(self.null.fileno())
            si.hStdOutput = si.hStdError = msvcrt.get_osfhandle(self.output.fileno())
            self.process, self.thread, self.pid, self.tid = win32process.CreateProcess(
                None, subprocess.list2cmdline(argv), None, None, True, flags,
                environment, str(cwd), si)
            win32job.AssignProcessToJobObject(self.job, self.process)
            win32process.ResumeThread(self.thread)
        except BaseException:
            if self.process is not None:
                win32process.TerminateProcess(self.process, 73)
                win32event.WaitForSingleObject(self.process, 10000)
            self.close()
            raise
        finally:
            for stream in (self.output, self.null):
                if stream is not None and not stream.closed: os.set_inheritable(stream.fileno(), False)
    def active(self):
        return self.jobapi.QueryInformationJobObject(
            self.job, self.jobapi.JobObjectBasicAccountingInformation)["ActiveProcesses"]
    def stop(self):
        self.jobapi.TerminateJobObject(self.job, 73)
        until = time.monotonic() + 10
        while self.active() and time.monotonic() < until: time.sleep(.02)
        require(self.active() == 0, "owned Job did not exit")
        self.wait_root()
    def wait_root(self):
        require(self.event.WaitForSingleObject(self.process, 10000) == 0,
                "exact owned process handle not signaled")
    def close(self):
        for handle in (self.thread, self.process, self.job):
            if handle is not None: handle.Close()
        for stream in (self.output, self.null):
            if stream is not None: stream.close()

def run_owned(argv, cwd, environment, log, guard, timeout=1800, reserve=64*MIB):
    guard(reserve)
    started, clock = utc(), time.monotonic()
    process = OwnedJob(argv, cwd, environment, log)
    pid = process.pid
    try:
        while process.active():
            guard()
            require(time.monotonic() - clock < timeout, "owned phase timeout")
            time.sleep(.25)
        process.wait_root()
        code = process.processapi.GetExitCodeProcess(process.process)
        require(code == 0, "owned command returned " + str(code))
        guard()
        return {"argv": argv, "pid": pid, "start_utc": started, "end_utc": utc(),
                "returncode": code, "owned_active_after": 0, "log": pin(log)}
    except BaseException:
        process.stop()
        raise
    finally: process.close()

def tree_entries(commit):
    require(re.fullmatch(r"[0-9a-f]{40}", commit), "full Git commit required")
    require(git("rev-parse", commit + "^{commit}").decode().strip() == commit, "commit identity")
    raw = git("ls-tree", "-r", "-l", "-z", commit, "--", NATIVE, *TOOLS)
    result = []
    for row in raw.split(b"\0"):
        if not row: continue
        info, path = row.split(b"\t", 1)
        mode, kind, oid, size = info.split()
        text = path.decode("utf-8")
        require(mode in (b"100644", b"100755") and kind == b"blob", "non-file frozen input")
        require(Path(text).suffix.lower() not in {".obj", ".lib", ".dll", ".exe", ".pdb", ".ilk"},
                "binary build artifact in source freeze")
        result.append((text, oid.decode(), int(size)))
    require(result and sum(x[2] for x in result) <= 96*MIB, "source logical cap")
    require(all(any(p == name for p, _, _ in result) for name in TOOLS), "missing frozen tool")
    return result

def freeze(root, commit, entries, guard):
    rows = []
    for index, (relative, oid, size) in enumerate(entries):
        destination = root / "source" / relative
        require(inside(destination, root / "source"), "frozen source escape")
        body = git("cat-file", "blob", oid)
        require(len(body) == size and hashlib.sha1(
            b"blob " + str(size).encode() + b"\0" + body).hexdigest() == oid, "Git blob mismatch")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as out: out.write(body)
        rows.append({"path": relative, "git_blob": oid, "bytes": size,
                     "sha256": hashlib.sha256(body).hexdigest()})
        if index % 64 == 0: guard()
    write(root / "evidence/source-freeze.json", {"commit": commit, "files": rows})
    guard()
    return rows

def source_intact(root, rows):
    for row in rows:
        p = root / "source" / row["path"]
        require(p.stat().st_size == row["bytes"] and digest(p) == row["sha256"], "frozen input changed")

def graph(build, source, names, required_defines, allowed_system_roots, source_defines=None,
          assertion_targets=None):
    reply = build / ".cmake/api/v1/reply"
    indexes = sorted(reply.glob("index-*.json"))
    require(len(indexes) == 1, "clean build must have one FileAPI index")
    index = load(indexes[0])
    models = [x for x in index["objects"] if x["kind"] == "codemodel"]
    require(len(models) == 1 and models[0].get("version", {}).get("major") == 2, "codemodel-v2 required")
    def item(name):
        p = reply / name
        require(inside(p, reply), "FileAPI filename escape")
        return load(p)
    model = item(models[0]["jsonFile"])
    require(Path(model["paths"]["source"]).resolve() == source.resolve() and
            Path(model["paths"]["build"]).resolve() == build.resolve(), "FileAPI roots")
    require(len(model["configurations"]) == 1, "single Release config")
    refs = model["configurations"][0]["targets"]
    by_id = {x["id"]: x for x in refs}
    by_name = {x["name"]: x["id"] for x in refs}
    require(all(n in by_name for n in names), "named target missing")
    pending, seen, selected, commands = [by_name[n] for n in names], set(), [], set()
    source_defines, matched = source_defines or {}, set()
    while pending:
        identity = pending.pop()
        if identity in seen: continue
        seen.add(identity)
        require(len(seen) <= 256, "selected target closure too large")
        target = item(by_id[identity]["jsonFile"])
        require(target["id"] == identity, "target identity")
        name = target["name"]
        require("bridge_compile" not in name and "presentation_compile" not in name,
                "duplicate compile-only camera target")
        pending.extend(d["id"] for d in target.get("dependencies", []) if d["id"] in by_id)
        groups = target.get("compileGroups", [])
        defines = {d["define"] for g in groups for d in g.get("defines", [])}
        require(set(required_defines.get(name, [])).issubset(defines), "required define missing: " + name)
        for group in groups:
            flags = " ".join(x["fragment"] for x in group.get("compileCommandFragments", []))
            require(set(required_defines.get(name, [])).issubset(
                {d["define"] for d in group.get("defines", [])}), "shared-header macro inconsistent: " + name)
            require(not BAD_FLAGS.search(flags), "forbidden compiler flag: " + name)
            if (name.endswith("_test") if assertion_targets is None else name in assertion_targets):
                require("/UNDEBUG" in flags or "-UNDEBUG" in flags, "assertions disabled: " + name)
            for include in group.get("includes", []):
                p = Path(include["path"])
                require(inside(p, source) or inside(p, build) or
                        any(inside(p, r) for r in allowed_system_roots), "external include: " + str(p))
        for row in target.get("sources", []):
            if "compileGroupIndex" not in row: continue
            p = Path(row["path"])
            p = p if p.is_absolute() else source / p
            require(inside(p, source) or (row.get("isGenerated") and inside(p, build)),
                    "external TU: " + str(p))
            normalized = os.path.normcase(str(p.resolve()))
            commands.add((name, normalized))
            key = name + ":" + p.relative_to(source).as_posix() if inside(p, source) else ""
            if key in source_defines:
                actual_defs = {x["define"] for x in groups[row["compileGroupIndex"]].get("defines", [])}
                require(set(source_defines[key]).issubset(actual_defs), "required source macro missing: " + key)
                if name == "xar_bridge_protocol":
                    require(not any(x.startswith("XAR_") for x in actual_defs), "private macros leaked into Protocol")
                matched.add(key)
        for artifact in target.get("artifacts", []):
            require(inside(build / artifact["path"], build), "external artifact")
        for fragment in target.get("link", {}).get("commandFragments", []):
            text = fragment["fragment"]
            require(not BAD_FLAGS.search(text) and "/INCREMENTAL" not in text.upper().replace("/INCREMENTAL:NO", ""),
                    "debug/incremental/LTCG link")
            require(not any(s in text.lower() for s in ("native29", "native28", "background-spill")),
                    "old build input in link")
            for token in re.findall(r'"[^"\n]+"|\S+', text):
                token = token.strip('"')
                if token.lower().endswith((".obj", ".lib", ".a")):
                    p = Path(token)
                    p = p if p.is_absolute() else build / p
                    require(inside(p, build) or any(inside(p, r) for r in allowed_system_roots),
                            "external old object/archive input")
        selected.append({"name": name, "type": target["type"], "defines": sorted(defines),
                         "fileapi": pin(reply / by_id[identity]["jsonFile"])})
    require(set(source_defines).issubset(matched), "expected source occurrence missing")
    compile_rows = load(build / "compile_commands.json")
    actual = []
    for row in compile_rows:
        text = row.get("command", " ".join(row.get("arguments", [])))
        output = row.get("output", "")
        output_name = re.search(r"CMakeFiles[\\/]([^\\/]+)\.dir", output or text)
        identity = (output_name.group(1), os.path.normcase(str(Path(row["file"]).resolve()))) if output_name else None
        if identity in commands: actual.append(row)
    require(actual and len(actual) <= 10000, "selected commands absent/over bound")
    for row in actual:
        text = row.get("command", " ".join(row.get("arguments", [])))
        require(not BAD_FLAGS.search(text), "actual compile command forbidden flags")
    return {"targets": selected, "selected_compile_rows": actual, "matched_macro_sources": sorted(matched),
            "source_count": len(commands), "index": pin(indexes[0])}

def temp_closed(build, evidence):
    temporary = build / ".msvc-temp"
    script = temporary / "capture-environment.cmd"
    if script.exists(): script.rename(evidence / "capture-environment.cmd")
    remaining = [p for p in temporary.rglob("*") if p.is_file()]
    require(not remaining, "owned TEMP remains: retain failure, no next phase")

def dependencies(build, capture, source, system_roots):
    """Keep authentic .ninja_deps; bounded unique-path manifest regenerates text."""
    objects, headers, seen = 0, 0, set()
    with capture.open("r", encoding="utf-8", errors="strict") as stream:
        for line in stream:
            if line.startswith("    "):
                p = Path(line.strip())
                p = p if p.is_absolute() else build / p
                require(inside(p, source) or inside(p, build) or
                        any(inside(p, r) for r in system_roots), "dependency outside frozen/system roots")
                require(len(seen) < 30000, "unique dependency cap")
                headers += 1
                seen.add(str(p.resolve()))
            elif ": #deps " in line:
                require("(VALID)" in line, "Ninja dependency record invalid")
                objects += 1
    require(objects > 0 and headers > 0 and (build / ".ninja_deps").is_file(), "actual deps missing")
    return {"text_capture": pin(capture), "authentic_binary_database": pin(build / ".ninja_deps"),
            "object_records": objects, "header_occurrences": headers, "unique_paths": sorted(seen),
            "text_retirement": "exact owned derivative retired only after manifest, retained DB reconstructs it"}

def validate_contract(plan, contract, args):
    require(contract["status"] == "ADMITTED" and contract["machine_id"] == machine(), "admitted machine")
    require(Path(contract["root"]).resolve() == EXACT_ROOT.resolve(), "unique child root")
    require(contract["hard_bytes"] == HARD and contract["jobs"] in range(1, 5), "finite child/jobs")
    require(contract["source_charge_cap_bytes"] == 96*MIB, "Root approved charged source96MiB")
    require(contract["plan_sha256"] == digest(args.plan) and
            contract["producer_sha256"] == digest(__file__), "plan/producer admission pins")
    require(contract["quota_remaining_bytes"] >= HARD and contract["minimum_free_bytes"] >= 2*1024**3,
            "admission quota/global floor missing")
    require(plan["schema"] == "native30-wholeclean-plan-v1" and plan["production"] == PRODUCTION,
            "production plan scope")
    require(re.fullmatch(r"[0-9a-f]{40}", contract["source_commit"]), "final exact commit")
    require(plan["cmake_defines"] and plan["required_target_defines"].get("xar_ck3_bridge"),
            "final macro contract missing")
    require(not EXACT_ROOT.exists(), "single attempt root already exists")

def read_macro_contract(plan, native=None):
    reference = plan["macro_contract"]
    path = (REPO / reference["path"]).resolve()
    require(inside(path, REPO) and digest(path) == reference["sha256"], "macro receipt pin")
    record = load(path)
    # Explicit finite projections rendered by its source owner, never infer
    # feature defaults or spread one Bridge argv across unrelated targets.
    projected = record["required_target_defines"]
    require(set(projected) == set(PRODUCTION), "three-family macro projection")
    base = {x.split("=", 1)[0]: "1" for x in record["cmake_defines"]}
    expanded = {}
    for target, row in projected.items():
        values = dict(base) if row["base"] == "cmake_ON_as_1" else {}
        for name in row["remove"]: values.pop(name, None)
        values.update(x.split("=", 1) for x in row["add"])
        require(len(values) == row["expanded_XAR_define_count"], "macro projection count")
        expanded[target] = [k + "=" + v for k, v in values.items()]
    native = native or REPO / NATIVE
    files = [native / "CMakeLists.txt", *sorted((native / "cmake").glob("*.cmake"))]
    options = set()
    for p in files:
        options.update(re.findall(r"\boption\s*\(\s*(XAR_\w+)", p.read_text(encoding="utf-8-sig")))
    definitions = {x.split("=", 1)[0]: x.split("=", 1)[1] for x in record["cmake_defines"]}
    missing = []
    for row in projected.values():
        for value in row["add"]:
            name, flag = value.split("=", 1)
            if flag not in ("0", "1"): continue # Version is CMake project metadata, checked on actual TU.
            if name not in options: missing.append(name)
            else: definitions[name] = "ON" if flag == "1" else "OFF"
    require(not missing, "recorded macro has no existing CMake option: " + ",".join(sorted(set(missing))))
    plan["cmake_defines"] = [k + "=" + v for k, v in definitions.items()] + plan["additional_cmake_defines"]
    plan["required_target_defines"] = {k: [] for k in PRODUCTION}
    source_names = {"xar_ck3_bridge": "src/bridge.cpp", "xar_ck3_12002_runtime": "src/ck3_12002.cpp",
                    "xar_bridge_protocol": "src/protocol.cpp"}
    plan["required_source_defines"] = {k + ":" + source_names[k]: v for k, v in expanded.items()}
    for target, values in plan.get("additional_target_defines", {}).items():
        plan["required_target_defines"].setdefault(target, []).extend(values)
    return pin(path)

def execute(args):
    require(os.name == "nt" and args.execute, "explicit Windows execute only")
    require(digest(args.admission) == args.admission_sha256, "admission SHA")
    plan, contract = load(args.plan), load(args.admission)
    macro_pin = read_macro_contract(plan)
    validate_contract(plan, contract, args)
    entries = tree_entries(contract["source_commit"])
    root, build = EXACT_ROOT, EXACT_ROOT / "build"
    root.mkdir(exist_ok=False)
    (root / "evidence").mkdir()
    guard = Guard(root, contract, FileAPI())
    result = {"schema": "native30-wholeclean-result-v1", "machine_id": contract["machine_id"],
              "start_utc": utc(), "admission": pin(args.admission), "plan": pin(args.plan),
              "status": "FAILED", "phases": [], "Game_calls": 0, "DLL_loaded": False,
              "macro_contract": macro_pin}
    try:
        guard(256*MIB)
        rows = freeze(root, contract["source_commit"], entries, guard)
        frozen_repo = root / "source"
        source = frozen_repo / NATIVE
        read_macro_contract(plan, source)
        write(root / "evidence/resolved-plan.json", plan)
        tool = frozen_repo / "tools/run_native_msvc.py"
        common = [sys.executable, "-B", str(tool), "--source-dir", str(source), "--build-dir", str(build),
                  "--configuration", "Release", "--jobs", str(contract["jobs"]),
                  "--defender-external-candidate", "native30-wholeclean"]
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1",
                           GIT_CEILING_DIRECTORIES=str(frozen_repo))
        for key in ("CL", "_CL_", "LINK", "CMAKE_BUILD_PARALLEL_LEVEL"):
            environment.pop(key, None)
        envroot = root / "environment-temp"
        envroot.mkdir()
        environment.update(TEMP=str(envroot), TMP=str(envroot))
        query = build / ".cmake/api/v1/query"
        query.mkdir(parents=True)
        (query / "codemodel-v2").touch()
        definitions = ["CMAKE_EXPORT_COMPILE_COMMANDS=ON", "BUILD_TESTING=ON", *plan["cmake_defines"]]
        configure = root / "evidence/configure"
        configure.mkdir()
        argv = common + ["--evidence-dir", str(configure), "--configure"]
        for value in definitions: argv += ["--cmake-define", value]
        result["phases"].append(run_owned(argv, root, environment, configure / "producer.log", guard))
        temp_closed(build, configure)
        tools = load(configure / "native-msvc-result.json")["tools"]
        binary_tools = {name: Path(tools["cl"]).with_name(name + ".exe") for name in ("dumpbin", "link", "lib")}
        tool_pins = {k: pin(v) for k, v in {**tools, **binary_tools}.items()}
        write(root / "evidence/tool-pins.json", tool_pins)
        selected_names = PRODUCTION + [x["target"] for x in plan["fixtures"]]
        actual_graph = graph(build, source, selected_names, plan["required_target_defines"],
                             plan["allowed_system_roots"], plan.get("required_source_defines"),
                             plan["assertion_targets"])
        write(root / "evidence/selected-fileapi-graph.json", actual_graph)
        selected_sources = {(x["name"], str((Path(row["path"]) if Path(row["path"]).is_absolute()
            else source / row["path"]).resolve())) for x in actual_graph["targets"]
            for row in load(Path(x["fileapi"]["path"])).get("sources", []) if "compileGroupIndex" in row}
        for target, required_sources in plan.get("required_sources", {}).items():
            require(all((target, str((source / value).resolve())) in selected_sources
                        for value in required_sources), "required component TU absent")
        result["phases"].append(run_owned([tools["ninja"], "-C", str(build), "-t", "commands", *selected_names],
            root, environment, root / "evidence/actual-generated-commands.log", guard))
        for number, targets in enumerate([PRODUCTION] + [[x["target"]] for x in plan["fixtures"]]):
            guard(256*MIB)
            stage = root / f"evidence/phase-{number:02d}"
            stage.mkdir()
            source_intact(root, rows)
            require(all(digest(row["path"]) == row["sha256"] for row in tool_pins.values()),
                    "tool bytes changed")
            argv = common + ["--evidence-dir", str(stage), "--build", "--target", *targets]
            result["phases"].append(run_owned(argv, root, environment, stage / "producer.log", guard))
            temp_closed(build, stage)
            if number:
                # Frozen helper has no .git opt-in. Use the original project's
                # existing exact-source Defender registrar explicitly; disabled
                # or admin-missing actual readback blocks EXE execution.
                sys.path.insert(0, str(frozen_repo / "tools"))
                import register_project_exe_exclusions as defender
                manifest = stage / "project-exe-manifest.json"
                receipt_path = stage / "project-exe-receipt.json"
                write(manifest, defender.collect_manifest(REPO, source, build, "Release", targets,
                                                         "native30-wholeclean"))
                result["phases"].append(run_owned([sys.executable, "-B",
                    str(frozen_repo / "tools/register_project_exe_exclusions.py"),
                    "--manifest", str(manifest), "--receipt", str(receipt_path)],
                    root, environment, stage / "registration.log", guard, timeout=240))
                receipt = load(receipt_path)
                require(receipt.get("status") == "verified", "EXE registration/readback unavailable")
                fixture = plan["fixtures"][number - 1]
                image = (build / fixture["artifact"]).resolve()
                require(inside(image, build) and image.is_file(), "fixture artifact identity")
                verified = {os.path.normcase(str(Path(p).resolve())) for p in receipt.get("verified_requested_paths", [])}
                require(os.path.normcase(str(image)) in verified, "exact EXE path not read back")
                fixture_args = [a.replace("$MACHINE_ID", contract["machine_id"]).replace("$OBSERVED_UTC", utc())
                                for a in fixture.get("args", [])]
                result["phases"].append(run_owned([str(image), *fixture_args], build,
                    environment, stage / "fixture.log", guard, timeout=120))
                if fixture.get("postcheck"):
                    checker = frozen_repo / fixture["postcheck"]
                    require(fixture["postcheck"] in TOOLS, "postchecker not frozen")
                    result["phases"].append(run_owned([sys.executable, "-B", str(checker),
                        str(stage / "fixture.log")], root, environment, stage / "postcheck.log", guard))
        deps_capture = envroot / "actual-ninja-deps.txt"
        result["phases"].append(run_owned([tools["ninja"], "-C", str(build), "-t", "deps"],
            root, environment, deps_capture, guard))
        summary = dependencies(build, deps_capture, source, plan["allowed_system_roots"])
        write(root / "evidence/actual-dependencies.json", summary)
        deps_capture.unlink() # Only this reproducible, successful owned text derivative.
        export_log = root / "evidence/actual-exports.log"
        dll = (build / plan["dll_artifact"]).resolve()
        require(inside(dll, build) and dll.is_file(), "production DLL artifact")
        result["phases"].append(run_owned([str(binary_tools["dumpbin"]), "/exports", str(dll)],
            root, environment, export_log, guard))
        exports = re.findall(r"^\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\w+)\s*$",
                             export_log.read_text(errors="strict"), re.M)
        require(sorted(n for _, n in exports) == sorted(plan["exports"]), "five exact exports changed")
        map_file = (build / plan["map_artifact"]).resolve()
        map_text = map_file.read_text(encoding="utf-8", errors="strict")
        require(all(value in map_text for value in plan["required_map_symbols"]), "required component deadstripped/missing")
        archive = (build / plan["runtime_artifact"]).resolve()
        members_log = root / "evidence/runtime-members.log"
        result["phases"].append(run_owned([str(binary_tools["lib"]), "/LIST", str(archive)],
            root, environment, members_log, guard))
        members = members_log.read_text(encoding="utf-8", errors="strict")
        require(all(value in members for value in plan["required_runtime_members"]), "fresh runtime member absent")
        write(root / "evidence/production-delivery.json", {"DLL": pin(dll), "exports": exports,
              "source_commit": contract["source_commit"], "deployed": False,
              "map": pin(map_file), "runtime_archive": pin(archive), "runtime_members": pin(members_log),
              "source_freeze": pin(root / "evidence/source-freeze.json")})
        source_intact(root, rows)
        require(not list(build.rglob("*.pdb")) and not list(build.rglob("*.ilk")), "unexpected debug outputs")
        result["status"] = "BUILT_FIXTURES_PASS_NOT_DEPLOYED"
    except BaseException as error:
        result["error"] = {"type": type(error).__name__, "text": str(error)}
    finally:
        result.update(end_utc=utc(), sampled_peak_eof=guard.peak_eof,
                      sampled_peak_allocation=guard.peak_allocation, guard_samples=guard.samples,
                      last_guard=guard.last, future_writes=0)
        write(root / "evidence/RESULT.json", result)
        final = inventory(root, guard.api)
        write(root / "evidence/FILES-CLOSED.json", {"machine_id": contract["machine_id"],
              "utc": utc(), "files_before_this_manifest": final, "future_writes": 0,
              "sampled_peak_is_not_continuous_peak": True})
        closed = guard()
        print(json.dumps({"closed": pin(root / "evidence/FILES-CLOSED.json"),
                          "actual_final_eof": closed["eof"], "actual_final_allocation": closed["allocation"],
                          "future_writes": 0, "owned_active_after": 0}))
    return 0 if result["status"] == "BUILT_FIXTURES_PASS_NOT_DEPLOYED" else 1

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--admission-sha256")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--inspect-plan", action="store_true", help="Read named CMake/macro source only; no root/configure")
    args = parser.parse_args()
    if args.inspect_plan:
        require(not args.execute, "inspect and execute are exclusive")
        plan = load(args.plan)
        read_macro_contract(plan)
        print(json.dumps({"cmake_defines": plan["cmake_defines"],
                          "source_macro_counts": {k: len(v) for k, v in plan["required_source_defines"].items()}}))
        return 0
    require(args.execute and args.admission and args.admission_sha256, "exact admission and execute required")
    return execute(args)

if __name__ == "__main__": raise SystemExit(main())
