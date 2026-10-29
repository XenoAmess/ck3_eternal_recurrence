package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real Windows physical archive and writer fixtures. No Game, native submission or production ledger. */
final class NativeOutcomeArchiveClosureTest {
    private static final String MACHINE = "archive-closure-fixture";
    private static final Instant NOW = Instant.parse("2026-10-24T00:00:00Z");
    @TempDir Path temp;
    private final Set<StorageWriteGuardTestSupport> storageScopes = new java.util.LinkedHashSet<>();
    @AfterEach void closeStorageScopes() throws IOException {
        IOException failure = null;
        for (StorageWriteGuardTestSupport storage : storageScopes) {
            try { storage.close(); }
            catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        }
        storageScopes.clear();
        if (failure != null) throw failure;
    }

    private final class Fixture {
        final Path root;
        final Layout layout;
        final ExactRef source;
        final ImmutableArtifactStore store;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(Path root, boolean reopen) throws IOException {
            this.root = root;
            if (!reopen) {
                Files.createDirectory(root); byte[] initial = ContinuityJson.canonical(state());
                Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), initial, StandardOpenOption.CREATE_NEW);
                Files.write(root.resolve("anchor.json"), initial, StandardOpenOption.CREATE_NEW);
                Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
                Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
                Files.createDirectory(root.resolve("artifacts"));
                Files.writeString(root.resolve("source.txt"), "actual reviewed fixture source", StandardOpenOption.CREATE_NEW);
            }
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            StorageWriteGuardTestSupport storage = reopen ? StorageWriteGuardTestSupport.forLayout(layout) : StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            assertSame(storage, store.storageGuard());
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("archive fixture must not commit"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer);
        }
        G2Source source() { return new G2Source(MACHINE, NOW.toString(), "1.20.0.4", source); }
        ExactRef packet(byte[] bytes) throws IOException {
            return writer.locked(session -> archive.preserveArtifact(session, bytes, WriterContracts.MAX_PIN_BYTES));
        }
        GuardEvidence guard(OperationKey operation) throws IOException {
            ExactRef nativePacket = packet(ack("guard-native").originalPacket());
            ExactRef hello = packet(ack("guard-hello").originalPacket());
            ExactRef basis = archive.preserveMaterial(raw("{\"schema\":\"archive-closure-fixture/v1\",\"kind\":\"guard\"}"));
            return new GuardEvidence(observation(), source(), "session-1", BigInteger.ONE, operation, nativePacket, hello,
                    "fixture-authority", NOW, NOW.plusSeconds(60), List.of(basis));
        }
        static ObjectNode state() {
            ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
            row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
            row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
            row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
            row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
            row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
            row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
        }
    }
    private Fixture fixture(String name) throws IOException { return new Fixture(temp.resolve(name), false); }
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
    private static NativeActionPort.AckReceived ack(String id) throws IOException {
        byte[] packet = NativeWire.packet(("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":true,\"result\":{}}").getBytes(StandardCharsets.UTF_8));
        var decoded = (NativeWire.CommandResult) NativeWire.decode(packet);
        return new NativeActionPort.AckReceived(id, true, decoded.result().token().map(value -> new RawJson(value.value())), new RawJson(decoded.payload().value()), packet);
    }
    private static ProposalLifecycle.ObservationIdentity observation() {
        return new ProposalLifecycle.ObservationIdentity(MACHINE, new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(1000)), "native-1", BigInteger.ONE, "episode-1"), 1);
    }
    private static ActionCommand command(Fixture f) {
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, observation(), f.source(), "paused/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand("action-1", observation(), f.source(), "session-1", new OperationKey("pause-map"), new OpportunityJson.Obj(Map.of()), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(60));
    }
    private static ActionReceipt pending(Fixture f, GuardEvidence guard) {
        ActionCommand command = command(f);
        var attempt = new ActionState.Attempt("never-replay", NOW, guard, new NativeRequest("pause-map", "timeline-control", raw("{}")));
        return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.of(attempt), Optional.empty(), "unknown must remain unresolved", List.of()));
    }

    @Test void evolvedUnknownRoundtripsPhysicalClosureAndReopensWithoutChangingPendingLedger() throws IOException {
        Fixture f = fixture("unknown"); byte[] originalLedger = Files.readAllBytes(f.layout.snapshot());
        var original = pending(f, f.guard(command(f).operation()));
        ExactRef receipt = f.writer.locked(session -> f.archive.inSession(session, archive -> archive.preserveReceipt(original)));
        long retained = f.store.retainedNativeBytes(); Fixture reopened = new Fixture(f.root, true);
        assertEquals(original, reopened.archive.loadReceipt(receipt)); assertEquals(receipt, reopened.archive.receiptReferenceOf(original));
        assertEquals(retained, reopened.store.retainedNativeBytes());
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, reopened.archive.loadReceipt(receipt).outcome());
        assertArrayEquals(originalLedger, Files.readAllBytes(f.layout.snapshot()));
        long reopenedSequence = reopened.writer.locked(session -> session.head().state().sequence());
        assertEquals(0L, reopenedSequence);
    }
    @Test void missingForeignAndNonJsonBasisRefuseBeforePublishingReceipt() throws IOException {
        Fixture f = fixture("missing"); GuardEvidence original = f.guard(command(f).operation());
        GuardEvidence foreign = new GuardEvidence(original.origin(), original.source(), original.sessionId(), original.connectionGeneration(), original.operation(),
                original.nativeEvidence(), original.capabilityEvidence(), original.authorityId(), original.observedAt(), original.validUntil(), List.of(f.source));
        long before = f.store.retainedNativeBytes();
        assertThrows(UncheckedIOException.class, () -> f.archive.preserveReceipt(pending(f, foreign))); assertEquals(before, f.store.retainedNativeBytes());
        ExactRef binary = f.packet(new byte[] {1, 2, 3});
        GuardEvidence wrongKind = new GuardEvidence(original.origin(), original.source(), original.sessionId(), original.connectionGeneration(), original.operation(),
                original.nativeEvidence(), original.capabilityEvidence(), original.authorityId(), original.observedAt(), original.validUntil(), List.of(binary));
        assertThrows(IllegalArgumentException.class, () -> f.archive.preserveReceipt(pending(f, wrongKind)));
    }
    @Test void corruptedRetainedBasisFailsReceiptReaderAndReferenceLookupWithoutRepair() throws IOException {
        Fixture f = fixture("corrupt"); GuardEvidence guard = f.guard(command(f).operation()); var original = pending(f, guard);
        ExactRef receipt = f.archive.preserveReceipt(original); byte[] ledger = Files.readAllBytes(f.layout.snapshot());
        Path body = Path.of(guard.supportingEvidence().getFirst().path()); Files.writeString(body, "{\"changed\":true}");
        byte[] changed = Files.readAllBytes(body);
        assertThrows(UncheckedIOException.class, () -> f.archive.loadReceipt(receipt));
        assertThrows(UncheckedIOException.class, () -> f.archive.receiptReferenceOf(original));
        assertArrayEquals(changed, Files.readAllBytes(body)); assertArrayEquals(ledger, Files.readAllBytes(f.layout.snapshot()));
    }
    @Test void planningReadVerifiesBothGuardClosuresAtProducerAndConsumer() throws IOException {
        Fixture f = fixture("read"); GuardEvidence guard = f.guard(new OperationKey("query-test"));
        PlanningReadGuard bound = new PlanningReadGuard(guard, true, true, true, "a".repeat(64));
        PlanningReadRequest request = new PlanningReadRequest(observation(), f.source(), "session-1", guard.operation(), new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(60));
        PlanningReadReceipt original = new PlanningReadReceipt(request, "query-test/v1", "independent-read", bound, bound, ack("independent-read"));
        ExactRef ref = f.archive.preserveRead(original); assertEquals(original, f.archive.loadRead(ref));
        Files.writeString(Path.of(guard.supportingEvidence().getFirst().path()), "{\"invalid\":true}");
        assertThrows(UncheckedIOException.class, () -> f.archive.loadRead(ref));
        assertThrows(UncheckedIOException.class, () -> f.archive.preserveRead(original));
    }
    @Test void frontendEffectRetainsFullPacketAndMaterialBasisAsDistinctKinds() throws IOException {
        Fixture f = fixture("frontend"); var nativeBefore = ack("frontend-before"); var nativeAfter = ack("frontend-after");
        ExactRef beforeRef = f.packet(nativeBefore.originalPacket()), afterRef = f.packet(nativeAfter.originalPacket()), hello = f.packet(ack("frontend-hello").originalPacket());
        FrontendIdentity before = new FrontendIdentity(MACHINE, observation().game(), "frontend-1", BigInteger.ONE, 123, new FrontendFrame.Menu(BigInteger.ONE), beforeRef, hello);
        FrontendIdentity after = new FrontendIdentity(MACHINE, observation().game(), "frontend-1", BigInteger.ONE, 123, new FrontendFrame.Menu(BigInteger.TWO), afterRef, hello);
        var values = List.<ProposalLifecycle.ExpectedValue>of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("selected"), true));
        var expected = new FrontendExpectedPostcondition(before, f.source(), "frontend-test/v1", values);
        var command = new ActionCommand("frontend-action", new CommandOrigin.Frontend(before), f.source(), "frontend-1", new OperationKey("select-test"),
                new OpportunityJson.Obj(Map.of()), new CommandExpectation.Frontend(expected), new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(60));
        ExactRef basis = f.archive.preserveMaterial(raw("{\"schema\":\"frontend-closure-fixture/v1\"}"));
        GuardEvidence guard = new GuardEvidence(command.origin(), f.source(), "frontend-1", BigInteger.ONE, command.operation(), beforeRef, hello, "frontend-authority", NOW, NOW.plusSeconds(60), List.of(basis));
        var attempt = new ActionState.Attempt("frontend-action-request", NOW, guard, new NativeRequest("select-test", Optional.empty(), raw("{}")));
        var effect = new FrontendEffectObservation(after, f.source(), "frontend-1", "frontend-test/v1", values, "frontend-after", NOW, afterRef, List.of(basis));
        var original = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, ack(attempt.requestId()), new ActionState.FrontendApplied(effect)));
        ExactRef receipt = f.archive.preserveReceipt(original); assertEquals(original, f.archive.loadReceipt(receipt));
        ArchiveOriginalEvidencePort originals = new ArchiveOriginalEvidencePort(f.archive);
        assertArrayEquals(nativeAfter.originalPacket(), f.writer.locked(session -> originals.read(session, afterRef, WriterContracts.MAX_PIN_BYTES)));
        Files.writeString(Path.of(basis.path()), "{\"source\":\"drift\"}");
        assertThrows(UncheckedIOException.class, () -> f.archive.loadReceipt(receipt));
    }
    @Test void unsolicitedPushMustMatchItsActualSnapshotPacketWithoutInventingAQuery() throws IOException {
        Fixture f = fixture("push"); ActionCommand command = command(f); GuardEvidence guard = f.guard(command.operation());
        byte[] packet = NativeWire.packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"native-1\",\"revision\":1,\"state\":{}}".getBytes(StandardCharsets.UTF_8));
        ExactRef originalPacket = f.packet(packet);
        var provenance = new ObservationProvenance.Push("native-1", BigInteger.ONE, originalPacket);
        var effect = new ActionState.EffectObservation(observation(), f.source(), "session-1", "paused/v1", command.expected().values(), provenance, NOW, originalPacket, List.of());
        var attempt = new ActionState.Attempt("action-request", NOW, guard, new NativeRequest("pause-map", "timeline-control", raw("{}")));
        var original = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, ack(attempt.requestId()), new ActionState.Applied(effect)));
        assertEquals(original, f.archive.loadReceipt(f.archive.preserveReceipt(original)));
        ExactRef wrongPacket = f.packet(NativeWire.packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"different\",\"revision\":1,\"state\":{}}".getBytes(StandardCharsets.UTF_8)));
        var fabricated = new ObservationProvenance.Push("native-1", BigInteger.ONE, wrongPacket);
        var wrongEffect = new ActionState.EffectObservation(observation(), f.source(), "session-1", "paused/v1", command.expected().values(), fabricated, NOW, wrongPacket, List.of());
        var wrong = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, ack(attempt.requestId()), new ActionState.Applied(wrongEffect)));
        assertThrows(UncheckedIOException.class, () -> f.archive.preserveReceipt(wrong));
    }
    @Test void concreteOriginalPortUsesExactWriterSessionRootBoundAndThread() throws IOException {
        Fixture f = fixture("port"), foreign = fixture("foreign"); var originals = new ArchiveOriginalEvidencePort(f.archive);
        byte[] packet = ack("port-packet").originalPacket(); ExactRef ref = f.packet(packet);
        AtomicReference<ContinuityStorePort.Session> escaped = new AtomicReference<>();
        f.writer.locked(session -> {
            escaped.set(session); assertSame(f.archive, originals.archive()); assertSame(f.writer, originals.writer());
            assertArrayEquals(packet, originals.read(session, ref, packet.length));
            assertThrows(IOException.class, () -> originals.read(session, ref, packet.length - 1));
            assertThrows(IOException.class, () -> originals.read(session, f.source, 1024));
            CompletionException crossed = assertThrows(CompletionException.class, () -> CompletableFuture.runAsync(() -> {
                try { originals.read(session, ref, WriterContracts.MAX_PIN_BYTES); } catch (IOException failure) { throw new UncheckedIOException(failure); }
            }).join());
            assertInstanceOf(IllegalArgumentException.class, crossed.getCause()); return null;
        });
        assertThrows(IllegalArgumentException.class, () -> originals.read(escaped.get(), ref, WriterContracts.MAX_PIN_BYTES));
        foreign.writer.locked(session -> { assertThrows(IOException.class, () -> originals.read(session, ref, WriterContracts.MAX_PIN_BYTES)); return null; });
    }
}
