"""Opt-in, bounded Windows check using harmless Python stdio processes.

Importing this module performs no native calls and starts no processes. The
explicit CLI creates an empty external attempt, launches a venv redirector,
and retains the actual queue/application generations through both exits.
No game, Steam, desktop, project MCP server, or RPC is involved.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import ntpath
import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap
import time
import traceback

from g2_saved_campaign.sdk_process_custody import RetainedProcessGeneration


LANE_CAP = 16 * 1024**2
REPO_ROOT = Path(__file__).resolve().parents[1]

APP_SOURCE = textwrap.dedent('''\
    """Harmless child: import pinned dependencies, then wait for EOF."""
    from datetime import datetime, timezone
    from importlib.metadata import version
    import json
    import os
    from pathlib import Path
    import site
    import sys

    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    root = Path(config["artifact_root"])
    dependency_root = Path(os.environ["XAR_FRESH_SDK_DEPENDENCY_ROOT"]).resolve()
    assert str(dependency_root) == config["dependency_root"]
    site.addsitedir(str(dependency_root))
    assert version("mcp") == "2.0.0"
    import win32api
    import pythoncom
    import mcp
    from mcp.client import stdio

    def write(name, value):
        pending = root / (name + ".pending")
        pending.write_text(json.dumps(value, indent=2) + "\\n", encoding="utf-8")
        pending.rename(root / name)

    write("application-ready.json", {
        "at_utc": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(),
        "sys_executable": sys.executable, "base_executable": sys._base_executable,
        "dependency_root": str(dependency_root), "mcp_distribution_version": version("mcp"),
        "win32api_source": win32api.__file__, "pythoncom_source": pythoncom.__file__,
        "mcp_source": mcp.__file__, "mcp_stdio_source": stdio.__file__,
        "dependency_bootstrap": "site.addsitedir", "mcp_imported": "mcp" in sys.modules,
        "rpc_submitted": False})
    payload = sys.stdin.buffer.read()
    assert payload == b""
    write("application-stdin-eof.json", {
        "at_utc": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(),
        "stdin_eof_observed": True, "stdin_bytes": len(payload), "exit_code_claim": 0,
        "kernel_exit_observed_by_child": False})
    ''')

QUEUE_SOURCE = textwrap.dedent('''\
    """Harmless queue using the installed real MCP stdio factory."""
    import asyncio
    from datetime import datetime, timezone
    from importlib.metadata import version
    import importlib.util
    import json
    import os
    from pathlib import Path
    import site
    import sys
    import time
    import traceback

    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    root = Path(config["artifact_root"])
    dependency_root = Path(config["dependency_root"]).resolve()
    site.addsitedir(str(dependency_root))
    assert version("mcp") == "2.0.0"
    sys.path.insert(0, config["repo_tools"])
    from g2_saved_campaign.sdk_process_custody import RetainedProcessGeneration, retain_mcp_stdio_process
    from mcp import StdioServerParameters
    from mcp.client import stdio

    spec = importlib.util.spec_from_file_location("harmless_real_supervisor", config["supervisor_source"])
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    supervisor.N = root

    def write(name, value):
        supervisor.write(root / name, value)

    async def wait_for(name):
        end = time.monotonic() + config["queue_timeout"]
        while not (root / name).is_file():
            if (root / "EXIT-HARMLESS-QUEUE").exists():
                raise RuntimeError("observer requested cooperative harmless queue exit")
            if time.monotonic() >= end:
                raise TimeoutError("bounded harmless queue receipt wait expired: " + name)
            await asyncio.sleep(.025)
        return supervisor.read(root / name, 16384)

    async def main():
        base = str(Path(sys._base_executable).resolve())
        assert base == config["base_executable"]
        original_factory = stdio._create_platform_compatible_process
        write("queue-bootstrap.json", {
            "at_utc": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(),
            "sys_executable": sys.executable, "base_executable": base,
            "dependency_root": str(dependency_root), "mcp_distribution_version": version("mcp"),
            "mcp_stdio_source": stdio.__file__, "dependency_bootstrap": "site.addsitedir",
            "rpc_submitted": False})
        application = None
        with RetainedProcessGeneration.capture(os.getpid(), expected_executable=base) as queue:
            queue.require_live()
            with (root / "application-stderr.log").open("x", encoding="utf-8") as errlog:
                async with retain_mcp_stdio_process(stdio, expected_executable=base) as capture:
                    async with stdio.stdio_client(StdioServerParameters(
                            command=base, args=["-B", "-X", "utf8", config["app_script"], sys.argv[1]],
                            cwd=str(root), env={"XAR_FRESH_SDK_DEPENDENCY_ROOT": str(dependency_root)}),
                            errlog=errlog):
                        application = capture.require_generation()
                        application.require_live()
                        ready = await wait_for("application-ready.json")
                        assert ready["pid"] == capture.creator_process.pid == application.pid
                        identities = [queue.identity("sdk_queue"), application.identity("sdk_application")]
                        write("ROOT-ACTUAL-SDK-PROCESS-GENERATIONS.json", {
                            "at_utc": datetime.now(timezone.utc).isoformat(), "processes": identities,
                            "application_creator": "actual_mcp_stdio_factory_return", "rpc_started": False,
                            "creator_pid": capture.creator_process.pid,
                            "creator_type": type(capture.creator_process).__qualname__})
                        pin = await wait_for("ROOT-ACTUAL-SDK-PROCESSES-PINNED.json")
                        supervisor.validate_sdk_pin(identities, pin)
                        application.require_live()
                        write("queue-ack-accepted.json", {
                            "at_utc": datetime.now(timezone.utc).isoformat(),
                            "exact_pin_validated": True, "processes": identities, "rpc_started": False})
                    observed = application.observe()
                    assert observed["kernel_exit_observed"] is True and observed["exit_code"] == 0
                    assert observed["observation_error"] is None
                    write("queue-application-exit-observed.json", observed)
                assert stdio._create_platform_compatible_process is original_factory
                assert application.observe()["observation_error"]["stage"] == "closed"
        write("queue-cleanup-completed.json", {
            "at_utc": datetime.now(timezone.utc).isoformat(), "stdio_context_closed": True,
            "factory_restored": True, "retained_application_handle_closed": True,
            "kernel_queue_exit_observed_by_self": False, "rpc_submitted": False})
        return 0

    try:
        result = asyncio.run(main())
    except BaseException as error:
        write("queue-failure.json", {"type": type(error).__name__, "message": str(error),
              "traceback": traceback.format_exc()[-16384:], "rpc_submitted": False})
        result = 1
    raise SystemExit(result)
    ''')


def stamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    if path.stat().st_size > 65536:
        raise RuntimeError("bounded harmless receipt exceeded 64 KiB")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    payload = json.dumps(value, indent=2) + "\n"
    if len(payload.encode("utf-8")) > 65536:
        raise RuntimeError("bounded harmless receipt exceeded 64 KiB")
    with path.open("x", encoding="utf-8") as stream:
        stream.write(payload)


def same_image(left, right):
    return ntpath.normcase(ntpath.normpath(str(left))) == ntpath.normcase(ntpath.normpath(str(right)))


def storage_guard(args, *, create=False):
    admission = read(args.storage_admission)
    review = datetime.fromisoformat(admission["review_at_utc"].replace("Z", "+00:00"))
    if (admission.get("status") != "ADMITTED" or review.tzinfo is None
            or datetime.now(timezone.utc) >= review):
        raise RuntimeError("original storage admission expired; no extension")
    if not any(args.artifact_root.is_relative_to(Path(root).resolve())
               for root in admission["approved_output_roots"]):
        raise RuntimeError("harmless process artifacts require the original admitted root")
    volume = args.artifact_root
    while not volume.exists():
        volume = volume.parent
    disk = shutil.disk_usage(volume)
    required = sum(admission[key] for key in ("this_write_peak", "other_unspent_reservations",
                                              "system_growth_reserve", "safety_margin"))
    if (disk.free < required
            or disk.used + admission["this_write_peak"] > admission["effective_project_quota"]):
        raise RuntimeError("original storage reservation is exhausted")
    if create:
        args.artifact_root.mkdir(parents=True, exist_ok=True)
        if any(args.artifact_root.iterdir()):
            raise RuntimeError("a new empty harmless bootstrap attempt is required")
    if sum(path.stat().st_size for path in args.artifact_root.rglob("*") if path.is_file()) > LANE_CAP:
        raise RuntimeError("harmless process lane exceeds 16 MiB")
    return admission, {"free_bytes": disk.free, "required_free_bytes": required,
                       "original_peak_bytes_unchanged": admission["this_write_peak"]}


def main(args):
    if os.name != "nt":
        raise RuntimeError("this explicit harmless process verifier requires Windows")
    args.artifact_root = args.artifact_root.resolve()
    args.venv_python = args.venv_python.resolve(strict=True)
    args.supervisor_source = args.supervisor_source.resolve(strict=True)
    args.storage_admission = args.storage_admission.resolve(strict=True)
    if (not same_image(args.venv_python, sys.executable)
            or args.venv_python.name.lower() != "python.exe"
            or args.venv_python.parent.name.lower() != "scripts"
            or not (args.venv_python.parents[1] / "pyvenv.cfg").is_file()):
        raise RuntimeError("invoke this verifier through the explicit matching Python venv")
    base = Path(sys._base_executable).resolve(strict=True)
    if same_image(base, args.venv_python):
        raise RuntimeError("this check specifically requires a distinct Windows venv redirector")
    dependency_root = (args.venv_python.parents[1] / "Lib/site-packages").resolve(strict=True)
    admission, capacity_start = storage_guard(args, create=True)
    root = args.artifact_root
    queue_script, app_script = root / "harmless_queue.py", root / "harmless_application.py"
    for path, source in ((queue_script, QUEUE_SOURCE), (app_script, APP_SOURCE)):
        with path.open("x", encoding="utf-8") as stream:
            stream.write(source)
    config = {"artifact_root": str(root), "repo_tools": str(REPO_ROOT / "tools"),
              "base_executable": str(base), "dependency_root": str(dependency_root),
              "supervisor_source": str(args.supervisor_source), "app_script": str(app_script),
              "queue_timeout": min(20, args.timeout), "mcp_required": "2.0.0"}
    config_path = root / "config.json"
    write(config_path, config)
    spec = importlib.util.spec_from_file_location("harmless_observer_supervisor", args.supervisor_source)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    supervisor.N = root
    source_pins = {str(path): digest(path) for path in (
        Path(__file__), REPO_ROOT / "tools/g2_saved_campaign/sdk_process_custody.py",
        args.supervisor_source, queue_script, app_script)}
    events, pair, process, wrapper = [], {}, None, None
    wrapper_identity = wrapper_exit = pair_result = failure = None
    pair_identities = None

    class RecordingGeneration:
        def __init__(self, generation):
            self.generation = generation

        @classmethod
        def capture(cls, pid, **kwargs):
            generation = RetainedProcessGeneration.capture(pid, **kwargs)
            events.append({"event": "exact_generation_handle_retained", "at_utc": stamp(),
                           "identity": generation.identity("observer_capture")})
            return cls(generation)

        def identity(self, role):
            return self.generation.identity(role)

        def require_live(self):
            result = self.generation.require_live()
            events.append({"event": "retained_generation_verified_live", "at_utc": stamp(),
                           "observation": result})
            return result

        def observe(self):
            return self.generation.observe()

        def close(self):
            self.generation.close()

    command = [str(args.venv_python), "-B", "-X", "utf8", str(queue_script), str(config_path)]
    write(root / "observer-launch.json", {"at_utc": stamp(), "argv": command,
          "game_steam_window_rpc_executed": False, "automatic_retry": False})
    started = time.monotonic()
    try:
        storage_guard(args)
        with (root / "queue-stdout.log").open("xb") as stdout, \
                (root / "queue-stderr.log").open("xb") as stderr:
            process = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            wrapper = RetainedProcessGeneration.capture(process.pid,
                expected_executable=str(args.venv_python))
            wrapper.require_live()
            wrapper_identity = wrapper.identity("venv_redirector_wrapper")
            write(root / "wrapper-generation.json", wrapper_identity)
            generations_path = root / "ROOT-ACTUAL-SDK-PROCESS-GENERATIONS.json"
            while not generations_path.is_file():
                if process.poll() is not None:
                    raise RuntimeError("harmless queue stopped before publishing actual generations")
                if time.monotonic() - started >= args.timeout:
                    raise TimeoutError("harmless queue generation publication deadline expired")
                time.sleep(.025)
            pair_identities = supervisor.validate_sdk_process_pair(read(generations_path)["processes"])
            if wrapper_identity["pid"] in {row["pid"] for row in pair_identities.values()}:
                raise AssertionError("venv wrapper must be distinct from actual queue and application")
            if not all(same_image(row["executable"], base) for row in pair_identities.values()):
                raise AssertionError("actual queue/application images must match the direct base interpreter")
            supervisor.retain_sdk_pair(pair, RecordingGeneration)
            pin = read(root / "ROOT-ACTUAL-SDK-PROCESSES-PINNED.json")
            supervisor.validate_sdk_pin(list(pair_identities.values()), pin)
            events.append({"event": "exact_pair_acknowledgement_published", "at_utc": stamp()})
            while pair_result is None:
                pair_result = supervisor.observe_retained_sdk_exit(pair)
                if pair_result is None:
                    if time.monotonic() - started >= args.timeout:
                        raise TimeoutError("both exact harmless generation exits were not observed in time")
                    time.sleep(.025)
            if pair_result["normal"] is not True:
                raise AssertionError("actual harmless queue/application exits were not both zero")
            if process.wait(timeout=max(1, args.timeout - (time.monotonic() - started))) != 0:
                raise AssertionError("venv redirector wrapper also failed")
            wrapper_exit = wrapper.observe()
            if wrapper_exit["kernel_exit_observed"] is not True or wrapper_exit["exit_code"] != 0:
                raise AssertionError("wrapper exit was not independently observed zero")
            bootstrap, ready = read(root / "queue-bootstrap.json"), read(root / "application-ready.json")
            if bootstrap["pid"] != pair_identities["sdk_queue"]["pid"]:
                raise AssertionError("queue self identity differs from its actual retained generation")
            if ready["pid"] != pair_identities["sdk_application"]["pid"]:
                raise AssertionError("actual creator child differs from the retained application generation")
            if not same_image(bootstrap["sys_executable"], args.venv_python):
                raise AssertionError("queue did not preserve the venv sys.executable redirector")
            if (not same_image(ready["sys_executable"], base)
                    or bootstrap["mcp_distribution_version"] != "2.0.0"
                    or ready["mcp_distribution_version"] != "2.0.0"
                    or ready["mcp_imported"] is not True
                    or not Path(ready["mcp_source"]).resolve().is_relative_to(dependency_root)
                    or not Path(ready["mcp_stdio_source"]).resolve().is_relative_to(dependency_root)):
                raise AssertionError("direct base child dependency bootstrap differs from the contract")
            ack = read(root / "queue-ack-accepted.json")
            if not (pin["at_utc"] <= ack["at_utc"] and ack["exact_pin_validated"] is True):
                raise AssertionError("queue did not validate the actual supervisor pin before cleanup")
            if read(root / "application-stdin-eof.json")["stdin_bytes"] != 0:
                raise AssertionError("harmless child received unexpected protocol traffic")
            cleanup = read(root / "queue-cleanup-completed.json")
            if not all(cleanup[key] is True for key in (
                    "stdio_context_closed", "factory_restored", "retained_application_handle_closed")):
                raise AssertionError("real stdio cleanup did not complete")
    except Exception as error:
        failure = {"type": type(error).__name__, "message": str(error),
                   "traceback": traceback.format_exc()[-16384:]}
        if not (root / "EXIT-HARMLESS-QUEUE").exists():
            write(root / "EXIT-HARMLESS-QUEUE", {"at_utc": stamp(), "reason": "test_failure_cleanup"})
        if process is not None:
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                failure["cooperative_cleanup"] = "wrapper exit still unknown after fixed grace"
        if wrapper is not None:
            wrapper_exit = wrapper.observe()
        if pair:
            try:
                pair_result = supervisor.observe_retained_sdk_exit(pair)
            except Exception as observation_error:
                failure["exit_observation_error"] = str(observation_error)
    finally:
        for generation in pair.values():
            generation.close()
        if wrapper is not None:
            wrapper.close()
    storage_failure = None
    try:
        closing_admission, capacity_close = storage_guard(args)
        if closing_admission != admission:
            raise RuntimeError("original storage admission changed during harmless verification")
    except Exception as error:
        capacity_close = {"check_error": str(error)}
        storage_failure = {"type": type(error).__name__, "message": str(error)}
    receipt = {"status": "GREEN" if failure is None and storage_failure is None else "RED",
        "at_utc": stamp(), "elapsed_seconds": time.monotonic() - started,
        "failure": failure, "storage_failure": storage_failure, "source_pins": source_pins,
        "wrapper_identity": wrapper_identity, "wrapper_exit": wrapper_exit,
        "actual_pair_identities": pair_identities, "actual_pair_exits": pair_result,
        "events": events, "capacity_start": capacity_start, "capacity_close": capacity_close,
        "review_at_utc_unchanged": admission["review_at_utc"], "lane_cap_bytes": LANE_CAP,
        "game_steam_window_rpc_executed": False, "runtime_campaign_credit": False,
        "scope": "real harmless venv wrapper, queue, dependency probe child; installed mcp2 stdio factory; actual supervisor retain/observe only"}
    write(root / "result.json", receipt)
    size = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    if size > LANE_CAP:
        raise RuntimeError("harmless process evidence exceeded the 16 MiB cap")
    print(json.dumps({"status": receipt["status"], "result": str(root / "result.json"),
                      "artifact_bytes": size, "wrapper_identity": wrapper_identity,
                      "actual_pair_exits": pair_result, "failure": failure,
                      "storage_failure": storage_failure}, indent=2))
    return 0 if receipt["status"] == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venv-python", type=Path, required=True)
    parser.add_argument("--supervisor-source", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--storage-admission", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=30, choices=range(5, 41))
    raise SystemExit(main(parser.parse_args()))
