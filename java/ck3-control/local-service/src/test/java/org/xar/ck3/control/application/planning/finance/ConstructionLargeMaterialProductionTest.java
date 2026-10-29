package org.xar.ck3.control.application.planning.finance;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual Windows archive/writer + production source/reducer/codec consumers. Software material is not a native-read qualification. */
public final class ConstructionLargeMaterialProductionTest {
    @TempDir Path root;
    private final java.util.ArrayList<StorageWriteGuardTestSupport> retainedGuards = new java.util.ArrayList<>();
    @AfterEach void closeActualSoftwareAllocationScopes() throws IOException {
        for (StorageWriteGuardTestSupport guard : retainedGuards) guard.close();
    }
    @Test void completeLargeMaterialReopensThroughTheSameArchiveAndCanonicalBodyKeepsOnlyItsReference() throws Exception {
        for (boolean legacy : new boolean[]{false, true}) {
            var fixture = new Fixture(root.resolve(legacy ? "large-legacy" : "large-refresh"), 8 * 1024 * 1024);
            fixture.writer.locked(same -> {
                Obj original = ledger().with("retained_original_extension", new Text("x".repeat(200_000)));
                Obj input = legacy ? obj("schema", new Text("xar.construction-material-reducer-input/v1"), "ledger", original,
                        "action_request_id", new Text("original-request"), "query_observation", query(), "root", Nil.INSTANCE, "cash", Nil.INSTANCE)
                        : input(original, query());
                byte[] archivedInput = encode(input); assertTrue(archivedInput.length > ContinuityJson.DOCUMENT_MAX_BYTES);
                var source = ConstructionMaterialSource.preserve(same, fixture.archive, input);
                assertEquals(source, ConstructionMaterialSource.decode(source.toJson()));
                assertEquals(source, ConstructionMaterialSource.decode(object(parse(encode(source.toJson())), "material source round trip")));
                assertEquals(input, DriverJson.object(fixture.archive.withSession(same).loadMaterial(source.input()).bytes(), ConstructionMaterialSource.MAX_INPUT_BYTES));
                var replay = source.load(same, fixture.archive);
                assertEquals(original, replay.ledger().original());
                assertEquals(legacy ? ConstructionMaterialReducer.InputVersion.LEGACY_V1 : ConstructionMaterialReducer.InputVersion.REFRESH_V2, replay.version());
                assertEquals(legacy ? Optional.empty() : Optional.of(ConstructionMaterialReducer.RefreshKind.COLD_MATERIAL), replay.refreshKind());
                assertArrayEquals(archivedInput, fixture.archive.withSession(same).loadMaterial(source.input()).bytes());
                assertArrayEquals(encode(ConstructionMaterialReducer.reduce(encode(input(original, query()))).originalBody()),
                        encode(ConstructionMaterialReducer.reduce(replay).originalBody()));
                Obj body = source.retainIn(ConstructionMaterialReducer.reduce(replay).originalBody());
                assertTrue(encode(body).length > ContinuityJson.DOCUMENT_MAX_BYTES);
                assertTrue(encode(body).length < ContinuityJson.DOMAIN_MAX_BYTES);
                assertEquals(source.toJson(), body.get(ConstructionMaterialSource.BODY_FIELD));
                assertNull(body.get("reducer_input")); assertNull(body.get("query_observation"));
                Obj details = obj("schema", new Text("construction-large-material-software/v1"), "material_source", source.toJson());
                ExactRef archived = fixture.archive.preserveArtifact(same, encode(body), ConstructionLedgerCodec.MAX_BYTES);
                var request = new DomainBodies.ImportRequest(DomainBodies.Slot.CONSTRUCTION, ConstructionLedgerCodec.SCHEMA,
                        archived, encode(details), List.of(source.input()), "actual-large-software-material");
                assertTrue(request.producerInput().length < ContinuityJson.DOCUMENT_MAX_BYTES);
                var before = same.head(); var prepared = same.previewImport(request); same.commitImport(prepared);
                var read = assertInstanceOf(DomainBodies.Available.class, same.readDomain(DomainBodies.Slot.CONSTRUCTION));
                assertArrayEquals(ContinuityJson.canonical(ContinuityJson.parseObject(encode(body), ConstructionLedgerCodec.MAX_BYTES), ConstructionLedgerCodec.MAX_BYTES), read.canonicalBody());
                assertEquals(body, ConstructionLedgerCodec.decodeLedger(read.canonicalBody()).original());
                var saved = ConstructionSavedBody.read(same, same.head().state(), List.of(fixture.source));
                assertEquals(body, saved.ledger().original()); saved.requireUnchanged(same);
                var reader = new FinanceStatePort.ReaderBinding(FinanceStatePort.Domain.CONSTRUCTION, fixture.source,
                        document -> ConstructionLedgerCodec.decodeLedger(document.bytes()).pending().isPresent() ? FinanceStatePort.Pending.PENDING : FinanceStatePort.Pending.CLEAR);
                var originalPin = same.capturePin(read.reference().payload(), ConstructionLedgerCodec.MAX_BYTES);
                byte[] originalBody = same.readPinned(originalPin, ConstructionLedgerCodec.MAX_BYTES);
                assertArrayEquals(encode(body), originalBody);
                assertTrue(CanonicalFinanceStateSource.sameOriginalBody(read.canonicalBody(), originalBody, ConstructionLedgerCodec.MAX_BYTES));
                assertEquals(FinanceStatePort.Pending.CLEAR, reader.reader().decode(new FinanceStatePort.Document(FinanceStatePort.Domain.CONSTRUCTION, read.reference().payload(), originalBody)));
                same.verifyPin(originalPin);
                assertEquals(before.state().sequence() + 1, same.head().state().sequence());
                return null;
            });
        }
    }
    @Test void actualCollectorRootFallbackReopensThroughTheArchiveAndFeedsTheExistingEconomicConsumer() throws Exception {
        for (Optional<BigInteger> observedIncome : List.of(Optional.of(BigInteger.ZERO), Optional.of(BigInteger.valueOf(-1)),
                Optional.of(BigInteger.valueOf(17)), Optional.<BigInteger>empty())) {
            String label = observedIncome.map(BigInteger::toString).orElse("unavailable");
            var fixture = new Fixture(root.resolve("root-fallback-" + label), 8 * 1024 * 1024);
            Obj nativeMaterial = query();
            Obj snapshot = object(nativeMaterial.get("starting_snapshot"), "software native snapshot").with("revision", n(77));
            var request = materialRequest(fixture.source, snapshot);
            Obj nativeRoot = materialRoot(request, observedIncome);
            fixture.writer.locked(same -> {
                var operations = new java.util.ArrayList<OperationKey>();
                var definitions = new FinanceReadContracts(query -> new FinanceReadContracts.Registration(fixture.source,
                        new FinanceReadContracts.Permission(Optional.empty(), "material-root-software:" + query.name(),
                                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP)));
                var reads = new PlanningReadPort() {
                    @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest original) {
                        throw new AssertionError("material collection must borrow its original writer");
                    }
                    @Override public <T> PlanningReadResult<T> read(ContinuityStorePort.Session borrowed, ReadContract<T> contract, PlanningReadRequest original) {
                        assertSame(same, borrowed); operations.add(original.operation());
                        if (original.operation().equals(FinanceReadContracts.Query.CASH.operation()))
                            return new PlanningReadResult.Unavailable<>("explicit software CASH unavailable", Optional.empty());
                        Obj result;
                        if (original.operation().equals(FinanceReadContracts.Query.ROOT.operation())) result = nativeRoot;
                        else {
                            assertEquals(FinanceReadContracts.Query.CONSTRUCTION.operation(), original.operation());
                            result = object(object(nativeMaterial.get("native_envelope"), "material native envelope").get("result"), "material native result");
                        }
                        String id = "software-root-fallback-" + operations.size();
                        Obj frame = obj("type", new Text("command_result"), "protocol_version", n(1), "request_id", new Text(id),
                                "ok", new Bool(true), "result", result);
                        byte[] raw = encode(frame);
                        byte[] packet = java.nio.ByteBuffer.allocate(raw.length + 4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
                        var ack = new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(encode(result))), new RawJson(raw), packet);
                        var binding = new GuardEvidence(original.before(), original.source(), original.sessionId(), BigInteger.ONE,
                                original.operation(), fixture.source, fixture.source, "material-root-software-read", java.time.Instant.now(), original.deadline());
                        var guard = new PlanningReadGuard(binding, true, true, true, "a".repeat(64));
                        var receipt = new PlanningReadReceipt(original, contract.contractId(), id, guard, guard, ack);
                        T decoded = contract.decode(receipt);
                        ExactRef rawReference = fixture.archive.withSession(same).preserveMaterial(new RawJson(raw));
                        return new PlanningReadResult.Known<>(decoded, receipt, rawReference);
                    }
                };
                var state = new FinanceStatePort(current -> { throw new AssertionError("read-only material does not query spending state"); }, List.of());
                var collector = new OrdinaryConstructionCollector(new OrdinaryFinanceCollector(definitions, reads, state),
                        new OrdinaryConstructionCollector.EndingSnapshot() {
                            @Override public Obj readCurrent(PlanningRequest current) { throw new AssertionError("borrowed snapshot required"); }
                            @Override public Obj readCurrent(ContinuityStorePort.Session borrowed, PlanningRequest current) {
                                assertSame(same, borrowed); assertEquals(request, current); return snapshot;
                            }
                        }, current -> { throw new AssertionError("material read grants no funding or action"); });
                var material = assertInstanceOf(OrdinaryConstructionCollector.MaterialAvailable.class, collector.material(same, request));
                assertEquals(List.of(FinanceReadContracts.Query.ROOT.operation(), FinanceReadContracts.Query.CASH.operation(),
                        FinanceReadContracts.Query.CONSTRUCTION.operation()), operations);
                assertEquals(2, material.originalReads().size()); assertTrue(material.cash().isEmpty());
                assertEquals(observedIncome.isPresent(), material.root().isPresent());
                for (var read : material.originalReads()) {
                    assertEquals(request.before(), read.request().before()); assertEquals(request.source(), read.request().source());
                    assertEquals(request.sessionId(), read.request().sessionId());
                }
                assertEquals(n(77), object(material.queryInput().get("starting_snapshot"), "actual collector public frame").get("revision"));
                assertEquals(n(3), object(material.queryInput().get("starting_snapshot"), "actual collector native frame").get("native_revision"));
                Obj completed = ConstructionMaterialReducer.reduce(encode(input(ledger(), query()))).originalBody()
                        .with("retained_original_extension", new Text("x".repeat(200_000)));
                var input = ConstructionMaterialReducer.input(ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH,
                        ConstructionLedgerCodec.decodeLedger(encode(completed)), "original-request", material.queryInput(), material.root(), material.cash());
                var source = ConstructionMaterialSource.preserve(same, fixture.archive, input);
                var replay = source.load(same, fixture.archive);
                assertEquals(ConstructionMaterialReducer.RefreshKind.COMPLETED_CASH, replay.refreshKind().orElseThrow());
                assertEquals(input, DriverJson.object(fixture.archive.withSession(same).loadMaterial(source.input()).bytes(), ConstructionMaterialSource.MAX_INPUT_BYTES));
                Obj body = source.retainIn(ConstructionMaterialReducer.reduce(replay).originalBody());
                ExactRef archived = fixture.archive.preserveArtifact(same, encode(body), ConstructionLedgerCodec.MAX_BYTES);
                Obj details = obj("schema", new Text("construction-large-material-software/v1"), "material_source", source.toJson());
                var imported = new DomainBodies.ImportRequest(DomainBodies.Slot.CONSTRUCTION, ConstructionLedgerCodec.SCHEMA,
                        archived, encode(details), List.of(source.input()), "actual-collected-root-fallback-" + label);
                same.commitImport(same.previewImport(imported));
                var read = assertInstanceOf(DomainBodies.Available.class, same.readDomain(DomainBodies.Slot.CONSTRUCTION));
                assertArrayEquals(ContinuityJson.canonical(ContinuityJson.parseObject(encode(body), ConstructionLedgerCodec.MAX_BYTES), ConstructionLedgerCodec.MAX_BYTES), read.canonicalBody());
                var saved = ConstructionSavedBody.read(same, same.head().state(), List.of(fixture.source)); saved.requireUnchanged(same);
                var receipt = saved.ledger().applied().orElseThrow();
                assertEquals(observedIncome, receipt.economy().postGross());
                assertEquals(observedIncome.map(ignored -> BigInteger.valueOf(820)), receipt.economy().incomeDate());
                assertTrue(receipt.economy().postCash().isEmpty()); assertNull(receipt.original().get("post_cash_v2"));
                assertEquals(n(77), receipt.original().get("post_public_revision"));
                assertEquals(n(3), receipt.original().get("post_native_revision"));
                var outcome = org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomy.classify(
                        new org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.OutcomeRequest(
                                receipt.economy(), "1.20.0.4", Optional.empty(), Optional.empty()));
                assertTrue(outcome.materialCompleted()); assertFalse(outcome.cash().observed());
                assertEquals(observedIncome, outcome.receipt().postGross());
                assertArrayEquals(encode(receipt.original()), outcome.receipt().original().bytes());
                assertEquals(body, ConstructionLedgerCodec.decodeLedger(read.canonicalBody()).original());
                return null;
            });
        }
    }
    @Test void missingWrongDigestForeignArchiveAndIdenticalBytesWithANewFileIdCannotSupplyOriginalMaterial() throws Exception {
        var fixture = new Fixture(root.resolve("identity"), 8 * 1024 * 1024);
        var foreign = new Fixture(root.resolve("foreign"), 8 * 1024 * 1024);
        var source = fixture.writer.locked(same -> ConstructionMaterialSource.preserve(same, fixture.archive, input(ledger(), query())));
        foreign.writer.locked(same -> { assertThrows(IOException.class, () -> source.load(same, fixture.archive)); assertThrows(IOException.class, () -> source.load(same, foreign.archive)); return null; });
        fixture.writer.locked(same -> {
            var wrong = new ConstructionMaterialSource(new ExactRef(source.input().path(), source.input().bytes(), "b".repeat(64)));
            assertThrows(IOException.class, () -> wrong.load(same, fixture.archive)); return null;
        });
        Path original = Path.of(source.input().path()), replacement = root.resolve("new-file-identical-bytes");
        byte[] raw = Files.readAllBytes(original); Files.write(replacement, raw); Files.move(replacement, original, StandardCopyOption.REPLACE_EXISTING);
        fixture.writer.locked(same -> { assertThrows(IOException.class, () -> source.load(same, fixture.archive)); return null; });
        assertArrayEquals(raw, Files.readAllBytes(original));
        var missing = new Fixture(root.resolve("missing"), 8 * 1024 * 1024);
        var missingSource = missing.writer.locked(same -> ConstructionMaterialSource.preserve(same, missing.archive, input(ledger(), query())));
        Files.delete(Path.of(missingSource.input().path()));
        missing.writer.locked(same -> { assertThrows(IOException.class, () -> missingSource.load(same, missing.archive)); return null; });
    }
    @Test void actualArchiveBudgetAndExistingCanonicalLimitsStaySeparateAndUnknownCannotBeCleared() throws Exception {
        var fixture = new Fixture(root.resolve("budget"), 65_536);
        fixture.writer.locked(same -> {
            Obj large = input(ledger().with("retained_original_extension", new Text("x".repeat(200_000))), query());
            long sequence = same.head().state().sequence();
            assertThrows(IOException.class, () -> ConstructionMaterialSource.preserve(same, fixture.archive, large));
            assertEquals(sequence, same.head().state().sequence());
            Obj unknown = ledger().with("pending", receipt().with("status", new Text("action_state_unknown")));
            var actualInput = ConstructionMaterialSource.preserve(same, fixture.archive, input(unknown, query()));
            assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.reduce(actualInput.load(same, fixture.archive)));
            assertEquals(new Text("action_state_unknown"), actualInput.load(same, fixture.archive).ledger().pending().orElseThrow().original().get("status"));
            assertThrows(IllegalArgumentException.class, () -> ConstructionDomainLifecycle.preparedZeroDispatchBody(actualInput.load(same, fixture.archive).ledger(), query()));
            return null;
        });
        var complete = new Fixture(root.resolve("bounds"), 8 * 1024 * 1024);
        complete.writer.locked(same -> {
            var source = ConstructionMaterialSource.preserve(same, complete.archive, input(ledger(), query()));
            assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialSource.decode(source.toJson().with("input", Nil.INSTANCE)));
            assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialSource.decode(source.toJson().with("extra", new Bool(true))));
            var removed = new java.util.LinkedHashMap<String,Value>(source.toJson().members()); removed.remove("input");
            assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialSource.decode(new Obj(removed)));
            Obj exact = object(parse(StrictJson.canonical(source.input().toJson())), "exact reference");
            for (Value wrong : List.of(new Bool(true), new Text("12"), Nil.INSTANCE))
                assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialSource.decode(source.toJson().with("input", exact.with("bytes", wrong))));
            Obj overflow = ledger().with("retained_original_extension", new Text("x".repeat(ContinuityJson.DOMAIN_MAX_BYTES)));
            assertThrows(IllegalArgumentException.class, () -> source.retainIn(overflow));
            assertThrows(IllegalArgumentException.class, () -> new ConstructionMaterialSource(new ExactRef(source.input().path(), ConstructionMaterialSource.MAX_INPUT_BYTES + 1L, source.input().sha256())));
            assertEquals(ContinuityJson.DOMAIN_MAX_BYTES, ConstructionDomainLifecycle.MAX_BYTES);
            assertEquals(ContinuityJson.DOCUMENT_MAX_BYTES, ConstructionDomainLifecycle.MAX_INPUT_BYTES);
            return null;
        });
    }
    @Test void aFailedRealStorageMutationBlocksNewMaterialUntilActualAccountingAndNeverResolvesActionUnknown() throws Exception {
        var fixture = new Fixture(root.resolve("storage-unknown"), 8 * 1024 * 1024);
        fixture.writer.locked(same -> {
            Path interrupted = root.resolve("storage-unknown").toAbsolutePath().normalize().resolve("interrupted-original.json");
            var plan = new StorageWriteGuard.WritePlan(fixture.guard.originalLock(), List.of(new StorageWriteGuard.FileCreate(interrupted, 2)));
            long sequence = same.head().state().sequence();
            assertThrows(IOException.class, () -> fixture.guard.write(plan, () -> {
                Files.write(interrupted, new byte[]{'{','}'}, java.nio.file.StandardOpenOption.CREATE_NEW);
                throw new IOException("controlled failure after actual file creation");
            }));
            assertTrue(fixture.guard.hasUnknownWrite()); assertTrue(Files.exists(interrupted));
            Obj unknown = ledger().with("pending", receipt().with("status", new Text("action_state_unknown")));
            assertThrows(IOException.class, () -> ConstructionMaterialSource.preserve(same, fixture.archive, input(unknown, query())));
            assertEquals(sequence, same.head().state().sequence());
            fixture.guard.reconcileStorageOnly();
            assertFalse(fixture.guard.hasUnknownWrite());
            var original = ConstructionMaterialSource.preserve(same, fixture.archive, input(unknown, query()));
            var retained = original.load(same, fixture.archive);
            assertEquals(new Text("action_state_unknown"), retained.ledger().pending().orElseThrow().original().get("status"));
            assertThrows(IllegalArgumentException.class, () -> ConstructionMaterialReducer.reduce(retained));
            assertEquals(sequence, same.head().state().sequence()); assertTrue(fixture.guard.validations() > 0);
            return null;
        });
    }
    /** Root's qualified physical stage may call this once with its actual installed lifecycle and archived reads.
     * This invokes the full production snapshot/source/read verifier twice through preview/commit; it creates no proof or fake read. */
    public static ConstructionDomainLifecycle.Publication assertActualMaterialPublication(ContinuityStorePort.Session same,
            ConstructionDomainLifecycle.Prepared lifecycle, NativeOutcomeArchive archive,
            ConstructionLedgerCodec.Ledger previous, ConstructionMaterialReducer.RefreshKind kind, String action,
            OrdinaryConstructionCollector.MaterialAvailable actual) throws IOException {
        byte[] complete = encode(ConstructionMaterialReducer.input(kind, previous, action, actual.queryInput(), actual.root(), actual.cash()));
        assertTrue(complete.length > ContinuityJson.DOCUMENT_MAX_BYTES, "this regression requires a real complete input above the old inline boundary");
        var publication = lifecycle.publishMaterial(same, previous, kind, action, actual);
        assertActualReadback(same, lifecycle, archive, complete);
        return publication;
    }
    /** A separate genuine pre-INTENT failure stage must supply its actual original pending/canonical absence and fresh Native reads. */
    public static ConstructionDomainLifecycle.Publication assertActualZeroDispatchPublication(ContinuityStorePort.Session same,
            ConstructionDomainLifecycle.Prepared lifecycle, NativeOutcomeArchive archive, PlanningRequest request,
            OrdinaryConstructionCollector.MaterialAvailable actual) throws IOException {
        var previous = lifecycle.read(same); var pending = previous.pending().orElseThrow();
        byte[] complete = encode(ConstructionMaterialReducer.input(ConstructionMaterialReducer.RefreshKind.PREPARED_ZERO_DISPATCH, previous, pending.identity().actionRequestId(), actual.queryInput(), actual.root(), actual.cash()));
        assertTrue(complete.length > ContinuityJson.DOCUMENT_MAX_BYTES);
        assertTrue(lifecycle.hasRecoverablePreparedHead(same));
        var publication = lifecycle.recoverPreparedWithoutIntent(same, request, actual).orElseThrow();
        assertActualReadback(same, lifecycle, archive, complete);
        assertEquals(Nil.INSTANCE, lifecycle.read(same).original().get("pending"));
        assertEquals(new Bool(false), object(lifecycle.read(same).original().get("last_pre_intent_zero_dispatch"), "actual zero-dispatch proof").get("replay_allowed"));
        return publication;
    }
    private static void assertActualReadback(ContinuityStorePort.Session same, ConstructionDomainLifecycle.Prepared lifecycle,
            NativeOutcomeArchive archive, byte[] complete) throws IOException {
        var actual = lifecycle.read(same);
        var source = ConstructionMaterialSource.decode(object(actual.original().get(ConstructionMaterialSource.BODY_FIELD), "actual committed material source"));
        assertEquals(complete.length, source.input().bytes()); assertEquals(ActionCodec.sha256(complete), source.input().sha256());
        assertArrayEquals(complete, archive.withSession(same).loadMaterial(source.input()).bytes());
        var loaded = source.load(same, archive); assertEquals(DriverJson.object(complete, ConstructionMaterialSource.MAX_INPUT_BYTES).get("ledger"), loaded.ledger().original());
        assertTrue(encode(actual.original()).length <= ContinuityJson.DOMAIN_MAX_BYTES);
        assertEquals(actual.original(), ConstructionSavedBody.read(same, same.head().state(), lifecycle.registration().producerSources()).ledger().original());
        assertEquals(source, ConstructionMaterialSource.decode(object(ConstructionLedgerCodec.decodeLedger(encode(actual.original())).original().get(ConstructionMaterialSource.BODY_FIELD), "source after canonical serde")));
    }
    /** This finite unit verifier checks the production material source/reducer and real canonical writer; it is not Root's physical verifier. */
    private final class Fixture {
        static final String MACHINE = "construction-large-material-software-machine";
        final ExactRef source;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        final StorageWriteGuardTestSupport guard;
        Fixture(Path directory, long archiveBudget) throws IOException {
            assertTrue(System.getProperty("os.name").startsWith("Windows"), "actual Windows FileID and allocation boundary required; not skipped");
            Files.createDirectories(directory);
            var state = StrictJson.object();
            state.put("schema", "root.ck3.continuity-window/v1"); state.put("machine_id", MACHINE); state.put("sequence", 0);
            state.put("window_id", 1); state.put("status", "running"); state.put("target_days", 10958); state.put("target_years", 30);
            state.put("calendar_year_days", 365.25); state.put("start_date_raw", 1000); state.put("target_date_raw", 263992);
            state.put("last_settled_date_raw", 1000); state.put("last_settled_cycles", 1); state.put("manual_repair_count", 1);
            state.put("automatic_recovery_count", 0); state.put("binding_lineage_count", 0);
            var game = state.putObject("game_binding"); game.put("pid", 123); game.put("creation_date", "2026-10-23T01:00:00Z");
            state.putNull("latest_binding"); state.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 1); state.put("NEXT", 2);
            Path snapshot = directory.resolve("ROOT-CONTINUITY-WINDOW.json"), anchor = directory.resolve("anchor.json");
            Files.write(snapshot, ContinuityJson.canonical(state)); Files.write(anchor, ContinuityJson.canonical(state));
            Files.write(directory.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0]); Files.createDirectory(directory.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Path producer = directory.resolve("actual-software-producer.java"); Files.writeString(producer, "construction large material source-bound software verifier v1");
            source = reference(producer); var layout = new Layout(snapshot, reference(anchor), MACHINE);
            Path objects = directory.resolve("objects"); Files.createDirectory(objects);
            guard = StorageWriteGuardTestSupport.create(layout.snapshot().getParent(), layout.lock(), 16 * 1024 * 1024);
            retainedGuards.add(guard);
            var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(objects, layout.lock(), archiveBudget), guard);
            var registration = new DomainBodies.Registration(DomainBodies.Slot.CONSTRUCTION, ConstructionLedgerCodec.SCHEMA,
                    ConstructionLedgerCodec.MAX_BYTES, List.of(source), (head, previous, request, body) -> verify(request, body));
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState head, Request request) { throw new AssertionError("only actual domain imports are used"); }
                @Override public ContinuityState reduce(ContinuityState head, Request request) { throw new AssertionError("only actual domain imports are used"); }
            }, Clock.systemUTC(), new ContinuityWriter.Extensions(List.of(registration), Optional.of(store), Optional.empty()), guard);
            assertSame(guard, store.storageGuard()); assertSame(guard, writer.storageGuard());
            archive = new NativeOutcomeArchive(store, writer);
        }
        private String verify(DomainBodies.ImportRequest request, byte[] body) throws IOException {
            Obj details = object(parse(request.producerInput()), "small actual fixture producer input");
            require(details.members().keySet().equals(java.util.Set.of("schema", "material_source"))
                    && new Text("construction-large-material-software/v1").equals(details.get("schema")), "exact software import contract required");
            var source = ConstructionMaterialSource.decode(object(details.get("material_source"), "actual software material source"));
            require(request.evidence().contains(source.input()), "actual complete source missing from writer evidence");
            Obj expected = source.retainIn(ConstructionMaterialReducer.reduce(source.load(writer.borrowedSession(), archive)).originalBody());
            require(Arrays.equals(body, encode(expected)), "actual source/reducer output differs from canonical import");
            return ActionCodec.sha256(body);
        }
    }
    private static Obj input(Obj original, Obj query) {
        return ConstructionMaterialReducer.input(ConstructionMaterialReducer.RefreshKind.COLD_MATERIAL, ConstructionLedgerCodec.decodeLedger(encode(original)), "original-request", query, Optional.empty(), Optional.empty());
    }
    private static Obj ledger() {
        return obj("schema", new Text(ConstructionLedgerCodec.SCHEMA), "pending", Nil.INSTANCE, "applied", receipt(), "applied_prior", new Arr(List.of()));
    }
    private static Obj receipt() {
        return object(parse(("{\"action_request_id\":\"original-request\",\"episode_run_id\":\"episode\",\"actor_character_id\":1,\"pre_native_revision\":2,\"pre_date_raw\":100,\"pre_proof_epoch\":5,\"source_bridge_pid\":42,\"source_bridge_creation_date\":\"old-process\",\"status\":\"applied\",\"postcondition_verified\":true,\"completion_status\":\"in_progress\",\"post_native_revision\":3,\"post_date_raw\":100,\"post_proof_epoch\":6,\"post_bridge_pid\":42,\"post_bridge_creation_date\":\"old-process\",\"completion_last_check_date_raw\":100,\"candidate\":{\"barony_title_id\":2,\"province_id\":3,\"building_type_id\":11,\"slot_index\":0,\"gold_before_raw\":100,\"stock_gold_cost_raw\":25}}").getBytes(StandardCharsets.UTF_8)), "original software receipt");
    }
    private static Obj tuple() { return obj("barony_title_id", n(2), "province_id", n(3), "building_type_id", n(11), "slot_index", n(0)); }
    private static Obj query() {
        Obj snapshot = obj("snapshot_id", new Text("native:3"), "revision", n(3), "native_revision", n(3), "date_raw", n(820), "episode_run_id", new Text("episode"),
                "paused", new Bool(true), "map_ready", new Bool(true), "active_event", Nil.INSTANCE, "pending_character_interaction", Nil.INSTANCE,
                "played_character", obj("character_id", n(1), "alive", new Bool(true)), "active_wars", new Arr(List.of()), "player_armies", new Arr(List.of()),
                "diagnostics", obj("bridge_pid", n(80), "bridge_creation_date", new Text("new-process"), "hello", obj("expected_ck3_version", new Text("1.20.0.4"),
                        "expected_ck3_sha256", new Text("98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"))));
        Obj idle = obj("barony_title_id", n(2), "province_id", n(3), "active", new Bool(false),
                "native_province_monthly_income_observed", new Bool(false), "native_province_monthly_income_raw", Nil.INSTANCE);
        Obj world = obj("status", new Text("source_available"), "snapshot_revision", n(3), "date_raw", n(820), "player_character_id", n(1),
                "native_final_legality_evaluated", new Bool(true), "native_cost_evaluated", new Bool(false), "player_gold_raw", n(75),
                "active_constructions", new Arr(List.of(idle)), "completed_buildings_observed", new Bool(true),
                "completed_buildings", new Arr(List.of(tuple())), "positive_income_coverage_complete", new Bool(true), "legal_samples", new Arr(List.of()));
        Obj probe = obj("advertised", new Bool(false), "snapshot_revision", n(3), "date_raw", n(820), "proof_epoch", n(2), "player_world_building_sources", world);
        Obj envelope = obj("type", new Text("command_result"), "protocol_version", n(1), "request_id", new Text("current-material-read"), "ok", new Bool(true),
                "result", obj("step", new Text("g2_player_construction_view_probe_v1"), "accepted", new Bool(true), "private_probe", probe));
        return obj("schema", new Text("xar.construction-query-observation-input.v1"), "starting_snapshot", snapshot, "ending_snapshot", snapshot,
                "native_envelope", envelope, "expected_revision", n(3), "native_query_request_id", new Text("current-material-read"), "material_receipt", new Bool(true), "wartime_observation", new Bool(false));
    }
    private static PlanningRequest materialRequest(ExactRef sourceRef, Obj snapshot) {
        var source = new org.xar.ck3.control.g2.common.G2Source(Fixture.MACHINE, "2026-10-26T00:00:00Z", "1.20.0.4", sourceRef);
        var game = new org.xar.ck3.control.contracts.GameGeneration(99,
                new org.xar.ck3.control.contracts.PythonOnlyUInt64(new BigInteger("133000000000000099")));
        var frame = new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(Fixture.MACHINE, game,
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                        new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.valueOf(3), BigInteger.valueOf(820)),
                        "native:3", BigInteger.valueOf(77), "episode"), 1);
        return new PlanningRequest(frame, source, "material-root-software-session", java.time.Instant.now().plusSeconds(120),
                new org.xar.ck3.control.application.planning.PlanningObservation(snapshot, List.of(), java.util.Set.of(), java.util.Set.of(),
                        Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false));
    }
    /** Existing pinned baseline fixture is expanded into explicit full-build software native packets, never live proof. */
    private static Obj materialRoot(PlanningRequest request, Optional<BigInteger> observedIncome) throws IOException {
        Obj original;
        try (var input = ConstructionLargeMaterialProductionTest.class.getResourceAsStream("/org/xar/ck3/control/application/driver/campaign-root-native-v1-fixture.json")) {
            if (input == null) throw new IOException("required original campaign-root fixture is missing; not skipped");
            byte[] raw = input.readNBytes(1782);
            if (raw.length != 1781 || !ActionCodec.sha256(raw).equals("c280918ca751f6eee63022b2b0815d64a8b266bd10711016248f48fe86938b86"))
                throw new IOException("required original campaign-root fixture changed");
            original = object(parse(raw), "original ROOT fixture");
        }
        Obj baseline = object(original.get("campaign_root_context"), "original baseline ROOT");
        var fields = new java.util.LinkedHashMap<>(baseline.members()); fields.remove("player_heir_candidate_v1");
        var positions = new java.util.ArrayList<Value>();
        for (String key : List.of("councillor_chancellor", "councillor_court_chaplain", "councillor_marshal", "councillor_spymaster", "councillor_steward"))
            positions.add(obj("position_key", new Text(key), "incumbent_character_id", Nil.INSTANCE, "task_key", Nil.INSTANCE,
                    "task_type", Nil.INSTANCE, "target", Nil.INSTANCE, "frozen", Nil.INSTANCE, "progress", Nil.INSTANCE));
        Obj council = obj("status", new Text("available"), "coverage_key", new Text("standard_landed_non_nomadic_core_v1"),
                "owner_character_id", n(1), "positions", new Arr(positions), "unavailable_reason", Nil.INSTANCE, "auxiliary_vacancies_complete", new Bool(false));
        var readiness = new java.util.LinkedHashMap<String, Value>();
        for (String key : List.of("adjacent_external_province_holders_ready", "capital_ready", "council_ready", "direct_landed_vassals_ready",
                "government_ready", "held_title_partition_ready", "lieges_ready", "player_domain_ready", "player_health_ready",
                "player_identity_ready", "player_monthly_gold_income_ready", "player_targeting_factions_ready", "primary_title_ready",
                "primary_title_succession_ready", "ready", "related_character_contexts_ready", "same_frame_ready", "selected_game_rule_tokens_ready"))
            readiness.put(key, new Bool(observedIncome.isPresent()));
        Obj provenance = object(baseline.get("provenance"), "baseline build provenance")
                .with("monthly_gold_income_rva", new Text("0x2BCA940")).with("character_health_rva", new Text("0x28C64E0"))
                .with("domain_size_rva", new Text("0x28B71E0")).with("domain_limit_rva", new Text("0x28B71B0"))
                .with("has_targeting_faction_trigger_rva", new Text("0x2B250B0")).with("council_position_lookup_rva", new Text("0x2684EE0"))
                .with("council_active_task_ids_enumerator_rva", new Text("0x2916CC0")).with("council_active_task_storage_slot_rva", new Text("0x5D1DEA0"))
                .with("council_value_progress_current_rva", new Text("0x31AB500")).with("council_value_progress_maximum_rva", new Text("0x31AB820"))
                .with("held_title_ids_offset", new Text("0x1E0")).with("title_province_rva", new Text("0x230F8E0"))
                .with("province_holder_character_id_rva", new Text("0x247D010"));
        var f = request.before().frame().identity();
        Obj root = new Obj(fields).with("snapshot_revision", new IntegerValue(f.nativeRevision())).with("date_raw", new IntegerValue(f.dateRaw()))
                .with("player_character_id", new IntegerValue(f.player())).with("top_liege_character_id", new IntegerValue(f.player()))
                .with("player_monthly_gold_income", obj("raw", new IntegerValue(observedIncome.orElse(BigInteger.ZERO)), "scale", n(100000)))
                .with("player_health", obj("raw", n(275000), "scale", n(100000))).with("player_domain_size", n(1)).with("player_domain_limit", n(7))
                .with("player_targeting_faction_count", n(0)).with("council", council).with("primary_title_succession_character_ids", new Arr(List.of()))
                .with("held_title_partition", new Arr(List.of(obj("title", baseline.get("primary_title"), "first_heir_character_id", Nil.INSTANCE,
                        "capital_province_id", baseline.get("capital_province_id"), "primary", new Bool(true)))))
                .with("direct_landed_vassal_character_ids", new Arr(List.of())).with("adjacent_external_province_holder_character_ids", new Arr(List.of()))
                .with("related_character_contexts", new Arr(List.of())).with("readiness", new Obj(readiness)).with("provenance", provenance);
        if (observedIncome.isEmpty()) {
            root = root.with("status", new Text("unavailable")).with("unavailable_reason", new Text("player_monthly_gold_income_unavailable"));
            for (String key : List.of("capital_province_id", "council", "government", "immediate_liege_character_id", "independent", "local_player_id",
                    "player_character_alive", "player_character_id", "player_domain_limit", "player_domain_size", "player_health",
                    "player_monthly_gold_income", "player_targeting_faction_count", "primary_title", "top_liege_character_id"))
                root = root.with(key, Nil.INSTANCE);
            root = root.with("held_title_partition", new Arr(List.of()));
        }
        return original.with("status", root.get("status")).with("query_sequence", n(1)).with("snapshot_revision", new IntegerValue(f.nativeRevision()))
                .with("campaign_root_context", root);
    }
    private static ExactRef reference(Path path) throws IOException { byte[] bytes = Files.readAllBytes(path); return new ExactRef(path.toAbsolutePath().toString(), bytes.length, ActionCodec.sha256(bytes)); }
    private static IntegerValue n(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
}
