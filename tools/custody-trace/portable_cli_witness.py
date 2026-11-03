"""Six new portability/output CLI invocations; no retention policy oracle.

Source authored after the original utility and selected candidate were read.
Initial five boundaries were frozen in NEW-WITNESS-ORACLE.json before this body.
The sixth was appended in NEW-WITNESS-ORACLE-ADDENDUM.json before its extension.
This is not blind and does not replay the old three DATA or producer vectors.
Uses only sys.executable, named source leaves and a unique owned work child.
The first actual invocation belongs to the Native owner.
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
TOTAL_SECONDS = 60
DATA = {"kind": "DATA", "caps": [2, 100, 8],
        "trace": [["portable-item", 3, 6]]}
SENTINEL = b"portable-existing-output\n"
STATE = {"kind": "new portability/output witness only",
         "planned_cli_invocations": 6, "cli_started": 0,
         "cli_completed": 0, "exit_zero_observed": 0,
         "cases_asserted": 0, "old_case_invocations": 0,
         "work_directory": None, "results": []}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def bounded_read(path, limit):
    with path.open("rb") as source:
        raw = source.read(limit + 1)
    require(len(raw) <= limit, "bounded read exceeded: " + path.name)
    return raw


def source_bytes(directory, name, expected_sha):
    raw = bounded_read(directory / name, SOURCE_LIMIT)
    require(hashlib.sha256(raw).hexdigest() == expected_sha,
            "source pin differs: " + name)
    return raw


def create_bytes(path, raw):
    with path.open("xb") as sink:
        sink.write(raw)


def run_cli(case, arguments, cwd, overall_deadline):
    require(time.monotonic() < overall_deadline,
            "overall deadline reached before " + case)
    command = [sys.executable, "-B"] + [str(item) for item in arguments]
    process = subprocess.Popen(
        command, cwd=str(cwd), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    STATE["cli_started"] += 1
    captures = {"stdout": bytearray(), "stderr": bytearray()}
    sizes = {"stdout": 0, "stderr": 0}
    errors = []
    overflow = threading.Event()

    def drain(label, pipe, limit):
        try:
            while True:
                chunk = pipe.read(4096)
                if not chunk:
                    break
                sizes[label] += len(chunk)
                room = limit + 1 - len(captures[label])
                if room > 0:
                    captures[label].extend(chunk[:room])
                if sizes[label] > limit:
                    overflow.set()
        except Exception as problem:
            errors.append(type(problem).__name__)
            overflow.set()
        finally:
            pipe.close()

    readers = [threading.Thread(target=drain,
                               args=("stdout", process.stdout, STDOUT_LIMIT),
                               daemon=True),
               threading.Thread(target=drain,
                               args=("stderr", process.stderr, STDERR_LIMIT),
                               daemon=True)]
    for reader in readers:
        reader.start()
    deadline = min(time.monotonic() + CHILD_SECONDS, overall_deadline)
    failure = None
    try:
        while process.poll() is None:
            if overflow.is_set():
                failure = "bounded subprocess output exceeded or reader failed"
                process.kill()  # Only this runner's just-created child.
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                failure = "subprocess deadline exceeded"
                process.kill()  # Never scans or targets unrelated processes.
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
    require(not any(reader.is_alive() for reader in readers),
            "bounded pipe drain did not finish")
    require(not errors, "subprocess pipe reader failed")
    require(failure is None and not overflow.is_set(),
            case + ": " + (failure or "bounded output exceeded"))
    STATE["cli_completed"] += 1
    STATE["exit_zero_observed"] += int(process.returncode == 0)
    record = {"case": case, "exit_code": process.returncode,
              "stdout_bytes": sizes["stdout"], "stderr_bytes": sizes["stderr"],
              "fields_asserted": False, "command": command}
    STATE["results"].append(record)
    return process.returncode, bytes(captures["stdout"]), bytes(captures["stderr"]), record


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate output JSON key")
        result[key] = value
    return result


def bad_constant(value):
    raise AssertionError("nonfinite output JSON value")


def assert_json(raw, producer_path, detail_limit):
    require(0 < len(raw) <= STDOUT_LIMIT and raw.endswith(b"\n"),
            "JSON output must be bounded and newline terminated")
    document = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_object,
                          parse_constant=bad_constant)
    require(type(document) is dict, "output root must be an object")
    require(document["schema"] == "custody-trace-analysis/DATA-v1"
            and document["kind"] == "DATA", "output DATA schema differs")
    require(document["caps"] == DATA["caps"] and document["trace_rows"] == 1,
            "new DATA identity differs")
    producer = document["producer"]
    require(type(producer["path"]) is str
            and Path(producer["path"]).is_absolute()
            and Path(producer["path"]) == producer_path,
            "selected producer path differs")
    require(producer["sha256"] == PRODUCER_SHA256, "reported producer pin differs")
    details = document["details"]
    require(details["requested_limit"] == detail_limit
            and details["emitted_rows"] == detail_limit
            and details["omitted_rows"] == 1 - detail_limit,
            "detail option/default differs")
    require(len(details["rows"]) == detail_limit, "detail row count differs")
    if detail_limit:
        require(details["rows"][0]["id"] == "portable-item", "detail input id differs")
        require(len(document["working_sets"]) == 1
                and document["working_sets"][0]["window_requests"] == 1,
                "window option differs")


def assert_success(result):
    code, stdout, stderr, record = result
    require(code == 0 and stderr == b"", "expected clean exit 0: " + record["case"])
    return stdout, record


def assert_failure(result, prefix, basename):
    code, stdout, stderr, record = result
    require(code == 2 and stdout == b"", "expected exit 2 and empty stdout: " + record["case"])
    text = stderr.decode("utf-8")
    require(text.startswith(prefix) and basename in text,
            "wrong first error: " + record["case"])
    return text, record


def mark_asserted(record):
    record["fields_asserted"] = True
    STATE["cases_asserted"] += 1


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path,
                        default=Path(__file__).resolve().parent,
                        help="directory with the two pinned source leaves; default this witness directory")
    parser.add_argument("--work-root", type=Path, required=True,
                        help="existing owned root; a unique child is created and retained")
    arguments = parser.parse_args()
    require(Path(sys.executable).is_absolute(), "sys.executable must be absolute")
    source_dir = arguments.source_dir.resolve(strict=True)
    work_root = arguments.work_root.resolve(strict=True)
    require(source_dir.is_dir() and work_root.is_dir(), "source-dir/work-root must exist as directories")
    analysis = source_bytes(source_dir, ANALYSIS_NAME, ANALYSIS_SHA256)
    producer = source_bytes(source_dir, PRODUCER_NAME, PRODUCER_SHA256)
    root = Path(tempfile.mkdtemp(prefix="custody-trace-portable-", dir=str(work_root)))
    STATE["work_directory"] = str(root)
    relocated = root / "relocated tools"
    analysis_only = root / "analysis only"
    external = root / "explicit producer"
    cwd = root / "separate cwd"
    for directory in (relocated, analysis_only, external, cwd):
        directory.mkdir()
    tool_default = relocated / ANALYSIS_NAME
    producer_default = relocated / PRODUCER_NAME
    tool_override = analysis_only / ANALYSIS_NAME
    producer_override = external / PRODUCER_NAME
    create_bytes(tool_default, analysis)
    create_bytes(producer_default, producer)
    create_bytes(tool_override, analysis)
    create_bytes(producer_override, producer)
    input_path = root / "new-portable-data.json"
    create_bytes(input_path, json.dumps(DATA, separators=(",", ":")).encode("utf-8") + b"\n")
    deadline = started + TOTAL_SECONDS

    raw, record = assert_success(run_cli(
        "relocated_default_stdout", [tool_default, input_path, "--detail-limit", "1", "--window-size", "1"],
        cwd, deadline))
    assert_json(raw, producer_default, 1)
    mark_asserted(record)

    output = root / "new-output.json"
    require(not (analysis_only / PRODUCER_NAME).exists() and not output.exists(),
            "explicit-override fixture must have no colocated producer/output")
    raw, record = assert_success(run_cli(
        "explicit_override_create_output", [tool_override, input_path, "--producer", producer_override,
                                             "--output", output], cwd, deadline))
    require(raw == b"", "file output must leave stdout empty")
    assert_json(bounded_read(output, STDOUT_LIMIT), producer_override, 0)
    mark_asserted(record)

    missing_input = root / "unique-missing-input.json"
    missing_producer = root / "unique-missing-producer.py"
    absent_output = root / "must-not-create-output.json"
    text, record = assert_failure(run_cli(
        "missing_input_precedes_producer_and_creation",
        [tool_override, missing_input, "--producer", missing_producer, "--output", absent_output],
        cwd, deadline), "FileNotFoundError: ", missing_input.name)
    require(missing_producer.name not in text and not absent_output.exists(),
            "missing input lost priority or output was created")
    mark_asserted(record)

    existing_output = root / "existing-output.json"
    create_bytes(existing_output, SENTINEL)
    text, record = assert_failure(run_cli(
        "existing_output_preserves_sentinel",
        [tool_override, input_path, "--producer", producer_override, "--output", existing_output],
        cwd, deadline), "FileExistsError: ", existing_output.name)
    require(bounded_read(existing_output, len(SENTINEL)) == SENTINEL,
            "existing output sentinel changed")
    mark_asserted(record)

    absent_parent = root / "must-not-create-parent"
    parent_output = absent_parent / "unique-missing-parent-output.json"
    text, record = assert_failure(run_cli(
        "missing_output_parent_not_created",
        [tool_override, input_path, "--producer", producer_override, "--output", parent_output],
        cwd, deadline), "FileNotFoundError: ", parent_output.name)
    require(not absent_parent.exists() and not parent_output.exists(),
            "missing output parent or file was created")
    mark_asserted(record)

    bad_producer = external / "wrong-sha-producer.py"
    bad_output = root / "must-not-create-after-wrong-sha.json"
    create_bytes(bad_producer, b"# finite wrong-SHA producer; must not execute\n")
    result = run_cli(
        "wrong_sha_override_does_not_fallback",
        [tool_default, input_path, "--producer", bad_producer, "--output", bad_output],
        cwd, deadline)
    code, stdout, stderr, record = result
    require(code == 2 and stdout == b""
            and stderr.decode("utf-8").splitlines()
                == ["ValueError: producer hash differs; explicit source review is required"]
            and not bad_output.exists(),
            "explicit wrong SHA must fail before output and never fall back to valid default")
    mark_asserted(record)
    require(STATE["cli_started"] == 6 and STATE["cli_completed"] == 6
            and STATE["exit_zero_observed"] == 2 and STATE["cases_asserted"] == 6,
            "invocation/assertion accounting differs")
    require(time.monotonic() <= deadline, "overall witness deadline exceeded")
    STATE["status"] = "ALL_SIX_NEW_CLI_BOUNDARIES_ASSERTED"
    print(json.dumps(STATE, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except Exception as problem:
        STATE["status"] = "WITNESS_FAILED"
        STATE["failure"] = type(problem).__name__ + ": " + str(problem)[:1024]
        print(json.dumps(STATE, separators=(",", ":")), file=sys.stderr)
        raise SystemExit(1)
