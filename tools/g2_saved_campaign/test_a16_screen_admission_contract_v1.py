"""Portable A16 contracts; no runtime or temp files."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import IntEnum
import hashlib
import inspect
import json
from pathlib import Path
import re
import sys
from typing import Protocol, cast, get_type_hints
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_source28_a16_cold_union_v1 as m16


class Number(IntEnum):
    SEQUENCE = 7


class ScreenParser(Protocol):
    def __call__(self, value: object, *, machine_id: str, repo: Path,
                 git_head: str, at_utc: datetime) -> m16.ScreenAdmissionV1: ...


def fragment_parser() -> ScreenParser:
    fragment = m16._fragment()
    scope: dict[str, object] = {"Path": Path, "datetime": datetime, "re": re}
    exec(compile(fragment, "<A16 fragment>", "exec"), scope)
    value = scope["parse_screen_admission_v1"]
    if not callable(value) or inspect.signature(value) != inspect.signature(m16.parse_screen_admission_v1):
        raise AssertionError("fragment parser signature changed")
    # Verified fragment signature.
    return cast(ScreenParser, value)


class ScreenAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Path(__file__).resolve().parent
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.head = "a" * 40
        self.ref = m16.ref(Path(m16.__file__))
        self.row = self.build()
        self.fragment = fragment_parser()

    def build(self, sequence: int = 7, *,
              refs: list[m16.ExactRef] | None = None) -> m16.ScreenAdmissionV1:
        return m16.build_screen_admission_v1(
            sequence=sequence, task_id="portable-fixture-only", repo=self.repo,
            git_head=self.head, observed_at_utc=self.now,
            provenance=[self.ref] if refs is None else refs)

    def wire(self) -> dict[str, object]:
        return m16.record(json.loads(json.dumps(self.row)))

    def parse(self, value: object, *, at: datetime | None = None) -> m16.ScreenAdmissionV1:
        return self.fragment(value, machine_id=m16.MACHINE, repo=self.repo,
                             git_head=self.head, at_utc=self.now if at is None else at)

    def reject_field(self, key: str, values: list[object]) -> None:
        for value in values:
            with self.subTest(field=key, value=value):
                row = self.wire()
                row[key] = value
                with self.assertRaises(ValueError):
                    self.parse(row)

    def test_builder_json_actual_fragment_roundtrip(self) -> None:
        row = self.wire()
        self.assertEqual(self.parse(row), self.row)
        self.assertEqual(m16.parse_screen_admission_v1(
            row, machine_id=m16.MACHINE, repo=self.repo,
            git_head=self.head, at_utc=self.now), self.parse(row))
        self.assertEqual(set(row), set(m16.ScreenAdmissionV1.__annotations__))
        self.assertIs(type(row["sequence"]), int)

    def test_public_and_fragment_annotations_resolve(self) -> None:
        for function in (m16.build_screen_admission_v1,
                         m16.parse_screen_admission_v1, self.fragment):
            self.assertIn("return", get_type_hints(function))

    def test_required_and_null_fields(self) -> None:
        for key in self.row:
            with self.subTest(missing=key):
                row = self.wire()
                del row[key]
                with self.assertRaises(ValueError):
                    self.parse(row)
            self.reject_field(key, [None])

    def test_legacy_aliases_are_not_accepted(self) -> None:
        for canonical, alias in (("sequence", "task_sequence"),
                                 ("observed_at_utc", "at_utc")):
            for replace in (False, True):
                with self.subTest(alias=alias, replace=replace):
                    row = self.wire()
                    row[alias] = row[canonical]
                    if replace:
                        del row[canonical]
                    with self.assertRaises(ValueError):
                        self.parse(row)

    def test_top_level_object_required(self) -> None:
        values: list[object] = [None, [], "", True, 0]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.parse(value)

    def test_sequence_exact_type_and_range(self) -> None:
        self.reject_field("sequence", [
            True, False, 7.0, Number.SEQUENCE, "7", [], {}, 0, -1, 2**53,
            float("nan"), float("inf")])
        for sequence in (1, 2**53 - 1):
            row = self.wire()
            row["sequence"] = sequence
            self.assertEqual(self.parse(row)["sequence"], sequence)

    def test_builder_rejects_noncanonical_sequence(self) -> None:
        for sequence in (True, False, Number.SEQUENCE, 0, -1, 2**53):
            with self.subTest(sequence=sequence), self.assertRaises(ValueError):
                self.build(sequence)

    def test_checkout_and_authority(self) -> None:
        self.reject_field("repo", [".", "tools/..", str(self.repo.parent), 1])
        self.reject_field("git_head", ["b" * 40, "x" * 40, "a" * 39, 1])

        for key, value in (("schema", "v2"), ("status", "RELEASED"),
                           ("machine_id", "other-machine"), ("reviewer", "root"),
                           ("task_id", "")):
            self.reject_field(key, [value])

    def test_current_utc_required(self) -> None:
        self.reject_field("observed_at_utc", [
            (self.now + timedelta(seconds=1)).isoformat(),
            (self.now - timedelta(seconds=601)).isoformat(),
            self.now.replace(tzinfo=None).isoformat(),
            self.now.astimezone(timezone(timedelta(hours=1))).isoformat(), "invalid"])
        for at in (self.now.replace(tzinfo=None),
                   self.now.astimezone(timezone(timedelta(hours=1)))):
            with self.assertRaises(ValueError):
                self.parse(self.wire(), at=at)

    def test_provenance_container_and_keys(self) -> None:
        self.reject_field("provenance", [[], {}, ["not-ref"], [self.ref] * 9])
        for missing in self.ref:
            ref: dict[str, object] = dict(self.ref)
            del ref[missing]
            self.reject_field("provenance", [[ref]])
        extra: dict[str, object] = dict(self.ref)
        extra["unexpected"] = True
        self.reject_field("provenance", [[extra]])

    def test_provenance_exact_values(self) -> None:
        for key, values in (
            ("bytes", [True, 1.0, Number.SEQUENCE, 0, -1, 2**53, "1"]),
            ("path", [None, ".", 1]),
            ("sha256", [None, "0" * 63, "G" * 64, 1]),
        ):
            for value in values:
                ref: dict[str, object] = dict(self.ref)
                ref[key] = value
                self.reject_field("provenance", [[ref]])

    def test_builder_checks_provenance(self) -> None:
        for reference in (
            m16.ExactRef(path=self.ref["path"], bytes=1,
                              sha256=self.ref["sha256"]),
            m16.ExactRef(path=self.ref["path"], bytes=self.ref["bytes"],
                              sha256="0" * 64),
        ):
            with self.assertRaises(ValueError):
                self.build(refs=[reference])

    def test_external_size_digest_pairs(self) -> None:
        sources = {f"module_{i}.py": f"# module {i}\n".encode() for i in range(26)}
        names: dict[str, object] = {Path(name).stem: None for name in sources}
        pins = m16._external_literal_pins_v1(sources, names)
        for name, (size, digest) in pins.items():
            self.assertIs(type(size), int)
            self.assertIs(type(digest), str)
            self.assertEqual(size, len(sources[name + ".py"]))
            self.assertEqual(digest, hashlib.sha256(sources[name + ".py"]).hexdigest())
        wire: object = json.loads(json.dumps(pins))
        self.assertEqual(wire, {name: list(pin) for name, pin in pins.items()})
        with self.assertRaises(ValueError):
            m16._external_literal_pins_v1(sources, {})


if __name__ == "__main__":
    unittest.main()
