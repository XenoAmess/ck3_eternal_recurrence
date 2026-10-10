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
from pathlib import Path
import subprocess
import uuid

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


class DefenderWmi:
    def __init__(self) -> None:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        self.services = win32com.client.GetObject(
            "winmgmts:{impersonationLevel=impersonate}!\\\\.\\" + NAMESPACE)

    def read_paths(self) -> list[str]:
        rows = list(self.services.ExecQuery("SELECT ExclusionPath FROM MSFT_MpPreference"))
        if len(rows) != 1:
            raise RuntimeError("Defender preference read did not return exactly one object")
        value = rows[0].Properties_.Item("ExclusionPath").Value
        return list(value or ())

    def add_path(self, path: str) -> int | None | dict:
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


def _write_receipt(path: Path, receipt: dict) -> None:
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
        return requested <= observed and prior <= observed
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
        _write_receipt(receipt_path, receipt)
    return receipt


def after_successful_build(repo: Path, source: Path, build: Path, configuration: str,
                           targets: list[str], external_candidate: str | None = None) -> dict:
    if not opted_in(repo):
        return {"status": "disabled", "reason": "Local Git opt-in absent/false or CI environment"}
    attempt = build / "defender-exe-exclusions" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    attempt.mkdir(parents=True, exist_ok=False)
    try:
        manifest = collect_manifest(repo, source, build, configuration, targets, external_candidate)
    except Exception as error:
        failed = {"schema": SCHEMA, "status": "settings_failed", "error": str(error),
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
    result = register_manifest(manifest, attempt / "receipt.json", manifest_bytes=manifest_path.read_bytes())
    return {"status": result["status"], "manifest": str(manifest_path), "receipt": str(attempt / "receipt.json"),
            "receipt_sha256": hashlib.sha256((attempt / "receipt.json").read_bytes()).hexdigest(),
            "error": result.get("error")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="Frozen exact CMake-target or successful MSVC-command manifest; never scan an EXE directory")
    parser.add_argument("--receipt", type=Path, required=True, help="New append-only output file")
    args = parser.parse_args()
    result = register_manifest(_json(args.manifest), args.receipt, manifest_bytes=args.manifest.read_bytes())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in ("disabled", "verified") else 1


if __name__ == "__main__":
    raise SystemExit(main())
