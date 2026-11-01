package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Source-owned DATA replay and rejecting writer ports only; no private issuer is forged and no physical/Game permission is provided. */
final class OrdinaryDeferredRecovery222Test {
    private static final Instant TIME = Instant.parse("2026-10-23T20:00:00Z");
    private static final SessionIdentity OWNER = new SessionIdentity("fixture-machine-1",
            new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001"))), "ordinary-1");
    private static final ExactRef REF = ref("source", "a");
    private static ExactRef ref(String name, String digit) { return new ExactRef("D:/fixture/" + name + ".json", 1, digit.repeat(64)); }
    private static ObservationIdentity frame(long revision, long date, String snapshot) {
        return new ObservationIdentity(OWNER.machineId(), OWNER.game(), new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(revision), BigInteger.valueOf(date)), snapshot, BigInteger.valueOf(revision), "episode-1"), 1);
    }
    private static SemanticEvidence semantic(ObservationIdentity frame, Instant time) {
        return new SemanticEvidence(frame, ref("semantic-" + time.getEpochSecond(), "b"), ref("native", "c"), ref("driver-stamp", "d"), ref("driver", "e"), time);
    }

    private static Fixture closed(JournalKind kind) throws IOException {
        var f = new Fixture(false);
        f.journal.retainCycle(OWNER, f.receipt);
        f.journal.settleCycle(OWNER, f.receipt, semantic(frame(2, 24024, "completed"), TIME.plusSeconds(3)));
        f.journal.commit(new JournalInput(OWNER, "batch-85", kind, Optional.empty(), Optional.empty(), Optional.empty(), List.of()));
        return f;
    }
    private static ObjectNode recovery(ContinuityState before, SemanticEvidence fresh) {
        var row = StrictJson.object();
        row.put("evidence_id", "settled-same-game:" + ContinuityJson.digest(before.toJson()));
        row.put("source", "java-settled-same-game-recovery/v1");
        row.set("session", OrdinaryCycleTransitions.sessionToJson(OWNER));
        row.put("operation", "SETTLED_SAME_GAME_RECOVERY");
        row.put("predecessor_head_digest", ContinuityJson.digest(before.toJson()));
        row.put("batch_id", "batch-85"); row.put("next_sequence", 86);
        row.set("cycle_record_ref", before.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD).get("head"));
        row.set("semantic", OrdinaryCycleTransitions.semanticToJson(fresh));
        return row;
    }
    private static WriterContracts.Request request(ObjectNode details) {
        return new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND, ContinuityJson.canonical(details), List.of());
    }
    private static SemanticEvidence fresh() { return semantic(frame(3, 24024, "fresh-recovery"), TIME.plusSeconds(6)); }
    private static WriterContracts.HistoricalTransition edge(Fixture f, ContinuityState before,
            WriterContracts.Request request, ContinuityState reduced) {
        long seq = before.sequence() + 1;
        ObjectNode after = reduced.toJson(); after.put("sequence", seq); after.put("last_event_identity", request.identity());
        var pin = new WriterContracts.Pin(REF, new WriterContracts.FileIdentity("1", "9007199254740993", "134000000000000001", TIME.toString(), 1));
        return new WriterContracts.HistoricalTransition(seq, request.kind(), request.details(), request.identity(), before,
                ContinuityState.fromJson(after, OWNER.machineId()), pin);
    }

    @Test void deferredPureReplayChangesOnlyBindingAndPreservesEverySavedAndCycleField() throws IOException {
        var f = closed(JournalKind.BATCH_DEFERRED); var before = f.store.current;
        var request = request(recovery(before, fresh())); var reduced = f.authority.reduce(before, request);
        var a = before.toJson(); var b = reduced.toJson(); a.remove("latest_binding"); b.remove("latest_binding");
        assertEquals(a, b); assertEquals(before.settledCycles(), reduced.settledCycles());
        assertEquals(before.settledDateRaw(), reduced.settledDateRaw());
        assertEquals(3, reduced.toJson().get("latest_binding").get("native_revision").longValue());
        f.authority.requireSettledSameGameHistoryEdge(edge(f, before, request, reduced), OWNER);
    }

    @Test void deferredReplayRejectsAnotherBatchOwnerAndUnexpectedBoundaryFields() throws IOException {
        var f = closed(JournalKind.BATCH_DEFERRED); var original = f.store.current;
        for (String problem : List.of("batch", "owner", "extra")) {
            ObjectNode state = original.toJson(); var boundary = (ObjectNode) state.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
            if (problem.equals("batch")) boundary.put("batch_id", "other-batch");
            if (problem.equals("owner")) ((ObjectNode) boundary.get("session")).put("session_id", "other-session");
            if (problem.equals("extra")) boundary.put("unexpected", true);
            var changed = ContinuityState.fromJson(state, OWNER.machineId());
            assertThrows(IllegalArgumentException.class, () -> f.authority.reduce(changed, request(recovery(changed, fresh()))), problem);
        }
    }

    @Test void deferredReplayRejectsWrongRunningBoundaryAndPendingCycle() throws IOException {
        var f = closed(JournalKind.BATCH_DEFERRED); var original = f.store.current;
        for (String kind : List.of("BATCH_INTERRUPTED", "SAVE_CONFIRMED", "BATCH_FINISHED")) {
            ObjectNode state = original.toJson(); ((ObjectNode)state.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)).put("boundary", kind);
            var changed = ContinuityState.fromJson(state, OWNER.machineId());
            assertThrows(IllegalArgumentException.class, () -> f.authority.reduce(changed, request(recovery(changed, fresh()))));
        }
        ObjectNode state = original.toJson(); ((ObjectNode)state.get(WriterContracts.ORDINARY_CYCLE_FIELD)).set("pending_receipt", REF.toJson());
        var pending = ContinuityState.fromJson(state, OWNER.machineId());
        assertThrows(IllegalArgumentException.class, () -> f.authority.reduce(pending, request(recovery(pending, fresh()))));
    }

    @Test void deferredReplayRejectsChangedHeadRegressedObservationAndChangedAfterCredit() throws IOException {
        var f = closed(JournalKind.BATCH_DEFERRED); var before = f.store.current;
        var wrong = recovery(before, fresh()); wrong.put("predecessor_head_digest", "0".repeat(64));
        assertThrows(IllegalArgumentException.class, () -> f.authority.reduce(before, request(wrong)));
        var wrongRecord = recovery(before, fresh()); wrongRecord.set("cycle_record_ref", REF.toJson());
        assertThrows(IllegalArgumentException.class, () -> f.authority.reduce(before, request(wrongRecord)));
        var regression = recovery(before, semantic(frame(1, 24000, "regressed"), TIME.plusSeconds(6)));
        assertThrows(IllegalArgumentException.class, () -> f.authority.reduce(before, request(regression)));
        var req = request(recovery(before, fresh())); var good = edge(f, before, req, f.authority.reduce(before, req));
        var after = good.after().toJson(); after.put("last_settled_cycles", good.after().settledCycles() + 1);
        var tampered = new WriterContracts.HistoricalTransition(good.sequence(), good.kind(), good.details(), good.eventIdentity(),
                good.before(), ContinuityState.fromJson(after, OWNER.machineId()), good.eventPin());
        assertThrows(IllegalArgumentException.class, () -> f.authority.requireSettledSameGameHistoryEdge(tampered, OWNER));
    }

    @Test void deferredWithoutPrivateSavedIssuerCannotPreviewOrCommitEvenWithValidReplayData() throws IOException {
        var f = closed(JournalKind.BATCH_DEFERRED); var before = f.store.current; int commits = f.store.commits;
        var req = request(recovery(before, fresh())); var reduced = f.authority.reduce(before, req);
        f.store.locked(same -> f.authority.withLocked(same, () -> {
            var previewFailure = assertThrows(IllegalArgumentException.class, () -> same.preview(req));
            assertTrue(previewFailure.getMessage().contains("fully verified saved history role"));
            var described = new WriterContracts.Prepared(same.head(), req, List.of(), List.of(), reduced, "a".repeat(64));
            var commitFailure = assertThrows(IllegalArgumentException.class, () -> same.commit(described));
            assertTrue(commitFailure.getMessage().contains("fully verified saved history role"));
            return null;
        }));
        assertEquals(commits, f.store.commits); assertArrayEquals(before.canonicalBytes(), f.store.current.canonicalBytes());
    }

    @Test void startedStillRequiresTheOriginalOpenRecoveryAnchor() throws IOException {
        var f = closed(JournalKind.BATCH_STARTED); var before = f.store.current;
        var req = request(recovery(before, fresh()));
        f.store.locked(same -> f.authority.withLocked(same, () -> {
            var failure = assertThrows(IllegalArgumentException.class, () -> same.preview(req));
            assertTrue(failure.getMessage().contains("actual recovery producer"));
            return null;
        }));
        assertArrayEquals(before.canonicalBytes(), f.store.current.canonicalBytes());
    }
    private static CheckpointPair pair(ObservationIdentity frame) {
        return new CheckpointPair(new CheckpointPair.FileWitness(ref("save", "7"), new FileStatIdentity(BigInteger.ONE, "9007199254740993", "134000000000000001")),
                new CheckpointPair.FileWitness(ref("driver", "e"), new FileStatIdentity(BigInteger.ONE, "9007199254740995", "134000000000000003")),
                frame, "lineage-1", 1, "save-1", REF, TIME.plusSeconds(4));
    }
    private static final class Fixture {
        final Archive archive = new Archive(); final Store store = new Store(); final OrdinaryCycleTransitions authority; final ContinuityBatchJournal journal;
        ActionReceipt receipt; boolean rejectSemantic; int checkpointChecks;
        Fixture(boolean controlOnly) {
            authority = new OrdinaryCycleTransitions(archive, (session, owner, semantic) -> {
                assertTrue(store.open); assertSame(store.session, session); assertEquals(OWNER, owner);
                if (rejectSemantic) throw new IOException("actual archived native/Driver changed");
                return new OrdinaryCycleTransitions.VerifiedSemantic(semantic.frame(), semantic.observedAt(), "archive-" + semantic.semantic().sha256(), "f".repeat(64));
            }, (session, owner, pair, proof) -> { assertTrue(store.open); checkpointChecks++; return "a".repeat(64); }, new OriginalWindowReducer.Policy(10958),
                    session -> { if (session != store.session) throw new IOException("another writer object's session is not the original authority"); assertTrue(store.open); });
            store.authority = authority; journal = new ContinuityBatchJournal(store, authority); install(makeReceipt(controlOnly));
        }
        void install(ActionReceipt value) {
            receipt = value; ExactRef receiptRef = archive.preserveReceipt(value); assertEquals(value, archive.loadReceipt(receiptRef));
            ExactRef record = archive.preserveRecord(new ActionRecord(value, Optional.empty())); ObjectNode row = store.current.toJson();
            row.put("sequence", value.sequence()); row.set(ContinuityActionJournal.STATE_FIELD, record.toJson()); store.current = ContinuityState.fromJson(row, OWNER.machineId());
        }
        private ActionReceipt makeReceipt(boolean controlOnly) {
            var before = frame(1, 24000, "before"); var after = controlOnly ? frame(1, 24000, "modal") : frame(2, 24024, "after");
            var source = new G2Source(OWNER.machineId(), TIME.toString(), "fixture-build", REF); var operation = new OperationKey("advance_life");
            List<ExpectedValue> flags = List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), !controlOnly),
                    new ExpectedBoolean(new FieldKey("timeline.advance_verified"), !controlOnly), new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), !controlOnly),
                    new ExpectedText(new FieldKey("progress_status"), controlOnly ? "modal_pending" : "postcondition"));
            var command = new ActionCommand("auto-1", before, source, OWNER.sessionId(), operation, new OpportunityJson.Obj(Map.of()),
                    new ExpectedPostcondition(1, before, source, "fixture-observer/v1", flags), new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), TIME.plusSeconds(10));
            var guard = new GuardEvidence(before, source, OWNER.sessionId(), BigInteger.ONE, operation, REF, REF, "fixture", TIME, TIME.plusSeconds(10));
            ActionState state;
            if (controlOnly) {
                var terminal = new GuardEvidence(after, source, OWNER.sessionId(), BigInteger.ONE, new OperationKey("advance_clock_status"), REF, REF, "fixture", TIME.plusSeconds(2), TIME.plusSeconds(10));
                var readGuard = new PlanningReadGuard(terminal, true, true, true, "a".repeat(64));
                var readRequest = new PlanningReadRequest(after, source, OWNER.sessionId(), new OperationKey("advance_clock_status"), new OpportunityJson.Obj(Map.of()), TIME.plusSeconds(10));
                var raw = new RawJson("{}".getBytes(StandardCharsets.UTF_8));
                var read = new PlanningReadReceipt(readRequest, "status/v1", "status-2", readGuard, readGuard,
                        new NativeActionPort.AckReceived("status-2", true, Optional.of(raw), raw, raw.bytes()));
                var request = new NativeRequest("advance_clock_cancel", Optional.empty(), raw);
                var attempt = new ActionState.Attempt("cancel-1", TIME.plusSeconds(1), guard, request);
                state = new ActionState.Settled(attempt, new NativeActionPort.AckReceived("cancel-1", true, Optional.of(raw), raw, raw.bytes()), new ActionState.ControlApplied(read, "status/v1", flags));
            } else {
                var observed = new ActionState.EffectObservation(after, source, OWNER.sessionId(), "fixture-observer/v1", flags, new ObservationProvenance.Query("native-read-2"), TIME.plusSeconds(2), REF);
                state = new ActionState.CompositeSettled(new CompositeExecution("advance-life/v1", TIME, guard, List.of()), new ActionState.Applied(observed));
            }
            return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), state);
        }
    }
    private static final class Store implements ContinuityStorePort {
        ContinuityState current = initial(); OrdinaryCycleTransitions authority; boolean open; int commits;
        private Thread ownerThread;
        final Session session = new Session() {
            @Override public void requireWriter(java.nio.file.Path originalWriterLock) {
                throw new AssertionError("in-memory cycle fixture has no physical writer-lock authority");
            }
            @Override public WriterContracts.Pin capturePin(ExactRef reference, int maximumBytes) {
                throw new AssertionError("in-memory cycle fixture cannot capture a physical file pin");
            }
            @Override public void verifyPin(WriterContracts.Pin pin) {
                throw new AssertionError("in-memory cycle fixture cannot verify a physical file pin");
            }
            @Override public WriterContracts.Head head() { assertTrue(open); return Store.this.head(); }
            @Override public WriterContracts.Prepared preview(WriterContracts.Request request) throws IOException {
                assertTrue(open); var before = head(); String checked = authority.revalidate(before, request);
                return new WriterContracts.Prepared(before, request, List.of(), List.of(), authority.reduce(current, request), checked);
            }
            @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) throws IOException {
                assertTrue(open); assertEquals(prepared.predecessor().digest(), head().digest());
                assertEquals(prepared.preconditionDigest(), authority.revalidate(head(), prepared.request()));
                var reduced = authority.reduce(current, prepared.request()); assertArrayEquals(prepared.reduced().canonicalBytes(), reduced.canonicalBytes());
                ObjectNode row = reduced.toJson(); row.put("sequence", current.sequence() + 1); current = ContinuityState.fromJson(row, OWNER.machineId()); commits++;
                return new WriterContracts.Receipt(WriterContracts.Disposition.COMMITTED, current, prepared.request().identity(), 1, false);
            }
            @Override public ExactRef persistedHead() { assertTrue(open); return REF; }
        };
        WriterContracts.Head head() { return new WriterContracts.Head(current, List.of(), List.of(), List.of(), false); }
        @Override public void requireSession(ContinuityStorePort.Session actual)throws IOException { if(!open||actual!=session||Thread.currentThread()!=ownerThread)throw new IOException("not the active original fixture writer session"); }
        @Override public <T> T locked(SessionWork<T> work) throws IOException { assertFalse(open); open = true; ownerThread = Thread.currentThread(); try { return work.run(session); } finally { open = false; ownerThread = null; } }
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request) throws IOException { return locked(view -> view.preview(request)); }
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) throws IOException { return locked(view -> view.commit(prepared)); }
        @Override public ExactRef persistedHead() { return REF; }
        private static ContinuityState initial() {
            ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", OWNER.machineId()); row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running");
            row.put("start_date_raw", 24000); row.put("target_date_raw", 286992); row.put("target_days", 10958); row.put("last_settled_cycles", 3); row.put("last_settled_date_raw", 24000); row.put("binding_lineage_count", 0);
            ObjectNode bound = row.putObject("latest_binding"); bound.put("date_raw", 24000); bound.put("actor_character_id", 29829); bound.put("episode_run_id", "episode-1"); bound.put("snapshot_id", "baseline"); bound.put("revision", 1); bound.put("native_revision", 1);
            return ContinuityState.fromJson(row, OWNER.machineId());
        }
    }
    private static final class Archive implements ActionPorts.OutcomeArchive {
        final Map<ExactRef, ActionReceipt> receipts = new HashMap<>(); final Map<ExactRef, ActionRecord> records = new HashMap<>(); final Map<ExactRef, RawJson> materials = new HashMap<>();
        ExactRef lastMaterial;
        @Override public <T> T inSession(ContinuityStorePort.Session session, java.util.function.Function<ActionPorts.OutcomeArchive,T> work) { return work.apply(this); }
        @Override public ActionPorts.OutcomeArchive withSession(ContinuityStorePort.Session session) { return this; }
        @Override public ExactRef preserveReceipt(ActionReceipt value) { ExactRef ref = ref("receipt-" + value.sequence(), "1"); receipts.put(ref,value); return ref; }
        @Override public ActionReceipt loadReceipt(ExactRef ref) { return Optional.ofNullable(receipts.get(ref)).orElseThrow(); }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value) { return receipts.entrySet().stream().filter(entry -> entry.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public ExactRef preserveRecord(ActionRecord value) { ExactRef ref = ref("record-" + value.receipt().sequence(), "2"); records.put(ref,value); return ref; }
        @Override public ActionRecord loadRecord(ExactRef ref) { return Optional.ofNullable(records.get(ref)).orElseThrow(); }
        @Override public ExactRef recordReferenceOf(ActionRecord value) { return records.entrySet().stream().filter(entry -> entry.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        @Override public ExactRef preserveMaterial(RawJson value) { String sha = ActionCodec.sha256(value.bytes()); ExactRef ref = new ExactRef("D:/fixture/material-" + sha + ".json", value.bytes().length, sha); materials.put(ref,value); lastMaterial=ref; return ref; }
        @Override public RawJson loadMaterial(ExactRef ref) { return Optional.ofNullable(materials.get(ref)).orElseThrow(); }
        @Override public ExactRef materialReferenceOf(RawJson value) { return materials.entrySet().stream().filter(entry -> entry.getValue().equals(value)).map(Map.Entry::getKey).findFirst().orElseThrow(); }
        ObjectNode latestMaterial() { return ContinuityJson.parseObject(materials.get(lastMaterial).bytes(), ContinuityJson.DOCUMENT_MAX_BYTES); }
        private static <T> T unexpected() { throw new AssertionError("unrequested native/archive operation"); }
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome original) { return unexpected(); }
        @Override public NativeActionPort.DispatchOutcome load(ExactRef original) { return unexpected(); }
        @Override public ExactRef preserveRequest(NativeRequest original) { return unexpected(); }
        @Override public NativeRequest loadRequest(ExactRef original) { return unexpected(); }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome original) { return unexpected(); }
        @Override public ExactRef requestReferenceOf(NativeRequest original) { return unexpected(); }
        @Override public ExactRef preserveRead(PlanningReadReceipt original) { return unexpected(); }
        @Override public PlanningReadReceipt loadRead(ExactRef original) { return unexpected(); }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt original) { return unexpected(); }
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame original) { return unexpected(); }
        @Override public byte[] loadNativeFrame(ExactRef original) { return unexpected(); }
    }
}
