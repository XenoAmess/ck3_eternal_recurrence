package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.application.effects.coa.NativeSourceObservation;
import org.xar.ck3.control.application.effects.normalexit.NormalExitPhaseObservation;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureOutcome;

/** Guarded cold frontend DATA only; physical success and private permits remain external. */
final class NativeOutcomeArchivePhysicalContractsTest {
    private static final String MACHINE = "archive-physical-software";
    @TempDir Path temp;

    private static final class Fixture implements AutoCloseable {
        final Path root;
        final Layout layout;
        final ExactRef source;
        final StorageWriteGuardTestSupport storage;
        final ImmutableArtifactStore store;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(Path root) throws IOException {
            this.root = root; Files.createDirectory(root);
            byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "explicit physical archive software fixture", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            storage = StorageWriteGuardTestSupport.create(layout);
            store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 16 * 1024 * 1024), storage);
            writer = writer(store); archive = new NativeOutcomeArchive(store, writer);
        }
        private ContinuityWriter writer(ImmutableArtifactStore installed) throws IOException {
            return new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("archive DATA fixture cannot commit"); }
            }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(), Optional.of(installed), Optional.empty()), storage);
        }
        NativeOutcomeArchive cold() throws IOException {
            StorageWriteGuardTestSupport existing = StorageWriteGuardTestSupport.forLayout(layout);
            assertSame(storage, existing);
            var installed = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 16 * 1024 * 1024), existing);
            return new NativeOutcomeArchive(installed, writer(installed));
        }
        ExactRef raw(byte[] bytes) throws IOException {
            return writer.locked(session -> archive.preserveArtifact(session, bytes, StrictJson.EXPLICIT_MAX_BYTES));
        }
        long sequence() throws IOException { return writer.locked(session -> session.head().state().sequence()); }
        @Override public void close() throws IOException { storage.close(); }
    }
    private Fixture fixture(String name) throws IOException { return new Fixture(temp.resolve(name)); }
    private static ObjectNode state() {
        ObjectNode n = StrictJson.object(); n.put("schema", "root.ck3.continuity-window/v1"); n.put("machine_id", MACHINE);
        n.put("sequence", 0); n.put("window_id", 1); n.put("status", "running"); n.put("target_days", 10958);
        n.put("target_years", 30); n.put("calendar_year_days", 365.25); n.put("start_date_raw", 1000); n.put("target_date_raw", 263992);
        n.put("last_settled_date_raw", 1000); n.put("last_settled_cycles", 1); n.put("manual_repair_count", 1);
        n.put("automatic_recovery_count", 0); n.put("binding_lineage_count", 0);
        n.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z"); n.putNull("latest_binding");
        n.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); n.put("NEXT", 11559); return n;
    }
    private static NativeActionPort.AckReceived ack(String requestId, Optional<String> result) throws IOException {
        String body = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"" + requestId
                + "\",\"ok\":true" + result.map(token -> ",\"result\":" + token).orElse("") + "}";
        byte[] packet = NativeWire.packet(body.getBytes(StandardCharsets.UTF_8));
        var actual = (NativeWire.CommandResult) NativeWire.decode(packet);
        return new NativeActionPort.AckReceived(actual.requestId(), actual.nativeOk(), actual.result().token().map(value -> new RawJson(value.value())), new RawJson(actual.payload().value()), packet);
    }
    private static ProposalLifecycle.ObservationIdentity observation() {
        return new ProposalLifecycle.ObservationIdentity(MACHINE, new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(1000)), "native-1", BigInteger.ONE, "episode-1"), 1);
    }
    private static final Instant NOW = Instant.parse("2026-10-24T05:45:00Z");
    private static RawJson raw(String value) { return new RawJson(value.getBytes(StandardCharsets.UTF_8)); }
    private static G2Source source(Fixture f) { return new G2Source(MACHINE, NOW.toString(), "1.20.0.4", f.source); }
    private static ActionCommand command(Fixture f, OperationKey operation, String schema) {
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, observation(), source(f), schema,
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("data_only"), true)));
        return new ActionCommand("physical-data-action", observation(), source(f), "session-1", operation, new OpportunityJson.Obj(Map.of()),
                expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
    }
    private static GuardEvidence guard(Fixture f, OperationKey operation) {
        ExactRef nativeData = f.archive.preserveMaterial(raw("{\"explicit_software_guard_native\":true}"));
        ExactRef capabilityData = f.archive.preserveMaterial(raw("{\"explicit_software_guard_capability\":true}"));
        return new GuardEvidence(observation(), source(f), "session-1", BigInteger.ONE, operation, nativeData, capabilityData,
                "DATA-not-runtime-authority", NOW, NOW.plusSeconds(30));
    }
    private static FrontendWindowCaptureRequest window(Fixture f) {
        ExactRef frontend = f.archive.preserveMaterial(raw("{\"software_frontend\":true}"));
        ExactRef preparation = f.archive.preserveMaterial(raw("{\"software_preparation\":true}"));
        return new FrontendWindowCaptureRequest("physical-data-request", NOW, NOW.plusSeconds(20),
                new FrontendWindowCaptureRequest.Owner(MACHINE, "session-1", 123, "18446744073709551615", "1".repeat(64), "9007199254740993"),
                frontend, f.source, List.of(preparation), new FrontendWindowCaptureRequest.Window("18446744073709551615",
                new FrontendWindowCaptureRequest.ScreenRect(-2560, -1440, 0, 0)), "0");
    }
    private static FrontendWindowCaptureOutcome unknown(FrontendWindowCaptureRequest request, ExactRef original) {
        return new FrontendWindowCaptureOutcome(request, original, FrontendWindowCaptureOutcome.Status.UNKNOWN,
                Optional.of(NOW.plusSeconds(1)), NOW.plusSeconds(2), request.window(), Optional.empty(), request.foregroundRootBefore(),
                Optional.empty(), Optional.empty(), 0, 0, Optional.empty(), Optional.empty(), Optional.empty(),
                Optional.of("explicit unresolved software DATA"), List.of(original));
    }
    private static PhysicalActionState submitting(Fixture f, FrontendWindowCaptureRequest request, ActionCommand command) {
        return new PhysicalActionState(new PreparedAction.WindowCaptureRequest(request), NOW, guard(f, command.operation()),
                PhysicalActionState.Phase.SUBMITTING, Optional.empty(), List.of(), "software DATA");
    }
    private static ActionReceipt receipt(ActionCommand command, ActionState state) {
        return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), state);
    }
    private static PlanningReadReceipt read(Fixture f, String id, OperationKey operation) throws IOException {
        var binding = guard(f, operation); var before = new PlanningReadGuard(binding, true, true, true, "a".repeat(64));
        var request = new PlanningReadRequest(observation(), source(f), "session-1", operation, new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(30));
        // Explicit software packet originals test DATA serialization, never native execution.
        return new PlanningReadReceipt(request, "software-data-read/v1", id, before, before, ack(id, Optional.of("{}")));
    }
    @Test void physicalUnknownDataUsesRealTypedArchiveAndColdReaderWithoutNativeWireOrGameCredit() throws IOException {
        try (Fixture f = fixture("physical")) {
            var request = window(f); var command = command(f, new OperationKey("prepare-frontend-coat-of-arms-framebuffer-v1"), "data-only/v1");
            ExactRef prepared = f.archive.preserveFrontendWindowCaptureRequest(request);
            var outcome = unknown(request, prepared); f.archive.preserveFrontendWindowCaptureOutcome(outcome);
            var state = new PhysicalActionState(new PreparedAction.WindowCaptureRequest(request), NOW, guard(f, command.operation()),
                    PhysicalActionState.Phase.UNKNOWN, Optional.of(new PhysicalOutcome.WindowCaptureOutcome(outcome)), List.of(prepared), "unresolved DATA");
            PhysicalActionCodec.preserve(state, f.archive);
            ActionReceipt original = receipt(command, state); ExactRef ref = f.archive.preserveReceipt(original);
            assertEquals(original, f.cold().loadReceipt(ref)); assertEquals(ref, f.archive.receiptReferenceOf(original));
            assertEquals(ActionReceipt.Outcome.UNRESOLVED, original.outcome());
            assertFalse(original.visibleGameplay()); assertFalse(original.eligibleAdvance()); assertEquals(0, f.sequence());
            assertThrows(RuntimeException.class, () -> f.archive.load(ref));
        }
    }
    @Test void readonlyPhysicalReferencesAndReceiptNeverPublishAMissingPreparedOriginal() throws IOException {
        try (Fixture f = fixture("missing-prepared")) {
            var request = window(f); var command = command(f, new OperationKey("prepare-frontend-coat-of-arms-framebuffer-v1"), "data-only/v1");
            var state = submitting(f, request, command); ActionReceipt original = receipt(command, state);
            long before = f.store.retainedNativeBytes();
            assertThrows(RuntimeException.class, () -> PhysicalActionCodec.references(state, f.archive));
            assertThrows(RuntimeException.class, () -> PhysicalActionCodec.encode(state, f.archive));
            assertThrows(RuntimeException.class, () -> f.archive.preserveReceipt(original));
            assertThrows(RuntimeException.class, () -> f.archive.receiptReferenceOf(original));
            assertEquals(before, f.store.retainedNativeBytes());
            PhysicalActionCodec.preserve(state, f.archive); // Only this explicit producer may retain the new request.
            ExactRef ref = f.archive.preserveReceipt(original);
            ExactRef prepared = f.archive.frontendWindowCaptureRequestReferenceOf(request); Files.delete(Path.of(prepared.path()));
            assertThrows(RuntimeException.class, () -> f.cold().loadReceipt(ref));
            assertFalse(Files.exists(Path.of(prepared.path()))); assertEquals(0, f.sequence());
        }
    }
    @Test void samePhysicalRequestIdCannotHideChangedCompletePreparedBody() throws IOException {
        try (Fixture f = fixture("physical-substitution")) {
            var request = window(f); var command = command(f, new OperationKey("prepare-frontend-coat-of-arms-framebuffer-v1"), "data-only/v1");
            ExactRef original = f.archive.preserveFrontendWindowCaptureRequest(request);
            var outcome = unknown(request, original); f.archive.preserveFrontendWindowCaptureOutcome(outcome);
            var changed = new FrontendWindowCaptureRequest(request.requestId(), request.preparedAt(), request.deadline(), request.owner(),
                    request.actualFrontendEvidence(), request.sourceRef(), request.preparationEvidence(), request.window(), "1");
            var state = new PhysicalActionState(new PreparedAction.WindowCaptureRequest(changed), NOW, guard(f, command.operation()),
                    PhysicalActionState.Phase.UNKNOWN, Optional.of(new PhysicalOutcome.WindowCaptureOutcome(outcome)), List.of(original), "changed DATA");
            PhysicalActionCodec.preserve(state, f.archive);
            long before = f.store.retainedNativeBytes();
            assertThrows(RuntimeException.class, () -> f.archive.preserveReceipt(receipt(command, state)));
            assertEquals(before, f.store.retainedNativeBytes()); assertEquals(0, f.sequence());
        }
    }
    @Test void sourceCompletionArchiveReadsSourceAsRawAndOnlyThreeRolesAsJson() throws IOException {
        try (Fixture f = fixture("source-data")) {
            var operation = new OperationKey("export-coat-of-arms-source-v1");
            var command = command(f, operation, NativeSourceObservation.SCHEMA);
            var guard = guard(f, operation); var prepared = new NativeRequest(operation.value(), Optional.empty(), raw("{}"));
            var attempt = new ActionState.Attempt("source-data-request", NOW, guard, prepared);
            var ack = ack(attempt.requestId(), Optional.of("{}"));
            ExactRef dispatch = f.archive.preserve(ack); f.archive.preserveRequest(prepared);
            ExactRef clipboard = f.archive.preserveMaterial(raw("{\"clipboard_original\":\"software\"}"));
            ExactRef after = f.archive.preserveMaterial(raw("{\"scope_original\":\"software\"}"));
            ExactRef result = f.archive.preserveMaterial(raw("{\"result_original\":\"software\"}"));
            var observation = new NativeSourceObservation(operation, ActionCodec.bodySha256(command), attempt.requestId(), NativeSourceObservation.Outcome.EXPORTED,
                    NOW.plusSeconds(1), dispatch, clipboard, after, result, List.of(f.source));
            // Archive custody only: this is not an installed source-domain verifier positive.
            var original = receipt(command, new ActionState.Settled(attempt, ack, new ActionState.NativeSourceCompleted(observation)));
            ExactRef ref = f.archive.preserveReceipt(original); assertEquals(original, f.cold().loadReceipt(ref));
            assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT, original.outcome()); assertFalse(original.visibleGameplay()); assertFalse(original.eligibleAdvance());
            assertEquals(0, f.sequence()); Files.writeString(Path.of(f.source.path()), "changed actual external source DATA");
            assertThrows(RuntimeException.class, () -> f.cold().loadReceipt(ref));
            assertThrows(RuntimeException.class, () -> f.archive.receiptReferenceOf(original));
        }
    }
    @Test void phaseDataCannotConvertAnAckWithoutOriginalCustodyIntoUiConfirmation() throws IOException {
        try (Fixture f = fixture("phase-missing-custody")) {
            var phase = NormalExitPhaseObservation.Phase.PREPARE_CONFIRMATION;
            var command = command(f, phase.selector().operationKey(), NormalExitPhaseObservation.SCHEMA);
            var query = NativeStepDiscriminator.NormalExit.QUERY_CONTEXT.operationKey();
            var before = read(f, "phase-before", query); var after = read(f, "phase-after", query);
            ExactRef beforeRef = f.archive.preserveRead(before), afterRef = f.archive.preserveRead(after);
            var prepared = new NativeRequest(command.operation().value(), Optional.empty(), raw("{}"));
            var attempt = new ActionState.Attempt("phase-data-request", NOW, guard(f, command.operation()), prepared);
            var ack = ack(attempt.requestId(), Optional.of("{}"));
            ExactRef submitted = f.archive.preserve(ack), preparedRef = f.archive.preserveRequest(prepared);
            var phaseData = new NormalExitPhaseObservation(phase, NormalExitPhaseObservation.Outcome.CONFIRMATION_VISIBLE,
                    command.actionId(), ActionCodec.bodySha256(command), attempt.requestId(), submitted, preparedRef,
                    observation(), observation(), source(f), "session-1", beforeRef, before, afterRef, after);
            var original = receipt(command, new ActionState.Settled(attempt, ack, new ActionState.NormalExitPhaseConfirmed(phaseData)));
            long retained = f.store.retainedNativeBytes();
            assertThrows(RuntimeException.class, () -> f.archive.preserveReceipt(original));
            assertEquals(retained, f.store.retainedNativeBytes()); assertEquals(0, f.sequence());
        }
    }
    @Test void actualArchiveProducerThenClosedWriterFeedsTheSoleReadonlyDataParser() throws IOException {
        ExactRef original; PlanningReadReceipt retained; byte[] ledger; Path snapshot; long files;
        try (Fixture f = fixture("readonly-read")) {
            retained = read(f, "readonly-original", new OperationKey("query-software-data"));
            original = f.archive.preserveRead(retained);
            assertEquals(retained, f.cold().loadRead(original));
            snapshot = f.layout.snapshot(); ledger = Files.readAllBytes(snapshot);
            try (var tree = Files.walk(f.root)) { files = tree.count(); }
        }
        // No writer, store, lock, callback authority or Root is constructed by this reader.
        NativeArchiveDataCodec.ReadData data = NativeArchiveDataCodec.retainedFiles().readData(original);
        assertEquals(original, data.original()); assertEquals(retained, data.receipt());
        assertArrayEquals(ledger, Files.readAllBytes(snapshot));
        try (var tree = Files.walk(snapshot.getParent())) { assertEquals(files, tree.count()); }
    }
    @Test void soleReadonlyAndLiveParsersRejectMalformedMetadataAndNeverRepairMissingGuardOriginals() throws IOException {
        try (Fixture f = fixture("readonly-negative")) {
            var retained = read(f, "readonly-negatives", new OperationKey("query-software-data"));
            ExactRef original = f.archive.preserveRead(retained); var reader = NativeArchiveDataCodec.retainedFiles();
            for (String field : List.of("schema", "request_id", "original_ref", "before", "adoption")) {
                ObjectNode row = (ObjectNode) StrictJson.parse(Files.readAllBytes(Path.of(original.path())));
                row.remove(field); ExactRef bad = f.raw(row.toString().getBytes(StandardCharsets.UTF_8));
                assertThrows(RuntimeException.class, () -> f.archive.loadRead(bad));
                assertThrows(RuntimeException.class, () -> reader.readData(bad));
            }
            String json = Files.readString(Path.of(original.path()));
            ExactRef duplicate = f.raw((json.substring(0, json.length()-1) + ",\"schema\":\"xar.planning-read-archive/v2\"}").getBytes(StandardCharsets.UTF_8));
            assertThrows(RuntimeException.class, () -> f.archive.loadRead(duplicate));
            assertThrows(RuntimeException.class, () -> reader.readData(duplicate));
            var corrupted = new NativeArchiveDataCodec((ref, max) -> {
                byte[] bytes = LedgerFiles.exact(ref, max).bytes(); bytes[bytes.length-1] ^= 1; return bytes;
            });
            assertThrows(IOException.class, () -> corrupted.readData(original));
            Path missing = Path.of(retained.before().binding().nativeEvidence().path()); Files.delete(missing);
            assertThrows(IOException.class, () -> reader.readData(original)); assertFalse(Files.exists(missing));
        }
    }
}
