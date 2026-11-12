package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.driver.DriverFactsRepository;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Two distinct strict Driver originals in an actual writer/archive scope; no Game or action permission is manufactured. */
final class OwnedHistoryRows68ScopeDataTest {
    private static final String MACHINE = "driver-complete333";
    private static final Instant NOW = Instant.parse("2026-11-02T00:00:00Z");
    private static final ActionPorts.HistoricalReadLimits LIMITS = new ActionPorts.HistoricalReadLimits(8, 4L * 1024 * 1024, 32);
    @TempDir Path temp;
    private final List<StorageWriteGuardTestSupport> storageScopes = new ArrayList<>();

    @AfterEach void closeStorage() throws IOException {
        IOException failure = null;
        for (var storage : storageScopes) try { storage.close(); }
        catch (IOException problem) { if (failure == null) failure = problem; else failure.addSuppressed(problem); }
        storageScopes.clear();
        if (failure != null) throw failure;
    }

    private final class Fixture {
        final DriverFrameEvidenceLoader loader = new DriverFrameEvidenceLoader(new DriverObservationAssembler(), true);
        final Layout layout;
        final ExactRef source;
        final ContinuityWriter writer;
        final NativeOutcomeArchive archive;
        Fixture(String name) throws IOException {
            Path root = Files.createDirectory(temp.resolve(name));
            byte[] state = ContinuityJson.canonical(state());
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("anchor.json"), state, StandardOpenOption.CREATE_NEW);
            Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"), new byte[0], StandardOpenOption.CREATE_NEW);
            Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
            Files.createDirectory(root.resolve("artifacts"));
            Files.writeString(root.resolve("source.txt"), "finite software source320", StandardOpenOption.CREATE_NEW);
            source = LedgerFiles.read(root.resolve("source.txt"), 1024).pin().reference();
            layout = new Layout(root.resolve("ROOT-CONTINUITY-WINDOW.json"),
                    LedgerFiles.read(root.resolve("anchor.json"), 65536).pin().reference(), MACHINE);
            var storage = StorageWriteGuardTestSupport.create(layout);
            storageScopes.add(storage);
            var store = new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"), layout.lock(), 8 * 1024 * 1024), storage);
            writer = new ContinuityWriter(layout, List.of(source), new TransitionAuthority() {
                @Override public String revalidate(ContinuityState before, Request request) { return ContinuityJson.digest(request.detailsObject()); }
                @Override public ContinuityState reduce(ContinuityState before, Request request) { throw new IllegalStateException("no fixture ledger commits"); }
            }, Clock.fixed(NOW, ZoneOffset.UTC), new ContinuityWriter.Extensions(List.of(), Optional.of(store), Optional.empty()), storage);
            archive = new NativeOutcomeArchive(store, writer, loader);
        }
    }
    private static ObjectNode state() {
        ObjectNode row = StrictJson.object(); row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 0); row.put("window_id", 1); row.put("status", "running"); row.put("target_days", 10958);
        row.put("target_years", 30); row.put("calendar_year_days", 365.25); row.put("start_date_raw", 1000); row.put("target_date_raw", 263992);
        row.put("last_settled_date_raw", 1000); row.put("last_settled_cycles", 1); row.put("manual_repair_count", 1);
        row.put("automatic_recovery_count", 0); row.put("binding_lineage_count", 0);
        row.putObject("game_binding").put("pid", 123).put("creation_date", "2026-10-23T01:00:00Z"); row.putNull("latest_binding");
        row.putObject("pending_cycle").put("stage", "auto_unsettled").put("auto_sequence", 11558); row.put("NEXT", 11559); return row;
    }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }


    private static byte[] driverRows(String goal,String... historyRows) {
        return bytes("{\"format_version\":2,\"pipe_name\":\"software333\",\"bridge_pid\":123,"
                + "\"episode_character_id\":73,\"episode_run_id\":\"episode333\",\"last_checkpoint\":null,"
                + "\"command_history\":["+String.join(",",historyRows)+"],\"rollback_war_failure\":null,"
                + "\"managed_restore_transaction\":null,\"succession_expectation\":null,\"succession_lifecycle\":null,"
                + "\"campaign_goal\":{\"name\":\""+goal+"\"},\"rollback_war_failures\":null}");
    }
    private static final String SHARED = "{\"index\":1,\"opaque\":{\"n\":1.00E+2,\"large\":18446744073709551617,\"text\":\"shared\"}}";
    private static final String OLD_SECOND = "{\"index\":2,\"opaque\":{\"text\":\"before\",\"n\":2.50}}";
    private static final String NEW_SECOND = "{\"index\":2,\"opaque\":{\"text\":\"after\",\"n\":2.50}}";

    private static final String NATIVE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
         "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{},"original_metric":1.00}
        """;

    private record Originals(RawJson driver, RawJson manifest, ExactRef manifestRef, byte[] packet,
            ExactRef nativeRef, ExactRef driverRef, NativeEffectEvidence.FrameBasis basis) { }
    private Originals originals(Fixture f,long version,byte[] completeRaw) {
        int nativeActor=73;
        byte[] raw = DriverStateSnapshot.decodeComplete(completeRaw).encode();
        var material = RawJson.fullMaterial(raw); ExactRef driverRef = f.archive.preserveMaterial(material);
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var known = DriverFactsRepository.imported(driverRef, raw, 3, 7, game, new OpportunityJson.Obj(Map.of()));
        String nativeState=NATIVE.strip().replace("\"character_id\":73","\"character_id\":"+nativeActor);
        byte[] packetJson = bytes("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"snapshot333\",\"revision\":9,\"state\":" + nativeState + "}");
        byte[] packet = ByteBuffer.allocate(packetJson.length + 4).order(ByteOrder.LITTLE_ENDIAN).putInt(packetJson.length).put(packetJson).array();
        var actual = new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession(MACHINE, game, BigInteger.valueOf(5), "session333"),
                "snapshot333", BigInteger.valueOf(9), new RawJson(bytes(nativeState)), packet, NOW);
        ExactRef nativeRef = f.archive.preserveNativeFrame(actual);
        var source = new G2Source(MACHINE, NOW.toString(), "source333", f.source);
        var extras=version==DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION
                ? new OpportunityJson.Obj(Map.of("episode_projection",new OpportunityJson.Text("native_campaign"))) : new OpportunityJson.Obj(Map.of());
        var manifest = DriverObservationEvidenceReader.encode(known, actual, BigInteger.TWO, version, source, extras, driverRef);
        ExactRef manifestRef = f.archive.preserveMaterial(manifest);
        return new Originals(material, manifest, manifestRef, packet, nativeRef, driverRef, new NativeEffectEvidence.FrameBasis(nativeRef, manifestRef));
    }


    @Test void twoDifferentArchivedDriversReuseOnlyExactOwnedRowsAndKeepAllFullOutputsAndOriginalReads() throws IOException {
        for(long profile:new long[]{1,DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION}) {
            var f=new Fixture("two-drivers-"+profile);
            var a=originals(f,profile,driverRows("goal-a",SHARED,OLD_SECOND));
            var b=originals(f,profile,driverRows("goal-b",SHARED,NEW_SECOND));
            assertNotEquals(a.driverRef(),b.driverRef());
            assertFalse(java.util.Arrays.equals(a.driver().bytes(),b.driver().bytes()));
            f.writer.locked(session->f.archive.inSession(session,bound->{
                var callbacks=new ArrayList<String>();
                var observed=recordCallbacks(bound,callbacks);
                var first=f.loader.loadFull(a.basis(),observed);
                assertEquals(expectedCallbacks(a),callbacks);
                assertPublicOracle(first);
                var firstRows=history(first);
                callbacks.clear();
                var second=f.loader.loadFull(b.basis(),observed);
                assertEquals(expectedCallbacks(b),callbacks,"each different Driver still reopens its complete original triple");
                assertPublicOracle(second);
                assertNotSame(first.facts().driver(),second.facts().driver());
                assertNotEquals(first.facts().driver(),second.facts().driver());
                var secondRows=history(second);
                assertEquals(2,firstRows.size());assertEquals(2,secondRows.size());
                assertEquals(firstRows.getFirst(),secondRows.getFirst());
                assertSame(firstRows.getFirst(),secondRows.getFirst(),"exact row bytes can share only immutable owned projection DATA");
                assertNotEquals(firstRows.get(1),secondRows.get(1));
                assertNotSame(firstRows.get(1),secondRows.get(1),"a changed row cannot borrow the preceding decoded value");
                var projected=f.loader.projectOwnedHistoryRows(second.facts().driver());
                assertEquals(secondRows,projected);assertSame(secondRows.getFirst(),projected.getFirst());
                assertThrows(UnsupportedOperationException.class,secondRows::clear);
                assertThrows(UnsupportedOperationException.class,()->((OpportunityJson.Obj)secondRows.getFirst()).members().clear());
                byte[] callerCopy=second.facts().driver().commandHistory().getFirst().originalRow().json();callerCopy[0]='[';
                assertSame(firstRows.getFirst(),f.loader.projectOwnedHistoryRows(second.facts().driver()).getFirst());
                assertPublicOracle(second);
                callbacks.clear();
                var ordinary=f.loader.load(b.basis(),observed);
                assertEquals(expectedCallbacks(b),callbacks);
                assertEquals(second.semantic(),ordinary.semantic());
                assertEquals(second.fullBindingSha256(),ordinary.fullBindingSha256());
                assertSame(secondRows.getFirst(),OpportunityJson.array(ordinary.semantic().get("native_command_history"),"actual ordinary history").getFirst());
                return null;
            }));
        }
    }

    @Test void equalArrayHashNeverSubstitutesDifferentFullRowBytesAcrossThreeStrictDrivers() throws IOException {
        var f=new Fixture("row-collision");
        String aa="{\"index\":1,\"text\":\"Aa\",\"n\":1.00}";
        String bb="{\"index\":1,\"text\":\"BB\",\"n\":1.00}";
        var a=originals(f,1,driverRows("collision-a",aa));
        var b=originals(f,1,driverRows("collision-b",bb));
        var again=originals(f,1,driverRows("collision-c",aa));
        var rawA=DriverStateSnapshot.decodeComplete(a.driver().bytes()).commandHistory().getFirst().originalRow().json();
        var rawB=DriverStateSnapshot.decodeComplete(b.driver().bytes()).commandHistory().getFirst().originalRow().json();
        assertFalse(java.util.Arrays.equals(rawA,rawB));
        assertEquals(java.util.Arrays.hashCode(rawA),java.util.Arrays.hashCode(rawB),"input property only, never a cache-algorithm oracle");
        f.writer.locked(session->f.archive.inSession(session,bound->{
            var first=f.loader.loadFull(a.basis(),bound);var firstRow=history(first).getFirst();assertPublicOracle(first);
            var second=f.loader.loadFull(b.basis(),bound);var secondRow=history(second).getFirst();assertPublicOracle(second);
            assertNotSame(first.facts().driver(),second.facts().driver());
            assertNotSame(firstRow,secondRow);assertNotEquals(firstRow,secondRow);
            assertEquals(new OpportunityJson.Text("Aa"),((OpportunityJson.Obj)firstRow).get("text"));
            assertEquals(new OpportunityJson.Text("BB"),((OpportunityJson.Obj)secondRow).get("text"));
            var third=f.loader.loadFull(again.basis(),bound);assertPublicOracle(third);
            assertNotSame(first.facts().driver(),third.facts().driver());
            assertEquals(firstRow,history(third).getFirst(),"exact Aa bytes remain correct even after single-slot collision replacement");
            assertNotEquals(secondRow,history(third).getFirst());
            return null;
        }));
    }

    @Test void publicCompleteWrongOwnerOldSessionOtherThreadAndOuterScopeCannotBorrowOwnedRowObjects() throws IOException {
        var f=new Fixture("row-scope");var original=originals(f,1,driverRows("scope-a",SHARED,OLD_SECOND));
        var stale=new AtomicReference<ContinuityStorePort.Session>();
        f.writer.locked(session->{stale.set(session);return null;});
        var escapedDriver=new AtomicReference<DriverStateSnapshot.Complete>();
        var escapedRow=new AtomicReference<OpportunityJson.Value>();
        f.writer.locked(session->f.archive.inSession(session,bound->{
            var full=f.loader.loadFull(original.basis(),bound);var driver=full.facts().driver();var rows=history(full);
            escapedDriver.set(driver);escapedRow.set(rows.getFirst());
            assertSame(rows.getFirst(),bound.inSession(session,nested->f.loader.projectOwnedHistoryRows(driver).getFirst()));
            var external=DriverStateSnapshot.decodeComplete(original.driver().bytes());
            assertEquals(driver,external);assertNotSame(driver,external);
            var externalRows=f.loader.projectOwnedHistoryRows(external);
            assertEquals(rows,externalRows);assertNotSame(rows.getFirst(),externalRows.getFirst());
            var publicCopy=new DriverStateSnapshot.Complete(driver.session(),driver.commandHistory(),driver.lastCheckpoint(),
                    driver.rollbackWarFailure(),driver.managedRestoreTransaction(),driver.successionExpectation(),
                    driver.successionLifecycle(),driver.campaignGoal(),driver.rollbackWarFailures());
            assertEquals(driver,publicCopy);assertNotSame(driver,publicCopy);
            var copiedRows=f.loader.projectOwnedHistoryRows(publicCopy);
            assertEquals(rows,copiedRows);assertNotSame(rows.getFirst(),copiedRows.getFirst());
            var threadRows=new AtomicReference<List<OpportunityJson.Value>>();var threadFailure=new AtomicReference<Throwable>();
            var thread=new Thread(()->{try{threadRows.set(f.loader.projectOwnedHistoryRows(driver));}catch(Throwable failure){threadFailure.set(failure);}});
            thread.start();try{thread.join(5000);}catch(InterruptedException failure){Thread.currentThread().interrupt();throw new AssertionError(failure);}
            assertFalse(thread.isAlive());assertNull(threadFailure.get());
            assertEquals(rows,threadRows.get());assertNotSame(rows.getFirst(),threadRows.get().getFirst());
            assertThrows(IllegalStateException.class,()->f.loader.inCompleteDriverDecodeScope(new Object(),session,bound,ignored->null));
            assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class,
                    ()->f.loader.inCompleteDriverDecodeScope(f.archive,stale.get(),bound,ignored->null));
            return null;
        }));
        var outside=f.loader.projectOwnedHistoryRows(escapedDriver.get());
        assertEquals(escapedRow.get(),outside.getFirst());assertNotSame(escapedRow.get(),outside.getFirst());
        f.writer.locked(session->f.archive.inSession(session,bound->{
            var full=f.loader.loadFull(original.basis(),bound);assertPublicOracle(full);
            assertNotSame(escapedDriver.get(),full.facts().driver());assertNotSame(escapedRow.get(),history(full).getFirst());
            return null;
        }));
    }

    @Test void strictDecodeFailureExplicitDiscardAndExceptionalScopeExitCannotLendEarlierRowData() throws IOException {
        var f=new Fixture("row-failures");
        var a=originals(f,1,driverRows("failure-a",SHARED,OLD_SECOND));
        var b=originals(f,1,driverRows("failure-b",SHARED,NEW_SECOND));
        var beforeExit=new AtomicReference<OpportunityJson.Value>();
        f.writer.locked(session->{
            var marker=new IOException("original scoped archive callback failed");var wrapper=new UncheckedIOException(marker);
            var actual=assertThrows(UncheckedIOException.class,()->f.archive.inSession(session,bound->{
                var first=f.loader.loadFull(a.basis(),bound);var old=history(first).getFirst();assertPublicOracle(first);
                assertThrows(IllegalArgumentException.class,()->f.loader.decodeCompleteDriverBytes(bytes("{}")));
                var afterFailure=f.loader.loadFull(b.basis(),bound);assertPublicOracle(afterFailure);
                assertNotSame(old,history(afterFailure).getFirst());
                var previous=history(afterFailure).getFirst();
                f.loader.discardHistoryProjection();
                var discarded=f.loader.projectOwnedHistoryRows(afterFailure.facts().driver());
                assertEquals(history(afterFailure),discarded);assertNotSame(previous,discarded.getFirst());
                beforeExit.set(discarded.getFirst());
                throw wrapper;
            }));
            assertSame(wrapper,actual);assertSame(marker,actual.getCause());
            f.archive.inSession(session,bound->{
                var next=f.loader.loadFull(a.basis(),bound);assertPublicOracle(next);
                assertEquals(beforeExit.get(),history(next).getFirst());assertNotSame(beforeExit.get(),history(next).getFirst());
                return null;
            });
            return null;
        });
    }

    private static ActionPorts.OutcomeArchive recordCallbacks(ActionPorts.OutcomeArchive original,List<String> calls) {
        return (ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
                    if(method.getName().equals("loadFullMaterial"))calls.add("material:"+((ExactRef)args[0]).sha256());
                    if(method.getName().equals("loadNativeFrame"))calls.add("native:"+((ExactRef)args[0]).sha256());
                    try{return method.invoke(original,args);}catch(java.lang.reflect.InvocationTargetException failure){throw failure.getCause();}
                });
    }
    private static List<String> expectedCallbacks(Originals original) {
        return List.of("material:"+original.manifestRef().sha256(),"native:"+original.nativeRef().sha256(),"material:"+original.driverRef().sha256());
    }
    private static void assertPublicOracle(DriverObservationAssembler.FullSnapshot actual) {
        var expected=new DriverObservationAssembler().projectFull(actual.actual(),actual.facts(),actual.originalEvidence());
        assertFull(expected,actual);
        assertArrayEquals(DriverJson.encode(expected.semantic()),DriverJson.encode(actual.semantic()));
        assertEquals(expected.semantic().members().keySet().stream().toList(),actual.semantic().members().keySet().stream().toList());
    }
    private static List<OpportunityJson.Value> history(DriverObservationAssembler.FullSnapshot value) {
        return OpportunityJson.array(value.semantic().get("native_command_history"),"actual complete native command history");
    }
    private static void assertFull(DriverObservationAssembler.FullSnapshot expected,DriverObservationAssembler.FullSnapshot actual) {
        assertEquals(expected.facts(),actual.facts());assertEquals(expected.semantic(),actual.semantic());
        assertEquals(expected.originalEvidence(),actual.originalEvidence());assertEquals(expected.fullBindingSha256(),actual.fullBindingSha256());
        assertEquals(expected.actual().session(),actual.actual().session());assertEquals(expected.actual().snapshotId(),actual.actual().snapshotId());
        assertEquals(expected.actual().nativeRevision(),actual.actual().nativeRevision());assertArrayEquals(expected.actual().state().bytes(),actual.actual().state().bytes());
        assertEquals(expected.actual().observedAt(),actual.actual().observedAt());assertArrayEquals(expected.actual().originalPacket(),actual.actual().originalPacket());
    }
}
