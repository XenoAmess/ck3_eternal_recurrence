"""Run all eight existing M6 integration cases against immutable Source31 in RAM.

Git supplies Python modules from the exact parent used by the Source32 producer.
No SDK export, checkout, Game, native call or filesystem fixture is created.
Missing Git history or source is an error, never a skipped qualification.
"""
from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
import importlib.abc
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

from tools.g2_saved_campaign import test_prepare_wartime_sway_opportunity_v1 as regression


SOURCE31_COMMIT = "12e81b52c736baec02a85f32098bae5bdaa66a31"
SOURCE_PREFIX = "ck3_autonomous_player/src/"
PACKAGE = "xar_autoplayer"
EXPECTED_CASES = 8
MAX_MODULE_BYTES = 2 * 1024 * 1024
MAX_IMPORTED_SOURCE_BYTES = 32 * 1024 * 1024


class MissingSource31Error(RuntimeError):
    """The exact immutable integration input is unavailable."""


@dataclass(frozen=True)
class _Blob:
    object_id: str
    size: int


class Source31GitReaderV1:
    """Read immutable Git blobs; retain imported sources only in process memory."""

    def __init__(self, repository: Path) -> None:
        self.repository = repository
        self.blobs: dict[str, _Blob] = {}
        self.cache: dict[str, bytes] = {}
        self.source_bytes = 0
        tree = self._git("ls-tree", "-r", "-l", "-z", SOURCE31_COMMIT, "--", SOURCE_PREFIX)
        for raw in tree.split(b"\0"):
            if not raw:
                continue
            header, separator, path = raw.partition(b"\t")
            parts = header.split()
            if not separator or len(parts) != 4 or parts[1] != b"blob":
                raise MissingSource31Error("Source31 has a malformed source-tree row")
            name = path.decode("utf-8")
            if not name.startswith(SOURCE_PREFIX):
                raise MissingSource31Error("Source31 tree row is outside the SDK prefix")
            relative = name[len(SOURCE_PREFIX):]
            if not relative.endswith(".py"):
                continue
            object_id = parts[2].decode("ascii")
            if re.fullmatch(r"[0-9a-f]{40}", object_id) is None or not parts[3].isdigit():
                raise MissingSource31Error("Source31 has an invalid source-blob identity")
            if relative in self.blobs:
                raise MissingSource31Error("Source31 repeats a source path")
            self.blobs[relative] = _Blob(object_id, int(parts[3]))
        if f"{PACKAGE}/__init__.py" not in self.blobs:
            raise MissingSource31Error("exact Source31 SDK source is absent; fetch its immutable history")

    def _git(self, *arguments: str) -> bytes:
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repository), *arguments],
                capture_output=True,
                check=False,
                env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
            )
        except OSError as error:
            raise MissingSource31Error("Git is required for the exact Source31 integration input") from error
        if result.returncode != 0:
            diagnostic = result.stderr.decode("utf-8", errors="replace").strip()
            raise MissingSource31Error(
                f"cannot read Source31 {SOURCE31_COMMIT}: {diagnostic[:1000]}"
            )
        return result.stdout

    def read_source(self, relative: str) -> bytes:
        """Return the named Source31 Python blob, with no working-tree fallback."""
        if relative in self.cache:
            return self.cache[relative]
        blob = self.blobs.get(relative)
        if blob is None:
            raise MissingSource31Error(f"Source31 Python source is absent: {relative}")
        if not 0 < blob.size <= MAX_MODULE_BYTES:
            raise MissingSource31Error(f"Source31 Python source exceeds its module budget: {relative}")
        if self.source_bytes + blob.size > MAX_IMPORTED_SOURCE_BYTES:
            raise MissingSource31Error("Source31 imported-source RAM budget exceeded")
        body = self._git("cat-file", "blob", blob.object_id)
        if len(body) != blob.size:
            raise MissingSource31Error(f"Source31 blob byte count differs: {relative}")
        self.cache[relative] = body
        self.source_bytes += len(body)
        return body


class _SourceLoader(importlib.abc.Loader):
    def __init__(self, reader: Source31GitReaderV1, relative: str, root: Path, package: bool) -> None:
        self.reader = reader
        self.relative = relative
        self.root = root
        self.package = package

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> ModuleType | None:
        return None

    def exec_module(self, module: ModuleType) -> None:
        filename = str(self.root / self.relative)
        module.__file__ = filename
        if self.package:
            module.__path__ = [str(self.root / PurePosixPath(self.relative).parent)]
        exec(compile(self.reader.read_source(self.relative), filename, "exec"), module.__dict__)


class _SourceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, reader: Source31GitReaderV1, root: Path) -> None:
        self.reader = reader
        self.root = root

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None = None,
        target: ModuleType | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        if fullname != PACKAGE and not fullname.startswith(PACKAGE + "."):
            return None
        relative = fullname.replace(".", "/")
        package = relative + "/__init__.py"
        if package in self.reader.blobs:
            return importlib.util.spec_from_loader(
                fullname, _SourceLoader(self.reader, package, self.root, True), is_package=True
            )
        module = relative + ".py"
        if module not in self.reader.blobs:
            raise MissingSource31Error(f"Source31 cannot import {fullname}; current checkout fallback forbidden")
        return importlib.util.spec_from_loader(
            fullname, _SourceLoader(self.reader, module, self.root, False), is_package=False
        )


def _sdk_name(name: str) -> bool:
    return name == PACKAGE or name.startswith(PACKAGE + ".")


@contextmanager
def source31_modules_v1(reader: Source31GitReaderV1) -> Iterator[Path]:
    """Install an isolated RAM source view for the unchanged eight-case runner."""
    root = reader.repository / ".ci-ram-source31-12e81b52"
    previous_modules = {name: module for name, module in sys.modules.items() if _sdk_name(name)}
    previous_source = regression.SOURCE_ROOT
    previous_bytecode = sys.dont_write_bytecode
    original_read_bytes = Path.read_bytes
    finder = _SourceFinder(reader, root)

    def read_preimage(path: Path) -> bytes:
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            return original_read_bytes(path)
        return reader.read_source(relative)

    for name in previous_modules:
        del sys.modules[name]
    sys.meta_path.insert(0, finder)
    sys.dont_write_bytecode = True
    regression.SOURCE_ROOT = root
    try:
        with patch.object(Path, "read_bytes", read_preimage):
            yield root
    finally:
        regression.SOURCE_ROOT = previous_source
        sys.dont_write_bytecode = previous_bytecode
        sys.meta_path.remove(finder)
        for name in list(sys.modules):
            if _sdk_name(name):
                del sys.modules[name]
        sys.modules.update(previous_modules)


class WartimeSwaySource31CiTests(unittest.TestCase):
    def test_all_eight_existing_producer_consumer_cases(self) -> None:
        reader = Source31GitReaderV1(Path(__file__).resolve().parents[2])
        with source31_modules_v1(reader):
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(regression.WartimeSwayTests)
            self.assertEqual(suite.countTestCases(), EXPECTED_CASES)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
        self.assertEqual(result.testsRun, EXPECTED_CASES)
        self.assertEqual(result.skipped, [], "the real producer/consumer cases must execute")
        self.assertEqual(result.expectedFailures, [])
        self.assertEqual(result.unexpectedSuccesses, [])
        self.assertTrue(result.wasSuccessful(), "Source31 M6 producer/consumer integration failed")
        print(json.dumps({
            "source31_commit": SOURCE31_COMMIT,
            "actual_integration_cases_run": result.testsRun,
            "skipped": len(result.skipped),
            "source_modules_read": len(reader.cache),
            "source_bytes_read": reader.source_bytes,
            "game_calls": 0,
            "business_credit_awarded": False,
        }))


if __name__ == "__main__":
    unittest.main()
