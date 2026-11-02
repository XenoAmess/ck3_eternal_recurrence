package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.math.BigInteger;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import java.util.Optional;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.OrdinaryAdmissionFixture225.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Pure original DATA ports. No physical writer, Saved issuer, Game or native authority. */
final class SettledRecoveryFrontier344Test {
    @Test void eachPreviewUsesFreshCompleteBranchAndFreshReceiptQualification() throws IOException {
        var h = new Harness();
        byte[] before = h.fixture.store.current.canonicalBytes();
        int commits = h.fixture.store.commits;
        h.fixture.store.locked(same -> h.authority.withLocked(same, () -> {
            for (int pass = 0; pass < 2; pass++) {
                h.archive.reset();
                var prepared = same.preview(h.request());
                assertEquals(same.head().digest(), prepared.predecessor().digest());
                // One record: first + final + revalidate SEM + public preview reducer SEM.
                assertEquals(4, h.archive.cycleReads);
                assertEquals(3, h.archive.receiptQualifications);
                assertEquals(1, h.archive.actionHistoryReads);
            }
            return null;
        }));
        assertEquals(commits, h.fixture.store.commits);
        assertArrayEquals(before, h.fixture.store.current.canonicalBytes());
    }

    @Test void missingDeepRecordRepeatedActionAndClassificationMismatchRejectBeforeActionCallbacks() throws IOException {
        for (String problem : List.of("missing", "repeated-action", "classification")) {
            var h = new Harness();
            ObjectNode record = h.fixture.archive.latestMaterial().deepCopy();
            record.put("completed_cycles", 5);
            record.set("previous", problem.equals("missing") ? ref("missing-cycle", "8").toJson() : h.cycleRef.toJson());
            if (problem.equals("classification")) record.put("classification", "CONTROL_ONLY");
            ExactRef newHead = h.fixture.archive.preserveMaterial(new RawJson(ContinuityJson.canonical(record)));
            ObjectNode state = h.fixture.store.current.toJson();
            ObjectNode branch = (ObjectNode) state.get(WriterContracts.ORDINARY_CYCLE_FIELD);
            branch.put("completed_cycles", 5); branch.set("head", newHead.toJson());
            h.fixture.store.current = ContinuityState.fromJson(state, OWNER.machineId());
            h.archive.cycleRef = newHead;
            byte[] before = h.fixture.store.current.canonicalBytes();
            int commits = h.fixture.store.commits;
            h.fixture.store.locked(same -> h.authority.withLocked(same, () -> {
                h.archive.reset();
                var failure = assertThrows(RuntimeException.class, () -> same.preview(h.request()), problem);
                if (problem.equals("repeated-action")) assertTrue(failure.getMessage().contains("occurs twice"));
                if (problem.equals("classification")) assertTrue(failure.getMessage().contains("classification"));
                assertEquals(0, h.archive.actionHistoryReads, problem);
                return null;
            }));
            assertEquals(commits, h.fixture.store.commits, problem);
            assertArrayEquals(before, h.fixture.store.current.canonicalBytes(), problem);
        }
    }

    @Test void readOnlyQualificationCallbackRemovingCheckedMaterialStillRejectsBeforePublication() throws IOException {
        var h = new Harness();
        byte[] before = h.fixture.store.current.canonicalBytes();
        int commits = h.fixture.store.commits;
        RawJson original = h.fixture.archive.materials.get(h.cycleRef);
        h.fixture.store.locked(same -> h.authority.withLocked(same, () -> {
            h.archive.reset(); h.archive.removeAfterActionRead = true;
            assertThrows(RuntimeException.class, () -> same.preview(h.request()));
            assertTrue(h.archive.removed);
            assertEquals(1, h.archive.actionHistoryReads);
            assertEquals(2, h.archive.cycleReads, "final full walk attempted original bytes after callback");
            assertEquals(commits, h.fixture.store.commits);
            assertArrayEquals(before, h.fixture.store.current.canonicalBytes());
            h.fixture.archive.materials.put(h.cycleRef, original);
            h.archive.reset();
            assertNotNull(same.preview(h.request()));
            assertEquals(4, h.archive.cycleReads, "restored original still fully revalidated on next call");
            return null;
        }));
        assertEquals(commits, h.fixture.store.commits);
        assertArrayEquals(before, h.fixture.store.current.canonicalBytes());
    }

    @Test void twoDistinctVisibleRootsNeedTheirOwnCompletedCycles() throws IOException {
        for (String coverage : List.of("both", "missing-second", "wrong-second")) {
            var fixture = new Fixture(false);
            fixture.journal.retainCycle(OWNER, fixture.receipt);
            fixture.journal.settleCycle(OWNER, fixture.receipt,
                    semantic(frame(2, 24024, "completed-first"), TIME.plusSeconds(3)));
            ExactRef firstCycle = ExactRef.fromJson(fixture.store.current.toJson()
                    .get(WriterContracts.ORDINARY_CYCLE_FIELD).get("head"));
            ExactRef firstReceipt = fixture.archive.receiptReferenceOf(fixture.receipt);
            ExactRef previousAction = ContinuityActionJournal.recordHead(fixture.store.current).orElseThrow();

            var before = frame(2, 24024, "completed-first");
            var source = fixture.receipt.command().source();
            var operation = new OperationKey("advance_life");
            List<ExpectedValue> flags = List.of(
                    new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true),
                    new ExpectedBoolean(new FieldKey("timeline.advance_verified"), true),
                    new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), true),
                    new ExpectedText(new FieldKey("progress_status"), "postcondition"));
            var command = new ActionCommand("auto-second-349", before, source, OWNER.sessionId(), operation,
                    new OpportunityJson.Obj(Map.of()),
                    new ExpectedPostcondition(1, before, source, "fixture-observer/v1", flags),
                    new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), TIME.plusSeconds(40));
            var guard = new GuardEvidence(before, source, OWNER.sessionId(), BigInteger.TWO, operation,
                    REF, REF, "fixture", TIME.plusSeconds(4), TIME.plusSeconds(40));
            var observed = new ActionState.EffectObservation(frame(3, 24048, "terminal-second"), source,
                    OWNER.sessionId(), "fixture-observer/v1", flags, new ObservationProvenance.Query("native-second-349"),
                    TIME.plusSeconds(5), REF);
            var second = new ActionReceipt(1, fixture.store.current.sequence() + 1, command,
                    ActionCodec.bodySha256(command), new ActionState.CompositeSettled(
                            new CompositeExecution("advance-life/v1", TIME.plusSeconds(4), guard, List.of()),
                            new ActionState.Applied(observed)));
            fixture.archive.preserveReceipt(second);
            ExactRef secondAction = fixture.archive.preserveRecord(new ActionRecord(second, Optional.of(previousAction)));
            ObjectNode linked = fixture.store.current.toJson(); linked.put("sequence", second.sequence());
            linked.set(ContinuityActionJournal.STATE_FIELD, secondAction.toJson());
            fixture.store.current = ContinuityState.fromJson(linked, OWNER.machineId());
            fixture.journal.retainCycle(OWNER, second);
            fixture.journal.settleCycle(OWNER, second,
                    semantic(frame(3, 24048, "completed-second"), TIME.plusSeconds(6)));
            ExactRef secondCycle = ExactRef.fromJson(fixture.store.current.toJson()
                    .get(WriterContracts.ORDINARY_CYCLE_FIELD).get("head"));
            assertNotEquals(firstCycle, secondCycle);
            ObjectNode actualSecondCycle = ContinuityJson.parseObject(fixture.archive.loadMaterial(secondCycle).bytes(),
                    ContinuityJson.DOCUMENT_MAX_BYTES);
            assertEquals(firstCycle, ExactRef.fromJson(actualSecondCycle.get("previous")));
            assertEquals(fixture.archive.receiptReferenceOf(second), ExactRef.fromJson(actualSecondCycle.get("receipt_ref")));
            var roots = ContinuityActionJournal.receipts(fixture.store.current, fixture.archive);
            assertEquals(2, roots.size());
            assertEquals(2, roots.stream().map(value -> value.command().actionId()).distinct().count());
            assertTrue(roots.stream().allMatch(value -> value.visibleGameplay()
                    && value.outcome() == ActionReceipt.Outcome.APPLIED_CONFIRMED));
            fixture.journal.commit(new JournalInput(OWNER, "batch-349", JournalKind.BATCH_INTERRUPTED,
                    Optional.empty(), Optional.empty(), Optional.empty(), List.of()));
            assertEquals(ContinuityState.Status.REPAIR_REQUIRED, fixture.store.current.status());

            ObjectNode state = fixture.store.current.toJson();
            ObjectNode branch = (ObjectNode) state.get(WriterContracts.ORDINARY_CYCLE_FIELD);
            if (coverage.equals("missing-second")) {
                branch.set("head", firstCycle.toJson()); branch.put("completed_cycles", 4);
            } else if (coverage.equals("wrong-second")) {
                ObjectNode wrong = actualSecondCycle.deepCopy(); wrong.set("receipt_ref", firstReceipt.toJson());
                ExactRef wrongRef = fixture.archive.preserveMaterial(new RawJson(ContinuityJson.canonical(wrong)));
                branch.set("head", wrongRef.toJson());
            }
            fixture.store.current = ContinuityState.fromJson(state, OWNER.machineId());
            var archive = new Reads(fixture, secondCycle);
            var authority = new OrdinaryCycleTransitions(archive, (same, owner, value) -> {
                fixture.store.requireSession(same); assertEquals(OWNER, owner);
                return new OrdinaryCycleTransitions.VerifiedSemantic(value.frame(), value.observedAt(),
                        "fixture-semantic-349", "f".repeat(64));
            }, (same, owner, pair, proof) -> { throw new AssertionError("no private SAVE permission"); },
                    new OriginalWindowReducer.Policy(10958), fixture.store::requireSession);
            fixture.store.authority = authority;
            var details = StrictJson.object(); details.put("evidence_id", "settled-multiroot-349");
            details.put("source", "java-settled-same-game-recovery/v1");
            details.set("session", OrdinaryCycleTransitions.sessionToJson(OWNER));
            details.put("operation", "SETTLED_SAME_GAME_RECOVERY");
            details.put("predecessor_head_digest", fixture.store.head().digest());
            details.put("batch_id", "batch-349"); details.put("next_sequence", 350);
            details.set("cycle_record_ref", branch.get("head"));
            details.set("semantic", OrdinaryCycleTransitions.semanticToJson(
                    semantic(frame(4, 24048, "fresh-two-root-recovery"), TIME.plusSeconds(9))));
            var request = new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,
                    ContinuityJson.canonical(details), List.of());
            byte[] original = fixture.store.current.canonicalBytes(); int commits = fixture.store.commits;
            fixture.store.locked(same -> authority.withLocked(same, () -> {
                if (coverage.equals("both")) {
                    var prepared = same.preview(request);
                    assertEquals(same.head().digest(), prepared.predecessor().digest());
                    assertEquals(fixture.store.current.settledCycles(), prepared.reduced().settledCycles());
                } else {
                    var rejected = assertThrows(IllegalArgumentException.class, () -> same.preview(request), coverage);
                    assertTrue(rejected.getMessage().contains(coverage.equals("missing-second")
                            ? "cannot discard a visible action" : "occurs twice"), rejected.getMessage());
                }
                return null;
            }));
            assertEquals(commits, fixture.store.commits, coverage);
            assertArrayEquals(original, fixture.store.current.canonicalBytes(), coverage);
        }
    }

    private static final class Harness {
        final Fixture fixture = new Fixture(false);
        final ExactRef cycleRef;
        final Reads archive;
        final OrdinaryCycleTransitions authority;
        Harness() throws IOException {
            fixture.journal.retainCycle(OWNER, fixture.receipt);
            fixture.journal.settleCycle(OWNER, fixture.receipt,
                    semantic(frame(2, 24024, "completed"), TIME.plusSeconds(3)));
            cycleRef = ExactRef.fromJson(fixture.store.current.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD).get("head"));
            fixture.journal.commit(new JournalInput(OWNER, "batch-344", JournalKind.BATCH_INTERRUPTED,
                    Optional.empty(), Optional.empty(), Optional.empty(), List.of()));
            assertEquals(ContinuityState.Status.REPAIR_REQUIRED, fixture.store.current.status());
            archive = new Reads(fixture, cycleRef);
            authority = new OrdinaryCycleTransitions(archive, (same, owner, value) -> {
                fixture.store.requireSession(same); assertEquals(OWNER, owner);
                return new OrdinaryCycleTransitions.VerifiedSemantic(value.frame(), value.observedAt(), "fixture-semantic", "f".repeat(64));
            }, (same, owner, pair, proof) -> { throw new AssertionError("no SAVE verifier permission in this fixture"); },
                    new OriginalWindowReducer.Policy(10958), fixture.store::requireSession);
            fixture.store.authority = authority;
        }
        WriterContracts.Request request() {
            var row = StrictJson.object(); row.put("evidence_id", "settled-recovery-344");
            row.put("source", "java-settled-same-game-recovery/v1");
            row.set("session", OrdinaryCycleTransitions.sessionToJson(OWNER));
            row.put("operation", "SETTLED_SAME_GAME_RECOVERY");
            row.put("predecessor_head_digest", fixture.store.head().digest());
            row.put("batch_id", "batch-344"); row.put("next_sequence", 345);
            row.set("cycle_record_ref", fixture.store.current.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD).get("head"));
            row.set("semantic", OrdinaryCycleTransitions.semanticToJson(
                    semantic(frame(3, 24024, "fresh-recovery"), TIME.plusSeconds(6))));
            return new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND, ContinuityJson.canonical(row), List.of());
        }
    }

    private static final class Reads implements ActionPorts.OutcomeArchive {
        final Fixture fixture;
        ExactRef cycleRef;
        int cycleReads, receiptQualifications, actionHistoryReads;
        boolean historySeen, removeAfterActionRead, removed;
        Reads(Fixture fixture, ExactRef cycleRef) { this.fixture = fixture; this.cycleRef = cycleRef; }
        void reset() {
            cycleReads = 0; receiptQualifications = 0; actionHistoryReads = 0;
            historySeen = false; removeAfterActionRead = false; removed = false;
        }
        void actual(ContinuityStorePort.Session same) {
            try { fixture.store.requireSession(same); } catch (IOException failure) { throw new UncheckedIOException(failure); }
        }
        @Override public ActionPorts.OutcomeArchive withSession(ContinuityStorePort.Session same) { actual(same); return this; }
        @Override public <T> T inSession(ContinuityStorePort.Session same, Function<ActionPorts.OutcomeArchive, T> work) {
            actual(same); return work.apply(this);
        }
        @Override public ActionRecord loadRecord(ExactRef ref) {
            historySeen = true; actionHistoryReads++; return fixture.archive.loadRecord(ref);
        }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { return fixture.archive.loadReceipt(ref); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) {
            ExactRef exact = fixture.archive.receiptReferenceOf(value); receiptQualifications++;
            if (historySeen && removeAfterActionRead && !removed) {
                assertNotNull(fixture.archive.materials.remove(cycleRef)); removed = true;
            }
            return exact;
        }
        @Override public RawJson loadMaterial(ExactRef ref) {
            if (cycleRef.equals(ref)) cycleReads++;
            return fixture.archive.loadMaterial(ref);
        }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { return fixture.archive.recordReferenceOf(value); }
        @Override public ExactRef materialReferenceOf(RawJson value) { return fixture.archive.materialReferenceOf(value); }
        private static <T> T denied() { throw new AssertionError("read-only fixture cannot publish or query originals"); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value) { return denied(); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref) { return denied(); }
        @Override public ExactRef preserveRequest(NativeRequest value) { return denied(); }
        @Override public NativeRequest loadRequest(ExactRef ref) { return denied(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value) { return denied(); }
        @Override public ExactRef requestReferenceOf(NativeRequest value) { return denied(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt value) { return denied(); }
        @Override public PlanningReadReceipt loadRead(ExactRef ref) { return denied(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value) { return denied(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { return denied(); }
        @Override public ExactRef preserveReceipt(ActionReceipt value) { return denied(); }
        @Override public ExactRef preserveMaterial(RawJson value) { return denied(); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value) { return denied(); }
        @Override public byte[] loadNativeFrame(ExactRef ref) { return denied(); }
    }
}
