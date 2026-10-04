"""Read-only CK3 preflight and Li Yu Dao L0 checks; never run live acceptance.

Exit 0: requested checks passed (L0 only, or preflight READY).
Exit 1: L0 code/check failure. Exit 2: live environment unavailable with no L0
failure. Exit 3: runner configuration/infrastructure failure. Reports always
separate these layers and keep live NOT_RUN. No game, Steam or MCP server is
started; supplied MCP evidence is inspected, not re-probed.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib
import uuid

SOURCE = Path(__file__).resolve().parents[1]
ROOT = SOURCE.parent
EXACT_VERSION = "1.20.0.3"
EXACT_EXE_SHA256 = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"
DEFAULT_GAME_DIR = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
NATIVE_ENTRY = ROOT / "tools/ck3_native_profile_mcp.py"
REQUIRED_BRIDGE_TOOLS = (
    "ck3_query_native_profile_v1",
    "ck3_take_profile_native_snapshot_v1",
    "ck3_query_profile_pending_interaction_v1",
    "ck3_reply_profile_pending_interaction_v1",
    "ck3_select_profile_event_option_v1",
    "ck3_save_profile_checkpoint_v1",
)
UNKNOWN_PRODUCT_CAPABILITIES = (
    "native faith/rite membership and leadership inspection on CK3 1.20.0.3",
    "native decision/interaction initiation for the active player",
    "union/schism consent, refusal and AI inactivity observation",
    "save reload followed by independent faith/rite state inspection",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def source_inputs(source: Path) -> list[dict]:
    return [{"path": path.relative_to(source).as_posix(), "sha256": digest(path), "size": path.stat().st_size}
            for path in sorted(source.rglob("*"))
            if path.is_file() and path.suffix in {".py", ".txt", ".yml", ".mod", ".json", ".in"} and "__pycache__" not in path.parts]


def capture_command(argv: list[str], output: Path, name: str, *, cwd: Path = ROOT, timeout: float = 60) -> dict:
    """Save exact output bytes, including failed or timed-out commands."""
    record = {"argv": argv, "cwd": str(cwd), "started_at": utc_now(), "timeout_seconds": timeout}
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout, check=False)
        stdout, stderr, rc = result.stdout, result.stderr, result.returncode
        record["execution"] = "COMPLETED"
    except subprocess.TimeoutExpired as error:
        stdout, stderr, rc = error.stdout or b"", error.stderr or b"", None
        record["execution"] = "TIMEOUT"
    except OSError as error:
        stdout, stderr, rc = b"", str(error).encode("utf-8"), None
        record["execution"] = "UNAVAILABLE"
    record.update(returncode=rc, finished_at=utc_now())
    for kind, data in (("stdout", stdout), ("stderr", stderr)):
        path = output / f"{name}.{kind}.txt"
        path.write_bytes(data)
        record[kind] = {"path": path.name, "size": len(data), "sha256": digest(path)}
    write_json(output / f"{name}.command.json", record)
    return record


def resolve_game_paths(game_dir: Path | None, game_exe: Path | None, environ: dict[str, str]) -> tuple[Path, Path]:
    selected_dir = game_dir or (Path(environ["XAR_CK3_GAME_DIR"]) if environ.get("XAR_CK3_GAME_DIR") else None)
    selected_exe = game_exe or (Path(environ["XAR_CK3_EXE"]) if environ.get("XAR_CK3_EXE") else None)
    if selected_dir is None:
        selected_dir = selected_exe.parent.parent / "game" if selected_exe else DEFAULT_GAME_DIR
    selected_dir = selected_dir.resolve()
    if selected_dir.name.lower() != "game" and (selected_dir / "game").is_dir():
        selected_dir = selected_dir / "game"
    return selected_dir, (selected_exe or selected_dir.parent / "binaries/ck3.exe").resolve()


def inspect_game(game_dir: Path, game_exe: Path, output: Path, *, expected_sha: str = EXACT_EXE_SHA256) -> dict:
    settings = game_dir.parent / "launcher/launcher-settings.json"
    result = {"game_dir": str(game_dir), "game_exe": str(game_exe), "launcher_settings": str(settings),
              "expected_version": EXACT_VERSION, "expected_exe_sha256": expected_sha, "issues": []}
    if not game_dir.is_dir():
        result["issues"].append("game-directory-missing")
    try:
        data = settings.read_bytes()
        (output / "launcher-settings.snapshot.json").write_bytes(data)
        payload = json.loads(data.decode("utf-8-sig"))
        result.update(launcher_settings_sha256=digest(settings), version=payload.get("rawVersion"),
                      display_version=payload.get("version"))
        if payload.get("rawVersion") != EXACT_VERSION:
            result["issues"].append("launcher-version-is-not-exact-1.20.0.3")
        declared_exe = payload.get("exePath")
        if not isinstance(declared_exe, str):
            result["issues"].append("launcher-executable-path-missing")
        elif (settings.parent / declared_exe).resolve() != game_exe:
            result["issues"].append("launcher-and-selected-executable-disagree")
    except (OSError, ValueError) as error:
        result["issues"].append(f"launcher-settings-unavailable: {error}")
    try:
        result["exe_sha256"] = digest(game_exe)
        result["exe_size"] = game_exe.stat().st_size
        if result["exe_sha256"] != expected_sha:
            result["issues"].append("executable-is-not-the-frozen-1.20-build")
    except OSError as error:
        result["issues"].append(f"game-executable-unavailable: {error}")
    result["status"] = "EXACT_BUILD" if not result["issues"] else "ENVIRONMENT_RED"
    return result


def inspect_processes(output: Path, command_runner=capture_command) -> dict:
    if os.name != "nt":
        return {"status": "UNKNOWN", "pids": [], "reason": "Windows tasklist is unavailable on this platform"}
    record = command_runner(["tasklist", "/FO", "CSV", "/NH"], output, "processes")
    if record["returncode"] != 0:
        return {"status": "UNKNOWN", "pids": [], "command": record, "reason": "process inventory failed"}
    text = (output / record["stdout"]["path"]).read_bytes().decode("utf-8", errors="replace")
    pids = []
    for row in csv.reader(io.StringIO(text)):
        if len(row) >= 2 and row[0].lower() == "ck3.exe" and row[1].isdigit():
            pids.append(int(row[1]))
    return {"status": "RUNNING" if pids else "NOT_RUNNING", "pids": pids, "command": record,
            "executable_identity": "NOT_PROVEN_BY_TASKLIST"}


def inspect_mcp(evidence: Path | None, output: Path, *, config: Path | None = None) -> dict:
    """Inspect an external tools/list response bound to the current build.

    Evidence JSON: endpoint, observed_at, game_version, ck3_exe_sha256,
    tools_response_path, tools_response_sha256. The response must contain
    tools (or result.tools). Paths resolve against the evidence file. This
    records supplied provenance; it does not establish endpoint freshness.
    """
    config = config or Path.home() / ".codex/config.toml"
    result = {"status": "NOT_PROVEN", "config_path": str(config), "configured_servers": [],
              "reprobed": False, "issues": [], "required_bridge_tools": list(REQUIRED_BRIDGE_TOOLS),
              "unknown_product_capabilities": list(UNKNOWN_PRODUCT_CAPABILITIES)}
    if config.is_file():
        result["config_sha256"] = digest(config)
        try:
            configured = tomllib.loads(config.read_text(encoding="utf-8-sig")).get("mcp_servers", {})
            for name, server in configured.items():
                searchable = " ".join([name, str(server.get("command", "")), *map(str, server.get("args", []))]).lower()
                if any(word in searchable for word in ("ck3", "kaishek", "operator")):
                    result["configured_servers"].append({"name": name, "transport": "http" if "url" in server else "stdio"})
        except (OSError, ValueError, AttributeError, TypeError) as error:
            result["config_error"] = str(error)
    if evidence is None:
        result["issues"].append("no-current-build-MCP-tools-response-evidence")
        return result
    try:
        data = evidence.read_bytes()
        (output / "mcp-evidence.snapshot.json").write_bytes(data)
        payload = json.loads(data.decode("utf-8-sig"))
        result.update(evidence_path=str(evidence.resolve()), evidence_sha256=digest(evidence),
                      endpoint=payload.get("endpoint"), observed_at=payload.get("observed_at"))
        if payload.get("game_version") != EXACT_VERSION or payload.get("ck3_exe_sha256") != EXACT_EXE_SHA256:
            result["issues"].append("MCP-evidence-does-not-identify-the-exact-1.20-build")
        if not isinstance(payload.get("endpoint"), str) or not payload.get("endpoint"):
            result["issues"].append("MCP-endpoint-not-identified")
        observed = datetime.fromisoformat(str(payload.get("observed_at", "")).replace("Z", "+00:00"))
        if observed.utcoffset() is None:
            raise ValueError("MCP observation must include a timezone")
        receipt = evidence.parent / payload["tools_response_path"]
        if digest(receipt) != payload["tools_response_sha256"]:
            raise ValueError("tools/list response SHA-256 mismatch")
        receipt_data = receipt.read_bytes()
        (output / "mcp-tools-response.snapshot.json").write_bytes(receipt_data)
        response = json.loads(receipt_data.decode("utf-8-sig"))
        rows = response.get("tools", response.get("result", {}).get("tools", []))
        names = sorted({row["name"] for row in rows if isinstance(row, dict) and isinstance(row.get("name"), str)})
        result["tool_names"] = names
        result["missing_bridge_tools"] = sorted(set(REQUIRED_BRIDGE_TOOLS) - set(names))
        if result["missing_bridge_tools"]:
            result["issues"].append("required-existing-native-bridge-tools-missing")
        result["status"] = "SUPPLIED_EVIDENCE_VALIDATED" if not result["issues"] else "NOT_PROVEN"
        result["freshness"] = "NOT_REPROBED; supplied observation only"
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        result["issues"].append(f"MCP-evidence-invalid: {error}")
    return result


def kaishek_preflight(game: dict, output: Path, profile: str | None, fixture: str | None) -> dict:
    adapter = ROOT / "tools/kaishek_preflight.py"
    if not profile or not fixture:
        return {"status": "NOT_APPLICABLE", "reason": "no Li Yu Dao CK3 1.20 profile and fixture declared",
                "adapter": str(adapter), "old_1_19_defaults_used": False}
    if "1.19" in profile or "1.19" in fixture:
        return {"status": "NOT_APPLICABLE", "reason": "historical 1.19 profile cannot establish this 1.20 preflight"}
    if game["status"] != "EXACT_BUILD":
        return {"status": "NOT_APPLICABLE", "reason": "exact CK3 1.20 game identity unavailable"}
    if not adapter.is_file():
        return {"status": "NOT_APPLICABLE", "reason": "repository kaishek adapter is missing"}
    try:
        spec = importlib.util.spec_from_file_location("lyd_kaishek_preflight", adapter)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.run_preflight(root=game["game_dir"], profile=profile, fixture=fixture,
                                    artifact_path=output / "kaishek-preflight.json", required=False,
                                    timeout_seconds=60, ck3_build=EXACT_VERSION,
                                    ck3_exe_sha256=game["exe_sha256"], require_origin_sync=False)
    except (OSError, ValueError, ImportError) as error:
        return {"status": "UNAVAILABLE", "reason": str(error)}


def l0_commands(source: Path, output: Path, command_runner=capture_command) -> list[dict]:
    tools = SOURCE / "tools"
    commands = [
        ("tool-tests", [sys.executable, str(tools / "test_build_release.py")]),
        ("runner-tests", [sys.executable, str(tools / "test_run_acceptance.py")]),
        ("school-consent-tests", [sys.executable, str(tools / "test_school_consent.py")]),
        ("content-generated-check", [sys.executable, str(tools / "gen_content.py"), "--output", str(source), "--check"]),
        ("runtime-generated-check", [sys.executable, str(tools / "gen_runtime.py"), "--output-dir", str(source), "--check"]),
        ("static", [sys.executable, str(tools / "validate_static.py"), "--source", str(source), "--report", str(output / "static-report.json")]),
        ("build-check", [sys.executable, str(tools / "build_release.py"), "--source", str(source), "--check"]),
    ]
    return [{"name": name, **command_runner(argv, output, name)} for name, argv in commands]


def decide_result(l0: dict, environment: dict) -> tuple[str, int]:
    if l0["status"] == "RED":
        return "L0_RED", 1
    if environment["status"] == "ENVIRONMENT_RED":
        return "ENVIRONMENT_RED", 2
    return ("L0_GREEN" if l0["status"] == "GREEN" else "PREFLIGHT_READY"), 0


def run(args: argparse.Namespace, *, command_runner=capture_command) -> dict:
    output = args.output.resolve()
    if output.exists():
        raise ValueError(f"report directory already exists; choose a fresh attempt: {output}")
    if output == args.source.resolve() or args.source.resolve() in output.parents:
        raise ValueError("report output must be outside the mod source")
    output.mkdir(parents=True)
    report = {"schema_version": 1, "product_id": "mod_li_yu_dao", "started_at": utc_now(),
              "report_directory": str(output), "python": {"executable": sys.executable, "version": sys.version},
              "mode": "preflight-only" if args.preflight_only else "preflight-and-L0",
               "product_scope": {"iteration": 2,
                                 "implemented_declared": "player entry, school selection, cultivation and repeated council-authorized affiliation proposals",
                                 "leadership": "DETACH_FACTORY_ONLY; challenger and teacher lifecycle pending iteration 3",
                                 "reunion_and_schism": "IMPLEMENTED; this runner provides no live-flow acceptance",
                                 "external_native_probe": "R0002 permanent primitive proof bound by portable receipt; distinct from formal-flow acceptance",
                                "live_language": "simp_chinese", "english": "L0 structure only"},
              "live": {"status": "NOT_RUN", "reason": "this runner performs read-only preflight and L0 only"},
              "side_effects": {"ck3_started": False, "steam_changed": False, "packages_installed": False, "mcp_server_started": False}}
    try:
        before = source_inputs(args.source.resolve())
        write_json(output / "source-inputs.before.json", {"files": before})
        game_dir, game_exe = resolve_game_paths(args.game_dir, args.game_exe, dict(os.environ))
        game = inspect_game(game_dir, game_exe, output)
        processes = inspect_processes(output, command_runner)
        mcp = inspect_mcp(args.mcp_evidence, output)
        kaishek = kaishek_preflight(game, output, args.kaishek_profile, args.kaishek_fixture)
        gaps = list(game["issues"])
        if processes["status"] != "RUNNING":
            gaps.append("no-observed-CK3-session" if processes["status"] == "NOT_RUNNING" else "CK3-process-state-unknown")
        gaps.extend(mcp["issues"])
        environment = {"status": "ENVIRONMENT_RED" if gaps else "READY_FOR_LIVE_PREFLIGHT",
                       "game": game, "processes": processes, "mcp": mcp, "kaishek": kaishek, "gaps": gaps,
                       "native_product_capabilities": "NOT_PROVEN",
                       "next_steps": [f"existing stdio entry: {sys.executable} {NATIVE_ENTRY} --profile <frozen-1.20-profile.json>",
                                      "provide actual tools/list response evidence for the exact current build",
                                      *UNKNOWN_PRODUCT_CAPABILITIES],
                       "boundary": "process presence, bridge tool listing and static corpus checks do not prove product live acceptance"}
        commands = [] if args.preflight_only else l0_commands(args.source.resolve(), output, command_runner)
        after = source_inputs(args.source.resolve())
        write_json(output / "source-inputs.after.json", {"files": after})
        stable = before == after
        l0 = {"status": "NOT_RUN" if args.preflight_only else ("GREEN" if all(row["returncode"] == 0 for row in commands) else "RED"),
              "commands": commands, "source_inputs_stable": stable,
               "tool_contracts": "NOT_RUN" if args.preflight_only else ("GREEN" if all(row["returncode"] == 0 for row in commands[:3]) else "RED"),
               "product_source": "NOT_RUN" if args.preflight_only else ("GREEN" if stable and all(row["returncode"] == 0 for row in commands[3:]) else "RED"),
              "proves": "generated bytes, structural parser, localization, player gates, references and reproducible runtime packaging only"}
        if not args.preflight_only and not stable:
            l0.update(status="RED", issue="source inputs changed during checks; this attempt does not bind one product revision")
        result, exit_code = decide_result(l0, environment)
        report.update(result=result, exit_code=exit_code, l0=l0, environment=environment)
    except Exception as error:
        report.update(result="RUNNER_ERROR", exit_code=3, error=f"{type(error).__name__}: {error}")
    report["finished_at"] = utc_now()
    write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "ck3_li_yu_dao_acceptance" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]))
    parser.add_argument("--game-dir", type=Path, help="CK3 game corpus or installation directory; environment: XAR_CK3_GAME_DIR")
    parser.add_argument("--game-exe", type=Path, help="explicit executable; environment: XAR_CK3_EXE")
    parser.add_argument("--mcp-evidence", type=Path, help="external exact-build tools/list evidence JSON; see inspect_mcp docstring")
    parser.add_argument("--kaishek-profile", default=os.environ.get("LYD_KAISHEK_PROFILE"))
    parser.add_argument("--kaishek-fixture", default=os.environ.get("LYD_KAISHEK_FIXTURE"))
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    try:
        report = run(args)
    except (OSError, ValueError) as error:
        print(f"LYD RUNNER ERROR: {error}", file=sys.stderr)
        return 3
    print(json.dumps({key: report[key] for key in ("result", "exit_code", "report_directory", "live")}, ensure_ascii=False, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
