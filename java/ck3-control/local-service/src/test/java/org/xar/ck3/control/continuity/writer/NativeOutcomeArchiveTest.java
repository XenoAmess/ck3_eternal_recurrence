package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
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
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Full physical archive producer -> all twenty typed consumer methods; no Game or real session ledger is touched. */
final class NativeOutcomeArchiveTest {
    private static final String MACHINE = "archive-test-fixture";
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
        final ImmutableArtifactStore artifacts;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(Path root) throws IOException { this(root, false); }
        Fixture(Path root, boolean reopen) throws IOException {
            this.root = root;
            if (!reopen) {
                Files.createDirectory(root); byte[] state = ContinuityJson.canonical(state());
                Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
                Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
                Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
                Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS")); Files.createDirectory(root.resolve("artifacts"));
                Files.writeString(root.resolve("reviewed-source.txt"), "archive fixture source", StandardOpenOption.CREATE_NEW);
            }
            source = LedgerFiles.read(root.resolve("reviewed-source.txt"), 100).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"), LedgerFiles.read(root.resolve("anchor.json"), 65_536).pin().reference(), MACHINE);
            StorageWriteGuardTestSupport storage = reopen ? StorageWriteGuardTestSupport.forLayout(layout) : StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            artifacts = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            assertSame(storage, artifacts.storageGuard());
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState predecessor, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState predecessor, Request request) { throw new IllegalStateException("archive fixture must never commit a ledger event"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(artifacts), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(artifacts, writer);
        }
        G2Source source() { return new G2Source(MACHINE, NOW.toString(), "1.20.0.4", source); }
        static ObjectNode state() {
            ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
            row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
            row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
            row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
            row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0); var game = row.putObject("game_binding");
            game.put("pid", 123); game.put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
            row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
        }
    }
    private Fixture fixture(String name) throws IOException { return new Fixture(temp.resolve(name)); }
    private static RawJson raw(String text) { return new RawJson(text.getBytes(StandardCharsets.UTF_8)); }
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
    private static GuardEvidence guard(Fixture f, OperationKey operation) {
        return new GuardEvidence(observation(), f.source(), "session-1", BigInteger.ONE, operation, f.source, f.source, "authority-1", NOW, NOW.plusSeconds(30));
    }
    private static PlanningReadReceipt read(Fixture f) throws IOException {
        OperationKey operation = new OperationKey("query-test"); var binding = guard(f, operation);
        var before = new PlanningReadGuard(binding, true, true, true, "a".repeat(64));
        var request = new PlanningReadRequest(observation(), f.source(), "session-1", operation, new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(30));
        return new PlanningReadReceipt(request, "query-test/v1", "read-1", before, before, ack("read-1", Optional.of("{\"missing\":null,\"empty\":[],\"id\":18446744073709551615}")));
    }
    private static ActionCommand command(Fixture f) {
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, observation(), f.source(), "paused/v1", List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand("action-1", observation(), f.source(), "session-1", new OperationKey("pause-map"), new OpportunityJson.Obj(Map.of()), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
    }
    private static long leaves(Path root) throws IOException { try (var values = Files.list(root)) { return values.count(); } }

    @Test void rawMaterialsRetainWhitespaceMissingNullEmptyAndUnsafeIntegerTokens() throws IOException {
        Fixture f = fixture("material"); RawJson original = raw(" {\"null\":null, \"empty\":[],\"object\":{},\"id\":18446744073709551615} \n");
        assertThrows(UncheckedIOException.class, () -> f.archive.materialReferenceOf(original)); assertEquals(0, leaves(f.artifacts.identity().root()));
        ExactRef ref = f.archive.preserveMaterial(original); assertEquals(ref, f.archive.materialReferenceOf(original));
        assertArrayEquals(original.bytes(), f.archive.loadMaterial(ref).bytes()); assertEquals(original.bytes().length, ref.bytes());
        assertNotEquals(ref, f.archive.preserveMaterial(raw("null"))); assertNotEquals(ref, f.archive.preserveMaterial(raw("{}")));
        assertNotEquals(f.archive.materialReferenceOf(raw("null")), f.archive.materialReferenceOf(raw("{}")));
    }
    @Test void repeatedSameWriterCallsRefuseCorruptionAndSameBytesReplacementWithoutRepair() throws IOException {
        for (boolean replace : List.of(false, true)) {
            Fixture f = fixture(replace ? "same-writer-replacement" : "same-writer-corruption");
            RawJson original = raw("{\"retained\":true}");
            byte[] ledger = Files.readAllBytes(f.layout.snapshot());
            f.writer.locked(session -> {
                var bound = f.archive.withSession(session);
                ExactRef ref = bound.preserveMaterial(original);
                assertEquals(original, bound.loadMaterial(ref));
                assertEquals(ref, bound.materialReferenceOf(original));
                byte[] detached = f.archive.readArtifact(session, ref, 1024);
                detached[0] = 0;
                assertEquals(original, bound.loadMaterial(ref));
                Path target = Path.of(ref.path());
                if (replace) {
                    Path retained = target.resolveSibling("retained-original.bin");
                    Files.move(target, retained);
                    Files.write(target, original.bytes(), StandardOpenOption.CREATE_NEW);
                    assertNotEquals(LedgerFiles.identity(retained).fileIdDecimal(), LedgerFiles.identity(target).fileIdDecimal());
                } else Files.writeString(target, "{\"changed\":true}", StandardOpenOption.TRUNCATE_EXISTING);
                byte[] changed = Files.readAllBytes(target);
                assertThrows(UncheckedIOException.class, () -> bound.loadMaterial(ref));
                assertThrows(UncheckedIOException.class, () -> bound.materialReferenceOf(original));
                assertThrows(UncheckedIOException.class, () -> bound.preserveMaterial(original));
                assertArrayEquals(changed, Files.readAllBytes(target));
                return null;
            });
            assertArrayEquals(ledger, Files.readAllBytes(f.layout.snapshot()));
        }
    }
    @Test void allNativeOutcomeBranchesPreserveOriginalPacketsAndExactOptionalPresence() throws IOException {
        Fixture f = fixture("outcomes");
        for (Optional<String> result : List.of(Optional.<String>empty(), Optional.of("null"), Optional.of("{}"), Optional.of("[]"))) {
            var original = ack("result-" + result.map(String::length).orElse(-1) + result.map(String::hashCode).orElse(0), result);
            ExactRef ref = f.archive.preserve(original); assertEquals(original, f.archive.load(ref)); assertEquals(ref, f.archive.referenceOf(original));
            assertArrayEquals(original.originalPacket(), ((NativeActionPort.AckReceived) f.archive.load(ref)).originalPacket());
        }
        var rejected = new NativeActionPort.RejectedBeforeDispatch("zero", new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE, 0, "nothing written", Optional.of(raw("null"))));
        assertEquals(rejected, f.archive.load(f.archive.preserve(rejected)));
        var unknown = new NativeActionPort.Unknown("uncertain", "unknown must not replay", new byte[] {1, 0, 2, 0}, Optional.of(raw("[]")));
        ExactRef unknownRef = f.archive.preserve(unknown); long stored = f.artifacts.retainedNativeBytes();
        assertEquals(unknown, f.archive.load(unknownRef)); assertEquals(unknownRef, f.archive.preserve(unknown)); assertEquals(stored, f.artifacts.retainedNativeBytes());
        var emptyPacket = new NativeActionPort.Unknown("uncertain-empty", "no retained packet", new byte[0], Optional.empty());
        assertEquals(emptyPacket, f.archive.load(f.archive.preserve(emptyPacket)));
    }
    @Test void fabricatedAckBindingIsRefusedBeforePublishingAnyArtifact() throws IOException {
        Fixture f = fixture("bad-ack"); var actual = ack("actual", Optional.of("null"));
        var altered = new NativeActionPort.AckReceived("different", true, actual.originalResultToken(), actual.originalFrame(), actual.originalPacket());
        assertThrows(UncheckedIOException.class, () -> f.archive.preserve(altered)); assertEquals(0, leaves(f.root.resolve("artifacts")));
    }
    @Test void requestAndReadCodecsUseActualPhysicalArtifactsAndRejectMissingWrongFields() throws IOException {
        Fixture f = fixture("read"); var originalRequest = new NativeRequest("query-test", Optional.empty(), raw("{\"null\":null,\"empty\":[]}"));
        ExactRef req = f.archive.preserveRequest(originalRequest); assertEquals(originalRequest, f.archive.loadRequest(req)); assertEquals(req, f.archive.requestReferenceOf(originalRequest));
        var original = read(f); ExactRef ref = f.archive.preserveRead(original); assertEquals(original, f.archive.loadRead(ref)); assertEquals(ref, f.archive.readReferenceOf(original));
        ObjectNode changed = (ObjectNode) StrictJson.parse(f.artifacts.read(ref, StrictJson.EXPLICIT_MAX_BYTES), StrictJson.EXPLICIT_MAX_BYTES);
        ((ObjectNode) changed.get("before")).put("paused", 1);
        ExactRef malformed = f.writer.locked(session -> f.archive.preserveArtifact(session, StrictJson.canonical(changed, StrictJson.EXPLICIT_MAX_BYTES), StrictJson.EXPLICIT_MAX_BYTES));
        assertThrows(IllegalArgumentException.class, () -> f.archive.loadRead(malformed));
        changed.remove("contract_id"); ExactRef missing = f.writer.locked(session -> f.archive.preserveArtifact(session, StrictJson.canonical(changed, StrictJson.EXPLICIT_MAX_BYTES), StrictJson.EXPLICIT_MAX_BYTES));
        assertThrows(IllegalArgumentException.class, () -> f.archive.loadRead(missing));
        assertEquals(original, f.archive.loadRead(ref));
    }
    @Test void frontendReadRoundtripHasNoInventedGameplayPlayerOrLivingMapFlags() throws IOException {
        Fixture f = fixture("frontend"); var identity = new FrontendIdentity(MACHINE, observation().game(), "frontend-1", BigInteger.ONE, 123,
                new FrontendFrame.Menu(BigInteger.ONE), f.source, f.source); var origin = new CommandOrigin.Frontend(identity);
        var guard = new GuardEvidence(origin, f.source(), "frontend-1", BigInteger.ONE, new OperationKey("query-menu"), f.source, f.source, "authority-1", NOW, NOW.plusSeconds(30));
        var readGuard = new PlanningReadGuard(guard, "b".repeat(64));
        var request = new PlanningReadRequest(origin, f.source(), "frontend-1", guard.operation(), new OpportunityJson.Obj(Map.of()), NOW.plusSeconds(30));
        var read = new PlanningReadReceipt(request, "menu/v1", "menu-read-1", readGuard, readGuard, ack("menu-read-1", Optional.of("{}")));
        var restored = f.archive.loadRead(f.archive.preserveRead(read)); assertEquals(read, restored);
        assertInstanceOf(CommandOrigin.Frontend.class, restored.request().origin()); assertInstanceOf(PlanningReadGuard.Frontend.class, restored.before().readiness());
        assertThrows(IllegalStateException.class, restored.request()::before); assertThrows(IllegalStateException.class, restored.before()::paused);
    }
    @Test void nativeSnapshotKeepsItsEntireFramedPacketAndRejectsAChangedState() throws IOException {
        Fixture f = fixture("frame"); byte[] packet = NativeWire.packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"native-1\",\"revision\":18446744073709551615,\"state\":{\"empty\":[],\"null\":null}}".getBytes(StandardCharsets.UTF_8));
        var decoded = (NativeWire.Snapshot) NativeWire.decode(packet);
        var session = new NativeObservationPort.TransportSession(MACHINE, observation().game(), BigInteger.ONE, "session-1");
        var frame = new NativeObservationPort.ObservedFrame(session, decoded.snapshotId(), decoded.revision(), new RawJson(decoded.state().value()), packet, NOW);
        ExactRef ref = f.archive.preserveNativeFrame(frame); assertArrayEquals(packet, f.archive.loadNativeFrame(ref)); assertEquals(packet.length, ref.bytes());
        var forged = new NativeObservationPort.ObservedFrame(session, decoded.snapshotId(), decoded.revision(), raw("{}"), packet, NOW);
        assertThrows(UncheckedIOException.class, () -> f.archive.preserveNativeFrame(forged));
    }
    @Test void recordReceiptAndUnknownChainReopenWithoutMutatingPendingLedgerOrDispatching() throws IOException {
        Fixture f = fixture("chain"); byte[] ledgerBefore = Files.readAllBytes(f.layout.snapshot()); ActionCommand command = command(f);
        ActionReceipt intent = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
        ExactRef receiptRef = f.archive.preserveReceipt(intent); assertEquals(intent, f.archive.loadReceipt(receiptRef)); assertEquals(receiptRef, f.archive.receiptReferenceOf(intent));
        ActionRecord first = new ActionRecord(intent, Optional.empty()); ExactRef firstRef = f.archive.preserveRecord(first); assertEquals(firstRef, f.archive.recordReferenceOf(first));
        var attempt = new ActionState.Attempt("unknown-request", NOW, guard(f, command.operation()), new NativeRequest("pause-map", "timeline-control", raw("{}")));
        var unknown = new NativeActionPort.Unknown(attempt.requestId(), "lost ACK", new byte[] {7, 6, 5}, Optional.empty());
        ActionReceipt pending = new ActionReceipt(1, 2, command, ActionCodec.bodySha256(command), new ActionState.Unknown(Optional.of(attempt), Optional.of(unknown), "never resubmit", List.of(f.source)));
        ActionRecord second = new ActionRecord(pending, Optional.of(firstRef)); ExactRef secondRef = f.archive.preserveRecord(second);
        Fixture reopened = new Fixture(f.root, true); assertEquals(second, reopened.archive.loadRecord(secondRef));
        assertEquals(first, reopened.archive.loadRecord(reopened.archive.loadRecord(secondRef).previous().orElseThrow()));
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, reopened.archive.loadRecord(secondRef).receipt().outcome());
        assertArrayEquals(ledgerBefore, Files.readAllBytes(f.layout.snapshot())); assertEquals(0L, f.writer.<Long>locked(session -> session.head().state().sequence()).longValue());
    }
    @Test void controlReceiptAutomaticallyPreservesItsQueryDependencies() throws IOException {
        Fixture f = fixture("control"); var command = command(f); var read = read(f);
        var attempt = new ActionState.Attempt(read.requestId(), NOW, guard(f, command.operation()), new NativeRequest("pause-map", "timeline-control", raw("{}")));
        var control = new ActionState.ControlApplied(read, List.of(read), "control/v1", command.expected().values());
        var receipt = new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command), new ActionState.Settled(attempt, read.original(), control));
        assertEquals(receipt, f.archive.loadReceipt(f.archive.preserveReceipt(receipt))); assertEquals(read, f.archive.loadRead(f.archive.readReferenceOf(read)));
    }
    @Test void sameWriterScopeIsLiveThreadBoundRestoredAndNeverReacquiresTheHeldLock() throws IOException {
        Fixture f = fixture("scope"); AtomicReference<ActionPorts.OutcomeArchive> escaped = new AtomicReference<>();
        ExactRef ref = f.writer.locked(session -> f.archive.inSession(session, bound -> {
            escaped.set(bound); ExactRef kept = f.archive.preserveMaterial(raw("{\"scope\":true}"));
            assertEquals(kept, bound.materialReferenceOf(raw("{\"scope\":true}")));
            f.archive.inSession(session, nested -> { assertEquals(kept, nested.materialReferenceOf(raw("{\"scope\":true}"))); return null; });
            CompletionException crossedThread = assertThrows(CompletionException.class, () -> CompletableFuture.runAsync(() -> bound.loadMaterial(kept)).join());
            assertInstanceOf(IllegalArgumentException.class, crossedThread.getCause());
            return kept;
        }));
        assertThrows(IllegalArgumentException.class, () -> escaped.get().loadMaterial(ref));
        assertEquals(raw("{\"scope\":true}"), f.archive.loadMaterial(ref));
        f.writer.locked(session -> {
            assertThrows(IllegalStateException.class, () -> f.archive.inSession(session, bound -> { throw new IllegalStateException("callback fault"); })); return null;
        });
        assertNotNull(f.archive.preserveMaterial(raw("{\"after_fault\":true}")));
    }
    @Test void anotherWriterSessionAndAnotherInstalledStoreAreRejected() throws IOException {
        Fixture a = fixture("writer-a"), b = fixture("writer-b");
        b.writer.locked(session -> { assertThrows(UncheckedIOException.class, () -> a.archive.withSession(session)); return null; });
        assertThrows(IOException.class, () -> new NativeOutcomeArchive(a.artifacts, b.writer));
        ImmutableArtifactStore alias = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(a.root.resolve("artifacts"), a.layout.lock(), 8 * 1024 * 1024), StorageWriteGuardTestSupport.forLayout(a.layout));
        assertThrows(IOException.class, () -> new NativeOutcomeArchive(alias, a.writer));
        ContinuityWriter alternateAuthority = new ContinuityWriter(a.layout, List.of(a.source), new TransitionAuthority() {
            @Override public String revalidate(ContinuityState predecessor, Request request) { return "a".repeat(64); }
            @Override public ContinuityState reduce(ContinuityState predecessor, Request request) { return predecessor; }
        }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(a.artifacts), Optional.empty()), a.artifacts.storageGuard());
        alternateAuthority.locked(session -> {
            assertThrows(UncheckedIOException.class, () -> a.archive.withSession(session)); return null;
        });
    }
    @Test void nativePacketsAboveOneMiBAreReadUnderTheActualBoundedWriterPinContract() throws IOException {
        Fixture f = fixture("large"); var original = ack("large-result", Optional.of("{\"payload\":\"" + "x".repeat(1_100_000) + "\"}"));
        ExactRef ref = f.writer.locked(session -> f.archive.inSession(session, bound -> {
            ExactRef retained = bound.preserve(original); assertEquals(original, bound.load(retained)); return retained;
        }));
        assertArrayEquals(original.originalPacket(), ((NativeActionPort.AckReceived) f.archive.load(ref)).originalPacket());
    }
    @Test void verifiedStoreResultSharesItsActualPinAndDetachedBytesWithTheLiveSession() throws Exception {
        Fixture f=fixture("single-committed-read");byte[] original="{\"schema\":\"read-pin-fixture/v1\",\"value\":73}".getBytes(StandardCharsets.UTF_8);
        Pin retained=f.writer.locked(same->f.artifacts.publish(original,1024));
        byte[] ledger=Files.readAllBytes(f.layout.snapshot());var escaped=new AtomicReference<ContinuityStorePort.Session>();
        f.writer.locked(same->{
            escaped.set(same);var result=f.artifacts.readOriginal(retained.reference(),1024);
            assertEquals(retained,result.pin());assertArrayEquals(original,result.bytes());
            byte[] caller=result.bytes();caller[0]^=1;assertArrayEquals(original,result.bytes(),"the held result must keep its own immutable bytes");
            try {
                var holder=NativeOutcomeArchive.class.getDeclaredField("readOriginalCapture");holder.setAccessible(true);
                Object trackerObject=holder.get(f.archive);if(!(trackerObject instanceof ThreadLocal<?> tracker))throw new AssertionError("actual READ capture holder absent");
                Class<?> captureClass=Class.forName(NativeOutcomeArchive.class.getName()+"$ReadOriginalCapture");
                var constructor=captureClass.getDeclaredConstructor(ContinuityStorePort.Session.class,List.class);constructor.setAccessible(true);
                Object capture=constructor.newInstance(same,List.of());ThreadLocal.class.getMethod("set",Object.class).invoke(tracker,capture);
                try {
                    assertArrayEquals(original,f.archive.readArtifact(same,retained.reference(),1024));
                    var pins=captureClass.getDeclaredField("pins");pins.setAccessible(true);
                    assertEquals(Map.of(retained.reference(),retained),pins.get(capture),"READ evidence must receive the exact verified committed payload Pin");
                } finally {tracker.remove();}
            } catch(ReflectiveOperationException failure){throw new IOException("test-only capture observation failed",failure);}
            assertThrows(IOException.class,()->f.archive.readArtifact(same,retained.reference(),original.length-1));
            assertThrows(IOException.class,()->f.archive.readArtifact(same,f.source,1024));
            assertThrows(IllegalArgumentException.class,()->f.archive.readArtifact(same,retained.reference(),0));
            assertArrayEquals(ledger,Files.readAllBytes(f.layout.snapshot()));return null;
        });
        assertThrows(IllegalArgumentException.class,()->f.archive.readArtifact(escaped.get(),retained.reference(),1024));
        assertArrayEquals(original,f.artifacts.readOriginal(retained.reference(),1024).bytes());
        assertArrayEquals(ledger,Files.readAllBytes(f.layout.snapshot()));
        System.out.println("PASS verified CAS Pin+detached bytes, READ tracker, exact bounds/root and closed Session; no ledger mutation");
    }
    @Test void firstCommittedMetadataAndDeclaredPayloadReferenceStillRejectMalformedOriginals() throws Exception {
        for(String change:List.of("schema","payload-ref")) {
            Fixture f=fixture("v2-first-metadata-"+change);byte[] original="{\"value\":73}".getBytes(StandardCharsets.UTF_8);
            Pin retained=f.writer.locked(same->f.artifacts.publish(original,1024));
            Path commit=Path.of(retained.reference().path()).resolveSibling(retained.reference().sha256()+".commit.json");
            byte[] before=Files.readAllBytes(f.layout.snapshot());
            var metadata=StrictJson.object(StrictJson.parse(Files.readAllBytes(commit)),Set.of("schema","payload","payload_identity","commit_identity"));
            if(change.equals("schema"))metadata.put("schema","wrong-existing-schema");
            else metadata.set("payload",new ExactRef(retained.reference().path(),retained.reference().bytes(),"0".repeat(64)).toJson());
            byte[] changed=StrictJson.canonical(metadata);Files.write(commit,changed,StandardOpenOption.TRUNCATE_EXISTING);
            f.writer.locked(same->{
                if(change.equals("schema"))assertThrows(IllegalArgumentException.class,()->f.archive.readArtifact(same,retained.reference(),1024));
                else assertThrows(IOException.class,()->f.archive.readArtifact(same,retained.reference(),1024));
                return null;
            });
            assertArrayEquals(changed,Files.readAllBytes(commit));assertArrayEquals(original,Files.readAllBytes(Path.of(retained.reference().path())));
            assertArrayEquals(before,Files.readAllBytes(f.layout.snapshot()));
        }
        System.out.println("PASS first CAS metadata schema and exact expected payload ref reject malformed originals without repair or ledger mutation");
    }
}
