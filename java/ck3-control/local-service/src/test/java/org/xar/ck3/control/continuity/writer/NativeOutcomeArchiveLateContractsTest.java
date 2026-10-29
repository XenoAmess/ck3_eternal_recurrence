package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.driver.PublicDataJson;
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
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real physical archive and original writer fixtures. Recorded proofs are data and grant no lifecycle authority. */
final class NativeOutcomeArchiveLateContractsTest {
    private static final String MACHINE = "archive-late-fixture";
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
        final Layout layout; final ImmutableArtifactStore store; final ContinuityWriter writer;
        final NativeOutcomeArchive archive; final ExactRef source;
        Fixture(Path root) throws IOException {
            Files.createDirectory(root);
            String state = """
                    {"schema":"root.ck3.continuity-window/v1","machine_id":"archive-late-fixture","sequence":0,"window_id":1,
                    "status":"running","target_days":10958,"target_years":30,"calendar_year_days":365.25,"start_date_raw":1000,
                    "target_date_raw":263992,"last_settled_date_raw":1000,"last_settled_cycles":1,"manual_repair_count":1,
                    "automatic_recovery_count":0,"binding_lineage_count":0,"game_binding":{"pid":123,"creation_date":"2026-10-23T01:00:00Z"},
                    "latest_binding":null,"pending_cycle":{"stage":"auto_unsettled","auto_sequence":11558},"NEXT":11559}
                    """;
            byte[] initial = ContinuityJson.canonical((ObjectNode) StrictJson.parse(bytes(state), 65536));
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), initial, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "actual reviewed lifecycle fixture source", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            StorageWriteGuardTestSupport storage = StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 16 * 1024 * 1024), storage);
            assertSame(storage, store.storageGuard());
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("no production ledger write in archive fixture"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer);
        }
        G2Source source() { return new G2Source(MACHINE, NOW.toString(), "1.20.0.4", source); }
        ExactRef packet(byte[] original) throws IOException { return writer.locked(session -> archive.preserveArtifact(session, original, WriterContracts.MAX_PIN_BYTES)); }
    }
    private Fixture fixture(String name) throws IOException { return new Fixture(temp.resolve(name)); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static RawJson raw(String value) { return new RawJson(bytes(value)); }
    private static ProposalLifecycle.ObservationIdentity observation() {
        return new ProposalLifecycle.ObservationIdentity(MACHINE, new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(1000)), "native-1", BigInteger.ONE, "episode-1"), 1);
    }
    private static NativeActionPort.AckReceived ack(String id, String step, BigInteger revision) throws IOException {
        byte[] packet = NativeWire.packet(bytes("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + id + "\",\"ok\":true,\"result\":{\"fixture\":true}}"));
        var reply = (NativeWire.CommandResult) NativeWire.decode(packet);
        return new NativeActionPort.AckReceived(id, true, reply.result().token().map(value -> new RawJson(value.value())), new RawJson(reply.payload().value()), packet,
                Optional.of(new NativeActionPort.OutboundPacket(id, NativeWire.execute(id, step, revision, bytes("{}")))));
    }
    private static JointBudgetSelector.Claims claims() { return new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()); }
    private static GuardEvidence gameplayGuard(Fixture f, OperationKey operation) {
        return new GuardEvidence(observation(), f.source(), "session-1", BigInteger.ONE, operation, f.source, f.source, "fixture-authority", NOW, NOW.plusSeconds(60));
    }
    private static ActionCommand lifecycleCommand(Fixture f) {
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, observation(), f.source(), "lifecycle-data/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("recorded"), true)));
        return new ActionCommand("lifecycle-parent", observation(), f.source(), "session-1", new OperationKey("death-terminal"), new OpportunityJson.Obj(Map.of()), expected, claims(), NOW.plusSeconds(60));
    }
    private static LifecycleTransitionProof proof(Fixture f, ActionCommand parent, int resultSize, String recordedParentId) throws IOException {
        Pin actual = LedgerFiles.exact(f.source, 1024).pin(); var identity = actual.identity();
        ObjectNode row = StrictJson.object(); row.put("schema", "xar.java-lifecycle-transition-proof/v1"); row.put("kind", "DEATH");
        row.put("parent_action_id", recordedParentId); row.put("body_sha256", ActionCodec.bodySha256(parent)); row.put("operation", parent.operation().value());
        row.put("committed_event_identity", "d".repeat(64));
        ObjectNode document = row.putArray("committed_documents").addObject(); document.set("reference", actual.reference().toJson());
        ObjectNode nativeId = document.putObject("native_identity"); nativeId.put("volume_serial", identity.volumeSerialDecimal());
        nativeId.put("file_id", identity.fileIdDecimal()); nativeId.put("creation_filetime", identity.creationFiletimeDecimal());
        nativeId.put("modified_instant", identity.modifiedInstant()); nativeId.put("bytes", identity.bytes());
        // A real ordinary external original; archive must not reinterpret this source path as a material locator.
        row.putArray("original_evidence").add(f.source.toJson()); row.putObject("result").put("payload", "x".repeat(resultSize));
        return LifecycleProofCodec.decodeRecorded(PublicDataJson.encode(row).bytes());
    }
    private static ActionReceipt lifecycleReceipt(Fixture f, ActionCommand command, LifecycleTransitionProof proof) {
        CompositeExecution execution = new CompositeExecution("lifecycle-fixture", NOW, gameplayGuard(f, command.operation()), List.of());
        return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.CompositeSettled(execution, new ActionState.LifecycleApplied(proof)));
    }
    private static ExactRef proofRef(Fixture f, ExactRef receipt) throws IOException {
        var body = PublicDataJson.object(new RawJson(f.store.read(receipt, ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES)));
        return ExactRef.fromJson(body.get("state").get("settlement").get("proof_ref"));
    }

    @Test void completeLargeLifecycleProofIsPublishedBeforeSmallReceiptAndRoundtripsWithoutLedgerWrite() throws IOException {
        Fixture f = fixture("large-proof"); ActionCommand command = lifecycleCommand(f);
        var original = lifecycleReceipt(f, command, proof(f, command, 2_200_000, command.actionId()));
        byte[] ledger = Files.readAllBytes(f.layout.snapshot());
        assertThrows(UncheckedIOException.class, () -> f.archive.receiptReferenceOf(original)); assertEquals(0, f.store.retainedNativeBytes());
        ExactRef receipt = f.writer.locked(session -> f.archive.inSession(session, archive -> archive.preserveReceipt(original)));
        ExactRef sidecar = proofRef(f, receipt); assertTrue(sidecar.bytes() > ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);
        assertTrue(receipt.bytes() < ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES);
        var loaded = f.archive.loadReceipt(receipt); var settlement = (ActionState.LifecycleApplied) ((ActionState.CompositeSettled) loaded.state()).settlement();
        byte[] encoded = ((ActionState.LifecycleApplied) ((ActionState.CompositeSettled) original.state()).settlement()).proof().encode();
        assertArrayEquals(encoded, settlement.proof().encode());
        assertArrayEquals(encoded, f.archive.loadMaterial(sidecar).bytes());
        assertArrayEquals(ActionReceiptCodec.encodeReceipt(original, f.archive), ActionReceiptCodec.encodeReceipt(loaded, f.archive));
        assertEquals(receipt, f.archive.receiptReferenceOf(loaded)); assertArrayEquals(ledger, Files.readAllBytes(f.layout.snapshot()));
    }
    @Test void lifecycleReaderRefusesChangedSidecarAndWrongParentWithoutConvertingExternalFiles() throws IOException {
        Fixture f = fixture("proof-corruption"); ActionCommand command = lifecycleCommand(f);
        var wrongParent = lifecycleReceipt(f, command, proof(f, command, 1, "different-parent"));
        assertThrows(IllegalArgumentException.class, () -> f.archive.preserveReceipt(wrongParent)); assertEquals(0, f.store.retainedNativeBytes());
        var original = lifecycleReceipt(f, command, proof(f, command, 10, command.actionId())); ExactRef receipt = f.archive.preserveReceipt(original);
        ExactRef sidecar = proofRef(f, receipt); Path body = Path.of(sidecar.path()); Files.writeString(body, "{\"changed\":true}");
        assertThrows(UncheckedIOException.class, () -> f.archive.loadReceipt(receipt));
        assertEquals("{\"changed\":true}", Files.readString(body));
        assertEquals("actual reviewed lifecycle fixture source", Files.readString(Path.of(f.source.path())));
    }

    private record EntryFixture(ActionReceipt receipt, PlanningReadReceipt rootRead) { }
    private static EntryFixture entry(Fixture f) throws IOException {
        ExactRef menu = f.packet(ack("menu-original", "query-frontend-gui-route-v1", BigInteger.ZERO).originalPacket());
        ExactRef hello = f.packet(ack("hello-original", "query-frontend-gui-route-v1", BigInteger.ZERO).originalPacket());
        FrontendIdentity before = new FrontendIdentity(MACHINE, observation().game(), "frontend-1", BigInteger.ONE, 123, new FrontendFrame.Menu(BigInteger.ONE), menu, hello);
        var values = List.<ProposalLifecycle.ExpectedValue>of(
                new ProposalLifecycle.ExpectedText(new ProposalLifecycle.FieldKey("selected_bookmark_key"), "bookmark_1066"),
                new ProposalLifecycle.ExpectedText(new ProposalLifecycle.FieldKey("selected_character_name_key"), "Robert"),
                new ProposalLifecycle.ExpectedInteger(new ProposalLifecycle.FieldKey("date_raw"), BigInteger.valueOf(1000)),
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("map_ready"), true),
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true));
        var expected = new FrontendGameplayExpectedPostcondition(before, f.source(), "entry-data/v2", "bookmark_1066", "Robert", 1000, values);
        OperationKey operation = new OperationKey("frontend-start-test");
        var command = new ActionCommand("entry-parent", new CommandOrigin.Frontend(before), f.source(), "frontend-1", operation, new OpportunityJson.Obj(Map.of()), new CommandExpectation.GameplayEntry(expected), claims(), NOW.plusSeconds(60));
        GuardEvidence guard = new GuardEvidence(command.origin(), f.source(), "frontend-1", BigInteger.ONE, operation, menu, hello, "frontend-fixture", NOW, NOW.plusSeconds(60));
        var attempt = new ActionState.Attempt("entry-submit", NOW, guard, new NativeRequest(operation.value(), Optional.empty(), raw("{}")));
        var readOperation = new OperationKey("query-campaign-root-context-v1"); GuardEvidence readGuard = gameplayGuard(f, readOperation);
        var guardedRead = new PlanningReadGuard(readGuard, true, true, true, "a".repeat(64));
        var request = new PlanningReadRequest(observation(), f.source(), "session-1", readOperation, new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(60));
        PlanningReadReceipt rootRead = new PlanningReadReceipt(request, "campaign-root-fixture/v1", "campaign-root-read", guardedRead, guardedRead, ack("campaign-root-read", readOperation.value(), BigInteger.ONE));
        byte[] packet = NativeWire.packet(bytes("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"native-1\",\"revision\":1,\"state\":{}}"));
        var transport = new NativeObservationPort.TransportSession(MACHINE, observation().game(), BigInteger.ONE, "session-1");
        ExactRef nativeFrame = f.archive.preserveNativeFrame(new NativeObservationPort.ObservedFrame(transport, "native-1", BigInteger.ONE, raw("{}"), packet, NOW));
        var semantic = new SemanticEvidence(observation(), f.archive.preserveMaterial(raw("{\"semantic\":1}")), nativeFrame,
                f.archive.preserveMaterial(raw("{\"driver_stamp\":1}")), f.archive.preserveMaterial(raw("{\"original_driver\":1}")), NOW);
        ExactRef sourceBasis = f.archive.preserveMaterial(raw("{\"schema\":\"source-bound-entry-fixture/v1\"}"));
        var observed = new FrontendGameplayObservation(before, f.source(), new SessionIdentity(MACHINE, observation().game(), "session-1"), BigInteger.ONE,
                "entry-data/v2", values, semantic, rootRead, List.of(sourceBasis));
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, ack(attempt.requestId(), operation.value(), BigInteger.ZERO), new ActionState.GameplayEntered(observed)));
        return new EntryFixture(receipt, rootRead);
    }
    @Test void gameplayEntryAutomaticallyArchivesActualCampaignRootReadBeforeSoleCodecReferencesIt() throws IOException {
        Fixture f = fixture("entry"); EntryFixture original = entry(f); byte[] ledger = Files.readAllBytes(f.layout.snapshot());
        assertThrows(UncheckedIOException.class, () -> f.archive.readReferenceOf(original.rootRead()));
        ExactRef receipt = f.archive.preserveReceipt(original.receipt());
        ExactRef read = f.archive.readReferenceOf(original.rootRead()); assertEquals(original.rootRead(), f.archive.loadRead(read));
        assertEquals(original.receipt(), f.archive.loadReceipt(receipt));
        assertArrayEquals(ledger, Files.readAllBytes(f.layout.snapshot()));
        ExactRef actualPacket = f.store.referenceOf(original.rootRead().original().originalPacket(), WriterContracts.MAX_PIN_BYTES).reference();
        Files.write(Path.of(actualPacket.path()), new byte[] {1, 2, 3});
        assertThrows(UncheckedIOException.class, () -> f.archive.loadReceipt(receipt));
        assertArrayEquals(new byte[] {1, 2, 3}, Files.readAllBytes(Path.of(actualPacket.path())));
    }
}
