"""Build and seal a finite CMake successor while borrowing immutable link inputs.

This producer does not contact CK3.  The predecessor's recorded source signatures,
actual Ninja dependencies and current include closure select the production TUs
that must be compiled. Changed runtime objects precede the retained archive at
link time; the large archive is never copied or rewritten. CMake still supplies
the actual production/fixture graph, compile commands and artifact identities.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
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
from typing import Protocol, TypedDict, runtime_checkable


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "ck3_autonomous_player/native_bridge/"
PRODUCTION = ("xar_ck3_bridge", "xar_ck3_12002_runtime", "xar_bridge_protocol")
MAX_BUDGET = 160 * 1024 * 1024


class Pin(TypedDict):
    path: str
    bytes: int
    sha256: str


class Execution(TypedDict):
    machine_id: str
    source_commit: str
    started_at_utc: str
    finished_at_utc: str
    argv: list[str]
    cwd: str
    original_wait_returncode: int
    stopped_reason: str | None
    log: Pin
    response_files: list[Pin]
    sampled_allocated_peak_bytes: int
    game_started_or_attached: bool
    actual_live_business_qualified: bool


@dataclass(frozen=True)
class Fixture:
    target: str
    arguments: tuple[str, ...]
    runtime_override_sources: tuple[str, ...]
    runtime_override_definitions: tuple[str, ...]


@dataclass(frozen=True)
class Config:
    machine_id: str
    source_commit: str
    output: Path
    admission: Pin
    budget: int
    baseline: Pin
    complete_build: Path
    incremental_inputs: Pin
    profile_cmake: Pin
    fixtures: tuple[Fixture, ...]
    qualification_targets: tuple[str, ...]
    wire_target: str
    wire_source: str
    wire_directory: str
    wire_packets: tuple[str, ...]


@dataclass(frozen=True)
class Compile:
    target: str
    source: Path
    output: Path
    argv: tuple[str, ...]


@runtime_checkable
class WindowsArguments(Protocol):
    def __call__(self, command: str) -> list[str]: ...


@runtime_checkable
class DependencyParser(Protocol):
    def __call__(self, text: str, baseline: Path) -> dict[str, set[Path]]: ...


@runtime_checkable
class IncludeClosure(Protocol):
    def __call__(self, path: Path, source: Path,
                 memo: dict[Path, set[Path]]) -> set[Path]: ...


@runtime_checkable
class ChildEnvironment(Protocol):
    def __call__(self, build_dir: Path) -> dict[str, str]: ...


@runtime_checkable
class MsvcInstallation(Protocol):
    def __call__(self, requested: Path | None, environment: dict[str, str]) -> Path: ...


@runtime_checkable
class MsvcInitializer(Protocol):
    def __call__(self, installation: Path, build_dir: Path,
                 environment: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]: ...


@runtime_checkable
class ManifestCollector(Protocol):
    def __call__(self, repo: Path, source: Path, build: Path, configuration: str,
                 targets: list[str], external_candidate: str | None = None) -> object: ...


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("JSON object keys must be strings")
        result[key] = item
    return result


def arr(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("JSON array required")
    return list(value)


def string(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("Nonempty JSON string required")
    return value


def strings(value: object) -> tuple[str, ...]:
    return tuple(string(item) for item in arr(value))


def integer(value: object, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError("Exact bounded integer required")
    return value


def read(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding="utf-8-sig"))
    return obj(value)


def pin(path: Path) -> Pin:
    path = path.resolve()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


@lru_cache(maxsize=4)
def compiler_signature(path: str) -> str:
    """CMake may spell the same compiler with a Windows short path."""
    return pin(Path(path))["sha256"]


def parse_pin(value: object) -> Pin:
    row = obj(value)
    require(set(row) == {"path", "bytes", "sha256"}, "Exact pin fields required")
    path, size, digest = string(row["path"]), integer(row["bytes"]), string(row["sha256"])
    require(Path(path).is_absolute() and re.fullmatch(r"[0-9a-f]{64}", digest), "Invalid pin")
    return {"path": path, "bytes": size, "sha256": digest}


def checked(value: object) -> Pin:
    expected = parse_pin(value)
    actual = pin(Path(expected["path"]))
    require(actual == expected, "Pinned input changed: " + expected["path"])
    return actual


def relative(value: object) -> str:
    name = string(value)
    path = Path(name)
    require(not path.is_absolute() and not path.anchor and ".." not in path.parts
            and "\\" not in name and ":" not in name, "Unsafe relative path")
    return path.as_posix()


def target_name(value: object) -> str:
    name = string(value)
    require(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name), "Invalid CMake target")
    return name


def parse_config(value: object) -> Config:
    row = obj(value)
    expected = {"schema", "machine_id", "source_commit", "output_dir", "storage_admission",
                "budget_bytes", "baseline_qualification", "complete_build_dir",
                "incremental_inputs", "profile_cmake", "fixtures", "qualification_targets", "wire"}
    require(set(row) == expected and row["schema"] == "ck3-configured-native-successor-v1",
            "Exact configured successor contract required")
    commit = string(row["source_commit"])
    require(re.fullmatch(r"[0-9a-f]{40}", commit), "Exact source commit required")
    budget = integer(row["budget_bytes"], 1)
    require(budget <= MAX_BUDGET, "Native lane exceeds 160 MiB")
    fixtures: list[Fixture] = []
    for raw in arr(row["fixtures"]):
        item = obj(raw)
        require(set(item) == {"target", "arguments", "runtime_override_sources",
                             "runtime_override_definitions"}, "Exact fixture fields required")
        definitions = strings(item["runtime_override_definitions"])
        require(all(re.fullmatch(r"[A-Z][A-Z0-9_]*=1", flag) for flag in definitions),
                "Fixture override definitions must be explicit enabled macros")
        fixtures.append(Fixture(target_name(item["target"]), strings(item["arguments"]),
            tuple(relative(path) for path in arr(item["runtime_override_sources"])), definitions))
    require(fixtures and len(fixtures) == len({item.target for item in fixtures})
            and not set(PRODUCTION).intersection(item.target for item in fixtures),
            "Distinct finite fixture targets required")
    qualified = tuple(target_name(item) for item in arr(row["qualification_targets"]))
    require(qualified and len(qualified) == len(set(qualified))
            and set(qualified) <= {item.target for item in fixtures}, "Exact qualification fixture subset required")
    wire = obj(row["wire"])
    require(set(wire) == {"target", "source", "directory", "packets"}, "Exact wire fields required")
    wire_target = target_name(wire["target"])
    require(wire_target in {item.target for item in fixtures}, "Wire target must be built and run")
    require(wire_target in qualified, "Wire producer must be selected for qualification")
    output, complete = Path(string(row["output_dir"])), Path(string(row["complete_build_dir"]))
    require(output.is_absolute() and complete.is_absolute() and output != complete
            and not output.is_relative_to(complete) and not complete.is_relative_to(output)
            and not output.resolve().is_relative_to(ROOT.resolve()),
            "Separate absolute output and baseline directories required")
    return Config(string(row["machine_id"]), commit, output.resolve(), parse_pin(row["storage_admission"]),
        budget, parse_pin(row["baseline_qualification"]), complete.resolve(),
        parse_pin(row["incremental_inputs"]), parse_pin(row["profile_cmake"]), tuple(fixtures), qualified,
        wire_target, relative(wire["source"]), relative(wire["directory"]),
        tuple(relative(path) for path in arr(wire["packets"])))


def config_json(config: Config) -> dict[str, object]:
    """The one JSON representation: tuple fields are encoded as JSON arrays."""
    return {"schema": "ck3-configured-native-successor-v1", "machine_id": config.machine_id,
        "source_commit": config.source_commit, "output_dir": str(config.output),
        "storage_admission": config.admission, "budget_bytes": config.budget,
        "baseline_qualification": config.baseline, "complete_build_dir": str(config.complete_build),
        "incremental_inputs": config.incremental_inputs, "profile_cmake": config.profile_cmake,
        "qualification_targets": list(config.qualification_targets),
        "fixtures": [{"target": item.target, "arguments": list(item.arguments),
                      "runtime_override_sources": list(item.runtime_override_sources),
                      "runtime_override_definitions": list(item.runtime_override_definitions)}
                     for item in config.fixtures],
        "wire": {"target": config.wire_target, "source": config.wire_source,
                 "directory": config.wire_directory, "packets": list(config.wire_packets)}}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], cwd=ROOT).decode("utf-8").strip()


def allocated(root: Path) -> int:
    if not root.exists():
        return 0
    total = 4096
    for parent, directories, files in os.walk(root, followlinks=False):
        total += len(directories) * 4096
        for name in files:
            path = Path(parent) / name
            require(not path.is_symlink(), "Native output contains a symbolic link")
            total += ((path.stat().st_size + 4095) // 4096) * 4096
    return total


def load_shared(path: Path, name: str) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "Shared producer unavailable")
    if spec is None or spec.loader is None:
        raise ValueError("Shared producer unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Producer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.native = ROOT / PREFIX
        self.build = config.output / "build"
        self.meta = config.output / "native-a01"
        self.env: dict[str, str] = {}
        self.tools: dict[str, str] = {}
        shared = load_shared(ROOT / "tools/build_native_flag_successor.py", "shared_flag_successor")
        arguments: object = getattr(shared, "windows_args", None)
        dependency_parser: object = getattr(shared, "parse_ninja_dependencies", None)
        closure: object = getattr(shared, "local_include_closure", None)
        require(isinstance(arguments, WindowsArguments) and isinstance(dependency_parser, DependencyParser)
                and isinstance(closure, IncludeClosure), "Shared dependency functions unavailable")
        if not isinstance(arguments, WindowsArguments) or not isinstance(dependency_parser, DependencyParser) or not isinstance(closure, IncludeClosure):
            raise ValueError("Shared dependency functions unavailable")
        self.arguments = arguments
        self.dependencies = dependency_parser
        self.closure = closure

    def gate(self) -> None:
        c = self.config
        require(git("rev-parse", "HEAD") == c.source_commit and not git("status", "--porcelain", "--untracked-files=all"),
                "Exact clean committed Root required")
        checked(c.admission)
        admission = read(Path(c.admission["path"]))
        require(admission.get("machine_id") == c.machine_id and admission.get("active") is True
                and admission.get("capacity_passed") is True and admission.get("quota_passed") is True,
                "Active machine-bound storage admission required")
        approved = Path(string(admission.get("approved_root"))).resolve()
        require(c.output.is_relative_to(approved) and c.output != approved,
                "Native output escapes the admitted scene root")
        expiry = datetime.fromisoformat(string(admission.get("expires_at_utc")).replace("Z", "+00:00"))
        require(datetime.now(timezone.utc) < expiry, "Storage admission expired")
        floor = integer(admission.get("required_free_bytes"))
        require(shutil.disk_usage(c.output.parent).free >= floor, "Admitted free-space floor no longer holds")
        require(allocated(c.output) < c.budget, "Native lane budget exhausted")

    def save(self, name: str, value: object) -> Pin:
        raw = (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode()
        require(allocated(self.config.output) + len(raw) + 8192 < self.config.budget, "Native metadata budget exhausted")
        path = self.config.output / relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
        return pin(path)

    def execute(self, name: str, argv: list[str], cwd: Path, timeout: int = 180) -> Pin:
        self.gate()
        started, begin = now(), time.monotonic()
        log = self.config.output / (name + ".log")
        peak, reason = allocated(self.config.output), None
        responses: list[Pin] = []
        for value in argv:
            if value.startswith("@"):
                response = Path(value[1:])
                responses.append(pin(response if response.is_absolute() else cwd / response))
        with log.open("xb") as stream:
            process = subprocess.Popen(argv, cwd=cwd, env=self.env, stdout=stream, stderr=subprocess.STDOUT)
            while process.poll() is None:
                peak = max(peak, allocated(self.config.output))
                if peak + 4 * 1024 * 1024 >= self.config.budget or time.monotonic() - begin > timeout:
                    reason = "budget-or-timeout"
                    process.terminate()
                    break
                time.sleep(0.2)
            code = process.wait(timeout=30)
        for response_ref in responses:
            checked(response_ref)
        evidence: Execution = {"machine_id": self.config.machine_id, "source_commit": self.config.source_commit,
            "started_at_utc": started, "finished_at_utc": now(), "argv": argv, "cwd": str(cwd),
            "original_wait_returncode": code, "stopped_reason": reason, "log": pin(log),
            "response_files": responses,
            "sampled_allocated_peak_bytes": max(peak, allocated(self.config.output)), "game_started_or_attached": False,
            "actual_live_business_qualified": False}
        receipt = self.save(name + ".actual.json", evidence)
        require(code == 0 and reason is None, "Actual command failed: " + name)
        return receipt

    def initialize(self) -> None:
        actual_machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8",
            str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT).decode("utf-8").strip()
        require(actual_machine == self.config.machine_id, "Actual machine identity differs from admission")
        self.gate()
        self.config.output.mkdir(exist_ok=False)
        self.build.mkdir()
        shared = load_shared(ROOT / "tools/run_native_msvc.py", "shared_native_msvc")
        child: object = getattr(shared, "child_environment", None)
        install: object = getattr(shared, "visual_studio_installation", None)
        initialize: object = getattr(shared, "initialize_msvc", None)
        if not isinstance(child, ChildEnvironment) or not isinstance(install, MsvcInstallation) or not isinstance(initialize, MsvcInitializer):
            raise ValueError("Shared MSVC initializer contract unavailable")
        self.env = child(self.build)
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"
        self.env, self.tools = initialize(install(None, self.env), self.build, self.env)
        require(not any(self.env.get(key) for key in ("CL", "_CL_", "LINK")), "Ambient compiler options refused")

    def configure(self) -> Pin:
        checked(self.config.profile_cmake)
        query = self.build / ".cmake/api/v1/query"
        query.mkdir(parents=True)
        (query / "codemodel-v2").write_bytes(b"")
        return self.execute("configure", [self.tools["cmake"], "-S", str(self.native), "-B", str(self.build),
            "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            "-DCMAKE_CXX_COMPILER=" + self.tools["cl"], "-DCMAKE_MAKE_PROGRAM=" + self.tools["ninja"],
            "-DCMAKE_PROJECT_TOP_LEVEL_INCLUDES=" + self.config.profile_cmake["path"]], self.config.output)

    def commands(self) -> list[Compile]:
        value: object = json.loads((self.build / "compile_commands.json").read_text(encoding="utf-8-sig"))
        result: list[Compile] = []
        for raw in arr(value):
            row = obj(raw)
            output = Path(string(row["output"]))
            output = output if output.is_absolute() else self.build / output
            parts = output.relative_to(self.build).parts
            if len(parts) < 2 or parts[0] != "CMakeFiles" or not parts[1].endswith(".dir"):
                continue
            result.append(Compile(parts[1][:-4], Path(string(row["file"])).resolve(), output,
                                  tuple(self.arguments(string(row["command"])))))
        return result

    def normalize(self, command: tuple[str, ...], source: Path, build: Path) -> list[str]:
        source_text, build_text = source.as_posix().lower(), build.as_posix().lower()
        require(command, "Actual compiler command must be nonempty")
        return ["compiler:" + compiler_signature(command[0]), *[
            token.replace("\\", "/").lower().replace(source_text, "@native@").replace(build_text, "@build@")
            for token in command[1:]]]

    def plan(self, rows: list[Compile]) -> tuple[list[Compile], dict[str, Path], Pin]:
        c = self.config
        baseline_ref = checked(c.baseline)
        baseline = read(Path(baseline_ref["path"]))
        require(baseline.get("machine_id") == c.machine_id, "Baseline belongs to another machine")
        snapshot = read(Path(checked(baseline["snapshot"])["path"]))
        old_native = Path(string(snapshot["snapshot_native_base"]))
        old_files: dict[str, tuple[int, str]] = {}
        for raw in arr(snapshot["files"]):
            snapshot_row = obj(raw)
            name = relative(snapshot_row["native_relative"])
            require(name not in old_files, "Duplicate baseline source")
            old_files[name] = (integer(snapshot_row["bytes"]), string(snapshot_row["sha256"]))
        current: dict[str, Pin] = {}
        for name in git("ls-files", "--", PREFIX).splitlines():
            current[name.removeprefix(PREFIX)] = pin(ROOT / name)
        changed_names = {name for name in old_files.keys() | current.keys()
                         if name not in old_files or name not in current
                         or old_files[name] != (current[name]["bytes"], current[name]["sha256"])}
        dependency_query = subprocess.run([self.tools["ninja"], "-C", str(c.complete_build), "-t", "deps"],
            env=self.env, capture_output=True, check=True, text=True, encoding="utf-8")
        dependency_file = self.config.output / "original-ninja-dependencies.txt"
        dependency_file.write_text(dependency_query.stdout, encoding="utf-8")
        dependencies = self.dependencies(dependency_query.stdout, c.complete_build)
        baseline_scope = read(Path(checked(baseline["configured_scope"])["path"]))
        old_commands_raw: object = json.loads(Path(checked(baseline_scope["compile_commands"])["path"])
                                            .read_text(encoding="utf-8-sig"))
        old_commands: dict[str, tuple[str, ...]] = {}
        old_build = Path(string(obj(arr(old_commands_raw)[0])["directory"]))
        for raw in arr(old_commands_raw):
            item = obj(raw)
            output = Path(string(item["output"]))
            output = output if output.is_absolute() else old_build / output
            old_commands[output.relative_to(old_build).as_posix()] = tuple(self.arguments(string(item["command"])))
        original_complete_source: Path | None = None
        for paths in dependencies.values():
            for path in paths:
                if path.name == "activity_typed_planner_v1.hpp":
                    original_complete_source = path.parent.parent.parent
                    break
            if original_complete_source is not None:
                break
        require(original_complete_source is not None, "Complete baseline source root unavailable")
        if original_complete_source is None:
            raise ValueError("Complete baseline source root unavailable")
        prior_inputs = read(Path(checked(c.incremental_inputs)["path"]))
        retained = [checked(raw) for raw in arr(prior_inputs["inputs"])]
        replacements: dict[str, Path] = {}
        new_object = checked(prior_inputs["new_object"])
        new_path = Path(new_object["path"])
        marker = new_path.parts.index("CMakeFiles")
        replacements[Path(*new_path.parts[marker:]).as_posix()] = new_path
        selected: list[Compile] = []
        selection: list[dict[str, object]] = []
        memo: dict[Path, set[Path]] = {}
        production_rows = [row for row in rows if row.target in PRODUCTION]
        require({row.target for row in production_rows} == set(PRODUCTION), "Incomplete production commands")
        for row in production_rows:
            output_name = row.output.relative_to(self.build).as_posix()
            require(output_name in old_commands and self.normalize(row.argv, self.native, self.build)
                    == self.normalize(old_commands[output_name], old_native, old_build),
                    "Production compile options changed: " + output_name)
            relative_source = row.source.relative_to(self.native).as_posix()
            old_dependencies = dependencies.get(output_name)
            require(old_dependencies is not None, "Actual old compiler dependencies missing: " + output_name)
            old_names = {path.relative_to(original_complete_source).as_posix() for path in old_dependencies or set()
                         if path.is_relative_to(original_complete_source)}
            new_names = {path.relative_to(self.native).as_posix() for path in self.closure(row.source, self.native, memo)
                         if path.is_relative_to(self.native)}
            affected = sorted(changed_names.intersection(old_names | new_names | {relative_source}))
            if affected:
                selected.append(row)
            selection.append({"target": row.target, "output": output_name, "source": relative_source,
                              "changed_dependencies": affected, "compiled": bool(affected)})
        require(selected, "No changed production input; refusing to relabel an old native qualification")
        retained_map = {Path(item["path"]).resolve(): item for item in retained}
        borrowed: dict[str, Path] = {}
        for row in production_rows:
            if row.target != "xar_ck3_bridge":
                continue
            name = row.output.relative_to(self.build).as_posix()
            path = replacements.get(name, c.complete_build / name)
            require(path in retained_map or path == new_path, "Bridge object lacks predecessor link provenance")
            borrowed[name] = path
        report = self.save("native-a01/PLAN.actual.json", {"machine_id": c.machine_id,
            "observed_at_utc": now(), "source_commit": c.source_commit,
            "baseline_qualification": baseline_ref, "baseline_incremental_inputs": c.incremental_inputs,
            "original_dependencies": pin(dependency_file), "changed_native_paths": sorted(changed_names),
            "production_selections": selection, "retained_link_inputs": retained,
            "retained_incremental_object": new_object, "archive_copies": 0})
        return selected, borrowed, report

    def compile(self, row: Compile, label: str, definitions: tuple[str, ...] = ()) -> Pin:
        row.output.parent.mkdir(parents=True, exist_ok=True)
        argv = ["/c" if token == "-c" else token for token in row.argv]
        argv.extend("/D" + definition for definition in definitions)
        return self.execute(label, argv, self.build)

    def fixture_link_objects(self, fixture: Fixture) -> list[Path]:
        """Read the actual Ninja link edge, including generated ON/OFF objects."""
        lines = (self.build / "build.ninja").read_text(encoding="utf-8-sig").splitlines()
        matches = [line for line in lines if line.startswith("build " + fixture.target + ".exe:")]
        require(len(matches) == 1, "Exact finite executable link edge required")
        edge = matches[0].split(": ", 1)[1].split(" ", 1)[1].split(" |", 1)[0]
        require("$" not in edge, "Escaped Ninja object paths require an explicit parser")
        paths = [Path(token) for token in self.arguments(edge)]
        require(paths and all(path.suffix == ".obj" for path in paths), "Finite edge has unexpected direct inputs")
        return [path if path.is_absolute() else self.build / path for path in paths]

    def link(self, label: str, objects: list[Path], libraries: list[Path], destination: Path,
             dll: bool = False) -> Pin:
        linker = Path(self.tools["cl"]).parent / "link.exe"
        arguments = ["/nologo", "/MACHINE:X64", "/INCREMENTAL:NO", "/OPT:REF",
                     "/OUT:" + str(destination), *map(str, objects), *map(str, libraries),
                     "bcrypt.lib", "kernel32.lib", "user32.lib", "gdi32.lib", "winspool.lib",
                     "shell32.lib", "ole32.lib", "oleaut32.lib", "uuid.lib", "comdlg32.lib", "advapi32.lib"]
        if dll:
            arguments.extend(["/DLL", "/IMPLIB:" + str(destination.with_suffix(".lib"))])
        response = self.build / (label + ".rsp")
        response.write_text(subprocess.list2cmdline(arguments), encoding="utf-8")
        return self.execute(label, [str(linker), "@" + str(response)], self.build)

    def run(self) -> Pin:
        self.initialize()
        self.configure()
        rows = self.commands()
        selected, borrowed, plan = self.plan(rows)
        compiled: dict[Path, Pin] = {}
        production_compiles: list[dict[str, object]] = []
        for index, row in enumerate(selected):
            compiled[row.output] = self.compile(row, "production-compile-" + str(index))
            production_compiles.append({"target": row.target, "source": pin(row.source),
                "object": pin(row.output), "actual_compile": compiled[row.output]})
        runtime_objects = [row.output for row in selected if row.target == "xar_ck3_12002_runtime"]
        bridge_objects = [row.output if row.output in compiled else borrowed[row.output.relative_to(self.build).as_posix()]
                          for row in rows if row.target == "xar_ck3_bridge"]
        libraries = [self.config.complete_build / "xar_bridge_protocol.lib",
                     self.config.complete_build / "xar_ck3_12002_runtime.lib"]
        plan_value = read(Path(plan["path"]))
        retained_refs = [parse_pin(item) for item in arr(plan_value["retained_link_inputs"])]
        retained_paths = {Path(item["path"]).resolve() for item in retained_refs}
        require(set(libraries) <= retained_paths, "Production libraries lack predecessor link provenance")
        dll = self.build / "xar_ck3_bridge.dll"
        production_execution = self.link("link-production", bridge_objects + runtime_objects, libraries, dll, True)
        self.save("native-a01/INCREMENTAL-RESULT.actual.json", {"machine_id": self.config.machine_id,
            "observed_at_utc": now(), "source_commit": self.config.source_commit,
            "production_plan": plan, "production_compiles": production_compiles,
            "actual_link": production_execution, "dll": pin(dll), "archive_copies": 0,
            "retained_archive_mode": "Changed complete runtime objects precede unchanged original archive",
            "game_started_or_attached": False})
        fixture_results: list[dict[str, object]] = []
        by_output = {row.output: row for row in rows}
        for fixture in self.config.fixtures:
            actual_objects = self.fixture_link_objects(fixture)
            own_rows = [by_output[path] for path in actual_objects if path in by_output
                        and by_output[path].target not in PRODUCTION]
            require(own_rows, "Configured finite fixture missing: " + fixture.target)
            own: list[Path] = []
            for index, row in enumerate(own_rows):
                if row.output not in compiled:
                    compiled[row.output] = self.compile(row, fixture.target + "-compile-" + str(index))
                own.append(row.output)
            for path in actual_objects:
                if path not in by_output or by_output[path].target not in PRODUCTION:
                    continue
                if path in compiled:
                    own.append(path)
                else:
                    own.append(borrowed[path.relative_to(self.build).as_posix()])
            overrides: list[Path] = []
            for index, name in enumerate(fixture.runtime_override_sources):
                original = next((row for row in rows if row.target == "xar_ck3_12002_runtime"
                                 and row.source == self.native / name), None)
                require(original is not None, "Fixture override must be a production TU")
                if original is None:
                    raise ValueError("Fixture override TU missing")
                output = self.build / "fixture-overrides" / fixture.target / (Path(name).name + ".obj")
                argv = tuple("/Fo" + str(output) if item.startswith("/Fo") else item for item in original.argv)
                replacement = Compile(fixture.target, original.source, output, argv)
                self.compile(replacement, fixture.target + "-override-" + str(index), fixture.runtime_override_definitions)
                overrides.append(output)
            override_sources = {self.native / name for name in fixture.runtime_override_sources}
            for row in own_rows:
                override_sources.update(self.closure(row.source, self.native, {}))
            runtime = [row.output for row in selected if row.target == "xar_ck3_12002_runtime"
                       and row.source not in override_sources]
            executable = self.build / (fixture.target + ".exe")
            self.link(fixture.target + "-link", own + overrides + runtime, libraries, executable)
            fixture_results.append({"target": fixture.target, "executable": pin(executable)})
        all_defender_binding = self.defender(fixture_results, "all-fixtures")
        for fixture, result in zip(self.config.fixtures, fixture_results, strict=True):
            arguments = [value.replace("{output}", str(self.config.output)).replace("{build}", str(self.build))
                         for value in fixture.arguments]
            result["execution"] = self.execute("test-" + fixture.target,
                [str(self.build / (fixture.target + ".exe")), *arguments], self.build)
        self.gate()
        for retained in retained_refs:
            checked(retained)
        checked(plan_value["retained_incremental_object"])
        self.save("native-a01/ALL-FIXTURES.actual.json", {"machine_id": self.config.machine_id,
            "observed_at_utc": now(), "source_commit": self.config.source_commit,
            "fixture_results": fixture_results, "defender_binding": all_defender_binding,
            "actual_live_business_qualified": False})
        qualified = [item for item in fixture_results if item["target"] in self.config.qualification_targets]
        defender_binding = self.defender(qualified, "qualification-subset")
        return self.seal(rows, qualified, production_execution, defender_binding, plan, dll)

    def defender(self, fixtures: list[dict[str, object]], label: str) -> Pin:
        manifest = self.config.output / (label + "-defender-manifest.json")
        receipt = self.config.output / (label + "-defender-receipt.json")
        shared = load_shared(ROOT / "tools/register_project_exe_exclusions.py", "shared_successor_defender")
        collector: object = getattr(shared, "collect_manifest", None)
        if not isinstance(collector, ManifestCollector):
            raise ValueError("Shared Defender manifest collector unavailable")
        value = collector(ROOT, self.native, self.build, "Release", [string(row["target"]) for row in fixtures])
        with manifest.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
        argv = [str(ROOT / "tools/.venv/Scripts/python.exe"), "-B", "-X", "utf8",
            str(ROOT / "tools/register_project_exe_exclusions.py"), "--manifest", str(manifest), "--receipt", str(receipt)]
        self.execute(label + "-defender-register", argv, ROOT, 120)
        value = read(receipt)
        require(value.get("status") == "verified" and value.get("admin_token") is True,
                "Administrative exact EXE exclusion readback required")
        return self.save("native-a01/" + label + "-defender-binding.actual.json", {"machine_id": self.config.machine_id,
            "observed_at_utc": now(), "status": "verified", "exact_executable_count": len(fixtures),
            "manifest": pin(manifest), "receipt": pin(receipt)})

    def seal(self, rows: list[Compile], fixtures: list[dict[str, object]], build_execution: Pin,
             defender: Pin, plan: Pin, dll: Path) -> Pin:
        c = self.config
        sources: list[dict[str, object]] = []
        for name in git("ls-files", "--", PREFIX).splitlines():
            actual = pin(ROOT / name)
            sources.append({"native_relative": name.removeprefix(PREFIX),
                            "bytes": actual["bytes"], "sha256": actual["sha256"]})
        snapshot = self.save("native-a01/SOURCE.actual.json", {"machine_id": c.machine_id,
            "observed_at_utc": now(), "root_commit": c.source_commit, "native_source_commit": c.source_commit,
            "source_count": len(sources), "files": sources, "Root_native_source_base": str(self.native),
            "snapshot_native_base": str(self.native), "source_mapping": "exact current clean committed source; no copy"})
        verification = self.save("native-a01/SOURCE-VERIFICATION.actual.json", {"machine_id": c.machine_id,
            "observed_at_utc": now(), "root_commit": c.source_commit, "source_manifest": snapshot,
            "all_snapshot_files_exactly_verified": len(sources), "all_original_inputs_still_exactly_verified": len(sources)})
        reply = self.build / ".cmake/api/v1/reply"
        index_path = max(reply.glob("index-*.json"), key=lambda path: path.stat().st_mtime_ns)
        index = read(index_path)
        model_entry = next(obj(item) for item in arr(index["objects"]) if obj(item).get("kind") == "codemodel")
        model_path = reply / string(model_entry["jsonFile"])
        model = read(model_path)
        entries = [obj(item) for item in arr(obj(arr(model["configurations"])[0])["targets"])]
        targets = {string(item["id"]): read(reply / relative(item["jsonFile"])) for item in entries}
        names = {string(item["name"]): string(item["id"]) for item in entries}
        production: dict[str, dict[str, object]] = {}
        pending = [names["xar_ck3_bridge"]]
        while pending:
            key = pending.pop()
            if key in production:
                continue
            production[key] = targets[key]
            pending.extend(string(obj(item)["id"]) for item in arr(targets[key].get("dependencies", []))
                           if string(obj(item)["id"]) in targets)
        require({string(item["name"]) for item in production.values()} == set(PRODUCTION),
                "Unexpected production dependency closure")
        counts = {string(item["name"]): sum("compileGroupIndex" in obj(source) for source in arr(item.get("sources", [])))
                  for item in production.values()}
        counts_from_commands = {name: sum(row.target == name for row in rows) for name in PRODUCTION}
        require(counts == counts_from_commands, "Actual production graph differs from compile commands")
        scope = self.save("native-a01/CONFIGURED-SCOPE.actual.json", {"machine_id": c.machine_id,
            "observed_at_utc": now(), "production_TUs": counts, "requested_EXEs": list(c.qualification_targets),
            "no_fixture_in_production": True, "targets": [
                {key: item.get(key, []) for key in ("name", "type", "sources", "compileGroups", "artifacts")}
                for item in [*production.values(), *(targets[names[target]] for target in c.qualification_targets)]],
            "codemodel": pin(model_path), "index": pin(index_path), "compile_commands": pin(self.build / "compile_commands.json"),
            "snapshot": snapshot})
        baseline = read(Path(c.baseline["path"]))
        profile_ref = checked(baseline["profile"])
        profile = read(Path(profile_ref["path"]))
        flags = {line.split(":", 1)[0]: line.split("=", 1)[1] for line in
                 (self.build / "CMakeCache.txt").read_text(encoding="utf-8-sig").splitlines() if ":BOOL=" in line}
        require(all(flags.get(key) == value for key, value in obj(profile["flags"]).items()), "Profile flag drift")
        dll_pin = pin(dll)
        freeze = self.save("native-a01/PRODUCTION-DLL-FROZEN.actual.json", {"machine_id": c.machine_id,
            "observed_at_utc": now(), "root_commit": c.source_commit, "original_DLL": dll_pin,
            "published_DLL": dll_pin, "build_execution": build_execution, "source_manifest": snapshot,
            "source_verification": verification, "profile": profile_ref, "scope": scope,
            "no_fixture_target_in_production_dependency_closure": True, "repository_default_flags_changed": False,
            "game_started_or_attached": False, "incremental_production_plan": plan,
            "incremental_production_result": pin(c.output / "native-a01/INCREMENTAL-RESULT.actual.json")})
        wire_fixture = next(item for item in fixtures if item["target"] == c.wire_target)
        wire_root = c.output / c.wire_directory
        wire = self.save("native-a01/WIRE-PACKETS.actual.json", {"machine_id": c.machine_id,
            "observed_at_utc": now(), "source_commit": c.source_commit, "packet_kind": "pilgrimage_execution",
            "status": "ACTUAL_PRODUCTION_SERIALIZER_PACKETS_OVER_OWNED_DTOS_NOT_LIVE",
            "source": pin(self.native / c.wire_source), "executable": wire_fixture["executable"],
            "execution": wire_fixture["execution"], "packets": [pin(wire_root / name) for name in c.wire_packets],
            "provenance": pin(wire_root / "PROVENANCE.json"), "owned_result_dtos": True,
            "game_queried": False, "native_runtime_qualified": False, "actual_live_business_qualified": False})
        delivery = self.save("native-a01/DELIVERY.actual.json", {"machine_id": c.machine_id,
            "observed_at_utc": now(), "root_commit": c.source_commit, "actual_live_business_qualified": False,
            "all_original_build_and_fixture_Popen_waits_recorded": True, "snapshot": snapshot,
            "profile": profile_ref, "scope": scope, "source_verification": verification,
            "production_freeze": freeze, "published_dll": dll_pin, "Defender_settings_verified": defender,
            "finite_tests": [{"name": item["target"], "execution": item["execution"], "exe": item["executable"]}
                             for item in fixtures], "game_started_or_attached": False,
            "complete_finite_regression": pin(c.output / "native-a01/ALL-FIXTURES.actual.json")})
        return self.save("native-a01/PUBLIC-RUNTIME-QUALIFICATION.actual.json", {
            "schema": "ck3-qualified-native-build-v1", "machine_id": c.machine_id,
            "observed_at_utc": now(), "source_commit": c.source_commit, "actual_live_business_qualified": False,
            "delivery": delivery, "snapshot": snapshot, "profile": profile_ref, "configured_scope": scope,
            "source_verification": verification, "production_freeze": freeze, "original_dll": dll_pin,
            "published_dll": dll_pin, "production_build_receipt": build_execution,
            "defender_binding": defender, "fixture_results": fixtures, "execution_wire_packets": wire})


def main() -> int:
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = parse_config(read(args.config))
    result = Producer(config).run()
    print(json.dumps({"qualified_native": result, "game_started": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
