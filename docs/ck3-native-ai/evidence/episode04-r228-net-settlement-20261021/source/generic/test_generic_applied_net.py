"""One bounded offline regression suite; all fixtures stay under this source lane."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import war_generic_applied_net_12004 as m

ROOT = Path(__file__).resolve().parent
RUN = Path("C:/ck3-e04-resume-20261020-a01/r15-complete-episode04-1030-a01/live-scene-r08-a02/driver-runs/desktop-3fevhd2-1c74096080--vanilla--R0228/hot-r08-repair-a02")
INPUT = m.FilePin(str(RUN / "R08-POSTLOAD-RESULT.json"), 50945, "e1e0f0f94c153b638c55848b0b2980e59eaf11e8ce1b2179b39d243a42c396c0")
STATIC = m.FilePin("C:/ck3-e04-resume-20261020-a01/r15-complete-episode04-1030-a01/source-support-a01/native-r08-static-a05/SOURCE.actual.json", 5422, m.STATIC_A05)
MACHINE = "desktop-3fevhd2-1c74096080"


def journal() -> dict[str, object]:
    root = m.obj(m.parse_json(INPUT.read()), "R228 result")
    return m.obj(m.req(root, "payment_before_disable"), "R228 journal")


def record(value: dict[str, object]) -> dict[str, object]:
    rows = m.seq(m.req(value, "records"), "records")
    row = m.obj(rows[0], "record")
    rows[0] = row
    value["records"] = rows
    return row


def projected(value: dict[str, object], window: m.Date32Window | None = None) -> m.AppliedNetProof:
    # Thin synthetic packet, never copy the 50KB original or touch its bytes.
    with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as directory:
        path = Path(directory) / "synthetic-journal.json"
        payload = json.dumps(value, separators=(",", ":"), allow_nan=False).encode()
        path.write_bytes(payload)
        pin = m.FilePin(str(path), len(payload), hashlib.sha256(payload).hexdigest())
        return m.consume_positive_applied_net(value, m.SourceBinding(MACHINE, pin, "", STATIC),
                                               strict_date32=window)


def window() -> m.Date32Window:
    raw = m.obj(m.parse_json((RUN / "r08-postload-control/prepared/BINDING.prepared.json").read_bytes()), "binding")
    expected = m.obj(m.req(raw, "expected"), "expected")
    before = m.obj(m.req(expected, "owner_binding"), "owner")
    after = deepcopy(before)
    after.update(native_revision="11", date_raw=53146896, absolute_day_raw=389454)
    return m.Date32Window(before, after)


class AppliedNetTests(unittest.TestCase):
    def test_actual_R228_financial_positive_original_unchanged(self) -> None:
        value = journal()
        proof = m.consume_positive_applied_net(value, m.SourceBinding(MACHINE, INPUT, "/payment_before_disable", STATIC))
        self.assertEqual(proof["status"], "POSITIVE_APPLIED_NET_PROVED")
        self.assertFalse(proof["date_qualified"])
        self.assertEqual(proof["callbacks"][0]["applied_net_raw"], "111391")
        self.assertEqual(proof["callbacks"][0]["context_terms_raw"]["value_28"], "273262")
        self.assertEqual(proof["callbacks"][0]["account_character_full_id"], 31254)
        self.assertEqual(proof["callbacks"][0]["observed_date_raw"], "300064548703630608")
        self.assertIsNone(proof["paid_maintenance_raw"])
        self.assertIsNone(proof["payer"])
        self.assertIsNone(proof["cadence"])
        self.assertEqual(m.parse_json(json.dumps(proof).encode()), proof)
        self.assertEqual(hashlib.sha256(INPUT.read()).hexdigest(), INPUT.sha256)
        with (ROOT / "R228-FINANCIAL-PROOF.actual.json").open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(proof, stream, indent=2)
            stream.write("\n")

    def test_amount_account_unwind_and_order_counterexamples(self) -> None:
        for mutation in ("amount", "wrapper", "formula", "unwind", "returned", "order", "float", "missing"):
            value = journal()
            row = record(value)
            if mutation == "amount":
                row["amount_raw"] = 111392
            elif mutation == "wrapper":
                row["receiver"] = 2857148843376
            elif mutation == "formula":
                ctx = m.obj(row["generic_wallet_context_v1"], "context")
                before = m.obj(ctx["before"], "context before")
                before["value_28"] = 273261
                ctx["before"] = before
                row["generic_wallet_context_v1"] = ctx
            elif mutation == "unwind":
                ctx = m.obj(row["generic_wallet_context_v1"], "context")
                trace = m.obj(ctx["parent_trace"], "trace")
                trace["parent_return_rva"] = 42957114
                ctx["parent_trace"] = trace
                row["generic_wallet_context_v1"] = ctx
            elif mutation == "returned":
                row["original_returned"] = False
            elif mutation == "order":
                row["returned_event"] = deepcopy(row["entry_event"])
            elif mutation == "float":
                after = m.obj(row["after"], "after")
                after["character_id"] = 31254.0
                row["after"] = after
            else:
                del row["amount_raw"]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                projected(value)

    def test_absent_callback_is_unknown_and_wrong_scalar_types_reject(self) -> None:
        value = journal()
        value["records"] = []
        sampling = m.obj(value["sampling"], "sampling")
        sampling["retained_records"] = 0
        value["sampling"] = sampling
        proof = projected(value)
        self.assertEqual(proof["status"], "NO_GENERIC_CALLBACK_EVIDENCE")
        self.assertEqual(proof["callbacks"], [])
        self.assertIsNone(proof["paid_maintenance_raw"])
        for invalid in (True, 111391.0, None):
            value = journal()
            record(value)["amount_raw"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                projected(value)
        with self.assertRaises(ValueError):
            m.parse_json(b'{"pid":1,"pid":2}')

    def test_date64_remains_pending_and_preserves_financial_proof(self) -> None:
        proof = projected(journal(), window())
        self.assertEqual(proof["status"], "POSITIVE_APPLIED_NET_PROVED")
        self.assertEqual(proof["date_status"], "PENDING")
        self.assertFalse(proof["date_qualified"])
        with self.assertRaises(m.Date32Pending):
            m.require_strict_date32(proof)

    def test_synthetic_date32_outer_revisions_bracket_not_equal(self) -> None:
        value = journal()
        row = record(value)
        for key in ("session_entry", "session_return"):
            item = m.obj(row[key], key)
            item["native_date_raw"] = 53146896
            row[key] = item
        current = m.obj(value["current_session"], "current")
        current["native_date_raw"] = 53146896
        value["current_session"] = current
        entry = m.session(row["session_entry"])
        returned = m.session(row["session_return"])
        m.validate_date32_window(window(), entry, returned, 2856849619424, m.session(current))
        proof = projected(value, window())
        self.assertEqual(proof["date_status"], "PENDING")
        self.assertIn("loaded-new-DLL", proof["date_diagnostic"] or "")
        for revision in ("8", "09", True):
            bad = m.obj(window().after_owner, "after")
            bad["native_revision"] = revision
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                m.validate_date32_window(m.Date32Window(window().before_owner, bad),
                                        entry, returned, 2856849619424, m.session(current))
        missing = m.obj(window().after_owner, "after")
        del missing["date_raw"]
        with self.assertRaises(ValueError):
            m.validate_date32_window(m.Date32Window(window().before_owner, missing),
                                    entry, returned, 2856849619424, m.session(current))

    def test_strict_requires_OS_original_and_exact_build_DLL_output(self) -> None:
        current = m.session(m.req(journal(), "current_session"))
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as directory:
            base = Path(directory)

            def packet(name: str, value: dict[str, object]) -> m.FilePin:
                path = base / name
                payload = json.dumps(value, separators=(",", ":"), allow_nan=False).encode()
                path.write_bytes(payload)
                return m.FilePin(str(path), len(payload), hashlib.sha256(payload).hexdigest())

            old_dll = m.FilePin(str(base / "build-a01/xar_ck3_bridge.dll"), 1, "b" * 64)
            absent = m.FilePin(str(base / "absent.json"), 1, "c" * 64)
            repeated = m.RuntimeIdentity(current.pid, str(current.birth), old_dll, old_dll,
                                         ("1", "2"), ("1", "2"), absent,
                                         build_output_receipt=absent)
            with self.subTest(case="caller repetition is not OS evidence"):
                with self.assertRaisesRegex(m.Date32Pending, "actual OS loaded-new-DLL"):
                    m.runtime_date32(repeated, current, MACHINE)

            build = packet("synthetic-build.json", {
                "machine_id": MACHINE, "original_Popen": True, "original_wait": True,
                "pid": 123, "created": "134370000000000001", "returncode": 0})
            output = packet("synthetic-output.json", {
                "schema": "xar.date32.build-output.v1", "machine_id": MACHINE,
                "producer_original_wait": build.wire(),
                "bridge_DLL": m.FilePin(old_dll.path, 1, "a" * 64).wire()})
            os_receipt = packet("synthetic-os.json", {})
            mismatched = m.RuntimeIdentity(current.pid, str(current.birth), old_dll, old_dll,
                                           ("1", "2"), ("1", "2"), build,
                                           os_loaded_module_receipt=os_receipt,
                                           build_output_receipt=output)
            with self.subTest(case="successful producer cannot qualify old DLL"):
                with self.assertRaisesRegex(ValueError, "actual output DLL differs"):
                    m.runtime_date32(mismatched, current, MACHINE)


if __name__ == "__main__":
    (ROOT / "tmp").mkdir(exist_ok=True)
    unittest.main()
