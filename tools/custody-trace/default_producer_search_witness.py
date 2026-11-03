"""One new public CLI check: a missing default peer cannot be borrowed from cwd.

Known-source author; not blind or a retention-policy/native-authority oracle.
Main fixture/assertions use one reviewed model function; author never ran it.
No prior witness/Test/input is run or modified by this file.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

ANALYSIS_NAME = "custody_trace_analysis.py"
PRODUCER_NAME = "custody_trace.py"
ANALYSIS_SHA256 = "5602d96fbbd63f1751568a7a746793e09e97c0632fed5fc6573bed749e127608"
PRODUCER_SHA256 = "2d2d54a77a3527c7aa37c04e6c1670fc0eff1536aa38fe89be793020aa432544"
SOURCE_LIMIT = 65536
STDOUT_LIMIT = 1048576
STDERR_LIMIT = 65536
CHILD_SECONDS = 10
INPUT_BYTES = b'{"kind":"DATA","caps":[1,1,4],"trace":[]}\n'
STATE = {"scenario": "default_missing_peer_ignores_valid_cwd_producer",
         "planned_cli_invocations": 1, "cli_started": 0, "cli_completed": 0,
         "observed_child_exit_code": None, "behavior_asserted": False,
         "work_directory": None, "raw_log_paths": None}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_bounded(path, limit):
    with path.open("rb") as source:
        raw = source.read(limit + 1)
    require(len(raw) <= limit, "bounded file read exceeded: " + path.name)
    return raw


def pinned_bytes(path, expected_sha):
    raw = read_bounded(path, SOURCE_LIMIT)
    require(hashlib.sha256(raw).hexdigest() == expected_sha,
            "selected source raw pin differs: " + path.name)
    return raw


def write_new(path, raw):
    with path.open("xb") as sink:
        sink.write(raw)


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path,
                        default=Path(__file__).resolve().parent,
                        help="exact two source peers; default this witness directory")
    parser.add_argument("--work-root", type=Path, required=True,
                        help="existing absolute owned root; new unique child is retained")
    arguments = parser.parse_args()
    require(Path(sys.executable).is_absolute(), "sys.executable must be absolute")
    require(arguments.work_root.is_absolute() and arguments.work_root.is_dir(),
            "work-root must be an existing absolute directory")
    arguments.source_dir = arguments.source_dir.resolve(strict=True)
    arguments.work_root = arguments.work_root.resolve(strict=True)
    require(arguments.source_dir.is_dir(), "source-dir must be a directory")
    return arguments


def run_one_cli(tool, input_path, output_path, cwd, log_dir):
    """One bounded child, no --producer; returns exit_code/stdout/stderr bytes.

    tool/input/output/cwd/log_dir must be owned absolute Paths. Existing log_dir
    is required. Raw bounded logs and observed process result are retained before
    output/timeout failures are raised. Never deletes any directory.
    """
    require(STATE["cli_started"] == 0, "only one target CLI is authorized")
    require(all(path.is_absolute() for path in (tool, input_path, output_path, cwd, log_dir)),
            "owned subprocess paths must be absolute")
    command = [sys.executable, "-B", "-X", "utf8", str(tool), str(input_path),
               "--output", str(output_path)]
    STATE["argv"] = command
    process = subprocess.Popen(
        command, cwd=str(cwd), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    STATE["cli_started"] = 1
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    sizes = {"stdout": 0, "stderr": 0}
    overflow = threading.Event()
    reader_errors = []

    def drain(label, pipe, limit):
        try:
            while True:
                chunk = pipe.read(4096)
                if not chunk:
                    break
                sizes[label] += len(chunk)
                room = limit + 1 - len(buffers[label])
                if room > 0:
                    buffers[label].extend(chunk[:room])
                if sizes[label] > limit:
                    overflow.set()
        except Exception as problem:
            reader_errors.append(type(problem).__name__)
            overflow.set()
        finally:
            pipe.close()

    readers = [threading.Thread(target=drain,
                               args=("stdout", process.stdout, STDOUT_LIMIT), daemon=True),
               threading.Thread(target=drain,
                               args=("stderr", process.stderr, STDERR_LIMIT), daemon=True)]
    for reader in readers:
        reader.start()
    failure = None
    deadline = time.monotonic() + CHILD_SECONDS
    try:
        while process.poll() is None:
            if overflow.is_set():
                failure = "bounded subprocess output exceeded or reader failed"
                process.kill()  # Only this witness's newly created child.
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                failure = "subprocess deadline exceeded"
                process.kill()
                break
            try:
                process.wait(timeout=min(remaining, 0.1))
            except subprocess.TimeoutExpired:
                pass
        process.wait(timeout=1)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=1)
        for reader in readers:
            reader.join(timeout=1)
        STATE["observed_child_exit_code"] = process.returncode
        STATE["cli_completed"] = int(process.returncode is not None)
        STATE["stdout_bytes"] = sizes["stdout"]
        STATE["stderr_bytes"] = sizes["stderr"]
        STATE["raw_log_truncated"] = overflow.is_set()
        stdout_log = log_dir / "cli.stdout.bin"
        stderr_log = log_dir / "cli.stderr.bin"
        write_new(stdout_log, bytes(buffers["stdout"]))
        write_new(stderr_log, bytes(buffers["stderr"]))
        STATE["raw_log_paths"] = {"stdout": str(stdout_log), "stderr": str(stderr_log)}
    require(not any(reader.is_alive() for reader in readers), "bounded pipe drain did not finish")
    require(not reader_errors, "subprocess pipe reader failed")
    require(failure is None and not overflow.is_set(), failure or "bounded output exceeded")
    return {"exit_code": process.returncode, "stdout": bytes(buffers["stdout"]),
            "stderr": bytes(buffers["stderr"])}


def main():
    arguments = parse_arguments()
    analysis_path = arguments.source_dir / ANALYSIS_NAME
    producer_path = arguments.source_dir / PRODUCER_NAME
    analysis_bytes = pinned_bytes(analysis_path, ANALYSIS_SHA256)
    producer_bytes = pinned_bytes(producer_path, PRODUCER_SHA256)

    work_dir = Path(tempfile.mkdtemp(prefix="default-producer-search-", dir=arguments.work_root))
    STATE["work_directory"] = str(work_dir)

    tool_dir = work_dir / "tool"
    cwd_dir = work_dir / "cwd"
    log_dir = work_dir / "logs"
    tool_dir.mkdir()
    cwd_dir.mkdir()
    log_dir.mkdir()

    tool_path = tool_dir / ANALYSIS_NAME
    write_new(tool_path, analysis_bytes)

    cwd_producer_path = cwd_dir / PRODUCER_NAME
    write_new(cwd_producer_path, producer_bytes)

    input_path = cwd_dir / "input.json"
    write_new(input_path, INPUT_BYTES)

    output_path = cwd_dir / "output.json"

    require(not (tool_dir / PRODUCER_NAME).exists(), "producer must not exist beside tool before invocation")
    require(not output_path.exists(), "output must not exist before invocation")

    result = run_one_cli(tool_path, input_path, output_path, cwd_dir, log_dir)

    require(read_bounded(tool_path, SOURCE_LIMIT) == analysis_bytes, "tool copy changed")
    require(read_bounded(cwd_producer_path, SOURCE_LIMIT) == producer_bytes, "cwd producer changed")
    require(not (tool_dir / PRODUCER_NAME).exists(), "producer appeared beside tool")

    require(result["exit_code"] == 2, "exit code must be 2")
    require(result["stdout"] == b"", "stdout must be empty")

    stderr_text = result["stderr"].decode("utf-8")
    lines = stderr_text.splitlines()
    require(len(lines) == 1, "stderr must contain exactly one logical line")
    line = lines[0]
    require(line.startswith("FileNotFoundError: "), "stderr line must start with FileNotFoundError: ")
    require(repr(str(tool_dir / PRODUCER_NAME)) in line, "stderr must contain repr of missing tool-only producer path")

    require(not output_path.exists(), "output must not exist after invocation")

    require(STATE["cli_started"] == 1, "cli_started must be 1")
    require(STATE["cli_completed"] == 1, "cli_completed must be 1")
    require(STATE["observed_child_exit_code"] == 2, "observed_child_exit_code must be 2")

    STATE["behavior_asserted"] = True
    STATE["source_bytes_unchanged"] = True
    STATE["status"] = "DEFAULT_PRODUCER_MISSING_WITHOUT_CWD_FALLBACK_ASSERTED"
    print(json.dumps(STATE, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as problem:
        STATE["status"] = "WITNESS_FAILED"
        STATE["failure"] = type(problem).__name__ + ": " + str(problem)[:1024]
        print(json.dumps(STATE, separators=(",", ":")), file=sys.stderr)
        raise SystemExit(1)
