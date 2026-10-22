"""In-memory execution of the real continuity reducers and admission boundary."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import hashlib
from pathlib import Path
from typing import Iterator, Protocol, runtime_checkable
import unittest

from tools.g2_saved_campaign import current_saved_continuity_v1 as continuity
from tools.g2_saved_campaign import root_continuity_window as actual_ledger
from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner
from tools.g2_saved_campaign.current_saved_basis_v1 import (
    CampaignOriginV1, ExactRefV1, JsonObject, JsonValue, canonical_json_v1, integer,
    json_object, parse_json, need,
)
from tools.g2_saved_campaign.file_stat_identity_v1 import FileStatIdentityV1
from tools.g2_saved_campaign.test_current_saved_basis_v1 import MACHINE, pure_basis

AT = "2026-10-21T19:00:00Z"
ROOT = Path("/synthetic-continuity-no-io").resolve()
CANONICAL = ROOT / "ROOT-CONTINUITY-WINDOW.json"
EVENTS = ROOT / "ROOT-CONTINUITY-WINDOW-EVENTS"


@runtime_checkable
class ActualReducerV1(Protocol):
    def __call__(self, previous: object, kind: str, details: JsonObject) -> object: ...


@runtime_checkable
class EmittedMainV1(Protocol):
    def __call__(self, first_control_sequence: int, *, qualify: bool = False) -> None: ...


@runtime_checkable
class LedgerConstructorV1(Protocol):
    def __call__(self, path: Path) -> object: ...


@runtime_checkable
class ForwardWriterV1(Protocol):
    def apply(self, kind: str, details: JsonObject) -> object: ...


def reducer(previous: object, kind: str, details: JsonObject) -> JsonObject:
    function: object = actual_ledger.transition
    if not isinstance(function, ActualReducerV1):
        raise TypeError("the actual ledger reducer is required")
    return json_object(function(previous, kind, details))


class MemoryReader:
    def __init__(self) -> None:
        self.documents: dict[str, continuity.PinnedContinuityDocumentV1] = {}
        self.probes = 0

    def put(self, path: Path, value: object) -> ExactRefV1:
        raw = canonical_json_v1(value)
        ref = ExactRefV1(str(path.resolve()), len(raw), hashlib.sha256(raw).hexdigest())
        self.documents[str(path.resolve())] = continuity.PinnedContinuityDocumentV1(
            ref, FileStatIdentityV1(len(raw), str(len(self.documents) + 1), "1"), raw)
        return ref

    def probe(self, path: str, limit: int) -> continuity.PinnedContinuityDocumentV1 | None:
        self.probes += 1
        document = self.documents.get(str(Path(path).resolve()))
        if document is not None and document.reference.bytes > limit:
            raise ValueError("bounded metadata")
        return document

    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        document = self.probe(reference.path, limit)
        if document is None or document.reference != reference:
            raise ValueError("exact memory source")
        return document.payload

    def stat(self, path: str) -> FileStatIdentityV1:
        return self.documents[str(Path(path).resolve())].identity


def state() -> JsonObject:
    return {
        "schema": "root.ck3.continuity-window/v1", "machine_id": MACHINE,
        "sequence": 225, "window_id": 2, "status": "running",
        "start_date_raw": 100, "target_date_raw": 100 + 10958 * 24,
        "target_days": 10958, "last_settled_cycles": 18,
        "last_settled_date_raw": 124, "game_binding": {"pid": 11, "creation_date": "old"},
        "cold_handoff_count": 11, "manual_repair_count": 15,
        "automatic_recovery_count": 0, "binding_lineage_count": 0,
        "unknown_requests": [7, 86],
    }


def verified(predecessor: JsonObject, token: str = "b") -> owner.CurrentSavedFeederV1:
    original = pure_basis()
    count = max(original.completed_cycles, integer(predecessor["last_settled_cycles"]))
    basis = replace(original,
        completed_cycles=count,
        origin=CampaignOriginV1(100, 100 + 10958 * 24, 10958,
            original.origin.original_wall_origin_utc, original.origin.campaign_id),
        progress=replace(original.progress,
            settled_cycles=count,
            ledger_cycles=integer(predecessor["last_settled_cycles"]),
            ledger_date_raw=integer(predecessor["last_settled_date_raw"])))
    reference = ExactRefV1(str(ROOT / (token + "-basis.json")), 1, token * 64)
    game = owner.CurrentGameIdentityV1(22, "123", "new")
    closed = owner.ClosedEpochV1(reference,
        owner.CurrentGameIdentityV1(11, "122", "old"), 103, (), AT, "synthetic-pipe")
    inputs = owner.CurrentSavedColdInputsV1(basis, {}, {}, {}, predecessor,
                                          closed, reference, reference)
    sources = owner.WarmSourceRefsV1(*(reference for _ in range(6)))
    proof = owner.WarmBoundProofV1(MACHINE, reference, reference, reference,
        basis.driver_identity, sources, game, basis.frame, (), 1,
        basis.driver_identity, "a" * 64, 1, True, AT)
    return owner.CurrentSavedFeederV1(inputs, proof,
        {"feeder_source_ref": reference.to_wire()}, basis.frame, game, reference, reference)


def cold_reducer(checked: owner.CurrentSavedFeederV1) -> continuity.ContinuityReducerV1:
    from tools.g2_saved_campaign.current_saved_campaign_feeder_v1 import make_current_saved_transition_v1
    return make_current_saved_transition_v1(reducer, verified=checked)


def commit_memory(reader: MemoryReader, previous: JsonObject, kind: str,
                  details: JsonObject, function: continuity.ContinuityReducerV1) -> JsonObject:
    # Run the actual reducer; this is the original writer envelope, no disk writer.
    after = function(previous, kind, details)
    identity = continuity.continuity_digest_v1({"kind": kind, "details": details})
    sequence = integer(previous["sequence"]) + 1
    after.update(sequence=sequence, last_event_identity=identity)
    reader.put(EVENTS / f"{sequence:08d}.json", {
        "sequence": sequence, "at_utc": AT, "kind": kind, "details": details,
        "identity": identity, "previous_sha256": continuity.continuity_digest_v1(previous),
        "after": after})
    key = continuity.continuity_digest_v1({"kind": kind, "evidence_id": details["evidence_id"]})
    reader.put(EVENTS / ("source-" + key + ".json"), {"sequence": sequence, "identity": identity})
    return after


def fixture() -> tuple[MemoryReader, ExactRefV1, JsonObject]:
    reader = MemoryReader()
    anchor = state()
    reference = reader.put(ROOT / "frozen225.json", anchor)
    checked = verified(anchor, "a")
    after = commit_memory(reader, anchor, owner.CURRENT_SAVED_COLD_KIND,
                          checked.expected_transition(), cold_reducer(checked))
    for number, cycles in ((227, 22), (228, 22)):
        after = commit_memory(reader, after, "repair_required", {
            "evidence_id": "synthetic-failure-" + str(number),
            "source": {"path": "/synthetic/original-evidence"},
            "frame": checked.opening.to_wire(), "completed_cycles": cycles,
            "reason": "original failure retained"}, reducer)
    reader.put(CANONICAL, after)
    return reader, reference, after


def view(reader: MemoryReader, anchor: ExactRefV1) -> continuity.ContinuityReadViewV1:
    return continuity.read_continuity_view_v1(canonical_path=CANONICAL, anchor_ref=anchor,
        expected_machine_id=MACHINE, reader=reader)


class ContinuityContractTests(unittest.TestCase):
    def test_actual_cold_then_real_fsm_225_to_228_and_stale_predecessor(self) -> None:
        reader, anchor, head = fixture()
        before = dict(reader.documents)
        current = view(reader, anchor)
        self.assertEqual((current.anchor_sequence, current.head_sequence), (225, 228))
        self.assertEqual(current.head_state, head)
        self.assertTrue(current.ready)
        self.assertEqual(len(current.event_refs), 3)
        stale = verified(state())
        with self.assertRaisesRegex(ValueError, "exact frozen predecessor"):
            continuity.dry_run_attachment_v1(current, kind=owner.CURRENT_SAVED_COLD_KIND,
                details=stale.expected_transition(), reducer=cold_reducer(stale),
                reducer_sources=(anchor,))
        self.assertEqual(reader.documents, before)

    def test_real_reducer_dryrun_and_writer_lock_predecessor_check(self) -> None:
        reader, anchor, _ = fixture()
        current = view(reader, anchor)
        checked = verified(current.head_state)
        wrapped = cold_reducer(checked)
        result = continuity.dry_run_attachment_v1(current, kind=owner.CURRENT_SAVED_COLD_KIND,
            details=checked.expected_transition(), reducer=wrapped, reducer_sources=(anchor,))
        self.assertEqual(result.committed_state["sequence"], 229)
        self.assertEqual(result.committed_state["cold_handoff_count"], 13)
        self.assertEqual(result.committed_state["unknown_requests"], [7, 86])
        self.assertEqual(result.committed_state["start_date_raw"], 100)
        function = continuity.checked_attachment_reducer_v1(wrapped, attachment=result, reader=reader)
        self.assertEqual(function(current.head_state, result.kind, result.details), result.reduced_state)
        changed = {**current.head_state, "sequence": 229}
        with self.assertRaisesRegex(ValueError, "changed after qualification"):
            function(changed, result.kind, result.details)

    def test_recovered_view_never_repairs_snapshot_or_missing_index(self) -> None:
        reader, anchor, _ = fixture()
        reader.put(CANONICAL, state())
        index_path = next(key for key in reader.documents if "source-" in key)
        del reader.documents[index_path]
        before = dict(reader.documents)
        recovered = view(reader, anchor)
        self.assertEqual(recovered.head_sequence, 228)
        self.assertFalse(recovered.ready)
        self.assertTrue(recovered.snapshot_needs_recovery)
        self.assertEqual(len(recovered.missing_source_indexes), 1)
        with self.assertRaisesRegex(ValueError, "metadata recovery required"):
            continuity.dry_run_attachment_v1(recovered, kind="repair_required",
                details={"evidence_id": "no-write", "source": "actual"}, reducer=reducer,
                reducer_sources=(anchor,))
        self.assertEqual(reader.documents, before)

    def test_chain_tamper_gap_index_type_and_machine_rejected(self) -> None:
        for change in ("digest", "gap", "index", "machine", "sequence"):
            with self.subTest(change=change):
                reader, anchor, _ = fixture()
                path = EVENTS / "00000227.json"
                original = reader.documents[str(path.resolve())].value()
                if change == "gap":
                    del reader.documents[str(path.resolve())]
                elif change == "index":
                    key = next(key for key in reader.documents if "source-" in key)
                    value = reader.documents[key].value()
                    reader.put(Path(key), {**value, "sequence": True})
                else:
                    if change == "digest": original["previous_sha256"] = "b" * 64
                    if change == "machine":
                        after = json_object(original["after"])
                        after["machine_id"] = "other-machine"
                        original["after"] = after
                    if change == "sequence": original["sequence"] = 227.0
                    reader.put(path, original)
                with self.assertRaises(ValueError):
                    view(reader, anchor)

    def test_binding_roundtrip_revalidates_actual_sources(self) -> None:
        reader, anchor, _ = fixture()
        current = view(reader, anchor)
        wire = parse_json(canonical_json_v1(current.to_wire()))
        self.assertEqual(continuity.validate_continuity_binding_v1(
            wire, expected_machine_id=MACHINE, reader=reader), current)
        changed = current.to_wire()
        changed["ready"] = False
        with self.assertRaises(ValueError):
            continuity.validate_continuity_binding_v1(
                changed, expected_machine_id=MACHINE, reader=reader)

    def test_closed_gate_rejects_stale_anchor_even_matching_business_counts(self) -> None:
        reader, anchor, _ = fixture()
        current = view(reader, anchor)
        original = verified(current.head_state).inputs.basis
        basis = replace(original, completed_cycles=22,
            progress=replace(original.progress, settled_cycles=22))
        with self.assertRaisesRegex(ValueError, "stale continuity predecessor"):
            continuity.validate_closed_continuity_frontier_v1(basis.to_wire(), current)
        new_anchor = reader.put(ROOT / "closed228.json", current.head_state)
        ready = view(reader, new_anchor)
        updated = replace(basis, refs=replace(basis.refs, ledger=new_anchor))
        continuity.validate_closed_continuity_frontier_v1(updated.to_wire(), ready)



    def test_emitted_qualify_executes_actual_attachment_before_return(self) -> None:
        import ast
        import io
        import json
        from types import SimpleNamespace
        from unittest.mock import patch
        from tools.g2_saved_campaign import current_saved_campaign_feeder_v1 as feeder
        from tools.g2_saved_campaign.test_current_saved_campaign_cold_v1 import feeder_admission
        emitted = ast.parse(feeder.emit_current_saved_feeder_launcher_v1())
        nodes: list[ast.stmt] = [node for node in emitted.body
                 if isinstance(node, ast.FunctionDef) and node.name == "main"]
        self.assertEqual(len(nodes), 1)
        for stale in (True, False):
            with self.subTest(stale=stale):
                reader, anchor, _ = fixture()
                current = view(reader, anchor)
                checked = verified(state() if stale else current.head_state)
                ledger_anchor = anchor if stale else reader.put(ROOT / "closed228.json", current.head_state)
                checked = replace(checked, inputs=replace(checked.inputs,
                    basis=replace(checked.inputs.basis,
                        refs=replace(checked.inputs.basis.refs, ledger=ledger_anchor))))
                admission = feeder_admission()
                from tools.g2_saved_campaign.first_full_checkpoint_v1 import FirstFullCheckpointPolicyV1
                budget = {"machine_id": checked.inputs.basis.machine_id,
                    "review_at_utc": admission.review_deadline_utc,
                    "first_full_checkpoint_reserve": {"admissible": True, "seconds": 30,
                        "bytes": 1048576, "reservation_mode": "explicit_operator_admitted"}}
                budget_ref = reader.put(ROOT / "finalize-budget.json", budget)
                admission = replace(admission, budget_ref=budget_ref)
                policy = FirstFullCheckpointPolicyV1(checked.inputs.basis.machine_id,
                    admission.first_control_sequence, checked.inputs.basis.completed_cycles,
                    admission.review_deadline_utc, budget_ref, 30, 1048576)
                reader.put(ROOT / "ROOT-P37C23-COLD-RESUME-ADMISSION.json",
                           {"first_full_checkpoint": policy.to_wire()})
                ledger_ref = reader.put(ROOT / "ledger-source.py", {})
                output: list[str] = []
                def qualified(*args: object, **kwargs: object) -> owner.CurrentSavedFeederV1:
                    return checked
                def opened(path: Path, *args: object, **kwargs: object) -> io.BytesIO:
                    self.assertEqual(path, ROOT / "CURRENT-SAVED-FEEDER-ADMISSION.json")
                    return io.BytesIO(canonical_json_v1(admission.to_wire()))
                namespace: dict[str, object] = {
                    "N": ROOT, "Path": Path, "JsonObject": JsonObject, "json": json,
                    "__file__": str(ROOT / "launcher.py"), "owner": owner,
                    "load_current_saved_feeder_inputs_v1": lambda: owner.WarmCurrentSavedFeederInputsV1(
                        checked.inputs, checked.warm_proof),
                    "decode_current_saved_feeder_admission_v1": feeder.decode_current_saved_feeder_admission_v1,
                    "LocalCurrentSavedFeederReaderV1": feeder.LocalCurrentSavedFeederReaderV1,
                    "qualify_current_saved_feeder_v1": qualified,
                    "ordinary": SimpleNamespace(CONTINUITY_WINDOW=CANONICAL,
                        read=lambda path: json.loads(reader.documents[str(path.resolve())].payload),
                        next_sequence=lambda: admission.first_control_sequence,
                        __file__=str(ROOT / "ordinary.py")),
                    "ledger": SimpleNamespace(transition=actual_ledger.transition,
                        __file__=ledger_ref.path),
                    "integer": integer, "json_object": json_object,
                    "need": need, "utc_now_v1": lambda: AT,
                    "make_current_saved_transition_v1": feeder.make_current_saved_transition_v1,
                    "LocalContinuityReaderV1": lambda: reader,
                    "read_continuity_view_v1": continuity.read_continuity_view_v1,
                    "dry_run_attachment_v1": continuity.dry_run_attachment_v1,
                    "print": lambda value: output.append(str(value)),
                }
                exec(compile(ast.Module(body=nodes, type_ignores=[]),
                    "<actual emitted feeder main>", "exec"), namespace)
                function = namespace["main"]
                if not isinstance(function, EmittedMainV1):
                    raise TypeError("actual emitted main")
                with patch.object(Path, "open", opened):
                    if stale:
                        with self.assertRaisesRegex(ValueError, "exact frozen predecessor"):
                            function(admission.first_control_sequence, qualify=True)
                        self.assertEqual(output, [])
                    else:
                        function(admission.first_control_sequence, qualify=True)
                        self.assertEqual(len(output), 1)
                        self.assertIn("READONLY_QUALIFIED", output[0])



    def test_original_writer_apply_rechecks_advanced_head_under_lock(self) -> None:
        from unittest.mock import patch
        reader, anchor, _ = fixture()
        current = view(reader, anchor)
        checked = verified(current.head_state)
        wrapped = cold_reducer(checked)
        preview = continuity.dry_run_attachment_v1(current,
            kind=owner.CURRENT_SAVED_COLD_KIND, details=checked.expected_transition(),
            reducer=wrapped, reducer_sources=(anchor,))
        advanced = commit_memory(reader, current.head_state, "repair_required",
            {"evidence_id": "another-committed-event", "source": "original",
             "frame": checked.opening.to_wire(), "completed_cycles": 22, "reason": "actual"},
            reducer)
        reader.put(CANONICAL, advanced)
        before = dict(reader.documents)
        entered: list[bool] = []
        writes: list[Path] = []
        @contextmanager
        def lock(instance: object) -> Iterator[None]:
            entered.append(True)
            yield
        def read(path: Path) -> JsonObject:
            self.assertTrue(entered)
            return reader.documents[str(path.resolve())].value()
        def atomic(path: Path, value: object, replace: bool = False) -> None:
            writes.append(path)
            raise AssertionError("writer must reject before any commit")
        constructor: object = actual_ledger.WindowLedger
        if not isinstance(constructor, LedgerConstructorV1):
            raise TypeError("actual WindowLedger constructor")
        writer = constructor(CANONICAL)
        if not isinstance(writer, ForwardWriterV1):
            raise TypeError("actual WindowLedger writer")
        with patch.object(actual_ledger.WindowLedger, "locked", lock), \
             patch.object(Path, "mkdir", lambda *args, **kwargs: None), \
             patch.object(Path, "exists", lambda path: str(path.resolve()) in reader.documents), \
             patch.object(actual_ledger, "read_small", read), \
             patch.object(actual_ledger, "_atomic", atomic), \
             patch.object(actual_ledger, "transition",
                 continuity.checked_attachment_reducer_v1(wrapped, attachment=preview, reader=reader)):
            with self.assertRaisesRegex(ValueError, "changed after qualification"):
                writer.apply(preview.kind, preview.details)
        self.assertTrue(entered)
        self.assertEqual(writes, [])
        self.assertEqual(reader.documents, before)

    def test_formal_forward_builder_json_and_distinct_new_authority(self) -> None:
        from tools.g2_saved_campaign import current_saved_campaign_feeder_v1 as feeder
        from tools.g2_saved_campaign.test_current_saved_campaign_cold_v1 import feeder_admission
        reader, anchor, _ = fixture()
        original = feeder_admission()
        original = replace(original, review_deadline_utc="2026-10-21T20:30:00Z")
        old_spec = reader.put(ROOT / "old-spec.json", {"nonce": original.feeder_task_nonce})
        original = replace(original, feeder_task_spec_ref=old_spec)
        old_ref = reader.put(ROOT / "original-admission.json", original.to_wire())
        source = reader.put(ROOT / "new-controller.py", {"source": "new"})
        spec = reader.put(ROOT / "new-spec.json", {"nonce": "5" * 32})
        closed = reader.put(ROOT / "old-CLOSED.json", {"machine_id": MACHINE,
            "nonce": original.feeder_task_nonce, "spec_sha256": old_spec.sha256,
            "job_active_after_stage": 0, "child_exit_code": 1, "bootstrap_exit_code": 1})
        failure = reader.put(ROOT / "old-error.json", {"machine_id": MACHINE,
            "status": "feeder_error_review_required", "error_type": "ValueError",
            "error": "exact frozen predecessor"})
        next_ref = reader.put(ROOT / "NEXT-SEQUENCE-P37.json",
                              {"next_sequence": original.first_control_sequence})
        binding = reader.put(ROOT / "binding.json", view(reader, anchor).to_wire())
        result = feeder.build_current_saved_warm_forward_admission_v1(
            original_admission_ref=old_ref, continuity_binding_ref=binding,
            continuity_source_ref=source, previous_task_closed_ref=closed,
            failure_ref=failure, next_ref=next_ref, sdk_pair_ref=anchor,
            controller_source_ref=source, controller_spec_ref=spec, budget_ref=anchor,
            runtime_root=ROOT, admission_path=ROOT / "forward.json",
            observed_at_utc=AT, review_deadline_utc="2026-10-21T20:30:00Z",
            expected_machine_id=MACHINE, reader=reader)
        parsed = feeder.parse_current_saved_warm_forward_admission_v1(
            parse_json(feeder.canonical_forward_bytes_v1(result)), expected_machine_id=MACHINE)
        self.assertEqual(parsed, result)
        self.assertEqual(parsed.original_admission_ref, old_ref)
        self.assertEqual(parsed.feeder_admission.actual_game_ref, original.actual_game_ref)
        self.assertEqual(parsed.feeder_admission.basis_ref, original.basis_ref)
        self.assertNotEqual(parsed.feeder_admission.feeder_source_ref, original.feeder_source_ref)
        for key, bad in (("ordinary_cycle_credit", True), ("game_day_credit", 0.0),
                         ("original_actions_replayed", True)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                feeder.parse_current_saved_warm_forward_admission_v1(
                    {**result.to_wire(), key: bad}, expected_machine_id=MACHINE)
        self.assertEqual(reader.documents[str(Path(old_ref.path).resolve())].value(), original.to_wire())


class ContinuityMetadataForwardTests(unittest.TestCase):
    def fixture(self) -> tuple[object, owner.CurrentSavedColdInputsV1,
                               continuity.ContinuityReadViewV1, ExactRefV1, ExactRefV1]:
        from unittest.mock import patch
        from tools.g2_saved_campaign import current_saved_basis_v1 as basis_api
        from tools.g2_saved_campaign.test_current_saved_basis_v1 import (
            EpochMemoryReader, ReadonlyPrefixUnknownFixture,
        )
        original_put = EpochMemoryReader.put
        def put(instance: EpochMemoryReader, name: str, value: object) -> ExactRefV1:
            if name == "original-ledger.json":
                # The existing business fixture predates ledger metadata. Supply
                # that production boundary before its refs/closed proofs freeze.
                value = {**json_object(value), "schema": "root.ck3.continuity-window/v1",
                    "sequence": 225, "window_id": 2, "status": "running",
                    "cold_handoff_count": 11,
                    "game_binding": json_object({"pid": 11, "creation_date": "old"})}
            return original_put(instance, name, value)
        with patch.object(EpochMemoryReader, "put", put):
            f = ReadonlyPrefixUnknownFixture()
        basis, basis_ref, qualification = f.build()
        reader = f.reader
        qualification_ref = reader.put("forward-original-qualification.json", qualification.to_wire())
        inputs = owner.validate_current_saved_cold_inputs_v1(basis,
            basis_ref=basis_ref, validation_ref=qualification_ref, reader=reader)
        memory = MemoryReader()
        raw = reader.raw[basis.refs.ledger.path]
        memory.documents[str(Path(basis.refs.ledger.path).resolve())] = continuity.PinnedContinuityDocumentV1(
            basis.refs.ledger, FileStatIdentityV1(len(raw), "100", "1"), raw)
        game = owner.CurrentGameIdentityV1(128, "134370765451291730", "new-managed-game")
        sources = owner.WarmSourceRefsV1(*(basis_ref for _ in range(6)))
        proof = owner.WarmBoundProofV1(MACHINE, basis_ref, qualification_ref,
            basis.refs.driver, basis.driver_identity, sources, game, basis.frame, (), 1,
            basis.driver_identity, "a" * 64, 1, True, AT)
        checked = owner.CurrentSavedFeederV1(inputs, proof,
            {"feeder_source_ref": basis_ref.to_wire()}, basis.frame, game, basis_ref, basis_ref)
        head = commit_memory(memory, inputs.old_ledger, owner.CURRENT_SAVED_COLD_KIND,
            checked.expected_transition(), cold_reducer(checked))
        memory.put(CANONICAL, head)
        current = view(memory, basis.refs.ledger)
        for doc in memory.documents.values():
            if doc.reference != basis.refs.ledger:
                reader.raw[doc.reference.path] = doc.payload
            reader.identities[doc.reference.path] = doc.identity
        binding_ref = reader.put("forward-binding.json", current.to_wire())
        head_path = "/epoch/forward-retained-ledger.json"
        head_raw = memory.read(current.snapshot_ref, 65536)
        reader.raw[head_path] = head_raw
        head_ref = ExactRefV1(head_path, len(head_raw), hashlib.sha256(head_raw).hexdigest())
        forward = basis_api.CurrentSavedContinuityForwardV1(MACHINE, AT, basis_ref,
            qualification_ref, binding_ref, head_ref)
        forward_ref = reader.put("forward-authority.json", forward.to_wire())
        return f, inputs, current, forward_ref, qualification_ref

    def test_original_builder_through_all_four_owner_consumers(self) -> None:
        from unittest.mock import patch
        from tools.g2_saved_campaign import current_saved_basis_v1 as basis_api
        from tools.g2_saved_campaign.test_current_saved_basis_v1 import ReadonlyPrefixUnknownFixture
        fixture, old, current, forward_ref, _ = self.fixture()
        self.assertIsInstance(fixture, ReadonlyPrefixUnknownFixture)
        if not isinstance(fixture, ReadonlyPrefixUnknownFixture):
            raise TypeError("the actual business fixture")
        reader = fixture.reader
        before = dict(reader.raw)
        forward = basis_api.parse_current_saved_continuity_forward_v1(
            basis_api.evidence(reader, forward_ref), expected_machine_id=MACHINE)
        basis = basis_api.build_current_saved_continuity_forward_basis_v1(
            forward, forward_ref=forward_ref, reader=reader)
        basis_ref = reader.put("forward-basis.json", basis.to_wire())
        qualification = basis_api.build_current_saved_continuity_qualification_v1(
            basis, basis_ref=basis_ref, observed_at_utc=AT, reader=reader)
        qualification_ref = reader.put("forward-qualification.json", qualification.to_wire())
        self.assertEqual(owner.parse_basis_qualification_v1(parse_json(canonical_json_v1(
            qualification.to_wire())), expected_machine_id=MACHINE), qualification)
        inputs = owner.validate_current_saved_cold_inputs_v1(basis, basis_ref=basis_ref,
            validation_ref=qualification_ref, reader=reader)
        self.assertEqual(inputs.closed_epoch, owner._closed_epoch(basis, reader))
        self.assertEqual(inputs.closed_epoch.sdk_processes, old.closed_epoch.sdk_processes)
        self.assertEqual(inputs.closed_epoch.old_game, old.closed_epoch.old_game)
        with patch.object(owner, "LocalBasisReaderV1", return_value=reader):
            result = owner.validate_current_saved_prepared_sdk_closure_v1(
                fixture.epoch.refs.sdk_closed.to_wire(), inputs=inputs)
        self.assertIs(result["normal"], False)
        self.assertEqual(basis.progress.ledger_cycles, old.basis.completed_cycles)
        self.assertEqual(basis.unknown_requests, old.basis.unknown_requests)
        self.assertEqual((inputs.seed, inputs.governance, basis.refs.driver, basis.refs.save),
            (old.seed, old.governance, old.basis.refs.driver, old.basis.refs.save))
        self.assertEqual(basis_api.decode_current_saved_basis_v1(
            basis_api.encode_current_saved_basis_v1(basis), expected_machine_id=MACHINE), basis)
        # Historical metadata must not reread a mutable canonical old SHA.
        reader.raw[current.snapshot_ref.path] = b"canonical legitimately advanced"
        owner.validate_current_saved_cold_inputs_v1(basis, basis_ref=basis_ref,
            validation_ref=qualification_ref, reader=reader)
        for ref in (fixture.epoch.refs.raw_state, fixture.epoch.refs.unknown_response,
                    fixture.epoch.refs.unknown_inflight):
            self.assertEqual(reader.raw[ref.path], before[ref.path])
        self.assertNotIn(basis.refs.driver.path, reader.read_paths)
        self.assertNotIn(basis.refs.save.path, reader.read_paths)

    def test_forward_rejects_business_credit_types_and_mutable_head(self) -> None:
        from unittest.mock import patch
        from tools.g2_saved_campaign import current_saved_basis_v1 as basis_api
        from tools.g2_saved_campaign.test_current_saved_basis_v1 import ReadonlyPrefixUnknownFixture
        fixture, old, current, forward_ref, _ = self.fixture()
        if not isinstance(fixture, ReadonlyPrefixUnknownFixture):
            raise TypeError("the actual business fixture")
        reader = fixture.reader
        forward = basis_api.parse_current_saved_continuity_forward_v1(
            basis_api.evidence(reader, forward_ref), expected_machine_id=MACHINE)
        for reference in (current.anchor_ref, current.event_refs[0], current.source_indexes[0].reference):
            identity = reader.identities[reference.path]
            reader.identities[reference.path] = replace(identity, file_id="999999999999999999")
            with self.assertRaisesRegex(ValueError, "immutable continuity source identity"):
                basis_api._continuity_forward_head_v1(forward, old.basis, reader=reader)
            reader.identities[reference.path] = identity
        event = current.event_refs[0]
        identity = reader.identities[event.path]
        original_read = reader.read
        def read_then_replace(reference: ExactRefV1, limit: int) -> bytes:
            raw = original_read(reference, limit)
            if reference == forward.ledger_ref:
                reader.identities[event.path] = replace(identity, file_id="999999999999999999")
            return raw
        with patch.object(reader, "read", side_effect=read_then_replace):
            with self.assertRaisesRegex(ValueError, "immutable continuity source identity"):
                basis_api._continuity_forward_head_v1(forward, old.basis, reader=reader)
        reader.identities[event.path] = identity
        for key, bad in (("new_ordinary_cycle_credit", True), ("new_game_day_credit", 0.0),
                         ("original_actions_replayed", True), ("original_validation_ref", None)):
            with self.assertRaises(ValueError):
                basis_api.parse_current_saved_continuity_forward_v1(
                    {**forward.to_wire(), key: bad}, expected_machine_id=MACHINE)
        with self.assertRaisesRegex(ValueError, "immutable retained head"):
            basis_api._continuity_forward_head_v1(
                replace(forward, ledger_ref=current.snapshot_ref), old.basis, reader=reader)
        reader.read_paths.clear()
        with self.assertRaisesRegex(ValueError, "historical anchor"):
            basis_api._continuity_forward_head_v1(forward, replace(old.basis,
                refs=replace(old.basis.refs, ledger=current.snapshot_ref)), reader=reader)
        self.assertEqual(reader.read_paths, [forward.continuity_binding_ref.path])
        memory = MemoryReader()
        for path, raw in reader.raw.items():
            reference = ExactRefV1(path, len(raw), hashlib.sha256(raw).hexdigest())
            memory.documents[str(Path(path).resolve())] = continuity.PinnedContinuityDocumentV1(
                reference, reader.identities.get(path, FileStatIdentityV1(len(raw), "100", "1")), raw)
        advanced_basis = replace(old.basis, completed_cycles=old.basis.completed_cycles + 7,
            progress=replace(old.basis.progress, settled_cycles=old.basis.completed_cycles + 7,
                ledger_cycles=old.basis.completed_cycles, ledger_date_raw=old.basis.frame.date_raw))
        active = verified(current.head_state)
        active = replace(active, inputs=replace(active.inputs, basis=advanced_basis,
            old_ledger=current.head_state), opening=advanced_basis.frame)
        advanced = commit_memory(memory, current.head_state, owner.CURRENT_SAVED_COLD_KIND,
            active.expected_transition(), cold_reducer(active))
        memory.put(CANONICAL, advanced)
        advanced_view = view(memory, old.basis.refs.ledger)
        for doc in memory.documents.values():
            if doc.reference.path != old.basis.refs.ledger.path:
                reader.raw[doc.reference.path] = doc.payload
            reader.identities[doc.reference.path] = doc.identity
        advanced_binding = reader.put("advanced-forward-binding.json", advanced_view.to_wire())
        raw = memory.read(advanced_view.snapshot_ref, 65536)
        path = "/epoch/advanced-retained-ledger.json"
        reader.raw[path] = raw
        advanced_ref = ExactRefV1(path, len(raw), hashlib.sha256(raw).hexdigest())
        # The actual reducer and exact event/index chain accept the newer
        # business coordinates; this metadata-only operation must still refuse.
        with self.assertRaisesRegex(ValueError, "only already proven settled business"):
            basis_api._continuity_forward_head_v1(replace(forward,
                continuity_binding_ref=advanced_binding, ledger_ref=advanced_ref), old.basis, reader=reader)


class SettledPrefixOutcomeTests(unittest.TestCase):
    def test_original_task_absence_does_not_invent_a_subprocess_returncode(self) -> None:
        from tools.g2_saved_campaign import current_saved_basis_v1 as b
        raw = {"machine_id": MACHINE, "utc": AT, "task_name": "XARG2ManagedOwner-nonce",
            "operation": "unregister", "actual": {"instances": 0, "absent_after": True,
                "arguments": "-B original-owner.py bootstrap --spec original-SPEC.json --spec-sha "+"a"*64}}
        observed=b.validate_current_saved_closed_task_absence_v1(raw,machine_id=MACHINE,nonce="nonce",spec_sha256="a"*64)
        self.assertIsNone(observed.process_exit_code)
        self.assertEqual(observed.transport,"original_cli")
        self.assertNotIn("returncode",raw)
        for missing in ("utc", "actual", "task_name"):
            with self.assertRaises(ValueError):
                b.validate_current_saved_closed_task_absence_v1({k:v for k,v in raw.items() if k!=missing},
                    machine_id=MACHINE,nonce="nonce",spec_sha256="a"*64)
        for key, value in (("machine_id", "other-machine"), ("operation", "register"),
                           ("task_name", "XARG2ManagedOwner-other")):
            with self.assertRaises(ValueError):
                b.validate_current_saved_closed_task_absence_v1({**raw,key:value},
                    machine_id=MACHINE,nonce="nonce",spec_sha256="a"*64)
        for bad in (True, 0.0):
            with self.assertRaises(ValueError):
                b.validate_current_saved_closed_task_absence_v1({**raw,"actual":{**b.record(raw['actual']),"instances":bad}},
                    machine_id=MACHINE,nonce="nonce",spec_sha256="a"*64)

    def test_complete_native_history_uses_its_own_bounded_domain(self) -> None:
        import base64
        import json
        import zlib
        from tools.g2_saved_campaign import current_saved_basis_v1 as b
        history = [{"index": 3, "command": "query-player-mercenary-context-v1", "ok": True,
                    "result": {"native_identity": 134370851483706939, "padding": "x"*1100000}}]
        raw = json.dumps(history, separators=(",", ":")).encode()
        packed = zlib.compress(raw)
        def document(payload: bytes, decoded: bytes) -> dict[str, object]:
            return {"schema": "xar.raw-closed-driver-history-opaque/v1", "encoding": "zlib+base64",
                "payload": base64.b64encode(payload).decode(), "decoded_bytes": len(decoded),
                "decoded_sha256": hashlib.sha256(decoded).hexdigest(), "row_count": 1}
        self.assertGreater(len(raw), 1048576)
        self.assertEqual(b.decode_readonly_prefix_history_v1(document(packed, raw)), history)
        for payload, decoded in ((packed+b"trailing", raw), (packed+packed, raw),
                (zlib.compress(b"x"*(b.MAX_CLOSED_HISTORY_RAW_BYTES_V1+1)),
                 b"x"*(b.MAX_CLOSED_HISTORY_RAW_BYTES_V1+1))):
            with self.assertRaises(ValueError):
                b.decode_readonly_prefix_history_v1(document(payload, decoded))

    def test_returned_error_and_parent_failure_are_unknown_without_replay(self) -> None:
        from tools.g2_saved_campaign import current_saved_basis_v1 as b
        request = {"sequence": 44, "tool": "ck3_auto_turn", "arguments": {}}
        response = {"request": request, "result": {"is_error": True, "result_type": "complete",
            "structured_content": {"error_type": "StepPostconditionError"}}}
        outcome = b.project_current_saved_unknown_response_v1(request, response, expected_sequence=44)
        self.assertEqual(outcome.kind, "returned_sdk_error")
        reference = ExactRefV1("/original/44.json", 1, "a"*64)
        full = {"request": {"sequence": 29, "command": "full_loop", "arguments": {"max_turns": 30}},
            "client_error": "SDK error", "replay_allowed": False, "original_response": reference.path}
        failure = {"stage": "request_dispatch", "replay_allowed": False,
            "request_identity": {"sequence": 29, "tool": None, "command": "full_loop"},
            "traceback_truncated": False, "locals_captured": False}
        b.validate_current_saved_unknown_failure_v1(failure, full, outcome=outcome,
            unknown_request=request, unknown_response=reference)
        self.assertEqual(parse_json(canonical_json_v1(outcome.to_wire())), outcome.to_wire())
        for bad in (True, 44.0):
            with self.assertRaises(ValueError):
                b.project_current_saved_unknown_response_v1(request, response, expected_sequence=bad)
        with self.assertRaises(ValueError):
            b.project_current_saved_unknown_response_v1(request,
                {"request": request, "result": {"is_error": False, "result_type": "complete",
                    "structured_content": {"error_type": "pretend"}}}, expected_sequence=44)
        with self.assertRaises(ValueError):
            b.validate_current_saved_unknown_failure_v1({**failure,
                "request_identity": {"sequence": 28, "tool": None, "command": "full_loop"}}, full,
                outcome=outcome, unknown_request=request, unknown_response=reference)

    def test_primitive_is_not_an_effect_classification(self) -> None:
        from tools.g2_saved_campaign import current_saved_basis_v1 as b
        frame = pure_basis().frame
        step = "query-player-mercenary-context-v1"
        observation = {"selected_step": step, "primitive_accepted": True,
            "submitted_pending": False, "business_success_inferred": False, "replay_allowed": False}
        body = {"status": "executed", "selected_step": step, "result": {
            "step": step, "accepted": True, "backend_id": "native-headless", "query_sequence": 1,
            "read_only": True, "status": "completed", "snapshot_revision": frame.native_revision,
            "date_raw": frame.date_raw, "player_mercenary_context": {"actual_typed_context": True}}}
        effect = b.project_current_saved_settled_observation_v1(body, observation, frame=frame)
        self.assertEqual(effect.counted_flags, ("primitive_accepted",))
        self.assertEqual(effect.effect, "native_observation")
        for key, value in (("read_only", False), ("query_sequence", True), ("snapshot_revision", 1.0)):
            with self.assertRaises(ValueError):
                b.project_current_saved_settled_observation_v1({**body,
                    "result": {**b.record(body["result"]), key: value}}, observation, frame=frame)
        for rejected in ("hire-mercenary-v1", "query-unknown-potentially-mutating-command", "surrender-war-1"):
            with self.assertRaises(ValueError):
                b.project_current_saved_settled_observation_v1({**body, "selected_step": rejected,
                    "result": {**b.record(body["result"]), "step": rejected}},
                    {**observation, "selected_step": rejected}, frame=frame)
        observed: tuple[tuple[str, dict[str, object], str], ...] = (
            ("query-observed-first-heir-marriage-result-v1-private", {
                "schema": "xar.ck3.observed-first-heir-marriage-private-action.v1", "schema_version": 1,
                "step": "query-observed-first-heir-marriage-result-v1-private", "accepted": True,
                "private_build": True, "advertised": False, "cold_recovery": True, "status": "marriage",
                "material_result": True, "pre_native_revision": 0, "post_native_revision": frame.native_revision,
                "heir_character_id": 123, "candidate_character_id": 456}, "formal_ledger_readback"),
            ("query-army-strengths-v1", {"accepted": True, "status": "available",
                "armies": [{"army_id": 123}]}, "native_observation"),
            ("query-war-termination-options-123", {"accepted": True, "status": "available",
                "step": "query-war-termination-options-123", "backend_id": "native-headless",
                "query_sequence": 1, "war_termination_options": {"war_id": 123}}, "native_observation"),
            ("query-route-contact-horizon-v1-123-to-456-h-1-789", {"accepted": True, "status": "available",
                "step": "query-route-contact-horizon-v1-123-to-456-h-1-789", "backend_id": "native-headless",
                "query_sequence": 1, "snapshot_revision": frame.native_revision,
                "route_contact_horizon": {"typed_preview": True}}, "native_observation"),
        )
        for selected, result, expected in observed:
            source = {"status": "executed", "selected_step": selected, "result": result}
            credit = {**observation, "selected_step": selected}
            projected = b.project_current_saved_settled_observation_v1(source, credit, frame=frame)
            self.assertEqual(projected.effect, expected)
            self.assertIs(projected.to_wire()["new_gameplay_action_claimed"], False)
            self.assertEqual(projected.to_wire()["new_credit_granted"], 0)
            for bad in (True, 0.0):
                with self.assertRaises(ValueError):
                    b.project_current_saved_settled_observation_v1(source,
                        {**credit, "construction_start_verified": bad}, frame=frame)

    def test_explicit_large_response_to_real_builder_and_four_owner_consumers(self) -> None:
        import base64
        import zlib
        from unittest.mock import patch
        from tools.g2_saved_campaign import current_saved_basis_v1 as b
        from tools.g2_saved_campaign.test_current_saved_basis_v1 import (
            ComposeBoundedEpochMemoryReader, EpochMemoryReader, ReadonlyPrefixUnknownFixture,
        )
        class Reader(ComposeBoundedEpochMemoryReader):
            response_reads = 0
            def read_response(self, reference: ExactRefV1, limit: int) -> bytes:
                b.integer(limit, 1, b.MAX_ORIGINAL_RESPONSE_BYTES_V1)
                self.response_reads += 1
                return EpochMemoryReader.read(self, reference, limit)
        f = ReadonlyPrefixUnknownFixture(); r = Reader()
        r.raw = f.reader.raw; r.identities = f.reader.identities; f.reader = r
        def updated(reference: ExactRefV1, value: object) -> ExactRefV1:
            return r.put(reference.path.removeprefix("/epoch/"), value)
        prefix = b.evidence(r, f.epoch.refs.prefix)
        entries = b.rows(prefix["entries"]); entry = b.record(entries[-1])
        auto_ref = b.parse_ref(entry["auto"]); auto = b.evidence(r, auto_ref)
        result = b.record(auto["result"]); body = b.record(result["structured_content"])
        event_ref = b.parse_ref(entry["event"]); event = b.evidence(r, event_ref)
        original_credit = b.record(event["observation"])
        step = "query-player-mercenary-context-v1"; frame = b.parse_frame(event["before"])
        observation = {**original_credit, "selected_step": step, "existing_focus_verified": False,
            "typed_nonmaterial_observation": False, "primitive_accepted": True}
        body.update(status="executed", selected_step=step, fixture_observation=observation,
            result={"step": step, "accepted": True, "backend_id": "native-headless",
                "query_sequence": 1, "read_only": True, "status": "completed",
                "snapshot_revision": frame.native_revision, "date_raw": frame.date_raw,
                "player_mercenary_context": {"qualified_fixture": True}},
            opaque_native_identity=134370851483706939, evidence_padding="x"*1050000)
        auto_ref = updated(auto_ref, {**auto, "result": {**result, "structured_content": body}})
        self.assertGreater(auto_ref.bytes, 1048576)
        with self.assertRaises(ValueError):
            b.evidence(r, auto_ref, 1048576)
        counts = b.json_object(event["cumulative_observation_counts"])
        for flag, counter in (("existing_focus_verified", "existing_focus_verified_turns"),
                              ("typed_nonmaterial_observation", "typed_nonmaterial_observation_turns")):
            if original_credit.get(flag) is True:
                counts[counter] = b.integer(counts[counter], 1)-1
        counts["primitive_accepted_turns"] = b.integer(counts.get("primitive_accepted_turns", 0))+1
        entry["auto"] = auto_ref.to_wire()
        entry["event"] = updated(event_ref, {**event, "selected_step": step,
            "observation": observation, "cumulative_observation_counts": counts}).to_wire()
        plan_ref = b.parse_ref(entry["auto_plan"]); plan = b.evidence(r, plan_ref)
        plan_result = b.record(plan["result"]); planned = b.record(plan_result["structured_content"])
        entry["auto_plan"] = updated(plan_ref, {**plan, "result": {**plan_result,
            "structured_content": {**planned, "selected_step": step}}}).to_wire()
        credit_ref = b.parse_ref(entry["ordinary_credit"]); credit = b.evidence(r, credit_ref)
        entry["ordinary_credit"] = updated(credit_ref, {**credit, "observation": observation}).to_wire()
        entries[-1] = entry
        refs = f.epoch.refs
        raw_state = b.evidence(r, refs.raw_state)
        state_ref = updated(refs.raw_state, {**raw_state, "counts": counts})
        request = b.evidence(r, refs.unknown_request)
        native_failure = {"is_error": True, "never_replay": True, "original_error": "failed unknown action"}
        response_ref = updated(refs.unknown_response, {"request": request, "result": {
            "is_error": True, "result_type": "complete",
            "structured_content": {"error_type": "StepPostconditionError",
                "diagnostics": {"original_failure": native_failure}}}})
        control = b.evidence(r, refs.failed_full_response)
        failure = b.evidence(r, refs.first_exception)
        failure_ref = updated(refs.first_exception, {**failure, "stage": "request_dispatch",
            "request_identity": {"sequence": b.record(control["request"])["sequence"],
                "tool": None, "command": "full_loop"}})
        control_ref = updated(refs.failed_full_response, {**control,
            "original_response": response_ref.path})
        unknown_step = "advance-original-unknown-action"
        unknown_plan = r.put("prefix/unknown-plan.json", {
            "source": "actual GameplayBridgeService.before_submit callback",
            "game_pid": b.evidence(r, refs.launch)["pid"],
            "request": {"parent_sequence": request["sequence"]},
            "result": {"structured_content": {"selected_step": unknown_step}}})
        prefix_ref = updated(refs.prefix, {**prefix, "entries": entries,
            "unknown_plan": unknown_plan.to_wire()})
        opaque = b.evidence(r, refs.history_tail)
        history = b.decode_readonly_prefix_history_v1(opaque)
        history.append({"index": b.integer(history[-1]["index"])+1,
            "command": unknown_step, "ok": False, "result": native_failure,
            "error": "StepPostconditionError: failed unknown action"})
        history_raw = b._exact_native_json_v1(history)
        count = b.integer(opaque["command_history_count"])+1
        history_ref = updated(refs.history_tail, {**opaque, "payload": base64.b64encode(zlib.compress(history_raw)).decode(),
            "decoded_bytes": len(history_raw), "decoded_sha256": hashlib.sha256(history_raw).hexdigest(),
            "row_count": len(history), "command_history_count": count})
        review = b.evidence(r, refs.driver_review)
        raw_ref = b.parse_ref(review["raw_observation"]); raw_witness = b.evidence(r, raw_ref)
        raw_ref = updated(raw_ref, {**raw_witness, "command_history_count": count,
            "post_checkpoint_history_opaque": history_ref.to_wire()})
        review_ref = updated(refs.driver_review, {**review,
            "Driver": {**b.record(review["Driver"]), "command_history_count": count},
            "raw_observation": raw_ref.to_wire(), "post_checkpoint_history_opaque": history_ref.to_wire()})
        reuse = b.evidence(r, refs.canonical_qualification)
        reuse_ref = updated(refs.canonical_qualification, {**reuse,
            "driver_review": review_ref.to_wire(), "history_tail": history_ref.to_wire()})
        changed = replace(refs, raw_state=state_ref, unknown_response=response_ref,
            first_exception=failure_ref, failed_full_response=control_ref, prefix=prefix_ref,
            history_tail=history_ref, driver_review=review_ref, canonical_qualification=reuse_ref)
        index = b.evidence(r, refs.closure_index); linked = b.record(index["refs"])
        for key, reference in changed.items():
            if key in linked:
                linked[key] = reference.to_wire()
        changed = replace(changed, closure_index=updated(refs.closure_index, {**index, "refs": linked}))
        f.epoch = replace(f.epoch, refs=changed)
        basis, basis_ref, qualification = f.build()
        qualification_ref = r.put("new-outcome-qualification.json", qualification.to_wire())
        self.assertEqual(owner.parse_basis_qualification_v1(parse_json(canonical_json_v1(
            qualification.to_wire())), expected_machine_id=MACHINE), qualification)
        inputs = owner.validate_current_saved_cold_inputs_v1(basis, basis_ref=basis_ref,
            validation_ref=qualification_ref, reader=r)
        self.assertEqual(owner._closed_epoch(basis, r), inputs.closed_epoch)
        with patch.object(owner, "LocalBasisReaderV1", return_value=r):
            owner.validate_current_saved_prepared_sdk_closure_v1(changed.sdk_closed.to_wire(), inputs=inputs)
        self.assertEqual(basis.completed_cycles, f.previous_basis.completed_cycles+2)
        self.assertEqual(basis.frame.date_raw, f.previous_basis.frame.date_raw)
        self.assertIsNotNone(b.evidence(r, state_ref)["pending_cycle"])
        self.assertIsNone(inputs.seed["pending_cycle"])
        self.assertEqual(basis.unknown_requests[-1].sequence, b.integer(request["sequence"]))
        self.assertGreater(r.response_reads, 0)
        self.assertNotIn(basis.refs.driver.path, r.read_paths)
        self.assertNotIn(basis.refs.save.path, r.read_paths)



def _owned_continuity_case_v1(label: str) -> Iterator[Path]:
    import os
    root = Path(os.environ["XAR_CONTINUITY_TEST_FIXTURE_ROOT"]).resolve(strict=True)
    need(root.name == "test-continuity" and root.is_dir(), "explicit owned continuity fixture root")
    need(not (getattr(root.lstat(), "st_file_attributes", 0) & 1024), "ordinary owned root")
    need(label.isascii() and label.replace("-", "").isalnum(), "finite case basename")
    target = root / label
    need(target.parent == root and not target.exists(), "create-only contained case")
    target.mkdir()
    try:
        yield target
    finally:
        need(target.resolve(strict=True).parent == root, "cleanup remains inside owned root")
        paths = list(target.rglob("*"))
        for path in paths:
            need(not (getattr(path.lstat(), "st_file_attributes", 0) & 1024),
                 "refuse cleanup through reparse point")
            need(path.resolve(strict=True).is_relative_to(target), "contained cleanup")
        for path in sorted(paths, key=lambda item: len(item.parts), reverse=True):
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()
        target.rmdir()


class _PhysicalCheckpointReader:
    def __init__(self, driver_path: str) -> None:
        self.local = owner.LocalBasisReaderV1()
        self.driver_path = driver_path
        self.driver_reads = 0

    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        if reference.path == self.driver_path:
            self.driver_reads += 1
        return self.local.read(reference, limit)

    def stat(self, path: str) -> FileStatIdentityV1:
        return self.local.stat(path)


def _physical_ref_v1(path: Path) -> ExactRefV1:
    payload = path.read_bytes()
    return ExactRefV1(str(path.resolve()), len(payload), hashlib.sha256(payload).hexdigest())


class SavedRecoveryMeasurementTests(unittest.TestCase):
    def test_original_sdk_measurement_hash_cache_and_rejections(self) -> None:
        import os
        from datetime import datetime, timezone
        from unittest.mock import patch
        from tools.ck3_live_run_id import current_machine_id
        from tools.g2_saved_campaign.current_saved_basis_v1 import PinnedCheckpointValidatorV1
        from xar_autoplayer import cold_checkpoint_validator as sdk
        from xar_autoplayer import native_session as sdk_session
        from xar_autoplayer.errors import AgentError

        with contextmanager(_owned_continuity_case_v1)("checkpoint-measurement") as root:
            profile = root / "profile"
            saves = profile / "save games"
            saves.mkdir(parents=True)
            save = saves / sdk_session.NATIVE_SESSION_CHECKPOINT_FILENAME
            save.write_bytes(b"x" * 4096)
            save_ref = _physical_ref_v1(save)
            checkpoint: JsonObject = {
                "name": sdk_session.NATIVE_SESSION_CHECKPOINT_FILENAME,
                "size": save_ref.bytes, "sha256": save_ref.sha256, "date_raw": 53279400,
                "history_index": 1, "episode_character_id": 31254,
                "episode_run_id": "fixture-measured-episode",
            }
            payload: JsonObject = {
                "format_version": 2, "pipe_name": "fixture-measured-pipe",
                "episode_character_id": 31254, "episode_run_id": "fixture-measured-episode",
                "last_checkpoint": checkpoint, "command_history": [{
                    "index": 1, "command": "save-checkpoint", "ok": True,
                    "result": {"checkpoint": {
                        "size": save_ref.bytes, "sha256": save_ref.sha256, "date_raw": 53279400}},
                }],
            }
            driver = root / "fixture-driver.json"
            driver.write_bytes(canonical_json_v1(payload))
            driver_ref = _physical_ref_v1(driver)
            reader = _PhysicalCheckpointReader(driver_ref.path)
            driver_identity = reader.stat(driver_ref.path)
            save_identity = reader.stat(save_ref.path)
            source_ref = _physical_ref_v1(Path(sdk.__file__))
            validator = PinnedCheckpointValidatorV1(
                source_ref, sdk.validate_cold_start_checkpoint_payload_for_pipe)
            original_hash = sdk_session._sha256_file
            hashes: list[Path] = []

            def counted_hash(path: Path) -> str:
                hashes.append(path)
                return original_hash(path)

            with patch.object(sdk_session, "_sha256_file", counted_hash):
                measured = continuity.measure_saved_recovery_checkpoint_v1(
                    driver_ref=driver_ref, driver_identity=driver_identity,
                    save_ref=save_ref, save_identity=save_identity,
                    checkpoint_validator=validator, pipe_name="fixture-measured-pipe",
                    expected_machine_id=current_machine_id(), observed_at_utc=datetime.now(timezone.utc).isoformat(), reader=reader)
            self.assertIs(sdk_session._sha256_file, original_hash)
            self.assertEqual(reader.driver_reads, 1)
            self.assertEqual(hashes, [save])
            self.assertEqual(measured.receipt.checkpoint, checkpoint)
            self.assertEqual(set(measured.anchor), {"name", "load_save_name", "path", "size",
                "sha256", "saved_date_raw", "history_index", "succession_lifecycle"})
            self.assertIn(measured.token, continuity._MEASURED_RECOVERY_ISSUED)
            self.assertEqual(driver.read_bytes(), canonical_json_v1(payload))
            # Exercise the issued-result boundary with a genuine SDK measurement;
            # this does not claim that the synthetic prior campaign is qualified.
            cache_fixture = CompletedUnsavedTailFixture()
            cache_checked = cache_fixture.validated()
            receipt_ref = cache_fixture.reader.put("measured-cache-receipt.json", measured.receipt.to_wire())
            cache_checked = replace(cache_checked,
                saved_basis=replace(cache_checked.saved_basis, machine_id=current_machine_id()),
                evidence=replace(cache_checked.evidence, sources=replace(cache_checked.evidence.sources,
                    canonical_checkpoint_qualification=receipt_ref)),
                driver_ref=driver_ref, driver_identity=driver_identity,
                save_ref=save_ref, save_identity=save_identity)

            class CacheEvidenceReader:
                def read(self, reference: ExactRefV1, limit: int) -> bytes:
                    return cache_fixture.reader.read(reference, limit)
                def stat(self, path: str) -> FileStatIdentityV1:
                    if path in (driver_ref.path, save_ref.path):
                        return reader.stat(path)
                    return cache_fixture.reader.stat(path)

            cache_reader = CacheEvidenceReader()
            continuity._check_measured_recovery_v1(measured, cache_checked, reader=cache_reader)
            for cache_mutation in ("anchor", "checkpoint", "clone"):
                with self.subTest(cache_mutation=cache_mutation):
                    original_anchor = deepcopy(measured.anchor)
                    original_checkpoint = deepcopy(measured.receipt.checkpoint)
                    suspect = measured
                    if cache_mutation == "anchor":
                        measured.anchor["succession_lifecycle"] = {"mutated": True}
                    elif cache_mutation == "checkpoint":
                        measured.receipt.checkpoint["history_index"] = 999
                    else:
                        suspect = replace(measured, anchor=deepcopy(measured.anchor))
                    try:
                        with self.assertRaisesRegex(ValueError, "exact issued canonical cache"):
                            continuity._check_measured_recovery_v1(suspect, cache_checked, reader=cache_reader)
                    finally:
                        measured.anchor.clear(); measured.anchor.update(original_anchor)
                        measured.receipt.checkpoint.clear()
                        measured.receipt.checkpoint.update(original_checkpoint)
                    self.assertEqual(driver.read_bytes(), canonical_json_v1(payload))
            continuity._check_measured_recovery_v1(measured, cache_checked, reader=cache_reader)
            original_receipt_bytes = cache_fixture.reader.raw[receipt_ref.path]
            with patch.object(sdk_session, "_sha256_file", counted_hash):
                later = continuity.measure_saved_recovery_checkpoint_v1(
                    driver_ref=driver_ref, driver_identity=driver_identity,
                    save_ref=save_ref, save_identity=save_identity,
                    checkpoint_validator=validator, pipe_name="fixture-measured-pipe",
                    expected_machine_id=current_machine_id(),
                    observed_at_utc=datetime.now(timezone.utc).isoformat(), reader=reader)
            continuity._check_measured_recovery_v1(later, cache_checked, reader=cache_reader)
            self.assertEqual(cache_fixture.reader.raw[receipt_ref.path], original_receipt_bytes)
            self.assertEqual(hashes, [save, save])
            self.assertEqual(reader.driver_reads, 2)
            continuity._MEASURED_RECOVERY_ISSUED.pop(later.token, None)
            continuity._MEASURED_RECOVERY_ISSUED.pop(measured.token, None)

            for mode in ("history", "save-sha", "driver-identity"):
                with self.subTest(mode=mode):
                    driver.write_bytes(canonical_json_v1(payload))
                    save.write_bytes(b"x" * 4096)
                    if mode == "history":
                        bad = json_object(payload)
                        bad["command_history"] = [{"index": 1, "command": "not-save", "ok": True}]
                        driver.write_bytes(canonical_json_v1(bad))
                    actual_driver_ref = _physical_ref_v1(driver)
                    actual_save_ref = _physical_ref_v1(save)
                    current_reader = _PhysicalCheckpointReader(actual_driver_ref.path)
                    before = driver.read_bytes()
                    before_tokens = set(continuity._MEASURED_RECOVERY_ISSUED)
                    old_driver_identity = current_reader.stat(actual_driver_ref.path)
                    old_save_identity = current_reader.stat(actual_save_ref.path)
                    if mode == "save-sha":
                        save.write_bytes(b"y" * 4096)

                    def hash_then_external_replace(path: Path) -> str:
                        digest = original_hash(path)
                        if mode == "driver-identity":
                            replacement = root / "external-driver-replacement.json"
                            replacement.write_bytes(before)
                            os.replace(replacement, driver)
                        return digest

                    with patch.object(sdk_session, "_sha256_file", hash_then_external_replace):
                        with self.assertRaises((ValueError, AgentError)):
                            continuity.measure_saved_recovery_checkpoint_v1(
                                driver_ref=actual_driver_ref, driver_identity=old_driver_identity,
                                save_ref=actual_save_ref, save_identity=old_save_identity,
                                checkpoint_validator=validator, pipe_name="fixture-measured-pipe",
                                expected_machine_id=current_machine_id(), observed_at_utc=datetime.now(timezone.utc).isoformat(),
                                reader=current_reader)
                    self.assertIs(sdk_session._sha256_file, original_hash)
                    self.assertEqual(driver.read_bytes(), before)
                    self.assertEqual(set(continuity._MEASURED_RECOVERY_ISSUED), before_tokens)
                    self.assertEqual(current_reader.driver_reads, 0 if mode == "save-sha" else 1)

class _RollbackMemoryPowerLoss(Exception):
    pass


class _RollbackMemoryStore:
    def __init__(self, plan: continuity.RollbackPairPlanV1, reader: MemoryReader,
                 anchor_ref: ExactRefV1) -> None:
        self.plan = plan
        self.anchor_ref = anchor_ref
        self.reader = reader
        self.canonical_path = plan.original_view.canonical_path
        self.path = Path(self.canonical_path)
        self.events = self.path.with_name("ROOT-CONTINUITY-WINDOW-EVENTS")
        self.held = False
        self.lock_entries = 0
        self.write_log: list[tuple[str, int | str]] = []
        self.fail_after: int | None = None

    @contextmanager
    def locked(self) -> Iterator[None]:
        need(not self.held, "one nonnested transaction lock")
        self.held = True
        self.lock_entries += 1
        try:
            yield
        finally:
            self.held = False

    def read_head(self) -> JsonObject:
        need(self.held, "transaction read is locked")
        return continuity.read_continuity_view_v1(
            canonical_path=self.path, anchor_ref=self.anchor_ref,
            expected_machine_id=MACHINE, reader=self.reader).head_state

    def _read(self, path: Path) -> JsonObject | None:
        need(self.held, "transaction read is locked")
        document = self.reader.probe(str(path.resolve()), 65536)
        return None if document is None else document.value()

    def read_snapshot(self) -> JsonObject:
        value = self._read(self.path)
        need(value is not None, "existing actual snapshot")
        if value is None:
            raise ValueError("snapshot")
        return value

    def read_event(self, sequence: int) -> JsonObject | None:
        return self._read(self.events / f"{sequence:08d}.json")

    def read_index(self, source_key: str) -> JsonObject | None:
        return self._read(self.events / ("source-" + source_key + ".json"))

    def _after_write(self, kind: str, key: int | str) -> None:
        need(self.held, "transaction write is locked")
        self.write_log.append((kind, key))
        if self.fail_after is not None and len(self.write_log) == self.fail_after:
            raise _RollbackMemoryPowerLoss("after original atomic persistence boundary")

    def create_event(self, sequence: int, event: JsonObject) -> None:
        path = self.events / f"{sequence:08d}.json"
        need(self._read(path) is None, "event create-only")
        self.reader.put(path, event)
        self._after_write("event", sequence)

    def replace_snapshot(self, payload: JsonObject) -> None:
        need(self.held, "snapshot write is locked")
        self.reader.put(self.path, payload)
        self._after_write("snapshot", integer(payload["sequence"]))

    def create_index(self, source_key: str, index: JsonObject) -> None:
        path = self.events / ("source-" + source_key + ".json")
        need(self._read(path) is None, "source-index create-only")
        self.reader.put(path, index)
        self._after_write("index", source_key)


from copy import deepcopy
from functools import lru_cache
from tools.g2_saved_campaign.test_current_saved_settled_closure_v1 import CompletedUnsavedTailFixture, SavedBusinessPriorV1


@lru_cache(maxsize=1)
def _original_ledger_payload_v1() -> bytes:
    payload = Path(actual_ledger.__file__).read_bytes()
    need(0 < len(payload) <= 131072, "bounded actual ledger source")
    return payload


@runtime_checkable
class _ActualWindowConstructorV1(Protocol):
    def __call__(self, path: Path) -> continuity.OriginalWindowLedgerV1: ...


@runtime_checkable
class _ActualAtomicV1(continuity.OriginalWindowAtomicV1, Protocol):
    pass


class _ProofLedgerReader:
    def __init__(self, fixture: CompletedUnsavedTailFixture, memory: MemoryReader,
                 physical: bool) -> None:
        self.fixture, self.memory, self.physical = fixture, memory, physical
        self.local = continuity.LocalContinuityReaderV1()

    def probe(self, path: str, limit: int) -> continuity.PinnedContinuityDocumentV1 | None:
        reference = self.fixture.basis.refs.ledger
        if Path(path).resolve() == Path(reference.path).resolve():
            raw = self.fixture.reader.read(reference, limit)
            return continuity.PinnedContinuityDocumentV1(
                reference, self.fixture.reader.stat(reference.path), raw)
        return self.local.probe(path, limit) if self.physical else self.memory.probe(path, limit)


class _QualifiedRollbackCase:
    def __init__(self, canonical: Path | None = None, *,
                 fixture: CompletedUnsavedTailFixture | None = None) -> None:
        self.fixture = CompletedUnsavedTailFixture() if fixture is None else fixture
        validated = self.fixture.validated()
        self.memory = MemoryReader()
        self.path = (ROOT / "managed-rollback" / "ROOT-CONTINUITY-WINDOW.json"
                     if canonical is None else canonical).resolve()
        self.events = self.path.with_name("ROOT-CONTINUITY-WINDOW-EVENTS")
        self.reader = _ProofLedgerReader(self.fixture, self.memory, canonical is not None)
        anchor = validated.saved_basis.refs.ledger
        anchor_raw = self.fixture.reader.read(anchor, 65536)
        self.memory.documents[str(Path(anchor.path).resolve())] = continuity.PinnedContinuityDocumentV1(
            anchor, self.fixture.reader.stat(anchor.path), anchor_raw)
        before = json_object(parse_json(anchor_raw))
        details: JsonObject = {
            "machine_id": self.fixture.basis.machine_id, "evidence_id": "original-completed-full",
            "source": self.fixture.proof.sources.successful_full_responses[0].path,
            "frame": validated.current_frame.to_wire(),
            "date_raw": validated.current_frame.date_raw,
            "completed_cycles": validated.current_cycles,
        }
        if canonical is None:
            from unittest.mock import patch
            self.memory.put(self.path, before)
            with patch(__name__ + ".EVENTS", self.events):
                head = commit_memory(self.memory, before, "settled_batch", details, reducer)
            self.memory.put(self.path, head)
            event = self.memory.probe(
                str(self.events / f"{integer(head['sequence']):08d}.json"), 65536)
        else:
            constructor: object = actual_ledger.WindowLedger
            atomic: object = actual_ledger._atomic
            if not isinstance(constructor, _ActualWindowConstructorV1) or not isinstance(atomic, _ActualAtomicV1):
                raise TypeError("actual original writer boundary")
            self.ledger = constructor(self.path)
            self.atomic = atomic
            self.events.mkdir()
            self.path.with_suffix(".lock").write_bytes(b"\0")
            self.atomic(self.path, before)
            self.atomic(self.events / f"{integer(before['sequence']):08d}.json", {"kind": "historical_anchor", "details": {"evidence_id": "fixture-prior-anchor"}, "identity": continuity.continuity_digest_v1(before), "after": before})
            original_writer: object = self.ledger
            if not isinstance(original_writer, ForwardWriterV1):
                raise TypeError("actual original apply")
            head = json_object(original_writer.apply("settled_batch", details))
            event = self.reader.probe(
                str(self.events / f"{integer(head['sequence']):08d}.json"), 65536)
        need(event is not None, "actual original predecessor event")
        if event is None:
            raise ValueError("event")
        self._source(event.reference.path, event.payload)
        writer = self._source(str(Path(self.fixture.proof.runtime_root) /
            "root_continuity_window_c23_100.py"), _original_ledger_payload_v1())
        frontier: JsonObject = {
            "schema": "xar.current-saved-historical-rollback-frontier/v1",
            "machine_id": self.fixture.basis.machine_id, "observed_at_utc": AT,
            "canonical_path": str(self.path), "anchor_ref": anchor.to_wire(),
            "head_event_ref": event.reference.to_wire(), "writer_source_ref": writer.to_wire(),
            "head_sequence": integer(head["sequence"]),
            "head_digest": continuity.continuity_digest_v1(head),
        }
        self.frontier_ref = self.fixture.reader.put("rollback-frontier.json", frontier)
        self.fixture.replace_frontier_v1(self.frontier_ref)
        self.plan = self.revalidate(self.fixture.proof_ref)

    def _source(self, path: str, raw: bytes) -> ExactRefV1:
        self.fixture.reader.raw[path] = raw
        self.fixture.reader.identities[path] = (owner.LocalBasisReaderV1().stat(path)
            if Path(path).is_file() else FileStatIdentityV1(
                len(raw), str(100000 + len(self.fixture.reader.raw)), "1"))
        return ExactRefV1(path, len(raw), hashlib.sha256(raw).hexdigest())

    def revalidate(self, proof_ref: ExactRefV1) -> continuity.RollbackPairPlanV1:
        need(proof_ref == self.fixture.proof_ref, "actual immutable proof ref")
        checked = self.fixture.validated(evidence_only=True)
        frontier = continuity.validate_saved_rollback_frontier_v1(self.frontier_ref,
            validated=checked, reader=self.fixture.reader, continuity_reader=self.reader)
        return continuity.build_saved_rollback_pair_plan_v1(checked, frontier)

    def memory_store(self) -> _RollbackMemoryStore:
        return _RollbackMemoryStore(self.plan, self.memory, self.fixture.basis.refs.ledger)

    def physical_store(self) -> continuity._OriginalRollbackPairStoreV1:
        return continuity._OriginalRollbackPairStoreV1(
            canonical_path=self.path, anchor_ref=self.fixture.basis.refs.ledger,
            machine_id=self.fixture.basis.machine_id, reader=self.reader, ledger=self.ledger, atomic=self.atomic)

    def commit(self, store: continuity.RollbackPairStoreV1,
               plan: continuity.RollbackPairPlanV1 | None = None) -> continuity.RollbackPairCommitV1:
        return continuity._commit_saved_rollback_pair_v1(
            store, self.plan if plan is None else plan, revalidate=self.revalidate, now_utc=AT)


class QualifiedRollbackPairTests(unittest.TestCase):
    def test_actual_proof_and_full_wire_one_lock_zero_credit(self) -> None:
        case = _QualifiedRollbackCase()
        store = case.memory_store()
        result = case.commit(store)
        self.assertEqual((result.writes, result.created_events, store.lock_entries), (6, 2, 1))
        self.assertEqual(store.write_log[0][0], "event")
        self.assertEqual(case.memory.documents[str(case.path)].value(), case.plan.second.committed_state)
        self.assertEqual(case.plan.first.committed_state["last_settled_cycles"], 22)
        self.assertEqual(case.plan.second.committed_state["last_settled_cycles"], 20)
        self.assertEqual(case.plan.second.committed_state["start_date_raw"], 100)
        self.assertEqual(case.plan.second.committed_state["target_days"], 10958)

    def test_head_and_second_index_drift_have_zero_writes(self) -> None:
        for mode in ("head", "index", "path"):
            with self.subTest(mode=mode):
                case = _QualifiedRollbackCase()
                store = case.memory_store()
                if mode == "head":
                    changed = json_object(case.plan.original_view.head_state)
                    changed["last_settled_cycles"] = 23
                    case.memory.put(case.path, changed)
                elif mode == "index":
                    key = continuity.continuity_digest_v1({"kind": case.plan.second.kind,
                        "evidence_id": case.plan.second.details["evidence_id"]})
                    case.memory.put(case.events / ("source-" + key + ".json"),
                                    {"sequence": 999, "identity": "b" * 64})
                else:
                    store.canonical_path = str(ROOT / "wrong.json")
                before = dict(case.memory.documents)
                with self.assertRaises(ValueError):
                    case.commit(store)
                self.assertEqual(store.write_log, [])
                self.assertEqual(case.memory.documents, before)

    def test_six_original_persistence_boundaries_resume_exactly(self) -> None:
        for boundary in range(1, 7):
            with self.subTest(boundary=boundary):
                case = _QualifiedRollbackCase()
                store = case.memory_store()
                store.fail_after = boundary
                with self.assertRaises(_RollbackMemoryPowerLoss):
                    case.commit(store)
                originals = {key: value for key, value in case.memory.documents.items()
                    if key.endswith(".json") and Path(key).parent == case.events}
                store.fail_after = None
                result = case.commit(store)
                for key, value in originals.items():
                    self.assertEqual(case.memory.documents[key], value)
                self.assertEqual(sum(kind == "event" for kind, _ in store.write_log), 2)
                self.assertEqual(case.memory.documents[str(case.path)].value(),
                                 case.plan.second.committed_state)
                self.assertTrue(result.recovered_after_first_event)

    def test_completed_retry_zero_writes(self) -> None:
        case = _QualifiedRollbackCase()
        store = case.memory_store()
        case.commit(store)
        count = len(store.write_log)
        result = case.commit(store)
        self.assertEqual((result.writes, result.created_events, len(store.write_log)), (0, 0, count))

    def test_same_evidence_id_changed_content_refused(self) -> None:
        case = _QualifiedRollbackCase()
        store = case.memory_store()
        store.fail_after = 1
        with self.assertRaises(_RollbackMemoryPowerLoss):
            case.commit(store)
        sequence = case.plan.original_view.head_sequence + 1
        path = case.events / f"{sequence:08d}.json"
        event = case.memory.documents[str(path)].value()
        event["details"] = {"evidence_id": case.plan.first.details["evidence_id"], "source": "changed"}
        case.memory.put(path, event)
        before = dict(case.memory.documents)
        store.fail_after = None
        with self.assertRaises(ValueError):
            case.commit(store)
        self.assertEqual(case.memory.documents, before)

    def test_forged_plan_revalidated_from_actual_shared_proof(self) -> None:
        case = _QualifiedRollbackCase()
        store = case.memory_store()
        with self.assertRaisesRegex(ValueError, "stale/forged"):
            case.commit(store, replace(case.plan, transaction_id="caller-GREEN"))
        self.assertEqual(store.write_log, [])

    def test_exact_parser_fields_and_bool_float_json_rejections(self) -> None:
        case = _QualifiedRollbackCase()
        proof = case.fixture.proof
        wire = parse_json(canonical_json_v1(proof.to_wire()))
        self.assertEqual(continuity.parse_completed_unsaved_tail_v1(
            wire, expected_machine_id=MACHINE), proof)
        for key, bad in (("new_ordinary_cycle_credit", True), ("new_game_day_credit", 0.0),
                         ("original_actions_replayed", 0), ("Driver_history_truncated", None)):
            changed = proof.to_wire()
            changed[key] = bad
            with self.assertRaises(ValueError):
                continuity.parse_completed_unsaved_tail_v1(
                    parse_json(canonical_json_v1(changed)), expected_machine_id=MACHINE)
        for mode in ("missing", "extra"):
            changed = proof.to_wire()
            if mode == "missing":
                del changed["sources"]
            else:
                changed["unknown_alias"] = None
            with self.assertRaises(ValueError):
                continuity.parse_completed_unsaved_tail_v1(changed, expected_machine_id=MACHINE)

    def test_missing_first_index_after_pair_repairs_only_that_index(self) -> None:
        case = _QualifiedRollbackCase()
        store = case.memory_store()
        case.commit(store)
        key = continuity.continuity_digest_v1({"kind": case.plan.first.kind,
            "evidence_id": case.plan.first.details["evidence_id"]})
        del case.memory.documents[str(case.events / ("source-" + key + ".json"))]
        before = {path: doc for path, doc in case.memory.documents.items()
                  if Path(path).name[:1].isdigit()}
        result = case.commit(store)
        self.assertEqual((result.writes, result.created_events), (1, 0))
        for path, doc in before.items():
            self.assertEqual(case.memory.documents[path], doc)

    def test_actual_original_head_fields_binding_and_frame_are_historical(self) -> None:
        case = _QualifiedRollbackCase()
        before = case.plan.original_view.head_state
        self.assertTrue({"sequence", "last_settled_cycles", "last_settled_date_raw",
                         "last_settled_source", "game_binding"} <= set(before))
        self.assertNotIn("last_settled_completed_cycles", before)
        after = case.plan.second.committed_state
        self.assertEqual(after["game_binding"], before["game_binding"])
        if "latest_binding" in before:
            self.assertEqual(after["latest_binding"], before["latest_binding"])
        self.assertEqual(after["status"], "repair_required")
        self.assertIs(json_object(after["unsaved_tail_recovery"])["requires_new_cold_binding"], True)
        store = case.memory_store()
        case.commit(store)
        self.assertEqual(case.memory.documents[str(case.path)].value(), after)


class OriginalRollbackFilesystemTests(unittest.TestCase):
    def test_real_atomic_event_snapshot_faults_and_exact_retry(self) -> None:
        import os
        from unittest.mock import patch
        for mode in ("after-event", "after-snapshot"):
            with self.subTest(mode=mode):
                with contextmanager(_owned_continuity_case_v1)("rollback-" + mode) as root:
                    case = _QualifiedRollbackCase(root / "ROOT-CONTINUITY-WINDOW.json")
                    store = case.physical_store()
                    real_atomic = case.atomic
                    calls: list[Path] = []
                    stopped = False

                    def fault(path: Path, value: JsonObject, replace: bool = False) -> None:
                        nonlocal stopped
                        real_atomic(path, value, replace=replace)
                        calls.append(path)
                        matched = (path == case.path if mode == "after-snapshot" else
                                   path == case.events / f"{case.plan.original_view.head_sequence+1:08d}.json")
                        if matched and not stopped:
                            stopped = True
                            raise _RollbackMemoryPowerLoss("after real original atomic operation")

                    with self.assertRaises(_RollbackMemoryPowerLoss):
                        case.commit(continuity._OriginalRollbackPairStoreV1(
                            canonical_path=case.path, anchor_ref=case.fixture.basis.refs.ledger,
                            machine_id=MACHINE, reader=case.reader, ledger=case.ledger, atomic=fault))
                    first = case.events / f"{case.plan.original_view.head_sequence+1:08d}.json"
                    before = first.read_bytes()
                    result = case.commit(store)
                    self.assertEqual(first.read_bytes(), before)
                    self.assertEqual(result.created_events, 1)
                    self.assertEqual(json_object(parse_json(case.path.read_bytes())),
                                     case.plan.second.committed_state)
                    self.assertEqual(list(root.rglob("*.pending")), [])
                    self.assertTrue(calls)

    def test_real_wrong_head_changes_no_event_snapshot_or_index(self) -> None:
        with contextmanager(_owned_continuity_case_v1)("rollback-wrong-head") as root:
            case = _QualifiedRollbackCase(root / "ROOT-CONTINUITY-WINDOW.json")
            changed = json_object(case.plan.original_view.head_state)
            changed["last_settled_cycles"] = 999
            case.atomic(case.path, changed, replace=True)
            before = {str(path.relative_to(root)): path.read_bytes()
                      for path in root.rglob("*") if path.is_file()}
            with self.assertRaises(ValueError):
                case.commit(case.physical_store())
            after = {str(path.relative_to(root)): path.read_bytes()
                     for path in root.rglob("*") if path.is_file()}
            self.assertEqual(after, before)


def _complete_saved_business_prior_v1(root: Path) -> SavedBusinessPriorV1:
    """Reuse the real complete producer; adapt only its fixture origin/resources."""
    from datetime import datetime, timezone
    from unittest.mock import patch
    from tools.ck3_live_run_id import current_machine_id
    from tools.g2_saved_campaign import test_current_saved_basis_v1 as basis_fixture
    from tools.g2_saved_campaign.current_saved_basis_v1 import (
        build_current_saved_basis_v1, qualify_current_saved_basis_v1, record)

    class CompletePriorProducer(basis_fixture.CurrentSavedBasisTests):
        @classmethod
        def write(cls, name: str, value: object) -> ExactRefV1:
            if name in ("stale-ledger.json", "origin-ledger.json", "governance.json", "driver.json"):
                row = record(value)
                if name == "driver.json":
                    row["bridge_pid"] = 10
                elif name == "governance.json":
                    row.update(governance_result_state=None, pending_focus=None)
                else:
                    row.update(target_days=10958,
                        target_date_raw=integer(row["start_date_raw"]) + 10958 * 24)
                    if name == "stale-ledger.json":
                        full = record(parse_json((cls.root / "full-100.json").read_bytes()))
                        body = record(record(full["result"])["structured_content"])
                        row.update(schema="root.ck3.continuity-window/v1",
                            sequence=1, window_id=1, status="running",
                            last_settled_cycles=integer(body["cumulative_cycles"]),
                            last_settled_date_raw=integer(body["actual_end_date_raw"]),
                            game_binding={"pid": 10, "creation_date": AT},
                            cold_handoff_count=0, manual_repair_count=0,
                            automatic_recovery_count=0, binding_lineage_count=0)
                value = row
            return super().write(name, value)

    need(root.is_dir(), "owned complete-prior directory")
    CompletePriorProducer.root = root
    CompletePriorProducer.reader = basis_fixture.DiskReader()
    CompletePriorProducer.peak_upper = 4096
    with patch.object(basis_fixture, "MACHINE", current_machine_id()):
        CompletePriorProducer.make_inputs()
    inputs = CompletePriorProducer.inputs
    inputs = replace(inputs, observed_at_utc=datetime.now(timezone.utc).isoformat(),
        origin=replace(inputs.origin, target_days=10958,
            target_date_raw=inputs.origin.start_date_raw + 10958 * 24))
    built = build_current_saved_basis_v1(inputs, reader=CompletePriorProducer.reader,
        checkpoint_validator=CompletePriorProducer.validator)
    qualified = qualify_current_saved_basis_v1(inputs, reader=CompletePriorProducer.reader,
        checkpoint_validator=CompletePriorProducer.validator)
    need(built == qualified.basis, "original complete build and qualifier agree")
    return SavedBusinessPriorV1(qualified, CompletePriorProducer.reader, "test-pipe")


class _RecoveryPhysicalEvidenceReader:
    def __init__(self, fixture: CompletedUnsavedTailFixture) -> None:
        self.fixture = fixture
        self.local = owner.LocalBasisReaderV1()
        self.driver_path = fixture.driver_ref.path
        self.save_path = fixture.basis.refs.save.path
        self.driver_payload_reads = 0

    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        if reference.path in (self.driver_path, self.save_path):
            if reference.path == self.driver_path:
                self.driver_payload_reads += 1
            return self.local.read(reference, limit)
        return self.fixture.reader.read(reference, limit)

    def stat(self, path: str) -> FileStatIdentityV1:
        if path in (self.driver_path, self.save_path):
            return self.local.stat(path)
        return self.fixture.reader.stat(path)

    def read_response(self, reference: ExactRefV1, limit: int) -> bytes:
        return self.fixture.reader.read_response(reference, limit)


class PublicSavedRecoveryTests(unittest.TestCase):
    def test_complete_producer_measure_public_commit_retry_and_final_qualification(self) -> None:
        from datetime import datetime, timezone
        from unittest.mock import patch
        from tools.ck3_live_run_id import current_machine_id
        from tools.g2_saved_campaign.current_saved_basis_v1 import record, rows, PinnedCheckpointValidatorV1
        from xar_autoplayer.cold_checkpoint_validator import validate_cold_start_checkpoint_payload_for_pipe
        from xar_autoplayer import native_session as sdk_session

        with contextmanager(_owned_continuity_case_v1)("public-saved-recovery") as root:
            prior_root = root / "prior"
            prior_root.mkdir()
            hash_paths: list[Path] = []
            original_hash = sdk_session._sha256_file

            def counted_hash(path: Path) -> str:
                hash_paths.append(path)
                return original_hash(path)

            with patch.object(sdk_session, "_sha256_file", counted_hash):
                saved_prior = _complete_saved_business_prior_v1(prior_root)
                prior = saved_prior.validated.basis
                self.assertEqual(len(hash_paths), 2)
                self.assertEqual(prior.origin.target_days, 10958)
                self.assertEqual(prior.progress.ledger_cycles, prior.completed_cycles)
                driver = Path(prior.refs.driver.path)
                payload = record(parse_json(driver.read_bytes()))
                payload["bridge_pid"] = 30
                history = rows(payload["command_history"])
                payload["command_history"] = [*history,
                    {"index": len(history) + 1, "command": "fixture-readonly-observation", "ok": True}]
                current_raw = canonical_json_v1(payload)
                replacement = root / "fixture-next-driver.json"
                replacement.write_bytes(current_raw)
                import os
                os.replace(replacement, driver)
                current_ref = ExactRefV1(str(driver.resolve()), len(current_raw),
                    hashlib.sha256(current_raw).hexdigest())
                local = owner.LocalBasisReaderV1()
                current_identity = local.stat(current_ref.path)
                self.assertNotEqual(current_identity.file_id, prior.driver_identity.file_id)
                f = CompletedUnsavedTailFixture(saved_prior=saved_prior,
                    metadata_root=root / "tail", current_driver_ref=current_ref,
                    current_driver_identity=current_identity)
                review_driver = record(f.review["Driver"])
                review_driver["command_history_count"] = len(rows(payload["command_history"]))
                f.review["Driver"] = review_driver
                reader = _RecoveryPhysicalEvidenceReader(f)

                validator = PinnedCheckpointValidatorV1(prior.refs.checkpoint_validator,
                    validate_cold_start_checkpoint_payload_for_pipe)

                def measure() -> continuity._MeasuredRecoveryCheckpointV1:
                    return continuity.measure_saved_recovery_checkpoint_v1(
                        driver_ref=current_ref, driver_identity=current_identity,
                        save_ref=prior.refs.save, save_identity=prior.save_identity,
                        checkpoint_validator=validator,
                        pipe_name=saved_prior.pipe_name, expected_machine_id=current_machine_id(),
                        observed_at_utc=datetime.now(timezone.utc).isoformat(), reader=reader)

                first = measure()
                self.assertEqual(reader.driver_payload_reads, 1)
                self.assertEqual(len(hash_paths), 3)
                canonical_ref = f.reader.put("tail-runtime/original-measurement.json", first.receipt.to_wire())
                f.proof = replace(f.proof, sources=replace(f.proof.sources,
                    canonical_checkpoint_qualification=canonical_ref))
                f.reseal()
                f.root.mkdir(parents=True)
                (f.root / "root_continuity_window_c23_100.py").write_bytes(_original_ledger_payload_v1())
                case = _QualifiedRollbackCase(root / "ROOT-CONTINUITY-WINDOW.json", fixture=f)
                evidence_bytes = f.reader.raw[f.proof_ref.path]
                canonical_bytes = f.reader.raw[canonical_ref.path]

                def public_commit(measured: continuity._MeasuredRecoveryCheckpointV1) -> continuity.RollbackPairCommitV1:
                    with f.io_scope():
                        return continuity.commit_completed_unsaved_tail_recovery_v1(
                            f.proof_ref, measurement=measured, expected_machine_id=current_machine_id(),
                            observed_at_utc=datetime.now(timezone.utc).isoformat(),
                            reader=reader, continuity_reader=case.reader)

                before_rejections = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
                for mutation in ("anchor", "checkpoint", "clone"):
                    with self.subTest(public_cache_mutation=mutation):
                        old_anchor = deepcopy(first.anchor)
                        old_checkpoint = deepcopy(first.receipt.checkpoint)
                        candidate = first
                        if mutation == "anchor":
                            first.anchor["succession_lifecycle"] = {"changed": True}
                        elif mutation == "checkpoint":
                            first.receipt.checkpoint["history_index"] = 999
                        else:
                            candidate = replace(first, anchor=deepcopy(first.anchor))
                        try:
                            with self.assertRaisesRegex(ValueError, "exact issued canonical cache"):
                                public_commit(candidate)
                        finally:
                            first.anchor.clear(); first.anchor.update(old_anchor)
                            first.receipt.checkpoint.clear()
                            first.receipt.checkpoint.update(old_checkpoint)
                        self.assertEqual(before_rejections,
                            {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()})
                original_proof = f.proof
                for mutation in ("validator", "pipe", "checkpoint", "driver_identity", "save_identity", "future_t1"):
                    with self.subTest(public_canonical_source=mutation):
                        bad_receipt = deepcopy(first.receipt.to_wire())
                        if mutation == "validator":
                            bad_receipt["validator_source_ref"] = replace(
                                prior.refs.checkpoint_validator, sha256="f" * 64).to_wire()
                        elif mutation == "pipe":
                            bad_receipt["pipe_name"] = "wrong-pipe"
                        elif mutation == "checkpoint":
                            wrong_checkpoint = json_object(bad_receipt["checkpoint"])
                            wrong_checkpoint["history_index"] = 999
                            bad_receipt["checkpoint"] = wrong_checkpoint
                        elif mutation in ("driver_identity", "save_identity"):
                            for suffix in ("_before", "_after"):
                                wrong_identity = json_object(bad_receipt[mutation + suffix])
                                wrong_identity["file_id"] = "999999999"
                                bad_receipt[mutation + suffix] = wrong_identity
                        else:
                            bad_receipt["observed_at_utc"] = "2099-01-01T00:00:00Z"
                        bad_ref = f.reader.put("tail-runtime/wrong-measurement.json", bad_receipt)
                        f.proof = replace(original_proof, sources=replace(original_proof.sources,
                            canonical_checkpoint_qualification=bad_ref))
                        f.reseal()
                        try:
                            with self.assertRaises(ValueError):
                                public_commit(first)
                        finally:
                            f.proof = original_proof
                            f.reseal()
                        self.assertEqual(before_rejections,
                            {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()})
                original_create = continuity._OriginalRollbackPairStoreV1.create_event

                def create_then_interrupt(store: continuity._OriginalRollbackPairStoreV1,
                                          sequence: int, event: JsonObject) -> None:
                    original_create(store, sequence, event)
                    if sequence == case.plan.original_view.head_sequence + 1:
                        raise _RollbackMemoryPowerLoss("actual first event persisted")

                with f.io_scope(), patch.object(continuity._OriginalRollbackPairStoreV1,
                                               "create_event", create_then_interrupt):
                    with self.assertRaises(_RollbackMemoryPowerLoss):
                        continuity.commit_completed_unsaved_tail_recovery_v1(
                            f.proof_ref, measurement=first, expected_machine_id=current_machine_id(),
                            observed_at_utc=datetime.now(timezone.utc).isoformat(),
                            reader=reader, continuity_reader=case.reader)
                continuity._MEASURED_RECOVERY_ISSUED.pop(first.token)
                later = measure()
                self.assertEqual(reader.driver_payload_reads, 2)
                self.assertEqual(len(hash_paths), 4)
                self.assertEqual(f.reader.raw[f.proof_ref.path], evidence_bytes)
                self.assertEqual(f.reader.raw[canonical_ref.path], canonical_bytes)
                try:
                    with f.io_scope():
                        committed = continuity.commit_completed_unsaved_tail_recovery_v1(
                            f.proof_ref, measurement=later, expected_machine_id=current_machine_id(),
                            observed_at_utc=datetime.now(timezone.utc).isoformat(),
                            reader=reader, continuity_reader=case.reader)
                    self.assertEqual(committed.phase, "RollbackPairCommitted")
                    self.assertTrue(committed.recovered_after_first_event)
                    head_ref = _physical_ref_v1(case.path)
                    second_key = continuity._source_key(case.plan.second)
                    second_index = case.events / ("source-" + second_key + ".json")
                    index_bytes = second_index.read_bytes()
                    second_index.unlink()
                    before_missing = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
                    with f.io_scope():
                        with self.assertRaisesRegex(ValueError,
                                "actual committed rollback head before final basis qualification"):
                            continuity.qualify_saved_recovery_basis_v1(
                                f.proof_ref, ledger_ref=head_ref, measurement=later,
                                expected_machine_id=current_machine_id(),
                                observed_at_utc=datetime.now(timezone.utc).isoformat(),
                                reader=reader, continuity_reader=case.reader)
                    self.assertEqual(before_missing,
                        {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()})
                    second_index.write_bytes(index_bytes)
                    with f.io_scope():
                        final = continuity.qualify_saved_recovery_basis_v1(
                            f.proof_ref, ledger_ref=head_ref, measurement=later,
                            expected_machine_id=current_machine_id(),
                            observed_at_utc=datetime.now(timezone.utc).isoformat(),
                            reader=reader, continuity_reader=case.reader)
                    self.assertEqual(final.basis.completed_cycles, prior.completed_cycles)
                    self.assertEqual(final.basis.frame, prior.frame)
                    self.assertEqual(final.basis.origin, prior.origin)
                    self.assertEqual(final.basis.next_sequence, f.validated().actual_next_sequence)
                    self.assertEqual(len(hash_paths), 4, "final qualifier uses actual measured cache")
                    self.assertEqual(reader.driver_payload_reads, 2)
                    self.assertEqual(driver.read_bytes(), current_raw)
                finally:
                    continuity._MEASURED_RECOVERY_ISSUED.pop(later.token, None)


if __name__ == "__main__":
    unittest.main()

