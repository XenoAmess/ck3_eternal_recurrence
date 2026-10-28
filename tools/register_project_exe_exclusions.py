#!/usr/bin/env python3
"""Opt-in exact-file Defender registration for proven project build EXE outputs."""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import os
import stat
from pathlib import Path
import subprocess
import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import Literal, Never, NotRequired, Protocol, TypedDict
from ck3_live_run_id import current_machine_id

CONFIG_KEY = "xar.defenderProjectExeExclusions"
NAMESPACE = r"root\Microsoft\Windows\Defender"
SCHEMA = "xar.project-exe-exclusions.v1"
QUERY = Path(".cmake/api/v1/query/client-xar-defender-exe/codemodel-v2")


def fingerprint(path: Path) -> dict:
    if not path.is_file() or path.suffix.lower() != ".exe":
        raise ValueError(f"Expected one existing EXE file: {path}")
    if any(c in str(path) for c in ("*", "?", "%")):
        raise ValueError("Wildcard/environment paths are not allowed")
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    return {"path": str(path.resolve()), "size": path.stat().st_size, "sha256": digest}


def opted_in(repo: Path) -> bool:
    # Local Git configuration is shared by linked worktrees, not cloned to CI.
    if os.environ.get("CI"):
        return False
    try:
        result = subprocess.run(["git", "-C", str(repo), "config", "--local", "--bool", "--get", CONFIG_KEY],
                                capture_output=True, text=True, check=False)
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def validate_source(repo: Path, source: Path, external_candidate: str | None) -> None:
    expected = (repo / "ck3_autonomous_player/native_bridge").resolve()
    if source.resolve() != expected and not (isinstance(external_candidate, str) and external_candidate.strip()):
        raise ValueError("Source must be this checkout native_bridge or an explicitly named external candidate")
    if not (source / "CMakeLists.txt").is_file():
        raise ValueError("Named project source has no CMakeLists.txt")


def request_codemodel(build: Path) -> None:
    query = build / QUERY
    query.parent.mkdir(parents=True, exist_ok=True)
    query.touch(exist_ok=True)


def has_codemodel_reply(build: Path) -> bool:
    indexes = sorted((build / ".cmake/api/v1/reply").glob("index-*.json"), key=lambda p: p.stat().st_mtime_ns)
    if not indexes:
        return False
    try:
        return any(x.get("kind") == "codemodel" and x.get("version", {}).get("major") == 2
                   for x in _json(indexes[-1]).get("objects", []))
    except (OSError, ValueError):
        return False


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_manifest(repo: Path, source: Path, build: Path, configuration: str,
                     targets: list[str], external_candidate: str | None = None) -> dict:
    source, build = source.resolve(), build.resolve()
    validate_source(repo, source, external_candidate)
    reply = build / ".cmake/api/v1/reply"
    indexes = sorted(reply.glob("index-*.json"), key=lambda p: p.stat().st_mtime_ns)
    if not indexes:
        raise ValueError("Missing CMake codemodel; configure with the file-api query before registration")
    index_path = indexes[-1]
    index = _json(index_path)
    models = [x for x in index.get("objects", []) if x.get("kind") == "codemodel" and x.get("version", {}).get("major") == 2]
    if len(models) != 1:
        raise ValueError("Exactly one codemodel-v2 object required")
    def reply_path(name: str) -> Path:
        path = (reply / name).resolve()
        if not path.is_relative_to(reply.resolve()):
            raise ValueError("CMake reply path escapes its directory")
        return path
    model_path = reply_path(models[0]["jsonFile"])
    model = _json(model_path)
    if Path(model["paths"]["source"]).resolve() != source or Path(model["paths"]["build"]).resolve() != build:
        raise ValueError("CMake codemodel source/build identity mismatch")
    configurations = model["configurations"]
    configs = [c for c in configurations if c.get("name") in (configuration, "")]
    if len(configs) != 1:
        raise ValueError("Requested CMake configuration not unique")
    rows = configs[0]["targets"]
    by_id = {row["id"]: row for row in rows}
    by_name = {row["name"]: row["id"] for row in rows}
    if targets == ["all"]:
        pending = list(by_id)
    else:
        if any(name not in by_name for name in targets):
            raise ValueError("Requested target absent from CMake codemodel")
        pending = [by_name[name] for name in targets]
    visited, files, provenance = set(), [], []
    while pending:
        identity = pending.pop()
        if identity in visited:
            continue
        visited.add(identity)
        row = by_id[identity]
        target_path = reply_path(row["jsonFile"])
        target = _json(target_path)
        if target.get("id") != identity or target.get("name") != row["name"]:
            raise ValueError("CMake target identity mismatch")
        pending.extend(d["id"] for d in target.get("dependencies", []) if d["id"] in by_id)
        if target.get("type") != "EXECUTABLE" or target.get("imported") or target.get("isGeneratorProvided"):
            continue
        target_source = (source / target["paths"]["source"]).resolve()
        if not target_source.is_relative_to(source):
            continue
        for artifact in target.get("artifacts", []):
            path = (build / artifact["path"]).resolve()
            if path.suffix.lower() != ".exe" or not path.is_file():
                continue
            if not path.is_relative_to(build):
                raise ValueError("Automatic EXE registration is restricted to its named build directory")
            record = fingerprint(path)
            record.update({"target": target["name"], "target_id": identity})
            files.append(record)
        provenance.append({"path": str(target_path), "sha256": hashlib.sha256(target_path.read_bytes()).hexdigest(),
                           "target": target["name"], "target_id": identity, "source": str(target_source)})
    unique = {ntpath.normcase(r["path"]): r for r in files}
    return {"schema": SCHEMA, "repo": str(repo.resolve()), "source_dir": str(source), "build_dir": str(build),
            "configuration": configuration, "requested_targets": targets, "external_candidate": external_candidate,
            "cmake_index": {"path": str(index_path), "sha256": hashlib.sha256(index_path.read_bytes()).hexdigest()},
            "cmake_codemodel": {"path": str(model_path), "sha256": hashlib.sha256(model_path.read_bytes()).hexdigest()},
            "target_provenance": provenance, "files": sorted(unique.values(), key=lambda r: r["path"])}


def collect_command_manifest(repo: Path, source: Path, build: Path, compiler_argv: list[str],
                             exe_paths: list[Path], external_candidate: str | None = None,
                             return_code: int = 0, source_commands: list[dict] | None = None) -> dict:
    source, build = source.resolve(), build.resolve()
    expected = (repo / "ck3_autonomous_player/native_bridge").resolve()
    if source != expected and not (isinstance(external_candidate, str) and external_candidate.strip()):
        raise ValueError("Command source must be checkout native_bridge or an explicitly named candidate")
    if not source.is_dir():
        raise ValueError("Named command source directory does not exist")
    if type(return_code) is not int or return_code != 0 or not compiler_argv:
        raise ValueError("Caller must provide its actual successful MSVC output command")
    tool = Path(compiler_argv[0]).name.lower()
    if tool not in ("cl.exe", "link.exe"):
        raise ValueError("Only actual MSVC cl.exe or link.exe output commands are accepted")
    def option_paths(argv: list[str], prefix: str) -> list[Path]:
        paths = []
        for i, arg in enumerate(argv):
            value = None
            if arg.lower() == prefix and i + 1 < len(argv):
                value = argv[i + 1]
            elif arg.lower().startswith(prefix) and len(arg) > len(prefix):
                value = arg[len(prefix):]
                # CL accepts both /Fe<path> and /Fe:<path>.
                if prefix == "/fe" and value.startswith(":"):
                    value = value[1:]
            if value:
                path = Path(value)
                if not path.is_absolute():
                    raise ValueError("MSVC output operand must be an explicit absolute file path")
                paths.append(path.resolve())
        return paths
    declared = option_paths(compiler_argv, "/fe" if tool == "cl.exe" else "/out:")
    def pin(path: Path) -> dict:
        return {"path": str(path.resolve()), "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    inputs, objects = [], []
    commands = [{"argv": compiler_argv, "return_code": return_code}] if tool == "cl.exe" else source_commands
    if not commands:
        raise ValueError("Actual link.exe requires prior successful CL/c source command provenance")
    for command in commands:
        argv = command["argv"]
        if type(command.get("return_code")) is not int or command["return_code"] != 0 or not argv or Path(argv[0]).name.lower() != "cl.exe":
            raise ValueError("Prior source command must be the caller actual successful cl.exe argv")
        for arg in argv[1:]:
            path = Path(arg)
            if path.suffix.lower() not in (".cpp", ".cc", ".cxx", ".c"):
                continue
            if not path.is_absolute() or not path.resolve().is_relative_to(source) or not path.is_file():
                raise ValueError("MSVC source argument must be an exact existing file in the named project/candidate")
            inputs.append(pin(path))
        if tool == "link.exe":
            if "/c" not in [arg.lower() for arg in argv]:
                raise ValueError("Prior linker input producer must be actual cl.exe /c")
            outputs = option_paths(argv, "/fo")
            if not outputs:
                raise ValueError("Actual CL/c command must declare exact absolute /Fo object output")
            for path in outputs:
                if path.suffix.lower() != ".obj" or not path.is_relative_to(build) or not path.is_file():
                    raise ValueError("CL/c object output must be an exact existing .obj within this build")
                objects.append(pin(path))
    if tool == "link.exe":
        linked = [Path(arg).resolve() for arg in compiler_argv[1:] if Path(arg).suffix.lower() == ".obj"]
        produced = {ntpath.normcase(row["path"]) for row in objects}
        if not linked or any(ntpath.normcase(str(path)) not in produced for path in linked):
            raise ValueError("Every linked object must have a matching actual successful CL/c producer")
    if not inputs or not exe_paths:
        raise ValueError("Explicit successful command requires source and EXE output operands")
    declared_keys = {ntpath.normcase(str(p)) for p in declared}
    files = []
    for item in exe_paths:
        path = Path(item).resolve()
        if not path.is_relative_to(build) or ntpath.normcase(str(path)) not in declared_keys:
            raise ValueError("EXE is not an exact declared MSVC output within this named build directory")
        files.append(fingerprint(path))
    if len({ntpath.normcase(row["path"]) for row in files}) != len(files):
        raise ValueError("Duplicate explicit EXE output")
    return {"schema": SCHEMA, "repo": str(repo.resolve()), "source_dir": str(source), "build_dir": str(build),
            "external_candidate": external_candidate,
            "command_provenance": {"kind": "msvc-explicit-command", "argv": compiler_argv,
                                   "return_code": return_code, "sources": inputs, "objects": objects,
                                   "source_commands": source_commands,
                                   "declaration_boundary": "Caller actual successful command chain; not inferred from EXE name or directory scan"},
            "files": files}


def after_successful_command_build(repo: Path, source: Path, build: Path,
                                   compiler_argv: list[str], exe_paths: list[Path],
                                   external_candidate: str | None = None,
                                   return_code: int = 0, source_commands: list[dict] | None = None) -> dict:
    if not opted_in(repo):
        return {"status": "disabled", "reason": "Local Git opt-in absent/false or CI environment"}
    attempt = build / "defender-exe-exclusions" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    attempt.mkdir(parents=True, exist_ok=False)
    try:
        manifest = collect_command_manifest(repo, source, build, compiler_argv, exe_paths, external_candidate, return_code, source_commands)
    except Exception as error:
        failed = {"schema": SCHEMA, "status": "settings_failed", "error": str(error),
                  "error_type": type(error).__name__, "method": "not-called; invalid explicit command provenance",
                  "before": None, "after": None, "calls": [], "files": [], "settings_success_is_runtime_trust": False}
        _write_receipt(attempt / "receipt.json", failed)
        return {"status": "settings_failed", "receipt": str(attempt / "receipt.json"), "error": str(error)}
    manifest_path = attempt / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = register_manifest(manifest, attempt / "receipt.json", manifest_bytes=manifest_path.read_bytes())
    return {"status": result["status"], "manifest": str(manifest_path), "receipt": str(attempt / "receipt.json"),
            "receipt_sha256": hashlib.sha256((attempt / "receipt.json").read_bytes()).hexdigest(), "error": result.get("error")}


class ExclusionSettings(TypedDict):
    ExclusionPath: list[str]
    ExclusionExtension: list[str]
    ExclusionProcess: list[str]


class NullableExclusionSettings(TypedDict):
    ExclusionPath: list[str]
    ExclusionExtension: list[str] | None
    ExclusionProcess: list[str] | None

ExclusionField = Literal["ExclusionPath", "ExclusionExtension", "ExclusionProcess"]

class ProviderPropertyObservation(TypedDict):
    name: ExclusionField
    cim_type: Literal[8]
    is_array: Literal[True]
    value_state: Literal["STRING_ARRAY", "OBSERVED_NULLABLE_VALUE"]

class WmiProperty(Protocol):
    Name: object
    Value: object
    CIMType: object
    IsArray: object

class WmiProperties(Protocol):
    def Item(self, name: str) -> WmiProperty: ...

class WmiPreferenceRow(Protocol):
    Properties_: WmiProperties

class WmiReadServices(Protocol):
    def ExecQuery(self, query: str) -> Iterable[WmiPreferenceRow]: ...

class DirectSettingsReadbackFields(TypedDict):
    observed_extensions_unchanged: bool
    observed_processes_unchanged: bool
    settings_readback_complete: bool
    settings_readback_error: str | None
    settings_readback_process_id: int
    settings_readback_token_user_sid: str

class DirectSettingsReadbackV1(DirectSettingsReadbackFields):
    settings_readback_schema: Literal["xar.project-exe-three-settings-readback/v1"]
    before_settings: ExclusionSettings | None
    after_settings: ExclusionSettings | None

class DirectSettingsReadbackV2(DirectSettingsReadbackFields):
    settings_readback_schema: Literal["xar.project-exe-three-settings-readback/v2"]
    before_settings: NullableExclusionSettings | None
    after_settings: NullableExclusionSettings | None
    before_property_observations: list[ProviderPropertyObservation] | None
    after_property_observations: list[ProviderPropertyObservation] | None
    nullable_observation_scope: str

DirectSettingsReadback = DirectSettingsReadbackV1 | DirectSettingsReadbackV2


class DefenderWmi:
    def __init__(self) -> None:
        import pythoncom
        import win32api
        import win32con
        import win32security
        import win32com.client
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
        try:
            user = win32security.GetTokenInformation(token, win32security.TokenUser)
            sid = user[0] if isinstance(user, tuple) else user
            self.token_user_sid: str = win32security.ConvertSidToStringSid(sid)
        finally:
            token.Close()
        self.before_settings: NullableExclusionSettings | None = None
        self.administrative_token_observed: bool = bool(ctypes.windll.shell32.IsUserAnAdmin())
        self.provider_nullable_observed: bool = False
        self.before_property_observations: list[ProviderPropertyObservation] | None = None
        self.after_property_observations: list[ProviderPropertyObservation] | None = None
        self.current_property_observations: list[ProviderPropertyObservation] | None = None
        self.after_settings: NullableExclusionSettings | None = None
        self.settings_readback_error: str | None = None
        pythoncom.CoInitialize()
        self.services = win32com.client.GetObject(
            "winmgmts:{impersonationLevel=impersonate}!\\\\.\\" + NAMESPACE)

    @staticmethod
    def _array(value: object, field: str) -> list[str]:
        if not isinstance(value, (list, tuple)):
            raise RuntimeError(f"Defender {field} readback is unavailable: expected an observed string array")
        result: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise RuntimeError(f"Defender {field} readback contains a non-string value")
            result.append(item)
        return result

    @staticmethod
    def _copy(settings: NullableExclusionSettings) -> NullableExclusionSettings:
        extensions, processes = settings["ExclusionExtension"], settings["ExclusionProcess"]
        return {"ExclusionPath": list(settings["ExclusionPath"]),
                "ExclusionExtension": None if extensions is None else list(extensions),
                "ExclusionProcess": None if processes is None else list(processes)}

    @staticmethod
    def _same_nonpath(before: list[str] | None, after: list[str] | None) -> bool:
        if before is None or after is None:
            return before is None and after is None
        return set(before) == set(after)

    @staticmethod
    def _v1_settings(settings: NullableExclusionSettings | None) -> ExclusionSettings | None:
        if settings is None:
            return None
        return {"ExclusionPath": list(settings["ExclusionPath"]),
                "ExclusionExtension": DefenderWmi._array(settings["ExclusionExtension"], "ExclusionExtension"),
                "ExclusionProcess": DefenderWmi._array(settings["ExclusionProcess"], "ExclusionProcess")}

    def _qualified_nullable_properties(self, props: WmiProperties,
                                       values: Mapping[str, object]) -> list[ProviderPropertyObservation]:
        if self.administrative_token_observed is not True or not self.token_user_sid:
            raise RuntimeError("Nullable Defender property observation requires an actual administrative token")
        result: list[ProviderPropertyObservation] = []
        fields: tuple[ExclusionField, ...] = ("ExclusionPath", "ExclusionExtension", "ExclusionProcess")
        for name in fields:
            prop = props.Item(name)
            if prop.Name != name or type(prop.CIMType) is not int or prop.CIMType != 8 or prop.IsArray is not True:
                raise RuntimeError("Defender nullable property schema is unavailable: " + name)
            result.append({"name": name, "cim_type": 8, "is_array": True,
                           "value_state": "OBSERVED_NULLABLE_VALUE" if values[name] is None else "STRING_ARRAY"})
        return result

    @staticmethod
    def _preference_rows(services: WmiReadServices) -> list[WmiPreferenceRow]:
        return list(services.ExecQuery(
            "SELECT ExclusionPath,ExclusionExtension,ExclusionProcess FROM MSFT_MpPreference"))

    def read_settings(self) -> NullableExclusionSettings:
        rows = self._preference_rows(self.services)
        if len(rows) != 1:
            raise RuntimeError("Defender preference read did not return exactly one object")
        props = rows[0].Properties_
        values: dict[str, object] = {name: props.Item(name).Value for name in
                                   ("ExclusionPath", "ExclusionExtension", "ExclusionProcess")}
        nullable = values["ExclusionExtension"] is None or values["ExclusionProcess"] is None
        if nullable or self.provider_nullable_observed:
            self.current_property_observations = self._qualified_nullable_properties(props, values)
            self.provider_nullable_observed = True
        else:
            self.current_property_observations = None
        return {"ExclusionPath": self._array(values["ExclusionPath"], "ExclusionPath"),
                "ExclusionExtension": None if nullable and values["ExclusionExtension"] is None else self._array(values["ExclusionExtension"], "ExclusionExtension"),
                "ExclusionProcess": None if nullable and values["ExclusionProcess"] is None else self._array(values["ExclusionProcess"], "ExclusionProcess")}

    def read_paths(self) -> list[str]:
        try:
            current = self.read_settings()
            before = self.before_settings
            if before is None:
                before = self._copy(current)
                self.before_settings = before
                self.before_property_observations = self.current_property_observations
            self.after_settings = self._copy(current)
            self.after_property_observations = self.current_property_observations
            for name, old_rows, new_rows in (
                    ("ExclusionExtension", before["ExclusionExtension"], current["ExclusionExtension"]),
                    ("ExclusionProcess", before["ExclusionProcess"], current["ExclusionProcess"])):
                if not self._same_nonpath(old_rows, new_rows):
                    raise RuntimeError("Defender non-path exclusion changed: " + name)
            if self.settings_readback_error is not None:
                raise RuntimeError("Earlier Defender settings readback failed; no qualified continuation")
            return list(current["ExclusionPath"])
        except Exception as error:
            if self.settings_readback_error is None:
                self.settings_readback_error = type(error).__name__ + ": " + str(error)
            raise

    def settings_readback(self) -> DirectSettingsReadback:
        before, after = self.before_settings, self.after_settings
        observations_before = self.before_property_observations
        observations_after = self.after_property_observations
        complete = before is not None and after is not None and self.settings_readback_error is None
        extensions_unchanged = processes_unchanged = False
        if before is not None and after is not None and self.settings_readback_error is None:
            extensions_unchanged = self._same_nonpath(before["ExclusionExtension"], after["ExclusionExtension"])
            processes_unchanged = self._same_nonpath(before["ExclusionProcess"], after["ExclusionProcess"])
        if self.provider_nullable_observed:
            complete = complete and observations_before is not None and observations_after is not None
        common: DirectSettingsReadbackFields = {
            "observed_extensions_unchanged": extensions_unchanged,
            "observed_processes_unchanged": processes_unchanged,
            "settings_readback_complete": complete,
            "settings_readback_error": self.settings_readback_error,
            "settings_readback_process_id": os.getpid(),
            "settings_readback_token_user_sid": self.token_user_sid,
        }
        if self.provider_nullable_observed:
            nullable_result: DirectSettingsReadbackV2 = {
                **common,
                "settings_readback_schema": "xar.project-exe-three-settings-readback/v2",
                "before_settings": None if before is None else self._copy(before),
                "after_settings": None if after is None else self._copy(after),
                "before_property_observations": None if observations_before is None else [row.copy() for row in observations_before],
                "after_property_observations": None if observations_after is None else [row.copy() for row in observations_after],
                "nullable_observation_scope": (
                    "Same administrative WMI client, one MSFT_MpPreference instance and existing Name/CIMType8/IsArray=true properties. "
                    "Python None is retained as an observed nullable CIM value, distinct from an empty array; raw VARIANT is not remeasured by this reader. "
                    "No assertion that effective exclusions are empty or unconfigured."),
            }
            return nullable_result
        array_result: DirectSettingsReadbackV1 = {
            **common,
            "settings_readback_schema": "xar.project-exe-three-settings-readback/v1",
            "before_settings": self._v1_settings(before),
            "after_settings": self._v1_settings(after),
        }
        return array_result

    def add_path(self, path: str) -> int | None | dict[str, object]:
        preference = self.services.Get("MSFT_MpPreference")
        parameters = preference.Methods_.Item("Add").InParameters.SpawnInstance_()
        parameters.Properties_.Item("ExclusionPath").Value = (path,)
        if any(p.Name == "Force" for p in parameters.Properties_):
            parameters.Properties_.Item("Force").Value = True
        result = preference.ExecMethod_("Add", parameters)
        if result is None:
            return None
        try:
            return int(result.Properties_.Item("ReturnValue").Value)
        except Exception as error:
            # The provider was invoked already. Do not turn an output-decoder
            # problem into a reason to invoke Add again; fresh readback decides.
            return {"return_value": None, "return_object_absent": False,
                    "return_decode_error": str(error), "return_decode_error_type": type(error).__name__}


def require_system_broker_readback(value: object) -> tuple[NullableExclusionSettings, NullableExclusionSettings]:
    """Validate the nullable SYSTEM branch without treating null as an empty array."""
    if not isinstance(value, dict):
        raise ValueError("SYSTEM readback object required")
    if value.get("settings_readback_schema") != "xar.project-exe-three-settings-readback/v2":
        raise ValueError("Explicit nullable SYSTEM readback schema required")
    if (value.get("settings_readback_complete") is not True or
            "settings_readback_error" not in value or value["settings_readback_error"] is not None or
            type(value.get("settings_readback_process_id")) is not int or
            not 1 <= value["settings_readback_process_id"] <= 0xffffffff or
            value.get("settings_readback_token_user_sid") != "S-1-5-18"):
        raise ValueError("Complete actual SYSTEM worker readback identity required")
    scope = ("Same administrative WMI client, one MSFT_MpPreference instance and existing Name/CIMType8/IsArray=true properties. "
             "Python None is retained as an observed nullable CIM value, distinct from an empty array; raw VARIANT is not remeasured by this reader. "
             "No assertion that effective exclusions are empty or unconfigured.")
    if value.get("nullable_observation_scope") != scope:
        raise ValueError("Nullable observation scope differs")
    fields: tuple[ExclusionField, ...] = ("ExclusionPath", "ExclusionExtension", "ExclusionProcess")
    parsed: list[NullableExclusionSettings] = []
    for phase in ("before", "after"):
        settings = value.get(phase + "_settings")
        props = value.get(phase + "_property_observations")
        if not isinstance(settings, dict) or set(settings) != set(fields):
            raise ValueError("Three complete setting fields required")
        if not isinstance(props, list) or len(props) != 3:
            raise ValueError("Three ordered property observations required")
        arrays: list[list[str] | None] = []
        for index, field in enumerate(fields):
            raw = settings[field]
            if raw is None and field != "ExclusionPath":
                array = None
            elif isinstance(raw, list) and all(isinstance(item, str) for item in raw):
                array = [str(item) for item in raw]
            else:
                raise ValueError("Path must be an array; nonpath values are nullable arrays")
            prop = props[index]
            if (not isinstance(prop, dict) or
                    set(prop) != {"name", "cim_type", "is_array", "value_state"} or
                    prop["name"] != field or type(prop["cim_type"]) is not int or
                    prop["cim_type"] != 8 or prop["is_array"] is not True or
                    prop["value_state"] != ("OBSERVED_NULLABLE_VALUE" if array is None else "STRING_ARRAY")):
                raise ValueError("Property observation does not match the actual value")
            arrays.append(array)
        paths = arrays[0]
        if paths is None:
            raise ValueError("Path cannot be null")
        parsed.append({"ExclusionPath": paths, "ExclusionExtension": arrays[1], "ExclusionProcess": arrays[2]})
    before, after = parsed
    nonpath_fields: tuple[Literal["ExclusionExtension", "ExclusionProcess"], ...] = ("ExclusionExtension", "ExclusionProcess")
    if all(settings[field] is not None for settings in (before, after)
           for field in nonpath_fields):
        raise ValueError("Nullable schema requires an actually observed null")
    for field in nonpath_fields:
        left, right = before[field], after[field]
        same = left is None and right is None if left is None or right is None else set(left) == set(right)
        if not same or value.get("observed_" + ("extensions" if field == "ExclusionExtension" else "processes") + "_unchanged") is not True:
            raise ValueError("Nonpath settings changed or were not observed unchanged")
    return before, after


def _write_receipt(path: Path, receipt: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = getattr(receipt, "broker_raw_bytes", None)
    if raw is not None:
        if not isinstance(raw, bytes) or json.loads(raw.decode("utf-8")) != dict(receipt):
            raise ValueError("Broker raw receipt bytes differ from returned receipt")
        with path.open("xb") as handle:
            handle.write(raw)
        return
    with path.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def register_manifest(manifest: dict, receipt_path: Path, *, client=None, admin: bool | None = None,
                      broker_dispatch=None, manifest_bytes: bytes | None = None) -> dict:
    if receipt_path.exists():
        raise FileExistsError(f"Receipt already exists; no WMI operation attempted: {receipt_path}")
    receipt = {"schema": SCHEMA, "status": "running", "method": "WMI MSFT_MpPreference.Add ExclusionPath only",
               "namespace": NAMESPACE, "before": None, "after": None, "calls": [], "files": manifest.get("files", []),
               "settings_success_is_runtime_trust": False, "exclusion_types_written": ["ExclusionPath exact files"]}
    stage = "manifest-validation"
    native_settings_client: DefenderWmi | None = None
    # Explicit admin/fake-client paths never discover or run a machine task.
    auto_broker = admin is None and client is None
    def record_readback(paths: list[str]) -> bool:
        receipt["after"] = paths
        observed = {ntpath.normcase(p) for p in paths}
        requested = {ntpath.normcase(r["path"]) for r in manifest["files"]}
        prior = {ntpath.normcase(p) for p in receipt["before"]}
        receipt["verified_requested_paths"] = [r["path"] for r in manifest["files"] if ntpath.normcase(r["path"]) in observed]
        receipt["missing_requested_paths"] = [r["path"] for r in manifest["files"] if ntpath.normcase(r["path"]) not in observed]
        receipt["observed_prior_settings_preserved"] = prior <= observed
        newly_present = (requested - prior) & observed
        receipt["partial_mutation"] = bool(newly_present) and not (requested <= observed and prior <= observed)
        paths_verified = requested <= observed and prior <= observed
        if native_settings_client is not None:
            evidence = native_settings_client.settings_readback()
            receipt.update(evidence)
            return paths_verified and evidence["settings_readback_complete"] and \
                evidence["observed_extensions_unchanged"] and evidence["observed_processes_unchanged"]
        return paths_verified
    try:
        repo = Path(manifest["repo"])
        if not opted_in(repo):
            receipt.update(status="disabled", reason="Local Git opt-in absent/false or CI environment")
            return receipt
        if manifest.get("schema") != SCHEMA:
            raise ValueError("Manifest schema mismatch")
        if "command_provenance" in manifest:
            provenance = manifest["command_provenance"]
            fresh = collect_command_manifest(repo, Path(manifest["source_dir"]), Path(manifest["build_dir"]),
                                             provenance["argv"], [Path(r["path"]) for r in manifest["files"]],
                                             manifest.get("external_candidate"), provenance["return_code"], provenance.get("source_commands"))
        else:
            fresh = collect_manifest(repo, Path(manifest["source_dir"]), Path(manifest["build_dir"]),
                                     manifest["configuration"], manifest["requested_targets"], manifest.get("external_candidate"))
        if fresh != manifest:
            raise ValueError("Frozen manifest bytes/provenance/current EXE identity changed")
        receipt["manifest_sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        if admin is None:
            admin = os.name == "nt" and bool(ctypes.windll.shell32.IsUserAnAdmin())
        receipt["admin_token"] = admin
        if not admin:
            if auto_broker or broker_dispatch is not None:
                stage = "broker-dispatch"
                dispatch = broker_dispatch
                if dispatch is None:
                    from project_exe_exclusion_broker_client import dispatch_manifest
                    dispatch = dispatch_manifest
                dispatch_kwargs = {"proof_dir": receipt_path.parent / ("broker-proof-" + uuid.uuid4().hex)}
                if manifest_bytes is not None:
                    dispatch_kwargs["manifest_bytes"] = manifest_bytes
                broker_receipt = dispatch(manifest, **dispatch_kwargs)
                if broker_receipt is not None:
                    if not isinstance(broker_receipt, dict) or broker_receipt.get("schema") != SCHEMA:
                        raise ValueError("Broker did not return an actual project EXE receipt")
                    receipt = broker_receipt
                    return receipt
            # Non-admin WMI may hide exclusions as empty arrays. Neither an
            # empty list nor existing-path verification is trustworthy here.
            receipt["admin_required_for_verified_readback"] = True
            receipt["readback_visibility"] = "unverified; administrative token required"
            raise PermissionError("admin_required_for_verified_readback; no Add attempted and no UAC bypass")
        receipt["readback_visibility"] = "same administrative token and WMI client for before/after"
        if client is None:
            if os.name != "nt":
                raise RuntimeError("Defender WMI registration requires Windows")
            client = DefenderWmi()
            native_settings_client = client
        stage = "before-readback"
        before = client.read_paths()
        receipt["before"] = before
        known = {ntpath.normcase(p) for p in before}
        for row in manifest["files"]:
            path = row["path"]
            stage = "pre-call-file-validation"
            if fingerprint(Path(path)) != {k: row[k] for k in ("path", "size", "sha256")}:
                raise ValueError("EXE changed before its Add call")
            if ntpath.normcase(path) in known:
                receipt["calls"].append({"path": path, "method": "already-present", "return_value": None})
                continue
            call = {"path": path, "method": "Add", "return_value": None, "return_value_available": False}
            receipt["calls"].append(call)
            stage = "Add-invocation"
            try:
                response = client.add_path(path)
            except Exception as error:
                call.update(call_error=str(error), call_error_type=type(error).__name__)
                raise
            if isinstance(response, dict):
                call.update(response)
                value = response.get("return_value")
            else:
                value = response
                call.update(return_value=value, return_object_absent=response is None)
            call["return_value_available"] = value is not None
            if value is not None and value != 0:
                stage = "Add-return-value"
                raise RuntimeError(f"WMI Add returned {value} for {path}")
            if value is None:
                # Nullable return objects and decoder errors need observation
                # before any next distinct Add. Never retry this path blindly.
                stage = "post-call-readback"
                observed_paths = client.read_paths()
                call["fresh_readback"] = observed_paths
                observed = {ntpath.normcase(p) for p in observed_paths}
                record_readback(observed_paths)
                if not (known | {ntpath.normcase(path)}) <= observed:
                    raise RuntimeError("Fresh readback after unavailable ReturnValue did not preserve prior/exact path")
                known = observed
            else:
                known.add(ntpath.normcase(path))
                if native_settings_client is not None:
                    stage = "post-call-readback"
                    observed_paths = client.read_paths()
                    call["fresh_readback"] = observed_paths
                    observed = {ntpath.normcase(p) for p in observed_paths}
                    record_readback(observed_paths)
                    if not known <= observed:
                        raise RuntimeError("Fresh three-setting readback did not preserve prior/exact paths")
                    known = observed
        stage = "final-readback"
        if not record_readback(client.read_paths()):
            raise RuntimeError("Defender readback missing requested exact paths or observed prior settings")
        receipt.update(status="verified", verification_source="same-admin-client fresh readback")
    except Exception as error:
        receipt.update(status="settings_failed", error=str(error), error_type=type(error).__name__, error_stage=stage)
        if stage == "broker-dispatch" and getattr(error, "proof", None) is not None:
            receipt["broker_failure_proof"] = error.proof
        if client is not None and admin and receipt["before"] is not None:
            try:
                fulfilled = record_readback(client.read_paths())
                # A provider can mutate then raise, or its output decoder can
                # fail. Preserve that fact independently of verified settings.
                if fulfilled and stage in ("Add-invocation", "Add-return-value", "post-call-readback", "final-readback"):
                    receipt.update(status="verified", verification_source="same-admin-client fresh readback after call/error")
            except Exception as read_error:
                receipt["after_read_error"] = str(read_error)
    finally:
        if native_settings_client is not None:
            receipt.update(native_settings_client.settings_readback())
            if native_settings_client.after_settings is not None:
                record_readback(native_settings_client.after_settings["ExclusionPath"])
        _write_receipt(receipt_path, receipt)
    return receipt




class ProjectExeBuildHookResult(TypedDict):
    status: Literal["disabled", "verified", "settings_failed", "not_applicable"]
    reason: NotRequired[str]
    manifest: NotRequired[str]
    receipt: NotRequired[str]
    receipt_sha256: NotRequired[str]
    error: NotRequired[str | None]

class NoProjectExecutableReceipt(TypedDict):
    schema: str
    machine_id: str
    observed_at_utc: str
    status: Literal["not_applicable"]
    reason: str
    source_dir: str
    build_dir: str
    requested_targets: list[str]
    broker_called: Literal[False]
    wmi_called: Literal[False]
    settings_success_is_runtime_trust: Literal[False]

class FailedBuildExclusionReceipt(TypedDict):
    schema: str
    status: Literal["settings_failed"]
    error: str
    error_type: str
    method: str
    before: None
    after: None
    calls: list[Never]
    files: list[Never]
    source_dir: str
    build_dir: str
    settings_success_is_runtime_trust: Literal[False]

def _no_project_executable_result(
    source: Path, build: Path, targets: Sequence[str], manifest_path: Path,
    receipt_path: Path,
) -> ProjectExeBuildHookResult:
    receipt: NoProjectExecutableReceipt = {
        "schema": SCHEMA, "status": "not_applicable",
        "machine_id": current_machine_id(),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "reason": "Validated requested CMake target closure contains no project executable outputs",
        "source_dir": str(source), "build_dir": str(build),
        "requested_targets": list(targets), "broker_called": False,
        "wmi_called": False, "settings_success_is_runtime_trust": False,
    }
    _write_receipt(receipt_path, receipt)
    return {
        "status": "not_applicable", "manifest": str(manifest_path),
        "receipt": str(receipt_path),
        "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "error": None,
    }

def _build_hook_status(value: object) -> Literal["disabled", "verified", "settings_failed"]:
    if value == "disabled":
        return "disabled"
    if value == "verified":
        return "verified"
    if value == "settings_failed":
        return "settings_failed"
    raise ValueError("Project EXE registration returned an invalid terminal status")

def after_successful_build(repo: Path, source: Path, build: Path, configuration: str,
                           targets: list[str], external_candidate: str | None = None) -> ProjectExeBuildHookResult:
    if not opted_in(repo):
        return {"status": "disabled", "reason": "Local Git opt-in absent/false or CI environment"}
    attempt = build / "defender-exe-exclusions" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    attempt.mkdir(parents=True, exist_ok=False)
    try:
        manifest = collect_manifest(repo, source, build, configuration, targets, external_candidate)
    except Exception as error:
        failed: FailedBuildExclusionReceipt = {"schema": SCHEMA, "status": "settings_failed", "error": str(error),
                  "error_type": type(error).__name__, "method": "not-called; invalid CMake provenance",
                  "before": None, "after": None, "calls": [], "files": [],
                  "source_dir": str(source), "build_dir": str(build),
                  "settings_success_is_runtime_trust": False}
        _write_receipt(attempt / "receipt.json", failed)
        return {"status": "settings_failed", "receipt": str(attempt / "receipt.json"),
                "receipt_sha256": hashlib.sha256((attempt / "receipt.json").read_bytes()).hexdigest(),
                "error": str(error)}
    manifest_path = attempt / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if manifest["files"] == []:
        return _no_project_executable_result(
            source, build, targets, manifest_path, attempt / "receipt.json")
    result = register_manifest(manifest, attempt / "receipt.json", manifest_bytes=manifest_path.read_bytes())
    result_error: object = result.get("error")
    if result_error is not None and not isinstance(result_error, str):
        raise ValueError("Project EXE registration returned an invalid error value")
    return {"status": _build_hook_status(result["status"]), "manifest": str(manifest_path), "receipt": str(attempt / "receipt.json"),
            "receipt_sha256": hashlib.sha256((attempt / "receipt.json").read_bytes()).hexdigest(),
            "error": result_error}


DECLARED_SCHEMA = "xar.project-exe-declared-path-exclusions/v1"
DECLARED_INJECTOR = "xar_ck3_bridge_injector"


class DeclaredFileRef(TypedDict):
    path: str
    bytes: int
    sha256: str


class DeclaredOutput(TypedDict):
    path: str
    target: str
    target_id: str
    expected_state: Literal["ABSENT"]


class DeclaredManifest(TypedDict):
    schema: Literal["xar.project-exe-declared-path-exclusions/v1"]
    machine_id: str
    repo: str
    source_dir: str
    build_dir: str
    configuration: Literal["Release"]
    requested_targets: list[str]
    external_candidate: str
    source_declaration_ref: DeclaredFileRef
    complete_source_refs: list[DeclaredFileRef]
    cmake_index: dict[str, str]
    cmake_codemodel: dict[str, str]
    target_provenance: list[dict[str, str]]
    configured_graph_refs: list[DeclaredFileRef]
    declared_outputs: list[DeclaredOutput]


def _declared_object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Declared JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Declared JSON string keys required")
        result[key] = item
    return result


def _declared_text(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("Declared nonempty string required")
    return value


def _declared_refs(value: object) -> list[DeclaredFileRef]:
    if not isinstance(value, list) or not 1 <= len(value) <= 65536:
        raise ValueError("Bounded nonempty declared references required")
    result: list[DeclaredFileRef] = []
    seen: set[str] = set()
    for item in value:
        row = _declared_object(item)
        size = row.get("bytes")
        digest = _declared_text(row.get("sha256"))
        path = _declared_text(row.get("path"))
        if set(row) != {"path", "bytes", "sha256"} or type(size) is not int or size < 0 or \
                len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest) or ntpath.normcase(path) in seen:
            raise ValueError("Exact typed unique declared reference required")
        seen.add(ntpath.normcase(path))
        result.append({"path": path, "bytes": size, "sha256": digest})
    return result


def _declared_plain(path: Path, *, directory: bool) -> None:
    if not path.is_absolute() or path != path.resolve(strict=True) or any(c in str(path) for c in "*?%"):
        raise ValueError("Canonical plain declared path required")
    for parent in [path, *path.parents]:
        info = parent.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("Reparse/symlink declaration is forbidden")
    info = path.lstat()
    if directory != stat.S_ISDIR(info.st_mode) or (not directory and not stat.S_ISREG(info.st_mode)):
        raise ValueError("Ordinary declaration file/directory required")


def _declared_verify_ref(ref: DeclaredFileRef) -> None:
    path = Path(ref["path"]); _declared_plain(path, directory=False)
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    if path.stat().st_size != ref["bytes"] or digest != ref["sha256"]:
        raise ValueError("Declared input bytes/hash changed")


def _declared_absent(path: Path) -> None:
    _declared_plain(path.parent, directory=True)
    if path.name != DECLARED_INJECTOR + ".exe" or any(c in str(path) for c in "*?%"):
        raise ValueError("Only the exact declared injector path is permitted")
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError("Declared output must be absent, not present or unknown")


def validate_declared_manifest(value: object) -> DeclaredManifest:
    row = _declared_object(value)
    required = {"schema", "machine_id", "repo", "source_dir", "build_dir", "configuration", "requested_targets",
                "external_candidate", "source_declaration_ref", "complete_source_refs", "cmake_index",
                "cmake_codemodel", "target_provenance", "configured_graph_refs", "declared_outputs"}
    if set(row) != required or row["schema"] != DECLARED_SCHEMA or row["machine_id"] != current_machine_id() or \
            row["configuration"] != "Release" or row["requested_targets"] != [DECLARED_INJECTOR]:
        raise ValueError("Exact current declared manifest schema/machine/target required")
    repo, source, build = (Path(_declared_text(row[name])) for name in ("repo", "source_dir", "build_dir"))
    for path in (repo, source, build):
        _declared_plain(path, directory=True)
    if source.is_relative_to(build) or build.is_relative_to(source):
        raise ValueError("Declared source/build must be disjoint")
    refs = _declared_refs(row["complete_source_refs"]); graph = _declared_refs(row["configured_graph_refs"])
    declaration_refs = _declared_refs([row["source_declaration_ref"]]); declaration_ref = declaration_refs[0]
    for ref in [*refs, *graph, declaration_ref]:
        _declared_verify_ref(ref)
    expected_sources = {ntpath.normcase(str(Path(ref["path"]))) for ref in refs}
    actual_sources: set[str] = set()
    for directory, dirs, files in os.walk(source, followlinks=False):
        for name in dirs:
            _declared_plain(Path(directory) / name, directory=True)
        for name in files:
            actual_sources.add(ntpath.normcase(str(Path(directory) / name)))
            if len(actual_sources) > 65536:
                raise ValueError("Bounded declared source inventory required")
    if actual_sources != expected_sources:
        raise ValueError("Complete declared source inventory changed")
    declaration = _declared_object(_json(Path(declaration_ref["path"])))
    if declaration.get("schema") != "xar.native-declared-output-source/v1" or declaration.get("machine_id") != row["machine_id"] or \
            declaration.get("configured_graph_refs") != graph:
        raise ValueError("Java declared source witness differs")
    request_ref = _declared_refs([declaration.get("declaration_request_ref")])[0]
    configure_ref = _declared_refs([declaration.get("configure_actual_ref")])[0]
    _declared_verify_ref(request_ref); _declared_verify_ref(configure_ref)
    _declared_verify_ref(_declared_refs([declaration.get("producer_tools_build_ref")])[0])
    request = _declared_object(_json(Path(request_ref["path"])))
    if request.get("stage") != "ENV" or request.get("source_root") != str(source) or request.get("build_root") != str(build) or \
            request.get("machine_id") != row["machine_id"] or request.get("complete_sources") != refs or \
            request.get("qualified_tools_build") != declaration.get("producer_tools_build_ref"):
        raise ValueError("Java reviewed declaration request/source identity differs")
    external = _declared_text(row["external_candidate"])
    observed = collect_manifest(repo, source, build, "Release", [DECLARED_INJECTOR], external)
    for key in ("repo", "source_dir", "build_dir", "configuration", "requested_targets", "external_candidate",
                "cmake_index", "cmake_codemodel", "target_provenance"):
        if observed.get(key) != row[key]:
            raise ValueError("Current CMake declaration provenance changed")
    if observed.get("files") != []:
        raise ValueError("Missing-output declaration cannot contain a current built EXE")
    provenance = row["target_provenance"]
    if not isinstance(provenance, list) or len(provenance) != 1:
        raise ValueError("One source-defined project injector required")
    target_pin = _declared_object(provenance[0])
    target = _declared_object(_json(Path(_declared_text(target_pin.get("path")))))
    artifacts = target.get("artifacts")
    if target.get("type") != "EXECUTABLE" or target.get("imported", False) or target.get("isGeneratorProvided", False) or \
            target.get("name") != DECLARED_INJECTOR or not isinstance(artifacts, list) or len(artifacts) != 1:
        raise ValueError("One nonimported project EXECUTABLE artifact required")
    artifact = _declared_object(artifacts[0])
    output_path = build / _declared_text(artifact.get("path"))
    expected_path = build / (DECLARED_INJECTOR + ".exe")
    if output_path != expected_path:
        raise ValueError("Exact declared output outside original build path")
    output_value = row["declared_outputs"]
    if not isinstance(output_value, list) or len(output_value) != 1:
        raise ValueError("One declared output row required")
    output_row = _declared_object(output_value[0])
    output: DeclaredOutput = {"path": str(expected_path), "target": DECLARED_INJECTOR,
                              "target_id": _declared_text(target.get("id")), "expected_state": "ABSENT"}
    if output_row != output:
        raise ValueError("Absent declaration path/target/state changed or fingerprint was invented")
    _declared_absent(expected_path)
    # Returning the validated original keeps the Java/Python JSON domain unchanged.
    return {"schema": "xar.project-exe-declared-path-exclusions/v1", "machine_id": _declared_text(row["machine_id"]),
            "repo": str(repo), "source_dir": str(source), "build_dir": str(build), "configuration": "Release",
            "requested_targets": [DECLARED_INJECTOR], "external_candidate": external,
            "source_declaration_ref": declaration_ref, "complete_source_refs": refs,
            "cmake_index": {k: _declared_text(v) for k, v in _declared_object(row["cmake_index"]).items()},
            "cmake_codemodel": {k: _declared_text(v) for k, v in _declared_object(row["cmake_codemodel"]).items()},
            "target_provenance": [{k: _declared_text(v) for k, v in target_pin.items()}],
            "configured_graph_refs": graph, "declared_outputs": [output]}


class DeclaredCall(TypedDict):
    path: str
    method: Literal["Add", "already-present"]
    return_value: int | None
    fresh_readback: NotRequired[list[str]]
    call_error: NotRequired[str]
    return_decode_error: NotRequired[str]


class DeclaredReceiptFields(TypedDict):
    schema: Literal["xar.project-exe-declared-path-exclusions/v1"]
    status: Literal["running", "disabled", "settings_failed", "verified"]
    method: str
    namespace: str
    proof_scope: Literal["DECLARED_PROJECT_EXE_PATH_ONLY"]
    settings_success_is_runtime_trust: Literal[False]
    admin_token: bool
    before: list[str] | None
    after: list[str] | None
    calls: list[DeclaredCall]
    declared_outputs: list[DeclaredOutput]
    manifest_sha256: str
    readback_visibility: str
    verified_requested_paths: list[str]
    missing_requested_paths: list[str]
    observed_prior_settings_preserved: bool
    partial_mutation: bool
    error: NotRequired[str]
    error_type: NotRequired[str]
    admin_required_for_verified_readback: NotRequired[bool]



class DeclaredReceiptV1(DeclaredReceiptFields, DirectSettingsReadbackV1):
    pass


class DeclaredReceiptV2(DeclaredReceiptFields, DirectSettingsReadbackV2):
    pass


DeclaredReceipt = DeclaredReceiptV1 | DeclaredReceiptV2


def _declared_with_readback(receipt: DeclaredReceipt, evidence: DirectSettingsReadback) -> DeclaredReceipt:
    common: DeclaredReceiptFields = {
        "schema": receipt["schema"], "status": receipt["status"], "method": receipt["method"],
        "namespace": receipt["namespace"], "proof_scope": receipt["proof_scope"],
        "settings_success_is_runtime_trust": receipt["settings_success_is_runtime_trust"],
        "admin_token": receipt["admin_token"], "before": receipt["before"], "after": receipt["after"],
        "calls": receipt["calls"], "declared_outputs": receipt["declared_outputs"],
        "manifest_sha256": receipt["manifest_sha256"], "readback_visibility": receipt["readback_visibility"],
        "verified_requested_paths": receipt["verified_requested_paths"],
        "missing_requested_paths": receipt["missing_requested_paths"],
        "observed_prior_settings_preserved": receipt["observed_prior_settings_preserved"],
        "partial_mutation": receipt["partial_mutation"]}
    if "error" in receipt:
        common["error"] = receipt["error"]
    if "error_type" in receipt:
        common["error_type"] = receipt["error_type"]
    if "admin_required_for_verified_readback" in receipt:
        common["admin_required_for_verified_readback"] = receipt["admin_required_for_verified_readback"]
    if evidence["settings_readback_schema"] == "xar.project-exe-three-settings-readback/v2":
        result_v2: DeclaredReceiptV2 = {**common, **evidence}
        return result_v2
    if evidence["settings_readback_schema"] == "xar.project-exe-three-settings-readback/v1":
        result_v1: DeclaredReceiptV1 = {**common, **evidence}
        return result_v1
    raise ValueError("Unknown direct settings readback schema")


def _declared_readback(receipt: DeclaredReceipt, client: DefenderWmi, path: str) -> tuple[DeclaredReceipt, bool]:
    after = client.read_paths(); receipt["after"] = after
    evidence = client.settings_readback()
    receipt = _declared_with_readback(receipt, evidence)
    before = receipt["before"]
    if before is None:
        return receipt, False
    prior = {ntpath.normcase(p) for p in before}; current = {ntpath.normcase(p) for p in after}
    present = ntpath.normcase(path) in current
    receipt["verified_requested_paths"] = [path] if present else []
    receipt["missing_requested_paths"] = [] if present else [path]
    receipt["observed_prior_settings_preserved"] = prior <= current
    receipt["partial_mutation"] = present and not prior <= current
    verified = present and prior <= current and receipt["settings_readback_complete"] and \
        receipt["observed_extensions_unchanged"] and receipt["observed_processes_unchanged"]
    return receipt, verified


def register_declared_path_manifest(value: object, receipt_path: Path, *, admin: bool | None = None) -> DeclaredReceipt:
    if receipt_path.exists():
        raise FileExistsError("Declared receipt exists; no replay or WMI action permitted")
    receipt: DeclaredReceipt = {
        "schema": "xar.project-exe-declared-path-exclusions/v1", "status": "running",
        "method": "WMI MSFT_MpPreference.Add ExclusionPath only", "namespace": NAMESPACE,
        "proof_scope": "DECLARED_PROJECT_EXE_PATH_ONLY", "settings_success_is_runtime_trust": False,
        "admin_token": False, "before": None, "after": None, "calls": [], "declared_outputs": [], "manifest_sha256": "",
        "readback_visibility": "unverified; administrative token required", "verified_requested_paths": [],
        "missing_requested_paths": [], "observed_prior_settings_preserved": False, "partial_mutation": False,
        "settings_readback_schema": "xar.project-exe-three-settings-readback/v1", "before_settings": None,
        "after_settings": None, "observed_extensions_unchanged": False, "observed_processes_unchanged": False,
        "settings_readback_complete": False, "settings_readback_error": None,
        "settings_readback_process_id": os.getpid(), "settings_readback_token_user_sid": ""}
    client: DefenderWmi | None = None
    manifest: DeclaredManifest | None = None
    path: str | None = None
    try:
        manifest = validate_declared_manifest(value)
        receipt["declared_outputs"] = manifest["declared_outputs"]
        receipt["manifest_sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        if not opted_in(Path(manifest["repo"])):
            receipt["status"] = "disabled"
            return receipt
        if admin is None:
            admin = os.name == "nt" and bool(ctypes.windll.shell32.IsUserAnAdmin())
        receipt["admin_token"] = admin
        if not admin:
            receipt["admin_required_for_verified_readback"] = True
            raise PermissionError("admin_required_for_verified_readback; no Add or broker attempted")
        client = DefenderWmi()
        receipt["readback_visibility"] = "same administrative token and WMI client for before/after"
        before = client.read_paths(); receipt["before"] = before
        path = manifest["declared_outputs"][0]["path"]
        if validate_declared_manifest(value) != manifest:
            raise ValueError("Declared source/graph changed before Add")
        if ntpath.normcase(path) in {ntpath.normcase(p) for p in before}:
            receipt["calls"].append({"path": path, "method": "already-present", "return_value": None})
        else:
            call: DeclaredCall = {"path": path, "method": "Add", "return_value": None}
            receipt["calls"].append(call)
            response = client.add_path(path)
            if isinstance(response, dict):
                code = response.get("return_value")
                if "return_decode_error" in response:
                    call["return_decode_error"] = _declared_text(response["return_decode_error"])
            else:
                code = response
            if code is not None and type(code) is not int:
                raise ValueError("Exact WMI integer or unavailable ReturnValue required")
            call["return_value"] = code
            receipt, verified = _declared_readback(receipt, client, path)
            fresh = receipt["after"]
            if fresh is None:
                raise RuntimeError("Declared Add lacks an actual fresh path readback")
            call["fresh_readback"] = list(fresh)
            if code not in (0, None) or not verified:
                raise RuntimeError("Fresh same-admin readback after the single Add did not verify all three settings")
        receipt, verified = _declared_readback(receipt, client, path)
        if not verified:
            raise RuntimeError("Final same-admin three-setting readback failed")
        _declared_absent(Path(path))
        if validate_declared_manifest(value) != manifest:
            raise ValueError("Declared source/graph changed during settings operation")
        receipt["status"] = "verified"
    except Exception as error:
        receipt["status"] = "settings_failed"; receipt["error"] = str(error); receipt["error_type"] = type(error).__name__
        if client is not None:
            receipt = _declared_with_readback(receipt, client.settings_readback())
        if client is not None and path is not None and receipt["before"] is not None:
            try:
                # Never repeat Add after a nullable decoder or provider exception.
                receipt, verified = _declared_readback(receipt, client, path)
                if verified and manifest is not None and validate_declared_manifest(value) == manifest:
                    receipt["status"] = "verified"
            except Exception as read_error:
                receipt["settings_readback_error"] = str(read_error); receipt["settings_readback_complete"] = False
    finally:
        _write_receipt(receipt_path, dict(receipt))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Frozen exact CMake-target or successful MSVC-command manifest; never scan an EXE directory")
    parser.add_argument("--receipt", type=Path, required=True, help="New append-only output file")
    args = parser.parse_args()
    manifest_value = _json(args.manifest)
    if manifest_value.get("schema") == DECLARED_SCHEMA:
        declared_result = register_declared_path_manifest(manifest_value, args.receipt)
        print(json.dumps(declared_result, ensure_ascii=False, indent=2))
        return 0 if declared_result["status"] == "verified" else 1
    result = register_manifest(manifest_value, args.receipt, manifest_bytes=args.manifest.read_bytes())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in ("disabled", "verified") else 1


if __name__ == "__main__":
    raise SystemExit(main())
