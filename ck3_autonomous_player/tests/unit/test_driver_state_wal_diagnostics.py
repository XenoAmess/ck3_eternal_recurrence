"""WAL cache and JSON publication diagnostics; synthetic Driver, no Game/RPC.

Set XAR_WAL_DIAGNOSTIC_ACTUAL_WAL and its SHA256 to additionally check a
reviewed small journal in RAM. Its base is never read by this test module.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import asdict, fields
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import driver_state_wal_v1 as wal
from xar_autoplayer.bridge import native_driver as nd
from xar_autoplayer.player_heir_fixed_dynasty_projection_v1 import (
    FixedDynastyCandidateProjectionV1,
)

# Reuse the existing tiny NativeDriver fixture, without importing a test suite
# through a generated module or making a second source file.
_fixture_path = Path(__file__).with_name("test_driver_state_wal_production_v1.py")
_fixture = ModuleType("_wal_diagnostic_existing_fixture")
_fixture.__file__ = str(_fixture_path)
exec(compile(_fixture_path.read_bytes(), str(_fixture_path), "exec"), vars(_fixture))


def projection():
    return asdict(FixedDynastyCandidateProjectionV1(
        "positive_witness", "one_living_native_player_heir_in_fixed_D0",
        717, 31, True, True, 1, None, (70, 100)))


class WalDiagnostics(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="wal-json-diagnostic-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def active_with_projection(self):
        obj = _fixture.driver(self.root)
        obj._persist_driver_state(persistence_reason="diagnostic_initial")
        obj._record_command("query-campaign-root-context-v1", ok=True, result={
            "player_heir_fixed_dynasty_projection_v1": projection(),
        })
        _fixture.record_day(obj)
        path = obj._native_driver_state_path()
        self.assertIsNone(obj._driver_state_error)
        self.assertEqual(json.loads(path.read_bytes())["format_version"], 3)
        self.assertIs(type(obj._command_history[0]["result"][
            "player_heir_fixed_dynasty_projection_v1"]["H_interval"]), tuple)
        return obj, path, path.with_name(wal.FILENAME)

    def test_real_dto_append_cache_equals_published_json(self):
        obj, _, journal = self.active_with_projection()
        disk = json.loads(journal.read_bytes())
        self.assertEqual(obj._driver_state_wal_document, disk)
        self.assertIs(type(disk["entries"][0]["history_rows"][0]["result"][
            "player_heir_fixed_dynasty_projection_v1"]["H_interval"]), list)
        self.assertEqual(wal._validated_entries(disk)[2], 2)

    def test_real_native_driver_full_barrier_with_tuple_dto(self):
        obj, path, journal = self.active_with_projection()
        obj._persist_driver_state(persistence_reason="diagnostic_DTO_full_barrier")
        self.assertIsNone(obj._driver_state_error)
        self.assertFalse(journal.exists())
        stored = json.loads(path.read_bytes())
        self.assertEqual(stored["format_version"], 2)
        self.assertEqual(stored["command_history"],
                         json.loads(json.dumps(obj._command_history)))
        self.assertEqual(obj._driver_state_wal_committed_rows, 2)
        self.assertEqual(wal.load_pair(path)[1], "base_only")

    def test_subsequent_eligible_append_with_tuple_dto(self):
        obj, path, journal = self.active_with_projection()
        base = path.read_bytes()
        _fixture.record_day(obj, 2424)
        self.assertIsNone(obj._driver_state_error)
        self.assertEqual(path.read_bytes(), base)
        self.assertEqual(obj._driver_state_wal_document, json.loads(journal.read_bytes()))
        self.assertEqual(wal._validated_entries(obj._driver_state_wal_document)[2], 3)

    def test_appended_cache_owns_json_values(self):
        obj, _, _ = self.active_with_projection()
        document = obj._driver_state_wal_document
        rows = [{"index": 3, "command": "query-small-readonly", "ok": True,
                 "result": {"nested": [(1, 2)]}}]
        scalars = obj._driver_state_wal_scalar_fields_locked_v1()
        result = wal.append_delta(document, rows, scalars)
        before = wal._canonical(result)
        rows[0]["result"]["nested"].append((3, 4))
        scalars["campaign_goal"] = {"unexpected": True}
        document["entries"][0]["history_rows"][0]["ok"] = False
        self.assertEqual(wal._canonical(result), before)
        self.assertEqual(result, json.loads(before))
        self.assertEqual(wal._validated_entries(result)[2], 3)

    def test_real_journal_tamper_still_refuses_full_barrier(self):
        obj, path, journal = self.active_with_projection()
        base = path.read_bytes()
        document = json.loads(journal.read_bytes())
        document["entries"][0]["history_rows"][0]["result"][
            "player_heir_fixed_dynasty_projection_v1"]["H_interval"] = [0, 100]
        changed = wal._canonical(document)
        journal.write_bytes(changed)
        obj._persist_driver_state(persistence_reason="diagnostic_tampered_pair")
        self.assertEqual(obj._driver_state_error,
                         "ValueError: Driver WAL pair changed; full barrier refused")
        self.assertEqual(path.read_bytes(), base)
        self.assertEqual(journal.read_bytes(), changed)
        with self.assertRaisesRegex(wal.JournalInvalid, "checksum mismatch"):
            wal._validated_entries(document)

    def test_real_base_identity_change_still_refuses_full_barrier(self):
        obj, path, journal = self.active_with_projection()
        base, journal_bytes = path.read_bytes(), journal.read_bytes()
        previous = wal.base_stat_identity(path)
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1000000000))
        self.assertNotEqual(wal.base_stat_identity(path), previous)
        obj._persist_driver_state(persistence_reason="diagnostic_changed_base")
        self.assertEqual(obj._driver_state_error,
                         "ValueError: Driver WAL pair changed; full barrier refused")
        self.assertEqual(path.read_bytes(), base)
        self.assertEqual(journal.read_bytes(), journal_bytes)

    def test_marker_and_delta_capacity_guards_remain(self):
        obj, _, _ = self.active_with_projection()
        document = obj._driver_state_wal_document
        rows = [{"index": 3, "command": "query-small-readonly", "ok": True}]
        scalars = obj._driver_state_wal_scalar_fields_locked_v1()
        marked = wal.mark_consolidation(document, b"synthetic-full-barrier")
        with self.assertRaisesRegex(wal.JournalInvalid, "marker forbids"):
            wal.append_delta(marked, rows, scalars)
        with patch.object(wal, "MAX_DELTA_BYTES", 1):
            with self.assertRaises(wal.JournalCapacity):
                wal.append_delta(document, rows, scalars)
        with patch.object(wal, "MAX_JOURNAL_BYTES", 1):
            with self.assertRaises(wal.JournalCapacity):
                wal.append_delta(document, rows, scalars)
        with self.assertRaisesRegex(wal.JournalInvalid, "contiguously"):
            wal.append_delta(document, [{**rows[0], "index": 4}], scalars)

    def test_completed_marker_cleanup_retry_with_dto(self):
        obj, path, journal = self.active_with_projection()
        unlink = Path.unlink

        def deny_marker(target, *args, **kwargs):
            if target == journal:
                raise PermissionError("synthetic marker cleanup denial")
            return unlink(target, *args, **kwargs)

        with patch.object(Path, "unlink", deny_marker):
            obj._persist_driver_state(persistence_reason="diagnostic_cleanup_denied")
        self.assertIsNone(obj._driver_state_error)
        self.assertEqual(wal.load_pair(path)[1], "already_consolidated")
        self.assertEqual(obj._driver_state_wal_document, json.loads(journal.read_bytes()))
        obj._persist_driver_state(persistence_reason="diagnostic_cleanup_retry")
        self.assertIsNone(obj._driver_state_error)
        self.assertFalse(journal.exists())
        self.assertEqual(wal.load_pair(path)[1], "base_only")

    @unittest.skipUnless(os.environ.get("XAR_WAL_DIAGNOSTIC_ACTUAL_WAL"),
                         "optional reviewed actual small-WAL diagnostic")
    def test_reviewed_actual_small_wal_exact_bytes_in_ram(self):
        path = Path(os.environ["XAR_WAL_DIAGNOSTIC_ACTUAL_WAL"])
        self.assertLessEqual(path.stat().st_size, 65536)
        raw = path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         os.environ["XAR_WAL_DIAGNOSTIC_ACTUAL_SHA256"])
        document = json.loads(raw)
        entries, _, last = wal._validated_entries(document)
        self.assertEqual(len(entries), 1)
        rows = copy.deepcopy(entries[0]["history_rows"])
        record = next(row for row in rows if
                      "player_heir_fixed_dynasty_projection_v1" in row.get("result", {}))
        dto = record["result"]["player_heir_fixed_dynasty_projection_v1"]
        names = {field.name for field in fields(FixedDynastyCandidateProjectionV1)}
        reconstructed = FixedDynastyCandidateProjectionV1(**{
            key: tuple(dto[key]) if key == "H_interval" else dto[key] for key in names})
        record["result"]["player_heir_fixed_dynasty_projection_v1"] = {
            **dto, **asdict(reconstructed)}
        header = {**document, "entries": []}
        actual = wal.append_delta(header, rows, copy.deepcopy(entries[0]["state_fields"]))
        self.assertEqual(wal._canonical(actual), raw)
        self.assertEqual(actual, document)
        self.assertEqual(wal._validated_entries(actual)[2], last)
        # This reproduction reads only the small journal, never its large base.


if __name__ == "__main__":
    unittest.main()
