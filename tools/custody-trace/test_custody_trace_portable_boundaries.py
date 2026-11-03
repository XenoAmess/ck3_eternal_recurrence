"""New public-CLI boundary checks. Source candidate; not executed by its author.

Place beside custody_trace_analysis.py and the pinned custody_trace.py.
Run with an explicit existing --work-root owned by the execution operator.
Only sandbox copies of the CLI and producer are used by child processes.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PRODUCER_SHA256 = "2d2d54a77a3527c7aa37c04e6c1670fc0eff1536aa38fe89be793020aa432544"
SOURCE_LIMIT = 65_536
DIAGNOSTIC_LIMIT = 16_384
OUTPUT_LIMIT = 1_048_576
CHILD_TIMEOUT_SECONDS = 15


def read_bounded(path, limit):
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise AssertionError("fixture or diagnostic exceeds its explicit byte cap")
    return raw


class PortableCliBoundaryTests(unittest.TestCase):
    work_root = None

    @classmethod
    def setUpClass(cls):
        if cls.work_root is None:
            raise AssertionError("invoke this Test script with --work-root")
        if not cls.work_root.is_absolute() or not cls.work_root.is_dir():
            raise AssertionError("--work-root must be an existing absolute directory")
        peer_dir = Path(__file__).resolve().parent
        cls.tool_bytes = read_bounded(peer_dir / "custody_trace_analysis.py", SOURCE_LIMIT)
        cls.producer_bytes = read_bounded(peer_dir / "custody_trace.py", SOURCE_LIMIT)
        if hashlib.sha256(cls.producer_bytes).hexdigest() != PRODUCER_SHA256:
            raise AssertionError("the peer producer is not the pinned raw-byte fixture")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(
            prefix="portable_cli_boundary_", dir=str(self.work_root))
        self.addCleanup(temporary.cleanup)
        self.sandbox = Path(temporary.name)
        self.tool_dir = self.sandbox / "tool package"
        self.cwd = self.sandbox / "working directory"
        self.logs = self.sandbox / "child logs"
        for directory in (self.tool_dir, self.cwd, self.logs):
            directory.mkdir()
        self.tool = self.tool_dir / "custody_trace_analysis.py"
        self.tool.write_bytes(self.tool_bytes)
        # The sandbox tool deliberately has no default producer.
        self.valid_producer = self.put("producers/custody_trace.py", self.producer_bytes)
        self.wrong_producer = self.put("producers/wrong.py", b"# nonmatching producer fixture\n")
        self.call_count = 0

    def put(self, relative, raw):
        path = self.cwd / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path

    def invoke(self, *arguments):
        self.call_count += 1
        stdout_path = self.logs / (str(self.call_count) + ".stdout")
        stderr_path = self.logs / (str(self.call_count) + ".stderr")
        argv = [sys.executable, "-X", "utf8", str(self.tool)]
        argv.extend(str(argument) for argument in arguments)
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            result = subprocess.run(
                argv, cwd=str(self.cwd), stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr, timeout=CHILD_TIMEOUT_SECONDS,
                check=False, shell=False)
        # Logs avoid unbounded in-memory communicate/capture output. Inspection
        # is capped; this trusted-source driver is not a disk/CPU sandbox.
        return (result.returncode,
                read_bounded(stdout_path, DIAGNOSTIC_LIMIT),
                read_bounded(stderr_path, DIAGNOSTIC_LIMIT))

    def assert_error(self, result, expected_line, output):
        returncode, stdout, stderr = result
        diagnostic = stderr.decode("utf-8", errors="replace")
        self.assertEqual(returncode, 2, diagnostic)
        self.assertEqual(stdout, b"", diagnostic)
        self.assertEqual(stderr.splitlines(), [expected_line.encode("ascii")])
        self.assertFalse(output.exists(), "an earlier failure created its output")

    def test_duplicate_json_precedes_bad_producer(self):
        input_path = self.put(
            "input files/duplicate.json",
            b'{"kind":"DATA","kind":"DATA","caps":[1,1,4],"trace":[]}')
        output = self.cwd / "duplicate-result.json"
        result = self.invoke(input_path, "--producer", self.wrong_producer,
                             "--output", output)
        self.assert_error(result, "ValueError: duplicate JSON object key", output)

    def test_extra_envelope_member_precedes_bad_producer(self):
        input_path = self.put(
            "input files/envelope.json",
            b'{"kind":"DATA","caps":[1,1,4],"trace":[],"unexpected":0}')
        output = self.cwd / "envelope-result.json"
        result = self.invoke(input_path, "--producer", self.wrong_producer,
                             "--output", output)
        self.assert_error(
            result, "ValueError: input must contain exactly kind, caps, and trace",
            output)

    def test_producer_sha_precedes_caps_and_control_reaches_caps(self):
        input_path = self.put(
            "input files/invalid-caps.json",
            b'{"kind":"DATA","caps":[0,1,4],"trace":[]}')
        bad_hash_output = self.cwd / "bad-hash-result.json"
        result = self.invoke(input_path, "--producer", self.wrong_producer,
                             "--output", bad_hash_output)
        self.assert_error(
            result,
            "ValueError: producer hash differs; explicit source review is required",
            bad_hash_output)

        caps_output = self.cwd / "caps-result.json"
        control = self.invoke(input_path, "--producer", self.valid_producer,
                              "--output", caps_output)
        self.assert_error(
            control, "ValueError: entries is outside its finite integer range",
            caps_output)

    def test_ninth_window_precedes_missing_input_and_producer(self):
        missing_input = self.cwd / "missing-input.json"
        missing_producer = self.cwd / "missing-producer.py"
        output = self.cwd / "window-result.json"
        self.assertFalse(missing_input.exists())
        self.assertFalse(missing_producer.exists())
        arguments = [missing_input, "--producer", missing_producer,
                     "--output", output]
        for _ in range(9):
            arguments.extend(("--window-size", "1"))
        result = self.invoke(*arguments)
        self.assert_error(
            result, "ValueError: at most eight window-size arguments are allowed",
            output)

    def test_relative_paths_use_cwd_and_keep_selected_producer_spelling(self):
        relative_input = Path("input files") / "empty.json"
        self.put(relative_input, b'{"kind":"DATA","caps":[1,1,4],"trace":[]}')
        (self.cwd / "relative" / "empty-hop").mkdir(parents=True)
        relative_producer = (Path("relative") / "empty-hop" / ".." / ".."
                             / "producers" / "custody_trace.py")
        relative_output = Path("result files") / "relative-result.json"
        (self.cwd / relative_output).parent.mkdir()
        self.assertFalse((self.tool_dir / "custody_trace.py").exists())
        returncode, stdout, stderr = self.invoke(
            relative_input, "--producer", relative_producer,
            "--output", relative_output)
        self.assertEqual(returncode, 0, stderr.decode("utf-8", errors="replace"))
        self.assertEqual(stdout, b"")
        self.assertEqual(stderr, b"")
        output = self.cwd / relative_output
        self.assertTrue(output.is_file())
        raw = read_bounded(output, OUTPUT_LIMIT)
        self.assertTrue(raw.endswith(b"\n"))
        document = json.loads(raw.decode("utf-8"))
        self.assertEqual(document["schema"], "custody-trace-analysis/DATA-v1")
        self.assertEqual(document["kind"], "DATA")
        self.assertEqual(document["producer"]["sha256"], PRODUCER_SHA256)
        self.assertEqual(document["producer"]["path"], str(relative_producer))
        self.assertEqual(document["trace_rows"], 0)
        self.assertEqual(document["details"]["rows"], [])
        self.assertFalse((self.tool_dir / relative_output).exists())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-root", required=True, type=Path,
                        help="existing absolute directory for unique disposable sandboxes")
    arguments, unittest_arguments = parser.parse_known_args()
    if not arguments.work_root.is_absolute() or not arguments.work_root.is_dir():
        parser.error("--work-root must name an existing absolute directory")
    PortableCliBoundaryTests.work_root = arguments.work_root
    unittest.main(argv=[sys.argv[0]] + unittest_arguments)


if __name__ == "__main__":
    main()

