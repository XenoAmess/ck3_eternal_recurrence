package org.xar.ck3.control.application.session;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.List;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class ExternalSaveRemountTest {
    @TempDir Path root;
    @Test void observedRemountDefersOnlyTheActualEmptyBatchAndPreservesOriginalSavedFrontier() throws Exception {
        try (var raw = getClass().getResourceAsStream("source56-named-remount.json.gz");
             var fixture = new GZIPInputStream(raw)) {
            var observed = StrictJson.parse(fixture.readAllBytes(), ContinuityJson.DOCUMENT_MAX_BYTES);
            var v1 = (ObjectNode) observed.get("v1");
            var previous = ExternalSaveOrigin.fromJson(v1.get("origin"));
            assertTrue(ContinuityJson.same(v1.get("origin"), previous.toJson()));
            var before = ContinuityState.fromJson((ObjectNode) observed.get("head"), previous.successor().machineId());
            var previousRef = ExactRef.fromJson(v1.get("origin_ref"));
            assertEquals(65, before.sequence());
            var game = new GameGeneration(previous.successor().game().pid() + 1, previous.successor().game().creationFiletime());
            var successor = new SessionIdentity(previous.successor().machineId(), game, "software-remount-successor");
            var session = new TransportSession(successor.machineId(), game, BigInteger.ONE, successor.sessionId());
            var opening = new ExternalSaveOrigin.NativeOpening(session, previous.opening().actor(),
                    previous.opening().dateRaw(), "native:1", BigInteger.ONE);
            var batch = before.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD).path("batch_id").textValue();
            var loaded = previous.loadedFile();
            var oldSave = loaded.reference();
            var copy = new CheckpointPair.FileWitness(new ExactRef(oldSave.path() + ".software-test", oldSave.bytes(), oldSave.sha256()), loaded.identity());
            var remount = new ExternalSaveOrigin(before.sequence(), ContinuityJson.digest(before.toJson()),
                    previous.successor(), successor, previous.savedPair(), copy, previous.retiredActionHead(),
                    opening, Optional.of(previousRef), Optional.of(batch));
            remount.requirePreviousOrigin(previous);
            assertEquals(remount, ExternalSaveOrigin.fromJson(remount.toJson()));
            var archive = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ExternalSaveRemountTest.class.getClassLoader(),
                    new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                        throw new AssertionError("pure replay accessed an original: " + method);
                    });
            var cycles = new OrdinaryCycleTransitions(archive, (same, owner, original) -> { throw new AssertionError(); },
                    (same, owner, pair, proof) -> { throw new AssertionError(); },
                    new OriginalWindowReducer.Policy(before.origin().targetDays()), same -> { throw new AssertionError(); });
            var details = v1.deepCopy();
            details.put("source", ExternalSaveOrigin.REMOUNT_SOURCE);
            details.set("session", OrdinaryCycleTransitions.sessionToJson(successor));
            details.set("origin", remount.toJson());
            var reference = new ExactRef("software:remount-origin", 1, "a".repeat(64));
            details.set("origin_ref", reference.toJson());
            var semantic = (ObjectNode) details.get("semantic");
            var identity = (ObjectNode) semantic.get("frame");
            identity.set("game", game.toJson());
            ((ObjectNode) identity.get("frame")).put("native_revision", "1").put("revision", "1").put("snapshot_id", "native:1");
            var request = new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND,
                    ContinuityJson.canonical(details), List.of());
            var after = actualWriterCommit(before, cycles, request);

            assertEquals(game, GameGeneration.fromJson(after.toJson().get("game_binding")));
            assertEquals(53179944, after.toJson().path("latest_binding").path("date_raw").longValue());
            assertEquals(53179344, after.settledDateRaw());
            assertEquals(471, (after.settledDateRaw() - after.origin().startDateRaw()) / 24);
            assertEquals(before.settledCycles(), after.settledCycles());
            assertEquals(57, after.toJson().path(OrdinaryCycleTransitions.STATE_FIELD).path("completed_cycles").longValue());
            assertEquals(ContinuityActionJournal.recordHead(before), ContinuityActionJournal.recordHead(after));
            var boundary = after.toJson().path(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
            assertEquals(batch, boundary.path("batch_id").textValue());
            assertEquals("BATCH_DEFERRED", boundary.path("boundary").textValue());
            assertEquals(previous.successor(), OrdinaryCycleTransitions.sessionFromJson(boundary.get("session")));
            assertEquals(reference, ExactRef.fromJson(after.toJson().get(WriterContracts.ORDINARY_EXTERNAL_SAVE_ORIGIN_FIELD)));

            var wrongFile = new CheckpointPair.FileWitness(new ExactRef(copy.reference().path(), oldSave.bytes(), "b".repeat(64)), loaded.identity());
            var wrong = new ExternalSaveOrigin(remount.predecessorSequence(), remount.predecessorDigest(),
                    remount.departed(), remount.successor(), remount.savedPair(), wrongFile, remount.retiredActionHead(),
                    remount.opening(), remount.previousOrigin(), remount.deferredBatch());
            assertThrows(IllegalArgumentException.class, () -> wrong.requirePreviousOrigin(previous));
        }
    }

    @Test void remountKeepsTheOriginalWasNeverSentAndItsInterruptedBatch() throws Exception {
        try (var raw = getClass().getResourceAsStream("source56-named-zero-dispatch.json.gz");
             var compressed = new GZIPInputStream(raw)) {
            var fixture = StrictJson.parse(compressed.readAllBytes(), StrictJson.EXPLICIT_MAX_BYTES);
            var events = fixture.get("events");
            var previousEvent = events.get(0);
            var details = ((ObjectNode) previousEvent.get("details")).deepCopy();
            var previous = ExternalSaveOrigin.fromJson(details.get("origin"));
            var previousRef = ExactRef.fromJson(details.get("origin_ref"));
            var machine = previous.successor().machineId();
            var before = ContinuityState.fromJson(events.get(5).get("after"), machine);
            assertEquals(71, before.sequence());
            assertEquals(ContinuityState.Status.REPAIR_REQUIRED, before.status());

            var archive = archivedActionData(fixture.get("materials"));
            var edges = historicalEdges(events, machine, 2, 4);
            var source = archive.loadRecord(ExactRef.fromJson(events.get(2).get("details").get("receipt_ref"))).receipt().command().source();
            var zero = ContinuityBatchJournal.verifyExternalZeroDispatch(edges, previous, source, archive);
            assertEquals(ContinuityActionJournal.recordHead(before).orElseThrow(), zero);
            var terminal = archive.loadRecord(zero).receipt();
            assertEquals(ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH, terminal.outcome());
            assertEquals(0, ((ActionState.RejectedBeforeDispatch) terminal.state()).dispatch().proof().requestBytesWritten());
            assertFalse(terminal.visibleGameplay());
            assertFalse(terminal.eligibleAdvance());
            assertThrows(IllegalArgumentException.class,
                    () -> ContinuityBatchJournal.verifyExternalZeroDispatch(edges.subList(0, 2), previous, source, archive));

            var game = new GameGeneration(previous.successor().game().pid() + 1, previous.successor().game().creationFiletime());
            var successor = new SessionIdentity(machine, game, "software-after-zero-write");
            var opening = new ExternalSaveOrigin.NativeOpening(new TransportSession(machine, game, BigInteger.ONE, successor.sessionId()),
                    previous.opening().actor(), previous.opening().dateRaw(), "native:1", BigInteger.ONE);
            var candidate = new ExternalSaveOrigin(before.sequence(), ContinuityJson.digest(before.toJson()), previous.successor(), successor,
                    previous.savedPair(), previous.loadedFile(), previous.retiredActionHead(), opening, Optional.of(previousRef),
                    Optional.empty(), Optional.of(zero));
            candidate.requirePreviousOrigin(previous);
            assertEquals(candidate, ExternalSaveOrigin.fromJson(candidate.toJson()));
            assertThrows(IllegalArgumentException.class, () -> candidate.requireOriginal(edges.getLast().after()));
            details.put("source", ExternalSaveOrigin.ZERO_DISPATCH_REMOUNT_SOURCE);
            details.set("session", OrdinaryCycleTransitions.sessionToJson(successor));
            details.set("origin", candidate.toJson());
            details.set("origin_ref", new ExactRef("fixture:zero-dispatch-origin", 1, "f".repeat(64)).toJson());
            var frame = (ObjectNode) details.get("semantic").get("frame");
            frame.set("game", game.toJson());
            ((ObjectNode) frame.get("frame")).put("native_revision", "1").put("revision", "1").put("snapshot_id", "native:1");
            var request = new WriterContracts.Request(OrdinaryCycleTransitions.CYCLE_KIND, ContinuityJson.canonical(details), List.of());
            var cycles = new OrdinaryCycleTransitions(archive, (same, owner, original) -> { throw new AssertionError(); },
                    (same, owner, pair, proof) -> { throw new AssertionError(); },
                    new OriginalWindowReducer.Policy(before.origin().targetDays()), same -> { throw new AssertionError(); });
            var committed = actualWriterCommit(before, cycles, request);
            assertEquals(ContinuityState.Status.RUNNING, committed.status());
            assertEquals(game, GameGeneration.fromJson(committed.toJson().get("game_binding")));
            assertEquals(53179344, committed.settledDateRaw());
            assertEquals(53179944, committed.toJson().path("latest_binding").path("date_raw").longValue());
            assertEquals(471, (committed.settledDateRaw() - committed.origin().startDateRaw()) / 24);
            assertEquals(before.settledCycles(), committed.settledCycles());
            assertEquals(ContinuityActionJournal.recordHead(before), ContinuityActionJournal.recordHead(committed));
            assertEquals(before.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD),
                    committed.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD));
        }
    }

    @Test void sameNamedGameRetainsItsPositiveUnknownAndEarlierObservations() throws Exception {
        try (var raw = getClass().getResourceAsStream("source56-named-full111-pending.json.gz");
             var compressed = new GZIPInputStream(raw)) {
            var fixture = StrictJson.parse(compressed.readAllBytes(), StrictJson.EXPLICIT_MAX_BYTES);
            var events = fixture.get("events");
            var origin = ExternalSaveOrigin.fromJson(events.get(0).get("details").get("origin"));
            var head = ContinuityState.fromJson(events.get(7).get("after"), origin.successor().machineId());
            var archive = archivedActionData(fixture.get("materials"));
            var edges = historicalEdges(events, origin.successor().machineId(), 2, 6);
            var source = archive.loadRecord(ExactRef.fromJson(events.get(2).get("details").get("receipt_ref")))
                    .receipt().command().source();
            var replay = ContinuityBatchJournal.verifyExternalFull111Action(edges, origin, source, archive, true);
            assertEquals(79, head.sequence());
            assertEquals(ContinuityState.Status.REPAIR_REQUIRED, head.status());
            assertEquals(53179344, head.settledDateRaw());
            assertEquals(ContinuityActionJournal.recordHead(head).orElseThrow(), replay.getKey());
            assertEquals(List.of(77L, 78L), replay.getValue().stream().map(ActionReceipt::sequence).toList());
            assertEquals(replay.getValue().getFirst().ack(), replay.getValue().getLast().ack());
            assertTrue(replay.getValue().getLast().ack().orElseThrow().nativeOk());
            assertFalse(replay.getValue().getLast().settled());
            assertThrows(ContractViolationException.class, () ->
                    ContinuityBatchJournal.verifyExternalZeroDispatch(edges.subList(0, 3), origin, source, archive));
        }
    }

    @Test void sameNamedGameCanRetainTheOriginalAppliedClosureAfterRestart() throws Exception {
        try (var raw = getClass().getResourceAsStream("source56-named-full111-pending.json.gz");
             var compressed = new GZIPInputStream(raw)) {
            var fixture = StrictJson.parse(compressed.readAllBytes(), StrictJson.EXPLICIT_MAX_BYTES);
            var events = fixture.get("events");
            var origin = ExternalSaveOrigin.fromJson(events.get(0).get("details").get("origin"));
            var owner = origin.successor();
            var archive = archivedActionData(fixture.get("materials"));
            var capture = archive.loadRecord(ExactRef.fromJson(events.get(6).get("details").get("receipt_ref"))).receipt();
            var edge = historicalEdges(events, owner.machineId(), 8, 8).getFirst();
            var closure = ContinuityBatchJournal.verifyExternalFull111Closure(edge, capture, capture.command().source(), archive);
            assertEquals(80, closure.getValue().sequence());
            assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED, closure.getValue().outcome());
            assertEquals(53179344, edge.after().settledDateRaw());
            assertEquals(5, edge.after().toJson().path("latest_binding").path("native_revision").longValue());
            assertEquals(BigInteger.valueOf(6), closure.getValue().command().before().frame().identity().nativeRevision());
            var prior = ContinuityState.fromJson(fixture.get("prior"), owner.machineId());
            var same = (org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session) Proxy.newProxyInstance(
                    getClass().getClassLoader(),
                    new Class<?>[]{org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session.class},
                    (proxy, method, args) -> {
                        if (method.getName().equals("head"))
                            return new WriterContracts.Head(ContinuityState.fromJson(events.get(13).get("after"), owner.machineId()),
                                    List.of(), List.of(), List.of(), false);
                        assertEquals("requireHistoricalState", method.getName());
                        assertEquals(prior.sequence(), args[0]);
                        assertEquals(ContinuityJson.digest(prior.toJson()), args[1]);
                        return prior;
                    });
            assertTrue(OrdinaryCycleTransitions.matchesRecordedArchivedFull111Completion(same, edge.after(), owner,
                    closure.getValue(), archive));
            assertFalse(OrdinaryCycleTransitions.matchesRecordedArchivedFull111Completion(same, edge.before(), owner, capture, archive));
            var historyEdge = historicalEdges(events, owner.machineId(), 9, 9).getFirst();
            var published = ContinuityBatchJournal.verifyExternalFull111Driver(historyEdge, closure.getValue());
            assertEquals(81, historyEdge.sequence());
            assertEquals(closure.getValue().sequence(), published.actionSequence());
            assertEquals(closure.getValue().command(), published.command());
            assertTrue(published.legacyRow().isEmpty());
            assertThrows(ContractViolationException.class,
                    () -> ContinuityBatchJournal.verifyExternalFull111Driver(historyEdge, capture));
            var completed = historicalEdges(events, owner.machineId(), 10, 13);
            var cycles = new OrdinaryCycleTransitions(archive, (sameWriter, actualOwner, semantic) -> {
                assertSame(same, sameWriter);
                assertEquals(owner, actualOwner);
                return new OrdinaryCycleTransitions.VerifiedSemantic(semantic.frame(), semantic.observedAt(),
                        "archived-software-fixture", semantic.semantic().sha256());
            }, (sameWriter, actualOwner, pair, proof) -> { throw new AssertionError(); },
                    new OriginalWindowReducer.Policy(edge.after().origin().targetDays()), known -> assertSame(same, known));
            for (var actual : completed) {
                var request = new WriterContracts.Request(actual.kind(), actual.details(), List.of());
                var expected = cycles.reduce(actual.before(), request).toJson()
                        .put("sequence", actual.sequence()).put("last_event_identity", actual.eventIdentity());
                assertTrue(ContinuityJson.same(actual.after().toJson(), expected), "WAL sequence " + actual.sequence());
            }
            var settled = completed.get(1);
            var request = new WriterContracts.Request(settled.kind(), settled.details(), List.of());
            var retained = cycles.withLocked(same, () ->
                    cycles.verifySettledExternalEvent(same, settled, owner, closure.getValue(), request));
            var head = completed.getLast().after();
            assertEquals("native:19", retained.frame().frame().snapshotId());
            assertEquals(58, head.toJson().get(WriterContracts.ORDINARY_CYCLE_FIELD).path("completed_cycles").longValue());
            assertEquals(56, head.settledCycles());
            assertEquals(53179344, head.settledDateRaw());
            assertEquals("migration121003-current131-root56-6",
                    head.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD).path("batch_id").textValue());
            assertEquals(closure.getKey(), ContinuityActionJournal.recordHead(head).orElseThrow());

        }
    }

    private static ActionPorts.OutcomeArchive archivedActionData(com.fasterxml.jackson.databind.JsonNode originals) {
        java.util.function.Function<ExactRef, byte[]> bytes = ref -> {
            var data = java.util.Base64.getDecoder().decode(originals.get(ref.sha256()).textValue());
            assertEquals(ref.bytes(), data.length);
            assertEquals(ref.sha256(), ActionCodec.sha256(data));
            return data;
        };
        var codec = new org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec((ref, limit) -> bytes.apply(ref));
        var dispatchRefs = new java.util.HashMap<Object, ExactRef>();
        var requestRefs = new java.util.HashMap<Object, ExactRef>();
        var recordRefs = new java.util.HashMap<Object, ExactRef>();
        var receiptRefs = new java.util.HashMap<Object, ExactRef>();
        return (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ExternalSaveRemountTest.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, arguments) -> {
                    if (method.getName().equals("withSession")) return proxy;
                    if (method.getName().equals("inSession")) {
                        @SuppressWarnings("unchecked")
                        var work = (java.util.function.Function<ActionPorts.OutcomeArchive, ?>) arguments[1];
                        return work.apply((ActionPorts.OutcomeArchive) proxy);
                    }
                    var arg = arguments[0];
                    return switch (method.getName()) {
                        case "loadRecord" -> {
                            var ref = (ExactRef) arg;
                            var record = org.xar.ck3.control.application.action.ActionRecordCodec.decode(bytes.apply(ref),
                                    (ActionPorts.OutcomeArchive) proxy);
                            recordRefs.put(record, ref);
                            yield record;
                        }
                        case "loadReceipt" -> {
                            var ref = (ExactRef) arg;
                            var receipt = org.xar.ck3.control.application.action.ActionReceiptCodec.decodeReceipt(
                                    bytes.apply(ref), (ActionPorts.OutcomeArchive) proxy);
                            receiptRefs.put(receipt, ref);
                            yield receipt;
                        }
                        case "loadMaterial" -> new org.xar.ck3.control.application.action.RawJson(bytes.apply((ExactRef) arg));
                        case "receiptReferenceOf" -> receiptRefs.get(arg);
                        case "load" -> {
                            var ref = (ExactRef) arg;
                            var dispatch = codec.decodeDispatchData(ref);
                            dispatchRefs.put(dispatch, ref);
                            yield dispatch;
                        }
                        case "loadRequest" -> {
                            var ref = (ExactRef) arg;
                            var request = codec.decodePreparedRequestData(ref);
                            requestRefs.put(request, ref);
                            yield request;
                        }
                        case "recordReferenceOf" -> recordRefs.get(arg);
                        case "referenceOf" -> dispatchRefs.get(arg);
                        case "requestReferenceOf" -> requestRefs.get(arg);
                        default -> throw new AssertionError("unexpected original reader " + method);
                    };
                });
    }

    private static List<WriterContracts.HistoricalTransition> historicalEdges(com.fasterxml.jackson.databind.JsonNode events,
            String machine, int first, int last) {
        var edges = new java.util.ArrayList<WriterContracts.HistoricalTransition>();
        for (int i = first; i <= last; i++) {
            var event = events.get(i);
            byte[] eventBytes = ContinuityJson.canonical(event);
            var pin = new WriterContracts.Pin(new ExactRef("fixture:event-" + i, eventBytes.length, ActionCodec.sha256(eventBytes)),
                    new WriterContracts.FileIdentity("1", Integer.toString(i), "1", "2026-11-27T10:41:00Z", eventBytes.length));
            edges.add(new WriterContracts.HistoricalTransition(event.path("sequence").longValue(), event.path("kind").textValue(),
                    ContinuityJson.canonical(event.get("details")), event.path("identity").textValue(),
                    ContinuityState.fromJson(events.get(i - 1).get("after"), machine),
                    ContinuityState.fromJson(event.get("after"), machine), pin));
        }
        return List.copyOf(edges);
    }

    private ContinuityState actualWriterCommit(ContinuityState before, OrdinaryCycleTransitions cycles,
            WriterContracts.Request request) throws Exception {
        byte[] initial = before.canonicalBytes();
        var anchor = Files.write(root.resolve("anchor.json"), initial);
        var source = new ExactRef(anchor.toString(), initial.length, ActionCodec.sha256(initial));
        var layout = new WriterContracts.Layout(Files.write(root.resolve("continuity.json"), initial), source, before.machineId());
        Files.createFile(layout.lock());
        Files.createDirectory(layout.events());
        var corruptBoundary = new AtomicBoolean();
        var authority = new WriterContracts.TransitionAuthority() {
            @Override public String revalidate(ContinuityState predecessor, WriterContracts.Request supplied) {
                return supplied.identity();
            }

            @Override public ContinuityState reduce(ContinuityState predecessor, WriterContracts.Request supplied) {
                var reduced = cycles.reduce(predecessor, supplied);
                if (!corruptBoundary.get()) return reduced;
                var body = reduced.toJson();
                ((ObjectNode) body.get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD)).put("boundary", "BATCH_FINISHED");
                return ContinuityState.fromJson(body, predecessor.machineId());
            }
        };
        var guard = StorageWriteGuardTestSupport.create(layout);
        var writer = new ContinuityWriter(layout, List.of(source), authority, Clock.systemUTC(), guard);

        writer.locked(same -> {
            var prepared = same.preview(request);
            corruptBoundary.set(true);
            try {
                assertThrows(ContractViolationException.class, () -> same.commit(prepared));
                assertArrayEquals(initial, Files.readAllBytes(layout.snapshot()));
                assertFalse(Files.exists(layout.event(before.sequence() + 1)));
            } finally {
                corruptBoundary.set(false);
            }
            return null;
        });

        var committed = writer.locked(same -> {
            var prepared = same.preview(request);
            var accepted = same.commit(prepared);
            same.requireCommitted(prepared, accepted);
            return accepted;
        });
        assertEquals(WriterContracts.Disposition.COMMITTED, committed.disposition());
        assertEquals(before.sequence() + 1, committed.head().sequence());
        assertTrue(Files.isRegularFile(layout.event(committed.head().sequence())));
        var reopened = new ContinuityWriter(layout, List.of(source), authority, Clock.systemUTC(), guard);
        reopened.locked(same -> {
            assertArrayEquals(committed.head().canonicalBytes(), same.head().state().canonicalBytes());
            return null;
        });
        return committed.head();
    }
}
