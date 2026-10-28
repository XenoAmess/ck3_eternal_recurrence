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
from typing import Literal, NotRequired, Protocol, TypedDict, runtime_checkable


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "ck3_autonomous_player/native_bridge/"
PRODUCTION = ("xar_ck3_bridge", "xar_ck3_12002_runtime", "xar_bridge_protocol")
MAX_BUDGET = 192 * 1024 * 1024
NONCOMPILED_CONSUMER_RELATIVE = "research/refill_add_live_12004/consume_live_refill_add.py"
HOST_TEST_COMPANION_RELATIVE = "research/test_ck3_12002_mcp_live.py"


class Pin(TypedDict):
    path: str
    bytes: int
    sha256: str


class NoncompiledConsumerReplay(TypedDict):
    before_blob: Pin
    after: Pin
    binding: Pin


class RetainedDependencyEvidence(TypedDict):
    qualification: Pin


class RetainedDependencyReuse(TypedDict):
    qualification: Pin
    production_freeze: Pin
    production_plan: Pin
    current_capture: Pin
    stale_outputs: list[str]


@dataclass(frozen=True)
class NinjaDependencyRecord:
    output: str
    status: Literal["VALID", "STALE"]
    normalized: bytes


@dataclass(frozen=True)
class NoncompiledReplayProof:
    replay: NoncompiledConsumerReplay
    originals: dict[str, Pin]
    currents: dict[str, Pin]


@runtime_checkable
class NativeSourceCheckoutQualifier(Protocol):
    def __call__(self, binding_path: Path | None, *, root: Path, runtime_commit: str,
                 native_commit: str, machine: str, qualified_native_ref: object,
                 qualification: dict[str, object], snapshot_ref: object,
                 snapshot: dict[str, object], native_shared_python_host_delta: Path | None = None
                 ) -> dict[str, object]: ...


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


class PreservedOutput(TypedDict):
    original: Pin
    preserved_path: str
    file_id: str
    device_id: str
    preserved: NotRequired[Pin]


class FixtureLinkResult(TypedDict):
    target: str
    executable: Pin
    actual_link: Pin


class FixtureProductionObjectBinding(TypedDict):
    configured_object: str
    object: Pin
    production_target: str
    native_relative: str
    source: Pin
    configured_compile_command_index: int


@dataclass(frozen=True)
class FixtureObjectProof:
    objects: list[FixtureProductionObjectBinding]
    production_plan: Pin
    incremental_production_result: Pin
    baseline_compile_commands: Pin
    original_dependencies: Pin


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
    compiled_seed: Pin | None = None
    retained_dependency_evidence: RetainedDependencyEvidence | None = None
    schema: Literal["ck3-configured-native-successor-v1", "ck3-configured-native-successor-v2", "ck3-configured-native-successor-v3"] = "ck3-configured-native-successor-v1"
    predecessor_qualification: Pin | None = None
    native_source_dir: Path | None = None
    development_build_dir: Path | None = None


@dataclass(frozen=True)
class Compile:
    target: str
    source: Path
    output: Path
    argv: tuple[str, ...]


@dataclass(frozen=True)
class QualifiedPredecessor:
    qualification: Pin
    snapshot: Pin
    compile_commands: Pin
    dependencies: Pin
    source_root: Path
    objects: dict[str, Pin]
    libraries: tuple[Pin, ...]
    source_signatures: dict[str, tuple[int, str]]


@dataclass(frozen=True)
class SeedCompile:
    source: Pin
    object: Pin
    execution: Pin


@dataclass(frozen=True)
class FixtureInputs:
    compiled: dict[Path, Pin]
    object_paths: dict[Path, Path]
    borrowed: dict[str, Path]
    libraries: list[Path]
    retained: list[Pin]
    plan: Pin
    production_execution: Pin
    dll: Path


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


@runtime_checkable
class FixtureObjectReader(Protocol):
    def __call__(self, target: dict[str, object], snapshot_root: Path, build_root: Path) -> set[Path]: ...


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
                "incremental_inputs", "profile_cmake", "fixtures", "qualification_targets", "wire", "compiled_seed"}
    schema = row.get("schema")
    require(schema in ("ck3-configured-native-successor-v1", "ck3-configured-native-successor-v2", "ck3-configured-native-successor-v3"),
            "Unsupported configured successor version")
    if schema in ("ck3-configured-native-successor-v2", "ck3-configured-native-successor-v3"):
        expected.add("retained_dependency_evidence")
    if schema == "ck3-configured-native-successor-v3":
        expected.update(("predecessor_qualification", "native_source_dir", "development_build_dir"))
    require(set(row) == expected,
            "Exact configured successor contract required")
    evidence: RetainedDependencyEvidence | None = None
    if schema == "ck3-configured-native-successor-v2" and row["retained_dependency_evidence"] is not None:
        declaration = obj(row["retained_dependency_evidence"])
        require(set(declaration) == {"qualification"}, "Exact retained dependency evidence required")
        evidence = {"qualification": parse_pin(declaration["qualification"])}
    require(evidence is None or row["compiled_seed"] is None,
            "Retained dependencies and compiled seed are distinct authorities")
    commit = string(row["source_commit"])
    require(re.fullmatch(r"[0-9a-f]{40}", commit), "Exact source commit required")
    budget = integer(row["budget_bytes"], 1)
    require(budget <= MAX_BUDGET, "Native lane exceeds 192 MiB")
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
    if schema == "ck3-configured-native-successor-v3":
        require(row["compiled_seed"] is None and row["retained_dependency_evidence"] is None,
                "A qualified predecessor is separate from compiled seeds/retained-dependency authority")
        development = Path(string(row["development_build_dir"]))
        native_source = Path(string(row["native_source_dir"]))
        require(development.is_absolute() and native_source.is_absolute()
                and development.parent.resolve() == output.parent.resolve() == native_source.parent.resolve()
                and len({development.resolve(), native_source.resolve(), output.resolve()}) == 3
                and not native_source.resolve().is_relative_to(ROOT.resolve()),
                "Separate native source/build and attempt directories in one external development root required")
    require(output.is_absolute() and complete.is_absolute() and output != complete
            and not output.is_relative_to(complete) and not complete.is_relative_to(output)
            and not output.resolve().is_relative_to(ROOT.resolve()),
            "Separate absolute output and baseline directories required")
    return Config(string(row["machine_id"]), commit, output.resolve(), parse_pin(row["storage_admission"]),
        budget, parse_pin(row["baseline_qualification"]), complete.resolve(),
        parse_pin(row["incremental_inputs"]), parse_pin(row["profile_cmake"]), tuple(fixtures), qualified,
        wire_target, relative(wire["source"]), relative(wire["directory"]),
        tuple(relative(path) for path in arr(wire["packets"])),
        None if row["compiled_seed"] is None else parse_pin(row["compiled_seed"]), evidence,
        "ck3-configured-native-successor-v3" if schema == "ck3-configured-native-successor-v3" else
        ("ck3-configured-native-successor-v2" if schema == "ck3-configured-native-successor-v2"
        else "ck3-configured-native-successor-v1"),
        None if schema != "ck3-configured-native-successor-v3" else parse_pin(row["predecessor_qualification"]),
        None if schema != "ck3-configured-native-successor-v3" else Path(string(row["native_source_dir"])).resolve(),
        None if schema != "ck3-configured-native-successor-v3" else Path(string(row["development_build_dir"])).resolve())


def config_json(config: Config) -> dict[str, object]:
    """The one JSON representation: tuple fields are encoded as JSON arrays."""
    require(config.schema in ("ck3-configured-native-successor-v2", "ck3-configured-native-successor-v3") or config.retained_dependency_evidence is None,
            "Retained dependencies require the v2 contract")
    require(config.schema == "ck3-configured-native-successor-v3" or all(value is None for value in
        (config.predecessor_qualification, config.native_source_dir, config.development_build_dir)),
        "Development predecessor/source/build fields require the v3 contract")
    result: dict[str, object] = {"schema": config.schema, "machine_id": config.machine_id,
        "source_commit": config.source_commit, "output_dir": str(config.output),
        "storage_admission": config.admission, "budget_bytes": config.budget,
        "baseline_qualification": config.baseline, "complete_build_dir": str(config.complete_build),
        "incremental_inputs": config.incremental_inputs, "profile_cmake": config.profile_cmake,
        "qualification_targets": list(config.qualification_targets),
        "compiled_seed": config.compiled_seed,
        "fixtures": [{"target": item.target, "arguments": list(item.arguments),
                      "runtime_override_sources": list(item.runtime_override_sources),
                      "runtime_override_definitions": list(item.runtime_override_definitions)}
                     for item in config.fixtures],
        "wire": {"target": config.wire_target, "source": config.wire_source,
                 "directory": config.wire_directory, "packets": list(config.wire_packets)}}
    if config.schema in ("ck3-configured-native-successor-v2", "ck3-configured-native-successor-v3"):
        result["retained_dependency_evidence"] = config.retained_dependency_evidence
    if config.schema == "ck3-configured-native-successor-v3":
        require(config.predecessor_qualification is not None and config.native_source_dir is not None
                and config.development_build_dir is not None, "Complete v3 development contract required")
        result.update(predecessor_qualification=config.predecessor_qualification,
            native_source_dir=str(config.native_source_dir), development_build_dir=str(config.development_build_dir))
    return result


def strict_ninja_dependency_records(reference: Pin) -> tuple[NinjaDependencyRecord, ...]:
    """Preserve the full capture, including ordered dependencies and line endings."""
    require(reference["bytes"] <= 16 * 1024 * 1024, "Dependency capture exceeds the finite input limit")
    raw = Path(checked(reference)["path"]).read_bytes()
    records: list[NinjaDependencyRecord] = []
    seen: set[str] = set()
    lines = raw.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        header = lines[index]
        match = re.fullmatch(rb"([^\r\n]+): #deps (0|[1-9][0-9]*), deps mtime ([0-9]+) \((VALID|STALE)\)(\r?\n)", header)
        require(match is not None, "Malformed Ninja dependency header")
        if match is None:
            raise ValueError("Malformed Ninja dependency header")
        name = relative(match[1].decode("utf-8"))
        require(name == match[1].decode("utf-8") and name.startswith("CMakeFiles/")
                and name.endswith(".obj") and name.casefold() not in seen, "Unsafe or duplicate Ninja output")
        count = int(match[2])
        require(count <= len(lines) - index - 2, "Ninja dependency count differs")
        body = lines[index + 1:index + 1 + count]
        require(all(re.fullmatch(rb"    [^\r\n]+\r?\n", line) is not None for line in body)
                and lines[index + 1 + count] == match[5], "Ninja dependency count/body differs")
        # Decode every dependency strictly, without normalizing its spelling or order.
        for line in body:
            line.decode("utf-8")
        normalized_header = header[:match.start(4)] + b"STATUS" + header[match.end(4):]
        records.append(NinjaDependencyRecord(name, "VALID" if match[4] == b"VALID" else "STALE",
            normalized_header + b"".join(body) + lines[index + 1 + count]))
        seen.add(name.casefold())
        index += count + 2
    require(records, "Empty Ninja dependency capture")
    return tuple(records)


def cmake_boolean_flags(path: Path) -> dict[str, str]:
    """Windows CMake comments may use the active code page; BOOL fields are ASCII."""
    result: dict[str, str] = {}
    for line in path.read_bytes().splitlines():
        if line.startswith((b"#", b"//")) or b":BOOL=" not in line:
            continue
        match = re.fullmatch(rb"([A-Za-z_][A-Za-z0-9_]*):BOOL=(.*)", line)
        if match is None:
            raise ValueError("Malformed CMake BOOL field")
        name, value = match[1].decode("ascii"), match[2].decode("ascii")
        require(name not in result, "Duplicate CMake BOOL field")
        result[name] = value
    require(result, "CMake cache contains no BOOL fields")
    return result


def same_metadata_content(actual: object, expected: object) -> bool:
    """Compare the JSON domain, allowing only the observation timestamp to differ."""
    left, right = obj(actual), obj(expected)
    left.pop("observed_at_utc", None)
    right.pop("observed_at_utc", None)
    return json.dumps(left, sort_keys=True, separators=(",", ":"), allow_nan=False) == json.dumps(
        right, sort_keys=True, separators=(",", ":"), allow_nan=False)


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
            try:
                size = path.stat().st_size
            except FileNotFoundError:
                # CMake atomically replaces FileAPI temporaries after os.walk.
                # A removed entry occupies no current bytes; other errors fail.
                continue
            total += ((size + 4095) // 4096) * 4096
    return total


def load_shared(path: Path, name: str) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "Shared producer unavailable")
    if spec is None or spec.loader is None:
        raise ValueError("Shared producer unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verified_noncompiled_consumer_replay(config: Config, value: object) -> NoncompiledReplayProof:
    """Revalidate the explicit source binding before replaying one noncompiled leaf."""
    row = obj(value)
    require(set(row) == {"before_blob", "after", "binding"}, "Exact noncompiled replay fields required")
    before, after, binding_ref = (checked(row[key]) for key in ("before_blob", "after", "binding"))
    native = (ROOT / PREFIX).resolve()
    require(Path(after["path"]) == native / NONCOMPILED_CONSUMER_RELATIVE,
            "Only the exact noncompiled consumer may be replayed")
    require(not Path(before["path"]).is_relative_to(ROOT.resolve()),
            "Original noncompiled consumer must be preserved outside the source checkout")
    original = subprocess.check_output(["git", "-c", "core.longpaths=true", "show", config.source_commit + ":" + PREFIX
        + NONCOMPILED_CONSUMER_RELATIVE], cwd=ROOT)
    require((len(original), hashlib.sha256(original).hexdigest()) == (before["bytes"], before["sha256"]),
            "Original noncompiled consumer differs from the actual compile Git blob")
    binding = read(Path(binding_ref["path"]))
    require(binding.get("schema") == "ck3-native-same-root-host-and-wire-consumer-binding-v1",
            "Explicit host-and-wire-consumer source binding required")
    qualified = checked(binding["qualified_native"])
    qualification = read(Path(qualified["path"]))
    snapshot_ref = checked(binding["snapshot"])
    snapshot = read(Path(snapshot_ref["path"]))
    delta = checked(binding["shared_python_host_delta"])
    shared = load_shared(ROOT / "tools/ck3_mod_acceptance_native_source_binding.py", "noncompiled_source_binding")
    qualify: object = getattr(shared, "qualified_native_source_checkout", None)
    if not isinstance(qualify, NativeSourceCheckoutQualifier):
        raise ValueError("Shared Native source checkout qualifier unavailable")
    context = qualify(Path(binding_ref["path"]), root=ROOT, runtime_commit=git("rev-parse", "HEAD"),
        native_commit=config.source_commit, machine=config.machine_id, qualified_native_ref=qualified,
        qualification=qualification, snapshot_ref=snapshot_ref, snapshot=snapshot,
        native_shared_python_host_delta=Path(delta["path"]))
    expected: NoncompiledConsumerReplay = {"before_blob": before, "after": after, "binding": binding_ref}
    originals = {name: checked(item) for name, item in obj(context.get("original_research_blobs")).items()}
    currents = {name: checked(item) for name, item in obj(context.get("runtime_research_pins")).items()}
    allowed = {NONCOMPILED_CONSUMER_RELATIVE, HOST_TEST_COMPANION_RELATIVE}
    require(context.get("noncompiled_replay") == expected and set(originals) == set(currents)
            and set(originals) in ({NONCOMPILED_CONSUMER_RELATIVE}, allowed)
            and originals.get(NONCOMPILED_CONSUMER_RELATIVE) == before
            and currents.get(NONCOMPILED_CONSUMER_RELATIVE) == after,
            "Replayed consumer pins differ from the fully qualified source binding")
    for name, original_ref in originals.items():
        require(Path(currents[name]["path"]) == native / name
                and not Path(original_ref["path"]).is_relative_to(ROOT.resolve()),
                "Replayed source must use its exact current path and external original blob")
        raw = subprocess.check_output(["git", "-c", "core.longpaths=true", "show",
            config.source_commit + ":" + PREFIX + name], cwd=ROOT)
        require((len(raw), hashlib.sha256(raw).hexdigest()) == (original_ref["bytes"], original_ref["sha256"]),
                "Replayed research source differs from its actual compile Git blob")
    for item in expected.values():
        checked(item)
    return NoncompiledReplayProof(expected, originals, currents)


class Producer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.native = ROOT / PREFIX if config.native_source_dir is None else config.native_source_dir
        self.build = config.output / "build" if config.development_build_dir is None else config.development_build_dir
        self.meta = config.output / "native-a01"
        self.env: dict[str, str] = {}
        self.tools: dict[str, str] = {}
        self.metadata_continuation = False
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
        actual_head = git("rev-parse", "HEAD")
        require(not git("status", "--porcelain", "--untracked-files=all"), "Clean committed Root required")
        if self.metadata_continuation:
            ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", c.source_commit, actual_head], cwd=ROOT, capture_output=True)
            require(ancestor.returncode == 0 and git("rev-parse", c.source_commit + ":" + PREFIX.rstrip("/"))
                    == git("rev-parse", actual_head + ":" + PREFIX.rstrip("/")),
                    "Metadata continuation needs the original or a clean descendant with an identical Native tree")
        else:
            require(actual_head == c.source_commit, "Exact clean committed Root required")
        checked(c.admission)
        admission = read(Path(c.admission["path"]))
        require(admission.get("machine_id") == c.machine_id and admission.get("active") is True
                and admission.get("capacity_passed") is True and admission.get("quota_passed") is True,
                "Active machine-bound storage admission required")
        require(c.budget <= integer(admission.get("budget_bytes"), 1), "Native lane exceeds admitted budget")
        approved = Path(string(admission.get("approved_root"))).resolve()
        require(c.output.is_relative_to(approved) and c.output != approved,
                "Native output escapes the admitted scene root")
        expiry = datetime.fromisoformat(string(admission.get("expires_at_utc")).replace("Z", "+00:00"))
        require(datetime.now(timezone.utc) < expiry, "Storage admission expired")
        floor = integer(admission.get("required_free_bytes"))
        require(shutil.disk_usage(c.output.parent).free >= floor, "Admitted free-space floor no longer holds")
        require(allocated(c.output.parent if c.schema == "ck3-configured-native-successor-v3" else c.output) < c.budget,
                "Native lane budget exhausted")

    def save(self, name: str, value: object) -> Pin:
        raw = (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode()
        budget_root = self.config.output.parent if self.config.schema == "ck3-configured-native-successor-v3" else self.config.output
        require(allocated(budget_root) + len(raw) + 8192 < self.config.budget, "Native metadata budget exhausted")
        path = self.config.output / relative(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
        return pin(path)

    def seal_save(self, name: str, value: object, *, resume: bool) -> Pin:
        path = self.config.output / relative(name)
        if resume and path.exists():
            require(same_metadata_content(read(path), value), "Existing seal metadata differs: " + name)
            return pin(path)
        return self.save(name, value)

    def execute(self, name: str, argv: list[str], cwd: Path, timeout: int = 180) -> Pin:
        self.gate()
        started, begin = now(), time.monotonic()
        log = self.config.output / (name + ".log")
        budget_root = self.config.output.parent if self.config.schema == "ck3-configured-native-successor-v3" else self.config.output
        peak, reason = allocated(budget_root), None
        responses: list[Pin] = []
        for value in argv:
            if value.startswith("@"):
                response = Path(value[1:])
                responses.append(pin(response if response.is_absolute() else cwd / response))
        with log.open("xb") as stream:
            process = subprocess.Popen(argv, cwd=cwd, env=self.env, stdout=stream, stderr=subprocess.STDOUT)
            while process.poll() is None:
                peak = max(peak, allocated(budget_root))
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
            "sampled_allocated_peak_bytes": max(peak, allocated(budget_root)), "game_started_or_attached": False,
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
        self.build.mkdir(exist_ok=self.config.schema == "ck3-configured-native-successor-v3")
        self.initialize_tools()

    def initialize_tools(self) -> None:
        """Use the same toolchain initialization for fresh and partial builds."""
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
        query.mkdir(parents=True, exist_ok=self.config.schema == "ck3-configured-native-successor-v3")
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
            ("/c" if token == "-c" else token).replace("\\", "/").lower().replace(source_text, "@native@").replace(build_text, "@build@")
            for token in command[1:]]]

    def unit_options(self, command: tuple[str, ...], source: Path, build: Path,
                     unit: Path, output: Path) -> list[str]:
        """Compare target options while retaining exactly one source/object binding."""
        normalized = self.normalize(command, source, build)
        unit_name = unit.as_posix().lower().replace(source.as_posix().lower(), "@native@")
        output_names = {output.as_posix().lower().replace(build.as_posix().lower(), "@build@"),
                        output.relative_to(build).as_posix().lower()}
        object_tokens = {"/fo" + name for name in output_names}
        require(normalized.count(unit_name) == 1 and
                sum(token in object_tokens for token in normalized) == 1,
                "New production unit requires one exact source/object compiler argument")
        return ["@unit@" if token == unit_name else "/fo@object@" if token in object_tokens else token
                for token in normalized]

    def retained_dependencies(self, current_capture: Pin) -> tuple[Pin, RetainedDependencyReuse]:
        """Reclaimed objects grant dependency-selection evidence, never link bytes."""
        c = self.config
        require(c.schema == "ck3-configured-native-successor-v2"
                and c.retained_dependency_evidence is not None and c.compiled_seed is None,
                "Explicit v2 retained dependency authority required")
        if c.retained_dependency_evidence is None:
            raise ValueError("Explicit v2 retained dependency authority required")
        require(Path(current_capture["path"]) == c.output / "original-ninja-dependencies.txt",
                "Retained dependency replay requires the original current capture path")
        qualification_ref = checked(c.retained_dependency_evidence["qualification"])
        qualification = read(Path(qualification_ref["path"]))
        require(set(qualification) == {"schema", "machine_id", "observed_at_utc", "source_commit",
            "actual_live_business_qualified", "delivery", "snapshot", "profile", "configured_scope",
            "source_verification", "production_freeze", "original_dll", "published_dll",
            "production_build_receipt", "defender_binding", "fixture_results", "execution_wire_packets"}
            and qualification["schema"] == "ck3-qualified-native-build-v1"
            and qualification["machine_id"] == c.machine_id
            and qualification["actual_live_business_qualified"] is False,
            "Original configured qualification identity required")
        commit = string(qualification["source_commit"])
        require(re.fullmatch(r"[0-9a-f]{40}", commit), "Exact historical source commit required")
        require(git("merge-base", commit, c.source_commit) == commit,
                "Retained dependency source must be an ancestor of the current source")
        freeze_ref = checked(qualification["production_freeze"])
        freeze = read(Path(freeze_ref["path"]))
        require(set(freeze) == {"machine_id", "observed_at_utc", "root_commit", "original_DLL", "published_DLL",
            "build_execution", "source_manifest", "source_verification", "profile", "scope",
            "no_fixture_target_in_production_dependency_closure", "repository_default_flags_changed",
            "game_started_or_attached", "incremental_production_plan", "incremental_production_result"}
            and freeze["machine_id"] == c.machine_id and freeze["root_commit"] == commit
            and freeze["no_fixture_target_in_production_dependency_closure"] is True
            and freeze["repository_default_flags_changed"] is False and freeze["game_started_or_attached"] is False,
            "Original frozen production identity required")
        for left, right in (("original_DLL", "original_dll"), ("published_DLL", "published_dll"),
                ("build_execution", "production_build_receipt"), ("source_manifest", "snapshot"),
                ("source_verification", "source_verification"), ("profile", "profile"), ("scope", "configured_scope")):
            require(checked(freeze[left]) == checked(qualification[right]), "Qualified production freeze binding differs")
        profile = read(Path(checked(qualification["profile"])["path"]))
        require(profile.get("machine_id") == c.machine_id and profile.get("repository_default_flags_changed") is False
                and checked(profile["profile"]) == checked(c.profile_cmake), "Retained dependency profile differs")
        source_ref = checked(qualification["snapshot"])
        source = read(Path(source_ref["path"]))
        files = arr(source["files"])
        require(files, "Historical source inventory is empty")
        source_names: set[str] = set()
        for raw in files:
            item = obj(raw)
            name = relative(item["native_relative"])
            require(name not in source_names and integer(item["bytes"]) >= 0
                    and re.fullmatch(r"[0-9a-f]{64}", string(item["sha256"])), "Invalid historical source inventory")
            source_names.add(name)
        verification = read(Path(checked(qualification["source_verification"])["path"]))
        require(source.get("machine_id") == verification.get("machine_id") == c.machine_id
                and source.get("root_commit") == source.get("native_source_commit") == verification.get("root_commit") == commit
                and integer(source["source_count"]) == len(files)
                and verification.get("source_manifest") == source_ref
                and integer(verification["all_snapshot_files_exactly_verified"]) == len(files)
                and integer(verification["all_original_inputs_still_exactly_verified"]) == len(files),
                "Historical source verification differs")
        plan_ref = checked(freeze["incremental_production_plan"])
        plan = read(Path(plan_ref["path"]))
        require(set(plan) == {"machine_id", "observed_at_utc", "source_commit", "baseline_qualification",
            "baseline_incremental_inputs", "original_dependencies", "changed_native_paths", "production_selections",
            "retained_link_inputs", "retained_incremental_object", "archive_copies"}
            and plan["machine_id"] == c.machine_id and plan["source_commit"] == commit
            and checked(plan["baseline_qualification"]) == checked(c.baseline)
            and checked(plan["baseline_incremental_inputs"]) == checked(c.incremental_inputs)
            and integer(plan["archive_copies"]) == 0, "Historical dependency plan provenance differs")
        incremental = read(Path(checked(freeze["incremental_production_result"])["path"]))
        require(incremental.get("machine_id") == c.machine_id and incremental.get("source_commit") == commit
                and incremental.get("production_plan") == plan_ref
                and incremental.get("actual_link") == qualification["production_build_receipt"]
                and incremental.get("dll") == qualification["original_dll"]
                and integer(incremental["archive_copies"]) == 0 and incremental.get("game_started_or_attached") is False,
                "Historical production result differs")
        execution = read(Path(checked(qualification["production_build_receipt"])["path"]))
        require(execution.get("machine_id") == c.machine_id and execution.get("source_commit") == commit
                and type(execution.get("original_wait_returncode")) is int and execution["original_wait_returncode"] == 0
                and execution.get("stopped_reason") is None and execution.get("game_started_or_attached") is False
                and execution.get("actual_live_business_qualified") is False, "Historical actual successful link required")
        checked(execution["log"])
        for response in arr(execution["response_files"]):
            checked(response)
        prior_inputs = read(Path(c.incremental_inputs["path"]))
        retained = [checked(raw) for raw in arr(plan["retained_link_inputs"])]
        require(retained == [checked(raw) for raw in arr(prior_inputs["inputs"])]
                and checked(plan["retained_incremental_object"]) == checked(prior_inputs["new_object"]),
                "Historical retained link inputs differ")
        libraries = {str(c.complete_build / name) for name in ("xar_ck3_12002_runtime.lib", "xar_bridge_protocol.lib")}
        require(libraries <= {item["path"] for item in retained}, "Retained archives do not bind the complete build root")
        dependency_ref = checked(plan["original_dependencies"])
        previous = strict_ninja_dependency_records(dependency_ref)
        current = strict_ninja_dependency_records(current_capture)
        require(len(previous) == len(current), "Retained dependency record count differs")
        stale: list[str] = []
        for before, after in zip(previous, current, strict=True):
            require(before.status == "VALID" and before.normalized == after.normalized,
                    "Retained dependency capture differs beyond VALID/STALE status")
            if after.status == "STALE":
                output = c.complete_build / after.output
                require(output.resolve() == output and output.is_relative_to(c.complete_build),
                        "Stale output escapes the complete build root")
                try:
                    output.lstat()
                except FileNotFoundError:
                    pass
                else:
                    raise ValueError("Stale dependency output is present; reclamation proof rejected")
                stale.append(after.output)
        require(stale, "Retained dependency evidence requires actual reclaimed outputs")
        return dependency_ref, {"qualification": qualification_ref, "production_freeze": freeze_ref,
            "production_plan": plan_ref, "current_capture": checked(current_capture), "stale_outputs": stale}

    def plan(self, rows: list[Compile], *, existing_plan: Pin | None = None,
             noncompiled_replay: object = None) -> tuple[list[Compile], dict[str, Path], Pin]:
        c = self.config
        if c.schema == "ck3-configured-native-successor-v3":
            require(noncompiled_replay is None, "v3 uses its actual development source, without replay aliases")
            return self.predecessor_plan(rows, existing_plan=existing_plan)
        require(noncompiled_replay is None or existing_plan is not None,
                "Noncompiled replay is restricted to an existing read-only production plan")
        replay = None if noncompiled_replay is None else verified_noncompiled_consumer_replay(c, noncompiled_replay)
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
        current_signatures = {name: (item["bytes"], item["sha256"]) for name, item in current.items()}
        if replay is not None:
            for name, before in replay.originals.items():
                require(current.get(name) == replay.currents[name], "Current noncompiled consumer is absent or changed")
                current_signatures[name] = (before["bytes"], before["sha256"])
        changed_names = {name for name in old_files.keys() | current_signatures.keys()
                         if name not in old_files or name not in current_signatures
                         or old_files[name] != current_signatures[name]}
        reuse: RetainedDependencyReuse | None = None
        if existing_plan is not None:
            original = read(Path(checked(existing_plan)["path"]))
            dependency_ref = checked(original["original_dependencies"])
            if c.retained_dependency_evidence is not None:
                declared_reuse = obj(original["retained_dependency_reuse"])
                retained_ref, reuse = self.retained_dependencies(checked(declared_reuse["current_capture"]))
                require(retained_ref == dependency_ref and declared_reuse == reuse,
                        "Replayed retained dependency provenance differs")
            dependency_text = Path(dependency_ref["path"]).read_text(encoding="utf-8")
        elif c.compiled_seed is None:
            dependency_query = subprocess.run([self.tools["ninja"], "-C", str(c.complete_build), "-t", "deps"],
                env=self.env, capture_output=True, check=True, text=True, encoding="utf-8")
            dependency_file = self.config.output / "original-ninja-dependencies.txt"
            dependency_file.write_text(dependency_query.stdout, encoding="utf-8")
            dependency_ref = pin(dependency_file)
            dependency_text = dependency_query.stdout
            if c.retained_dependency_evidence is not None:
                dependency_ref, reuse = self.retained_dependencies(dependency_ref)
                dependency_text = Path(dependency_ref["path"]).read_text(encoding="utf-8")
        else:
            seed_declaration = read(Path(checked(c.compiled_seed)["path"]))
            dependency_ref = checked(seed_declaration["original_dependencies"])
            dependency_text = Path(dependency_ref["path"]).read_text(encoding="utf-8")
        dependencies = self.dependencies(dependency_text, c.complete_build)
        if replay is not None:
            leaves = {(self.native / name).resolve() for name in replay.originals}
            for row in rows:
                require(row.source.resolve() not in leaves and not any(
                    name.lower() in argument.replace("\\", "/").lower()
                    for name in replay.originals for argument in row.argv),
                    "Noncompiled consumer occurs in a configured compiler command")
            require(not any(path.as_posix().lower().endswith("/" + name.lower())
                            for name in replay.originals for paths in dependencies.values() for path in paths),
                    "Noncompiled consumer occurs in the original compiler dependencies")
            all_memo: dict[Path, set[Path]] = {}
            built_targets = set(PRODUCTION) | {fixture.target for fixture in c.fixtures}
            require(not any(leaves.intersection(path.resolve() for path in self.closure(row.source, self.native, all_memo))
                            for row in rows if row.target in built_targets),
                    "Noncompiled consumer occurs in the current include closure")
        baseline_scope = read(Path(checked(baseline["configured_scope"])["path"]))
        old_commands_raw: object = json.loads(Path(checked(baseline_scope["compile_commands"])["path"])
                                            .read_text(encoding="utf-8-sig"))
        old_commands: dict[str, tuple[str, ...]] = {}
        old_units: dict[str, Path] = {}
        old_build = Path(string(obj(arr(old_commands_raw)[0])["directory"]))
        for raw in arr(old_commands_raw):
            item = obj(raw)
            output = Path(string(item["output"]))
            output = output if output.is_absolute() else old_build / output
            old_commands[output.relative_to(old_build).as_posix()] = tuple(self.arguments(string(item["command"])))
            old_units[output.relative_to(old_build).as_posix()] = Path(string(item["file"]))
            if replay is not None:
                require(not any(name.lower() in argument.replace("\\", "/").lower()
                                for name in replay.originals
                                for argument in old_commands[output.relative_to(old_build).as_posix()]),
                        "Noncompiled consumer occurs in a baseline compiler command")
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
        outputs = [row.output.relative_to(self.build).as_posix() for row in production_rows]
        require(len(outputs) == len(set(outputs)), "Duplicate production output")
        old_production = {name for name in old_commands
                          if any(name.startswith("CMakeFiles/" + target + ".dir/") for target in PRODUCTION)}
        require(old_production <= set(outputs), "Removing or renaming a retained production unit is unsupported")
        for row in production_rows:
            output_name = row.output.relative_to(self.build).as_posix()
            relative_source = row.source.relative_to(self.native).as_posix()
            old_dependencies = dependencies.get(output_name)
            new_unit = output_name not in old_commands
            if new_unit:
                require(relative_source not in old_files and relative_source in current
                        and old_dependencies is None
                        and row.target in ("xar_ck3_bridge", "xar_ck3_12002_runtime"),
                        "New production output must bind a genuinely new supported source without old dependencies")
                templates = [name for name in old_production
                             if name.startswith("CMakeFiles/" + row.target + ".dir/")]
                options = self.unit_options(row.argv, self.native, self.build, row.source, row.output)
                require(any(options == self.unit_options(old_commands[name], old_native, old_build,
                                                        old_units[name], old_build / name) for name in templates),
                        "New production unit changed target compiler options")
            else:
                require(self.normalize(row.argv, self.native, self.build)
                        == self.normalize(old_commands[output_name], old_native, old_build),
                        "Production compile options changed: " + output_name)
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
            if new_unit:
                require(bool(affected), "A new production unit must actually be compiled")
                selection[-1]["new_translation_unit"] = True
        require(selected, "No changed production input; refusing to relabel an old native qualification")
        retained_map = {Path(item["path"]).resolve(): item for item in retained}
        borrowed: dict[str, Path] = {}
        for row in production_rows:
            if row.target != "xar_ck3_bridge":
                continue
            name = row.output.relative_to(self.build).as_posix()
            if name not in old_commands:
                continue  # New bridge objects must come from the actual compile, never a borrowed path.
            path = replacements.get(name, c.complete_build / name)
            require(path in retained_map or path == new_path, "Bridge object lacks predecessor link provenance")
            borrowed[name] = path
        value: dict[str, object] = {"machine_id": c.machine_id,
            "observed_at_utc": now(), "source_commit": c.source_commit,
            "baseline_qualification": baseline_ref, "baseline_incremental_inputs": c.incremental_inputs,
            "original_dependencies": dependency_ref, "changed_native_paths": sorted(changed_names),
            "production_selections": selection, "retained_link_inputs": retained,
            "retained_incremental_object": new_object, "archive_copies": 0}
        if c.schema == "ck3-configured-native-successor-v2":
            value["retained_dependency_reuse"] = reuse
        if existing_plan is not None:
            require(same_metadata_content(read(Path(existing_plan["path"])), value),
                    "Recomputed source/options/dependency/retained production plan differs")
            report = existing_plan
        else:
            report = self.save("native-a01/PLAN.actual.json", value)
        return selected, borrowed, report

    def qualified_predecessor(self) -> QualifiedPredecessor:
        """Read the actual linked object graph, including every prior delta object/archive."""
        c = self.config
        require(c.schema == "ck3-configured-native-successor-v3" and c.predecessor_qualification is not None,
                "Explicit qualified predecessor required")
        if c.predecessor_qualification is None:
            raise ValueError("Explicit qualified predecessor required")
        reference = checked(c.predecessor_qualification)
        require(reference == checked(c.baseline), "v3 baseline must be its explicit qualified predecessor")
        q = read(Path(reference["path"]))
        require(q.get("schema") == "ck3-qualified-native-build-v1" and q.get("machine_id") == c.machine_id
                and q.get("actual_live_business_qualified") is False, "Qualified predecessor identity differs")
        commit = string(q["source_commit"])
        require(git("merge-base", commit, c.source_commit) == commit, "Predecessor is not a source ancestor")
        snapshot_ref, scope_ref, freeze_ref = (checked(q[key]) for key in ("snapshot", "configured_scope", "production_freeze"))
        snapshot, scope, frozen = (read(Path(ref["path"])) for ref in (snapshot_ref, scope_ref, freeze_ref))
        verification = read(Path(checked(q["source_verification"])["path"]))
        require(snapshot.get("machine_id") == verification.get("machine_id") == c.machine_id
                and snapshot.get("root_commit") == snapshot.get("native_source_commit") == commit
                and verification.get("source_manifest") == snapshot_ref
                and verification.get("root_commit") == commit
                and frozen.get("source_manifest") == snapshot_ref and frozen.get("scope") == scope_ref
                and frozen.get("root_commit") == commit and frozen.get("game_started_or_attached") is False,
                "Predecessor source/freeze provenance differs")
        source_root = Path(string(snapshot["snapshot_native_base"]))
        signatures: dict[str, tuple[int, str]] = {}
        for raw in arr(snapshot["files"]):
            item = obj(raw); name = relative(item["native_relative"])
            require(name not in signatures, "Duplicate predecessor source identity")
            signatures[name] = (integer(item["bytes"]), string(item["sha256"]))
        require(integer(snapshot["source_count"]) == len(signatures)
                and integer(verification["all_snapshot_files_exactly_verified"]) == len(signatures)
                and integer(verification["all_original_inputs_still_exactly_verified"]) == len(signatures),
                "Predecessor source verification is incomplete")
        plan_ref, result_ref = (checked(frozen[key]) for key in ("incremental_production_plan", "incremental_production_result"))
        plan, result = read(Path(plan_ref["path"])), read(Path(result_ref["path"]))
        require(plan.get("machine_id") == result.get("machine_id") == c.machine_id
                and plan.get("source_commit") == result.get("source_commit") == commit
                and result.get("production_plan") == plan_ref and result.get("actual_link") == q["production_build_receipt"]
                and result.get("dll") == q["original_dll"] == frozen["original_DLL"]
                and result.get("game_started_or_attached") is False
                and integer(result["archive_copies"]) == integer(plan["archive_copies"]) == 0,
                "Predecessor actual incremental/link graph differs")
        checked(q["original_dll"]); checked(q["published_dll"])
        execution = read(Path(checked(q["production_build_receipt"])["path"]))
        require(execution.get("machine_id") == c.machine_id and execution.get("source_commit") == commit
                and integer(execution["original_wait_returncode"]) == 0 and execution.get("stopped_reason") is None
                and execution.get("actual_live_business_qualified") is False
                and execution.get("game_started_or_attached") is False, "Predecessor actual link did not succeed")
        checked(execution["log"])
        response_refs = [checked(value) for value in arr(execution["response_files"])]
        require(len(response_refs) == 1, "One original predecessor link response required")
        link_args = self.arguments(Path(response_refs[0]["path"]).read_text(encoding="utf-8"))
        require(strings(execution["argv"])[-1] == "@" + response_refs[0]["path"], "Predecessor link response invocation differs")
        declared = {Path(value["path"]): value for value in
            [checked(raw) for raw in arr(plan["retained_link_inputs"])]+[checked(plan["retained_incremental_object"])]}
        for raw in arr(result["production_compiles"]):
            item = obj(raw); source, compiled_output = parse_pin(item["source"]), checked(item["object"])
            name = Path(source["path"]).relative_to(source_root).as_posix()
            require(signatures.get(name) == (source["bytes"], source["sha256"]), "Predecessor compiled source identity differs")
            actual = read(Path(checked(item["actual_compile"])["path"]))
            require(actual.get("machine_id") == c.machine_id and actual.get("source_commit") == commit
                    and integer(actual["original_wait_returncode"]) == 0 and actual.get("stopped_reason") is None,
                    "Predecessor original compile failed")
            checked(actual["log"])
            declared[Path(compiled_output["path"])] = compiled_output
        if result["changed_runtime_archive"] is not None:
            archive = checked(result["changed_runtime_archive"])
            actual = read(Path(checked(result["changed_runtime_archive_execution"])["path"]))
            require(integer(actual["original_wait_returncode"]) == 0 and actual.get("stopped_reason") is None,
                    "Predecessor original changed archive failed")
            checked(actual["log"]); declared[Path(archive["path"])] = archive
        commands_ref = checked(scope["compile_commands"])
        commands = [obj(raw) for raw in arr(json.loads(Path(commands_ref["path"]).read_text(encoding="utf-8-sig")))]
        old_build = Path(string(commands[0]["directory"]))
        objects: dict[str, Pin] = {}
        for row in commands:
            output = Path(string(row["output"])); output = output if output.is_absolute() else old_build/output
            name = output.relative_to(old_build).as_posix()
            if not name.startswith("CMakeFiles/xar_ck3_bridge.dir/"):
                continue
            candidates = [Path(token) for token in link_args if token.lower().endswith(".obj")
                and Path(token).parts[-len(Path(name).parts):] == Path(name).parts]
            require(len(candidates) == 1 and candidates[0] in declared and name not in objects,
                    "Predecessor actual linked bridge object is missing, ambiguous or undeclared")
            objects[name] = declared[candidates[0]]
        libraries: list[Pin] = []
        for token in link_args:
            path = Path(token)
            if path.is_absolute() and path.suffix.lower() in (".obj", ".lib"):
                require(path in declared, "Predecessor actual link has an unpinned input")
                if path.suffix.lower() == ".lib": libraries.append(declared[path])
        require(objects and libraries, "Complete linked predecessor object/archive graph required")
        return QualifiedPredecessor(reference, snapshot_ref, commands_ref, checked(plan["original_dependencies"]),
            source_root, objects, tuple(libraries), signatures)

    def predecessor_plan(self, rows: list[Compile], *, existing_plan: Pin | None = None
            ) -> tuple[list[Compile], dict[str, Path], Pin]:
        prior = self.qualified_predecessor()
        current: dict[str, Pin] = {}
        for name in git("ls-files", "--", PREFIX).splitlines():
            relative_name = name.removeprefix(PREFIX)
            original, development = pin(ROOT/name), pin(self.native/relative_name)
            require((original["bytes"], original["sha256"]) == (development["bytes"], development["sha256"]),
                    "Development native source differs from the current committed Root")
            current[relative_name] = development
        require({path.relative_to(self.native).as_posix() for path in self.native.rglob("*") if path.is_file()}
                == set(current), "Development native source contains stale or untracked files")
        changed = {name for name in prior.source_signatures.keys() | current.keys()
            if name not in current or prior.source_signatures.get(name) != (current[name]["bytes"], current[name]["sha256"])}
        commands = [obj(raw) for raw in arr(json.loads(Path(prior.compile_commands["path"]).read_text(encoding="utf-8-sig")))]
        old_build = Path(string(commands[0]["directory"]))
        old_rows: dict[str, tuple[str, ...]] = {}
        for item in commands:
            output = Path(string(item["output"])); output = output if output.is_absolute() else old_build/output
            old_rows[output.relative_to(old_build).as_posix()] = tuple(self.arguments(string(item["command"])))
        selected: list[Compile] = []; selection: list[dict[str, object]] = []; memo: dict[Path, set[Path]] = {}
        old_dependencies = self.dependencies(Path(prior.dependencies["path"]).read_text(encoding="utf-8"), self.config.complete_build)
        roots = {path.parent.parent.parent for paths in old_dependencies.values() for path in paths
            if path.name == "activity_typed_planner_v1.hpp"}
        require(len(roots) == 1, "Original predecessor compiler dependency source root required")
        dependency_root = next(iter(roots))
        for row in rows:
            if row.target not in PRODUCTION: continue
            name = row.output.relative_to(self.build).as_posix()
            require(name in old_rows and self.normalize(row.argv,self.native,self.build)
                == self.normalize(old_rows[name],prior.source_root,old_build), "Predecessor production compiler options changed")
            dependencies = {path.relative_to(self.native).as_posix() for path in self.closure(row.source,self.native,memo)
                if path.is_relative_to(self.native)}
            dependencies.update(path.relative_to(dependency_root).as_posix() for path in old_dependencies.get(name,set())
                if path.is_relative_to(dependency_root))
            affected = sorted(changed.intersection(dependencies | {row.source.relative_to(self.native).as_posix()}))
            if affected: selected.append(row)
            selection.append({"target":row.target,"output":name,"source":row.source.relative_to(self.native).as_posix(),
                "changed_dependencies":affected,"compiled":bool(affected)})
        require(selected and {row.target for row in rows if row.target in PRODUCTION} == set(PRODUCTION),
                "An actual changed complete production graph required")
        bridge = {row.output.relative_to(self.build).as_posix() for row in rows if row.target == "xar_ck3_bridge"}
        require(bridge == set(prior.objects), "Predecessor bridge graph changed")
        retained = [*prior.objects.values(), *prior.libraries]
        value: dict[str, object] = {"machine_id":self.config.machine_id,"observed_at_utc":now(),
            "source_commit":self.config.source_commit,"baseline_qualification":self.config.baseline,
            "baseline_incremental_inputs":self.config.incremental_inputs,"original_dependencies":prior.dependencies,
            "changed_native_paths":sorted(changed),"production_selections":selection,"retained_link_inputs":retained,
            "retained_incremental_object":next(iter(prior.objects.values())),"archive_copies":0,
            "predecessor_qualification":prior.qualification,"predecessor_compile_commands":prior.compile_commands,
            "predecessor_libraries":list(prior.libraries)}
        if existing_plan is not None:
            require(same_metadata_content(read(Path(checked(existing_plan)["path"])),value), "Predecessor production replay differs")
            report = existing_plan
        else: report = self.save("native-a01/PLAN.actual.json",value)
        return selected,{name:Path(ref["path"]) for name,ref in prior.objects.items()},report

    def compile(self, row: Compile, label: str, definitions: tuple[str, ...] = ()) -> Pin:
        row.output.parent.mkdir(parents=True, exist_ok=True)
        argv = ["/c" if token == "-c" else token for token in row.argv]
        argv.extend("/D" + definition for definition in definitions)
        return self.execute(label, argv, self.build)

    def successful_seeds(self, rows: list[Compile]) -> dict[str, SeedCompile]:
        """A failed link may retain independently successful, exactly bound CL outputs."""
        if self.config.compiled_seed is None:
            return {}
        seed_ref = checked(self.config.compiled_seed)
        seed = read(Path(seed_ref["path"]))
        require(set(seed) == {"schema", "machine_id", "observed_at_utc", "source_commit", "native_source_base",
            "native_subtree_tree_id", "source_manifest", "production_compiles", "failed_link", "original_dependencies"},
            "Exact successful-compile seed contract required")
        require(seed["schema"] == "ck3-native-successful-compile-seed-v1"
                and seed["machine_id"] == self.config.machine_id, "Compile seed schema/machine differs")
        string(seed["observed_at_utc"])
        checked(seed["original_dependencies"])
        commit = string(seed["source_commit"])
        require(re.fullmatch(r"[0-9a-f]{40}", commit), "Compile seed commit invalid")
        old_source = Path(string(seed["native_source_base"])).resolve()
        tree = string(seed["native_subtree_tree_id"])
        require(git("rev-parse", commit + ":" + PREFIX.rstrip("/")) == tree
                == git("rev-parse", self.config.source_commit + ":" + PREFIX.rstrip("/")),
                "Compile seed and runtime Native Git trees differ")
        declared: set[str] = set()
        for raw in arr(seed["source_manifest"]):
            item = obj(raw)
            require(set(item) == {"native_relative", "bytes", "sha256"}, "Compile seed source row differs")
            name = relative(item["native_relative"])
            require(name not in declared, "Duplicate seed source")
            declared.add(name)
            actual = pin(self.native / name)
            require(actual["bytes"] == integer(item["bytes"]) and actual["sha256"] == string(item["sha256"]),
                    "Compile seed dependency bytes changed: " + name)
        tracked = {name.removeprefix(PREFIX) for name in git("ls-files", "--", PREFIX).splitlines()}
        require(declared == tracked, "Compile seed omits Native input paths")
        failed_link = read(Path(checked(seed["failed_link"])["path"]))
        require(failed_link.get("machine_id") == self.config.machine_id
                and failed_link.get("source_commit") == commit
                and integer(failed_link.get("original_wait_returncode"), 1) > 0,
                "Seed must preserve the actual failed link rather than relabel it successful")
        by_name = {row.output.relative_to(self.build).as_posix(): row for row in rows if row.target in PRODUCTION}
        result: dict[str, SeedCompile] = {}
        for raw in arr(seed["production_compiles"]):
            item = obj(raw)
            require(set(item) == {"target", "original_output", "source", "object", "execution"},
                    "Exact successful compile fields required")
            name = relative(item["original_output"])
            require(name not in result and name in by_name, "Duplicate or unknown compile seed output")
            row = by_name[name]
            require(item["target"] == row.target, "Compile seed target differs")
            source, output, execution = checked(item["source"]), checked(item["object"]), checked(item["execution"])
            actual_execution = read(Path(execution["path"]))
            require(actual_execution.get("machine_id") == self.config.machine_id
                    and actual_execution.get("source_commit") == commit
                    and type(actual_execution.get("original_wait_returncode")) is int
                    and actual_execution["original_wait_returncode"] == 0
                    and actual_execution.get("stopped_reason") is None
                    and actual_execution.get("game_started_or_attached") is False,
                    "Compile seed lacks its actual successful original execution")
            previous_argv = strings(actual_execution["argv"])
            previous_build = Path(string(actual_execution["cwd"])).resolve()
            require(self.normalize(row.argv, self.native, self.build)
                    == self.normalize(previous_argv, old_source, previous_build)
                    and source == pin(row.source), "Compile seed command/source differs from fresh CMake")
            require(Path(output["path"]).resolve() == previous_build / name,
                    "Compile seed output does not match its actual command directory")
            result[name] = SeedCompile(source, output, execution)
        require(result, "Successful compile seed is empty")
        return result

    def archive_runtime(self, objects: list[Path]) -> tuple[Path | None, Pin | None]:
        """Keep changed members lazy; direct objects force unused OFF transports into link."""
        if not objects:
            return None, None
        archive_root = self.config.output if self.config.schema == "ck3-configured-native-successor-v3" else self.build
        destination = archive_root / "changed-runtime.lib"
        response = archive_root / "changed-runtime.rsp"
        response.write_text(subprocess.list2cmdline(list(map(str, objects))), encoding="utf-8")
        execution = self.execute("archive-changed-runtime", [str(Path(self.tools["cl"]).parent / "lib.exe"),
            "/nologo", "/machine:x64", "/OUT:" + str(destination), "@" + str(response)], self.build)
        return destination, execution

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
        response = (self.config.output if self.config.schema == "ck3-configured-native-successor-v3" else self.build) / (label + ".rsp")
        with response.open("x", encoding="utf-8") as stream:
            stream.write(subprocess.list2cmdline(arguments))
        return self.execute(label, [str(linker), "@" + str(response)], self.build)

    def run(self) -> Pin:
        self.initialize()
        self.configure()
        rows = self.commands()
        selected, borrowed, plan = self.plan(rows)
        seeds = self.successful_seeds(rows)
        compiled: dict[Path, Pin] = {}
        object_paths: dict[Path, Path] = {}
        production_compiles: list[dict[str, object]] = []
        for index, row in enumerate(selected):
            seed = seeds.get(row.output.relative_to(self.build).as_posix())
            if seed is None:
                compiled[row.output] = self.compile(row, "production-compile-" + str(index))
                object_paths[row.output] = row.output
            else:
                compiled[row.output] = seed.execution
                object_paths[row.output] = Path(seed.object["path"])
            production_compiles.append({"target": row.target, "source": pin(row.source),
                "object": pin(object_paths[row.output]), "actual_compile": compiled[row.output],
                "compile_reused": seed is not None})
        runtime_objects = [object_paths[row.output] for row in selected if row.target == "xar_ck3_12002_runtime"]
        bridge_objects = [object_paths[row.output] if row.output in compiled else borrowed[row.output.relative_to(self.build).as_posix()]
                          for row in rows if row.target == "xar_ck3_bridge"]
        retained_libraries = ([Path(ref["path"]) for ref in self.qualified_predecessor().libraries]
            if self.config.schema == "ck3-configured-native-successor-v3" else
            [self.config.complete_build / "xar_bridge_protocol.lib", self.config.complete_build / "xar_ck3_12002_runtime.lib"])
        plan_value = read(Path(plan["path"]))
        retained_refs = [parse_pin(item) for item in arr(plan_value["retained_link_inputs"])]
        retained_paths = {Path(item["path"]).resolve() for item in retained_refs}
        require(set(retained_libraries) <= retained_paths, "Production libraries lack predecessor link provenance")
        delta, archive_execution = self.archive_runtime(runtime_objects)
        libraries = [retained_libraries[0], *([delta] if delta is not None else []), *retained_libraries[1:]]
        dll = (self.config.output if self.config.schema == "ck3-configured-native-successor-v3" else self.build) / "xar_ck3_bridge.dll"
        production_execution = self.link("link-production", bridge_objects, libraries, dll, True)
        self.save("native-a01/INCREMENTAL-RESULT.actual.json", {"machine_id": self.config.machine_id,
            "observed_at_utc": now(), "source_commit": self.config.source_commit,
            "production_plan": plan, "production_compiles": production_compiles,
            "actual_link": production_execution, "dll": pin(dll), "archive_copies": 0,
            "changed_runtime_archive": None if delta is None else pin(delta),
            "changed_runtime_archive_execution": archive_execution,
            "compiled_seed": self.config.compiled_seed,
            "retained_archive_mode": "Small changed-member archive precedes unchanged original archive; both are selected lazily",
            "game_started_or_attached": False})
        return self.finish_fixtures(rows, FixtureInputs(compiled, object_paths, borrowed,
            libraries, retained_refs, plan, production_execution, dll))

    def finish_fixtures(self, rows: list[Compile], inputs: FixtureInputs, *, label: str = "") -> Pin:
        """Compile, link and execute the configured fixtures through one path."""
        compiled, object_paths, borrowed = inputs.compiled, inputs.object_paths, inputs.borrowed
        fixture_results: list[dict[str, object]] = []
        links: list[FixtureLinkResult] = []
        by_output = {row.output: row for row in rows}
        for fixture in self.config.fixtures:
            actual_objects = self.fixture_link_objects(fixture)
            own_rows = [by_output[path] for path in actual_objects if path in by_output
                        and by_output[path].target not in PRODUCTION]
            require(own_rows, "Configured finite fixture missing: " + fixture.target)
            own: list[Path] = []
            for index, row in enumerate(own_rows):
                if row.output not in compiled:
                    compiled[row.output] = self.compile(row, label + fixture.target + "-compile-" + str(index))
                    object_paths[row.output] = row.output
                own.append(row.output)
            for path in actual_objects:
                if path not in by_output or by_output[path].target not in PRODUCTION:
                    continue
                if path in compiled:
                    own.append(object_paths[path])
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
                self.compile(replacement, label + fixture.target + "-override-" + str(index), fixture.runtime_override_definitions)
                overrides.append(output)
            executable = self.build / (fixture.target + ".exe")
            execution = self.link(label + fixture.target + "-link", own + overrides, inputs.libraries, executable)
            links.append({"target": fixture.target, "executable": pin(executable), "actual_link": execution})
            fixture_results.append({"target": fixture.target, "executable": pin(executable)})
        self.save("native-a01/" + label + "FIXTURE-LINKS.actual.json", {"machine_id": self.config.machine_id,
            "observed_at_utc": now(), "source_commit": self.config.source_commit, "fixtures": links})
        all_defender_binding = self.defender(fixture_results, label + "all-fixtures")
        for fixture, result in zip(self.config.fixtures, fixture_results, strict=True):
            arguments = [value.replace("{output}", str(self.config.output)).replace("{build}", str(self.build))
                         for value in fixture.arguments]
            result["execution"] = self.execute(label + "test-" + fixture.target,
                [str(self.build / (fixture.target + ".exe")), *arguments], self.build)
        self.gate()
        for retained in inputs.retained:
            checked(retained)
        checked(read(Path(inputs.plan["path"]))["retained_incremental_object"])
        self.save("native-a01/ALL-FIXTURES.actual.json", {"machine_id": self.config.machine_id,
            "observed_at_utc": now(), "source_commit": self.config.source_commit,
            "fixture_results": fixture_results, "defender_binding": all_defender_binding,
            "actual_live_business_qualified": False})
        qualified = [item for item in fixture_results if item["target"] in self.config.qualification_targets]
        defender_binding = self.defender(qualified, label + "qualification-subset")
        if label:
            defender_binding = self.save("native-a01/qualification-subset-defender-binding.actual.json",
                read(Path(defender_binding["path"])))
        return self.seal(rows, qualified, inputs.production_execution, defender_binding, inputs.plan, inputs.dll)

    def successful_execution(self, value: object) -> tuple[Pin, dict[str, object]]:
        reference = checked(value)
        execution = read(Path(reference["path"]))
        require(execution.get("machine_id") == self.config.machine_id
                and execution.get("source_commit") == self.config.source_commit
                and type(execution.get("original_wait_returncode")) is int
                and execution["original_wait_returncode"] == 0 and execution.get("stopped_reason") is None
                and execution.get("game_started_or_attached") is False
                and execution.get("actual_live_business_qualified") is False,
                "Original successful command execution required")
        checked(execution["log"])
        for response in arr(execution["response_files"]):
            checked(response)
        return reference, execution

    def original_fixture_inputs(self, rows: list[Compile]) -> FixtureInputs:
        """Verify the completed production graph before any partial-build mutation."""
        c = self.config
        require(c.compiled_seed is None, "Fixture resume requires original, unseeded production commands")
        checked(c.baseline)
        checked(c.incremental_inputs)
        checked(c.profile_cmake)
        _, configured = self.successful_execution(pin(c.output / "configure.actual.json"))
        arguments = strings(configured["argv"])
        for flag, value in (("-S", str(self.native)), ("-B", str(self.build)), ("-G", "Ninja")):
            require(arguments.count(flag) == 1 and arguments.index(flag) + 1 < len(arguments)
                    and arguments[arguments.index(flag) + 1] == value, "Original configured source/build graph differs")
        require("-DCMAKE_PROJECT_TOP_LEVEL_INCLUDES=" + c.profile_cmake["path"] in arguments
                and "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON" in arguments,
                "Original configured profile/compile graph differs")
        incremental = read(self.meta / "INCREMENTAL-RESULT.actual.json")
        require(set(incremental) == {"machine_id", "observed_at_utc", "source_commit", "production_plan",
            "production_compiles", "actual_link", "dll", "archive_copies", "changed_runtime_archive",
            "changed_runtime_archive_execution", "compiled_seed", "retained_archive_mode", "game_started_or_attached"},
            "Exact original production result fields required")
        require(incremental.get("machine_id") == c.machine_id and incremental.get("source_commit") == c.source_commit
                and incremental.get("game_started_or_attached") is False
                and type(incremental.get("archive_copies")) is int and incremental["archive_copies"] == 0
                and incremental.get("compiled_seed") is None, "Original unseeded production identity required")
        production, _ = self.successful_execution(incremental["actual_link"])
        require(Path(production["path"]) == c.output / "link-production.actual.json",
                "Original production link path differs")
        dll = checked(incremental["dll"])
        require(Path(dll["path"]) == (c.output if c.schema == "ck3-configured-native-successor-v3" else self.build) / "xar_ck3_bridge.dll", "Original configured DLL path differs")
        plan = checked(incremental["production_plan"])
        require(Path(plan["path"]) == self.meta / "PLAN.actual.json", "Original production plan path differs")
        original = read(Path(plan["path"]))
        require(original.get("machine_id") == c.machine_id and original.get("source_commit") == c.source_commit
                and original.get("baseline_qualification") == c.baseline
                and original.get("baseline_incremental_inputs") == c.incremental_inputs,
                "Original production plan provenance differs")
        checked(original["original_dependencies"])
        if c.retained_dependency_evidence is not None:
            dependency_ref, reuse = self.retained_dependencies(checked(obj(original["retained_dependency_reuse"])["current_capture"]))
            require(original["original_dependencies"] == dependency_ref and original["retained_dependency_reuse"] == reuse,
                    "Original fixture retained dependency provenance differs")
        production_rows = {row.output.relative_to(self.build).as_posix(): row for row in rows if row.target in PRODUCTION}
        declared: set[str] = set()
        selected: set[str] = set()
        for raw in arr(original["production_selections"]):
            item = obj(raw)
            name = relative(item["output"])
            require(name in production_rows and name not in declared, "Original production graph differs")
            row = production_rows[name]
            require(item["target"] == row.target and item["source"] == row.source.relative_to(self.native).as_posix()
                    and type(item["compiled"]) is bool, "Original production source/selection differs")
            declared.add(name)
            if item["compiled"]:
                selected.add(name)
        require(declared == set(production_rows), "Original production graph is incomplete")
        compiled: dict[Path, Pin] = {}
        object_paths: dict[Path, Path] = {}
        for raw in arr(incremental["production_compiles"]):
            item = obj(raw)
            source, output = checked(item["source"]), checked(item["object"])
            name = Path(output["path"]).relative_to(self.build).as_posix()
            require(name in selected and Path(output["path"]) not in compiled and item.get("compile_reused") is False,
                    "Original production compile set differs")
            row = production_rows[name]
            execution, actual = self.successful_execution(item["actual_compile"])
            require(item["target"] == row.target and source == pin(row.source)
                    and Path(string(actual["cwd"])) == self.build
                    and self.normalize(strings(actual["argv"]), self.native, self.build)
                    == self.normalize(row.argv, self.native, self.build), "Original production compiler inputs differ")
            compiled[row.output], object_paths[row.output] = execution, Path(output["path"])
        require({path.relative_to(self.build).as_posix() for path in compiled} == selected,
                "Original production compiles are incomplete")
        retained = [checked(value) for value in arr(original["retained_link_inputs"])]
        replacement = checked(original["retained_incremental_object"])
        retained.append(replacement)
        retained_paths = {Path(value["path"]) for value in retained}
        borrowed: dict[str, Path] = {}
        for name, row in production_rows.items():
            if row.target != "xar_ck3_bridge" or row.output in compiled:
                continue
            candidates = [path for path in retained_paths if path.parts[-len(Path(name).parts):] == Path(name).parts]
            require(len(candidates) == 1, "Original retained bridge object is ambiguous or missing")
            borrowed[name] = candidates[0]
        libraries = ([Path(ref["path"]) for ref in self.qualified_predecessor().libraries]
            if c.schema == "ck3-configured-native-successor-v3" else
            [c.complete_build / "xar_bridge_protocol.lib", c.complete_build / "xar_ck3_12002_runtime.lib"])
        require(set(libraries) <= retained_paths, "Original runtime library provenance differs")
        if incremental["changed_runtime_archive"] is not None:
            archive = checked(incremental["changed_runtime_archive"])
            require(Path(archive["path"]) == (c.output if c.schema == "ck3-configured-native-successor-v3" else self.build) / "changed-runtime.lib", "Original changed archive path differs")
            self.successful_execution(incremental["changed_runtime_archive_execution"])
            libraries.insert(1, Path(archive["path"]))
        else:
            require(incremental["changed_runtime_archive_execution"] is None, "Missing archive has an execution")
        return FixtureInputs(compiled, object_paths, borrowed, libraries, retained, plan, production, Path(dll["path"]))

    def preserve_fixture_outputs(self, rows: list[Compile], label: str) -> Pin:
        """Rename unknown outputs; preserve exact bytes and native file identity."""
        paths: set[Path] = set()
        by_output = {row.output: row for row in rows}
        for fixture in self.config.fixtures:
            for path in self.fixture_link_objects(fixture):
                if path in by_output and by_output[path].target not in PRODUCTION:
                    paths.add(path)
            paths.update(self.build / (fixture.target + suffix) for suffix in (".exe", ".lib", ".exp", ".pdb", ".ilk"))
            paths.update(self.build / "fixture-overrides" / fixture.target / (Path(name).name + ".obj")
                         for name in fixture.runtime_override_sources)
        originals: list[PreservedOutput] = []
        for path in sorted(paths):
            if not path.exists():
                continue
            require(path.is_relative_to(self.build) and path.is_file() and not path.is_symlink(),
                    "Unknown fixture output is not a regular configured file")
            identity = path.stat()
            destination = self.config.output / (label + "preserved") / path.relative_to(self.build)
            require(not destination.exists(), "Preserved original destination already exists")
            originals.append({"original": pin(path), "preserved_path": str(destination),
                "file_id": str(identity.st_ino), "device_id": str(identity.st_dev)})
        intent = self.save("native-a01/" + label + "PRESERVATION-INTENT.actual.json", {
            "machine_id": self.config.machine_id, "observed_at_utc": now(), "source_commit": self.config.source_commit,
            "unknown_originals": originals, "old_link_success_inferred": False})
        for item in originals:
            original = checked(item["original"])
            path, destination = Path(original["path"]), Path(string(item["preserved_path"]))
            destination.parent.mkdir(parents=True, exist_ok=True)
            require(not destination.exists(), "Preserved original destination appeared")
            path.rename(destination)
            identity = destination.stat()
            preserved = pin(destination)
            require(preserved["sha256"] == original["sha256"] and preserved["bytes"] == original["bytes"]
                    and str(identity.st_ino) == item["file_id"] and str(identity.st_dev) == item["device_id"],
                    "Renamed original bytes or native file identity changed")
            item["preserved"] = preserved
        return self.save("native-a01/" + label + "PRESERVED.actual.json", {"machine_id": self.config.machine_id,
            "observed_at_utc": now(), "source_commit": self.config.source_commit, "intent": intent,
            "unknown_originals": originals, "old_link_success_inferred": False})

    def resume_fixtures(self, label: str) -> Pin:
        """Resume a pre-execution fixture failure without configure or production work."""
        require(isinstance(label, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,100}", label),
                "A finite unique continuation label is required")
        label += "-"
        self.metadata_continuation = True
        actual_machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8",
            str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT).decode("utf-8").strip()
        require(actual_machine == self.config.machine_id, "Actual continuation machine differs")
        self.gate()
        require(not (self.meta / "ALL-FIXTURES.actual.json").exists(), "Completed fixtures require metadata-only continuation")
        for fixture in self.config.fixtures:
            require(not list(self.config.output.glob("*test-" + fixture.target + ".log")),
                    "Fixture resume is only available before any original fixture execution")
            for value in fixture.arguments:
                argument = Path(value.replace("{output}", str(self.config.output)).replace("{build}", str(self.build)))
                if argument.is_absolute() and argument.is_relative_to(self.config.output):
                    require(not argument.exists(), "Original fixture argument output already exists")
        rows = self.commands()
        inputs = self.original_fixture_inputs(rows)
        self.initialize_tools()
        preserved = self.preserve_fixture_outputs(rows, label)
        self.save("native-a01/" + label + "RESUME-FIXTURES.actual.json", {"machine_id": self.config.machine_id,
            "observed_at_utc": now(), "native_source_commit": self.config.source_commit,
            "metadata_source_commit": git("rev-parse", "HEAD"), "producer": pin(Path(__file__)),
            "compile_commands": pin(self.build / "compile_commands.json"), "ninja": pin(self.build / "build.ninja"),
            "original_incremental_result": pin(self.meta / "INCREMENTAL-RESULT.actual.json"),
            "preserved_unknown_outputs": preserved, "new_production_compilation_performed": False,
            "new_production_link_performed": False, "actual_live_business_qualified": False})
        return self.finish_fixtures(rows, inputs, label=label)

    def defender(self, fixtures: list[dict[str, object]], label: str) -> Pin:
        manifest = self.config.output / (label + "-defender-manifest.json")
        receipt = self.config.output / (label + "-defender-receipt.json")
        shared = load_shared(ROOT / "tools/register_project_exe_exclusions.py", "shared_successor_defender")
        collector: object = getattr(shared, "collect_manifest", None)
        if not isinstance(collector, ManifestCollector):
            raise ValueError("Shared Defender manifest collector unavailable")
        targets = [string(row["target"]) for row in fixtures]
        value = (collector(ROOT, self.native, self.build, "Release", targets,
                    "configured-native-development:" + self.config.source_commit)
            if self.config.schema == "ck3-configured-native-successor-v3" else
            collector(ROOT, self.native, self.build, "Release", targets))
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

    def resume_seal(self) -> Pin:
        """Continue metadata after completed original commands; never rebuild or rerun."""
        self.metadata_continuation = True
        actual_machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8",
            str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT).decode("utf-8").strip()
        require(actual_machine == self.config.machine_id, "Actual continuation machine differs")
        self.gate()
        rows = self.commands()
        if self.config.retained_dependency_evidence is not None:
            self.plan(rows, existing_plan=pin(self.meta / "PLAN.actual.json"))
        self.successful_seeds(rows)
        report = read(self.meta / "ALL-FIXTURES.actual.json")
        require(report.get("machine_id") == self.config.machine_id and report.get("source_commit") == self.config.source_commit
                and report.get("actual_live_business_qualified") is False, "Original complete finite report required")
        fixtures = [obj(item) for item in arr(report["fixture_results"])]
        require(len(fixtures) == len(self.config.fixtures)
                and {string(item["target"]) for item in fixtures} == {item.target for item in self.config.fixtures},
                "Continuation must retain every originally requested fixture")
        all_binding = read(Path(checked(report["defender_binding"])["path"]))
        require(all_binding.get("machine_id") == self.config.machine_id and all_binding.get("status") == "verified"
                and type(all_binding.get("exact_executable_count")) is int
                and all_binding["exact_executable_count"] == len(fixtures), "Original all-fixture Defender binding differs")
        for key in ("manifest", "receipt"):
            checked(all_binding[key])
        administrative = read(Path(parse_pin(all_binding["receipt"])["path"]))
        require(administrative.get("status") == "verified" and administrative.get("admin_token") is True
                and administrative.get("missing_requested_paths") == []
                and set(strings(administrative["verified_requested_paths"]))
                == {parse_pin(item["executable"])["path"] for item in fixtures}, "Actual all-fixture administrative readback differs")
        for fixture in fixtures:
            require(set(fixture) == {"target", "executable", "execution"}, "Original fixture fields differ")
            executable = checked(fixture["executable"])
            execution = read(Path(checked(fixture["execution"])["path"]))
            require(execution.get("machine_id") == self.config.machine_id and execution.get("source_commit") == self.config.source_commit
                    and type(execution.get("original_wait_returncode")) is int and execution["original_wait_returncode"] == 0
                    and execution.get("stopped_reason") is None and execution.get("game_started_or_attached") is False
                    and execution.get("actual_live_business_qualified") is False
                    and strings(execution["argv"])[0] == executable["path"], "Cannot continue an unsuccessful fixture")
            checked(execution["log"])
        production = self.config.output / "link-production.actual.json"
        actual_link = read(production)
        require(actual_link.get("machine_id") == self.config.machine_id and actual_link.get("source_commit") == self.config.source_commit
                and type(actual_link.get("original_wait_returncode")) is int and actual_link["original_wait_returncode"] == 0
                and actual_link.get("stopped_reason") is None and actual_link.get("game_started_or_attached") is False
                and actual_link.get("actual_live_business_qualified") is False, "Original successful production link required")
        checked(actual_link["log"])
        for response in arr(actual_link["response_files"]):
            checked(response)
        incremental = read(self.meta / "INCREMENTAL-RESULT.actual.json")
        require(incremental.get("source_commit") == self.config.source_commit and incremental.get("actual_link") == pin(production),
                "Original production identity differs")
        checked(incremental["dll"])
        if incremental["changed_runtime_archive"] is not None:
            checked(incremental["changed_runtime_archive"])
            archive = read(Path(checked(incremental["changed_runtime_archive_execution"])["path"]))
            require(archive.get("machine_id") == self.config.machine_id and archive.get("source_commit") == self.config.source_commit
                    and type(archive.get("original_wait_returncode")) is int and archive["original_wait_returncode"] == 0
                    and archive.get("stopped_reason") is None, "Original changed-runtime archive execution failed")
        for raw in arr(incremental["production_compiles"]):
            item = obj(raw)
            for field in ("source", "object", "actual_compile"):
                checked(item[field])
            compile_execution = read(Path(parse_pin(item["actual_compile"])["path"]))
            require(compile_execution.get("machine_id") == self.config.machine_id
                    and type(compile_execution.get("original_wait_returncode")) is int
                    and compile_execution["original_wait_returncode"] == 0 and compile_execution.get("stopped_reason") is None,
                    "Original individual compile was unsuccessful")
        plan = pin(self.meta / "PLAN.actual.json")
        original_plan = read(Path(plan["path"]))
        for original in arr(original_plan["retained_link_inputs"]):
            checked(original)
        checked(original_plan["retained_incremental_object"])
        subset = [item for item in fixtures if item["target"] in self.config.qualification_targets]
        binding = pin(self.meta / "qualification-subset-defender-binding.actual.json")
        actual_binding = read(Path(binding["path"]))
        require(actual_binding.get("machine_id") == self.config.machine_id and actual_binding.get("status") == "verified"
                and type(actual_binding.get("exact_executable_count")) is int and actual_binding["exact_executable_count"] == len(subset),
                "Original exact administrative subset readback required")
        for field in ("manifest", "receipt"):
            checked(actual_binding[field])
        self.save("native-a01/SEAL-RESUME-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".actual.json", {
            "machine_id": self.config.machine_id, "observed_at_utc": now(), "native_source_commit": self.config.source_commit,
            "metadata_source_commit": git("rev-parse", "HEAD"), "producer": pin(Path(__file__)),
            "original_production_execution": pin(production), "original_complete_fixtures": pin(self.meta / "ALL-FIXTURES.actual.json"),
            "new_compilation_performed": False, "new_fixture_execution_performed": False,
            "native_outputs_modified": False, "actual_live_business_qualified": False})
        return self.seal(self.commands(), subset, pin(production), binding, plan, self.build / "xar_ck3_bridge.dll", resume=True)

    def fixture_link_support_document(self, qualification: dict[str, object], config_ref: Pin) -> dict[str, object]:
        """Bind configured raw objects to the physical objects in actual link RSPs."""
        scope_ref, freeze_ref = checked(qualification["configured_scope"]), checked(qualification["production_freeze"])
        scope = read(Path(scope_ref["path"]))
        checked(scope["compile_commands"])
        model = read(Path(checked(scope["codemodel"])["path"]))
        reply = Path(parse_pin(scope["codemodel"])["path"]).parent
        entries = [obj(item) for item in arr(obj(arr(model["configurations"])[0])["targets"])]
        shared = load_shared(ROOT / "tools/ck3_mod_acceptance_build_runtime.py", "fixture_object_link_reader")
        reader: object = getattr(shared, "fixture_object_inputs", None)
        require(isinstance(reader, FixtureObjectReader), "Shared FileAPI object reader unavailable")
        if not isinstance(reader, FixtureObjectReader):
            raise ValueError("Shared FileAPI object reader unavailable")
        fixtures = [obj(item) for item in arr(qualification["fixture_results"])]
        raw_inputs: dict[str, set[Path]] = {}
        file_api: dict[str, Pin] = {}
        for fixture in fixtures:
            name = string(fixture["target"])
            matches = [entry for entry in entries if entry["name"] == name]
            require(len(matches) == 1, "Exact fixture FileAPI target required")
            path = reply / relative(matches[0]["jsonFile"])
            inputs = reader(read(path), self.native, self.build)
            if inputs:
                raw_inputs[name], file_api[name] = inputs, pin(path)
        require(raw_inputs, "No external fixture objects require link support")
        proof = verified_fixture_object_bindings(read(Path(checked(config_ref)["path"])),
            sorted(str(path) for path in set().union(*raw_inputs.values())))
        physical = {Path(item["configured_object"]): item["object"] for item in proof.objects}
        declarations = {name: [physical[path] for path in sorted(paths)] for name, paths in raw_inputs.items()}
        actual_links: dict[str, Pin] = {}
        indices = [read(path) for path in self.meta.glob("*FIXTURE-LINKS.actual.json")]
        by_output = {row.output: row for row in self.commands()}
        for name, paths in raw_inputs.items():
            fixture = next(row for row in fixtures if row["target"] == name)
            configured = next(row for row in self.config.fixtures if row.target == name)
            require(not configured.runtime_override_sources and not configured.runtime_override_definitions,
                    "Raw production-object support requires the configured fixture without overrides")
            candidates = [obj(row) for index in indices
                if index.get("machine_id") == self.config.machine_id and index.get("source_commit") == self.config.source_commit
                for row in arr(index["fixtures"])
                if obj(row).get("target") == name and obj(row).get("executable") == fixture["executable"]]
            require(len(candidates) == 1, "Exact actual fixture link execution index required")
            link, execution = self.successful_execution(candidates[0]["actual_link"])
            response_refs = [checked(value) for value in arr(execution["response_files"])]
            require(len(response_refs) == 1, "Exact fixture linker response file required")
            arguments = self.arguments(Path(response_refs[0]["path"]).read_text(encoding="utf-8"))
            linked_objects = [Path(value).resolve() for value in arguments if Path(value).suffix.lower() == ".obj"]
            own = {path for path in self.fixture_link_objects(configured)
                   if path in by_output and by_output[path].target not in PRODUCTION}
            expected = {Path(physical[path]["path"]) for path in paths} | own
            destinations = [Path(value[5:]).resolve() for value in arguments if value.upper().startswith("/OUT:")]
            require(len(linked_objects) == len(set(linked_objects)) and set(linked_objects) == expected
                    and destinations == [Path(parse_pin(fixture["executable"])["path"])],
                    "Actual fixture RSP object map or configured EXE differs")
            actual_links[name] = link
        return {"schema": "ck3-fixture-production-object-link-support-v2", "machine_id": self.config.machine_id,
            "observed_at_utc": now(), "source_commit": self.config.source_commit,
            "actual_live_business_qualified": False, "configured_scope": scope_ref, "production_freeze": freeze_ref,
            "fixture_results": fixtures, "fixture_file_api": file_api, "fixtures": declarations,
            "objects": proof.objects, "producer_config": config_ref, "production_plan": proof.production_plan,
            "incremental_production_result": proof.incremental_production_result,
            "baseline_compile_commands": proof.baseline_compile_commands, "original_dependencies": proof.original_dependencies,
            "actual_links": actual_links}

    def seal_fixture_links(self, label: str) -> Pin:
        """Add source-bound link support in a new metadata directory, retaining old Q."""
        require(isinstance(label, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,100}", label),
                "A finite unique link-support label is required")
        self.metadata_continuation = True
        actual_machine = subprocess.check_output([sys.executable, "-B", "-X", "utf8",
            str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT).decode("utf-8").strip()
        require(actual_machine == self.config.machine_id, "Actual link-support machine differs")
        self.gate()
        original_ref = pin(self.meta / "PUBLIC-RUNTIME-QUALIFICATION.actual.json")
        qualification = read(Path(original_ref["path"]))
        require(qualification.get("schema") == "ck3-qualified-native-build-v1"
                and qualification.get("machine_id") == self.config.machine_id
                and qualification.get("source_commit") == self.config.source_commit
                and qualification.get("actual_live_business_qualified") is False
                and "fixture_link_support" not in qualification, "Original qualified build needs exactly one new link-support seal")
        for field in ("delivery", "snapshot", "profile", "configured_scope", "source_verification",
                      "production_freeze", "original_dll", "published_dll", "defender_binding"):
            checked(qualification[field])
        self.successful_execution(qualification["production_build_receipt"])
        for raw in arr(qualification["fixture_results"]):
            fixture = obj(raw)
            executable = checked(fixture["executable"])
            _, execution = self.successful_execution(fixture["execution"])
            require(strings(execution["argv"])[0] == executable["path"], "Original finite EXE execution differs")
        prefix = "native-a01/" + label + "/"
        config_ref = self.save(prefix + "CONFIG.actual.json", config_json(self.config))
        support = self.fixture_link_support_document(qualification, config_ref)
        support_ref = self.save(prefix + "FIXTURE-LINK-SUPPORT.actual.json", support)
        qualification.update(fixture_link_support=support_ref, observed_at_utc=now())
        result = self.save(prefix + "PUBLIC-RUNTIME-QUALIFICATION.actual.json", qualification)
        self.save(prefix + "METADATA-SEAL.actual.json", {"machine_id": self.config.machine_id,
            "observed_at_utc": now(), "native_source_commit": self.config.source_commit,
            "metadata_source_commit": git("rev-parse", "HEAD"), "producer": pin(Path(__file__)),
            "original_qualification": original_ref, "qualification": result, "fixture_link_support": support_ref,
            "native_outputs_modified": False, "new_compilation_performed": False,
            "new_link_or_fixture_execution_performed": False, "actual_live_business_qualified": False})
        checked(original_ref)
        return result

    def seal(self, rows: list[Compile], fixtures: list[dict[str, object]], build_execution: Pin,
             defender: Pin, plan: Pin, dll: Path, *, resume: bool = False) -> Pin:
        c = self.config
        if c.retained_dependency_evidence is not None or c.schema == "ck3-configured-native-successor-v3":
            self.plan(rows, existing_plan=plan)
        sources: list[dict[str, object]] = []
        for name in git("ls-files", "--", PREFIX).splitlines():
            actual = pin(ROOT / name)
            if c.schema == "ck3-configured-native-successor-v3":
                development = pin(self.native/name.removeprefix(PREFIX))
                require((actual["bytes"], actual["sha256"]) == (development["bytes"], development["sha256"]),
                        "Development source changed before final seal")
            sources.append({"native_relative": name.removeprefix(PREFIX),
                            "bytes": actual["bytes"], "sha256": actual["sha256"]})
        snapshot = self.seal_save("native-a01/SOURCE.actual.json", {"machine_id": c.machine_id,
            "observed_at_utc": now(), "root_commit": c.source_commit, "native_source_commit": c.source_commit,
            "source_count": len(sources), "files": sources, "Root_native_source_base": str(ROOT/PREFIX),
            "snapshot_native_base": str(self.native), "source_mapping":
                "exact native-only development source matches clean committed Root; retained objects/archives referenced without copying"
                if c.schema == "ck3-configured-native-successor-v3" else "exact current clean committed source; no copy"}, resume=resume)
        verification = self.seal_save("native-a01/SOURCE-VERIFICATION.actual.json", {"machine_id": c.machine_id,
            "observed_at_utc": now(), "root_commit": c.source_commit, "source_manifest": snapshot,
            "all_snapshot_files_exactly_verified": len(sources), "all_original_inputs_still_exactly_verified": len(sources)}, resume=resume)
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
        scope = self.seal_save("native-a01/CONFIGURED-SCOPE.actual.json", {"machine_id": c.machine_id,
            "observed_at_utc": now(), "production_TUs": counts, "requested_EXEs": list(c.qualification_targets),
            "no_fixture_in_production": True, "targets": [
                {key: item.get(key, []) for key in ("name", "type", "sources", "compileGroups", "artifacts")}
                for item in [*production.values(), *(targets[names[target]] for target in c.qualification_targets)]],
            "codemodel": pin(model_path), "index": pin(index_path), "compile_commands": pin(self.build / "compile_commands.json"),
            "snapshot": snapshot}, resume=resume)
        baseline = read(Path(c.baseline["path"]))
        profile_ref = checked(baseline["profile"])
        profile = read(Path(profile_ref["path"]))
        flags = cmake_boolean_flags(self.build / "CMakeCache.txt")
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


def verified_fixture_object_bindings(config_value: object, configured_outputs: list[str], *,
                                     noncompiled_replay: object = None) -> FixtureObjectProof:
    """Read-only replay of the original source/dependency/options and object proof."""
    config = parse_config(config_value)
    outputs = strings(configured_outputs)
    require(outputs and len(outputs) == len(set(outputs)), "Distinct configured fixture objects required")
    producer = Producer(config)  # Loads parsers only; no initialize, gate, configure or commands execute.
    require(all(Path(name).is_absolute() and Path(name) == Path(name).resolve()
                and Path(name).is_relative_to(producer.build / "CMakeFiles")
                and Path(name).suffix.lower() == ".obj" for name in outputs),
            "Configured fixture objects must be exact absolute production build paths")
    rows = producer.commands()
    incremental_ref = pin(producer.meta / "INCREMENTAL-RESULT.actual.json")
    incremental = read(Path(incremental_ref["path"]))
    plan_ref = checked(incremental["production_plan"])
    selected, borrowed, _ = producer.plan(rows, existing_plan=plan_ref, noncompiled_replay=noncompiled_replay)
    inputs = producer.original_fixture_inputs(rows)
    require({row.output for row in selected} == set(inputs.compiled)
            and all(borrowed[name] == path for name, path in inputs.borrowed.items()),
            "Recomputed physical production object selection differs")
    raw_commands: object = json.loads((producer.build / "compile_commands.json").read_text(encoding="utf-8-sig"))
    indices: dict[Path, int] = {}
    for index, raw in enumerate(arr(raw_commands)):
        command = obj(raw)
        output = Path(string(command["output"]))
        output = output if output.is_absolute() else producer.build / output
        require(output not in indices, "Duplicate configured compile output")
        indices[output] = index
    by_output = {row.output: row for row in rows if row.target in PRODUCTION}
    objects: list[FixtureProductionObjectBinding] = []
    for name in sorted(outputs):
        path = Path(name)
        require(path.is_absolute() and path == path.resolve() and path in by_output,
                "Fixture raw object is not a configured production output")
        row = by_output[path]
        physical = inputs.object_paths.get(path)
        if physical is None:
            physical = inputs.borrowed.get(path.relative_to(producer.build).as_posix())
        require(physical is not None, "Fixture raw object has no actual retained or successful compile proof")
        if physical is None:
            raise ValueError("Fixture physical object missing")
        objects.append({"configured_object": str(path), "object": pin(physical),
            "production_target": row.target, "native_relative": row.source.relative_to(producer.native).as_posix(),
            "source": pin(row.source), "configured_compile_command_index": indices[path]})
    baseline = read(Path(config.baseline["path"]))
    baseline_scope = read(Path(checked(baseline["configured_scope"])["path"]))
    original = read(Path(plan_ref["path"]))
    return FixtureObjectProof(objects, plan_ref, incremental_ref, checked(baseline_scope["compile_commands"]),
        checked(original["original_dependencies"]))


def main() -> int:
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    continuation = parser.add_mutually_exclusive_group()
    continuation.add_argument("--seal-existing", action="store_true", help="Validate completed original commands and continue missing metadata only")
    continuation.add_argument("--resume-fixtures", metavar="UNIQUE_LABEL",
        help="Validate completed production, preserve unknown outputs and actually rebuild/run fixtures")
    continuation.add_argument("--seal-fixture-links", metavar="UNIQUE_LABEL",
        help="Add exact source-bound retained fixture-object support to a new metadata-only qualification")
    args = parser.parse_args()
    config = parse_config(read(args.config))
    producer = Producer(config)
    if args.seal_fixture_links is not None:
        result = producer.seal_fixture_links(args.seal_fixture_links)
    elif args.resume_fixtures is not None:
        result = producer.resume_fixtures(args.resume_fixtures)
    else:
        result = producer.resume_seal() if args.seal_existing else producer.run()
    print(json.dumps({"qualified_native": result, "game_started": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
