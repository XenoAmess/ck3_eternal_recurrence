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

/** Actual writer/archive owned Driver scope; immutable projection DATA is never an authority. */
final class OwnedHistoryProjection62Test {
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


    private static final String DRIVER = """
        {"format_version":2,"pipe_name":"software333","bridge_pid":123,"episode_character_id":73,"episode_run_id":"episode333",
         "last_checkpoint":null,"command_history":[{"index":1,"opaque":{"n":1.00E+2,"large":18446744073709551617}}],
         "rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
         "succession_lifecycle":null,"campaign_goal":{"name":"goal333"},"rollback_war_failures":null}
        """;
    private static byte[] driver(int revision) { return bytes(DRIVER.replace("goal333", "goal333-" + revision)); }
    private static final String NATIVE = """
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
         "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
         "active_wars":[],"player_armies":[],"diagnostics":{},"original_metric":1.00}
        """;

    private record Originals(RawJson driver, RawJson manifest, ExactRef manifestRef, byte[] packet,
            ExactRef nativeRef, NativeEffectEvidence.FrameBasis basis) { }
    private Originals originals(Fixture f,long version) { return originals(f,version,73); }
    private Originals originals(Fixture f,long version,int nativeActor) {
        byte[] raw = DriverStateSnapshot.decodeComplete(driver(0)).encode();
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
        return new Originals(material, manifest, manifestRef, packet, nativeRef, new NativeEffectEvidence.FrameBasis(nativeRef, manifestRef));
    }


    @Test void actualArchiveLoadsAndPublicReplayReuseOnlyOwnedRowsWhileEveryOriginalIsReopened() throws IOException {
        var f=new Fixture("owned-rows");var original=originals(f,1);
        f.writer.locked(session->f.archive.inSession(session,bound->{
            var materialLoads=new AtomicInteger();var nativeLoads=new AtomicInteger();
            var counted=(ActionPorts.OutcomeArchive)Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
                        if(method.getName().equals("loadFullMaterial"))materialLoads.incrementAndGet();
                        if(method.getName().equals("loadNativeFrame"))nativeLoads.incrementAndGet();
                        try{return method.invoke(bound,args);}catch(java.lang.reflect.InvocationTargetException failure){throw failure.getCause();}
                    });
            var first=f.loader.loadFull(original.basis(),counted);
            var rows=f.loader.projectOwnedHistoryRows(first.facts().driver());
            assertSame(rows.getFirst(),history(first).getFirst());
            var second=f.loader.loadFull(original.basis(),counted);
            assertFull(first,second);assertSame(first.facts().driver(),second.facts().driver());
            assertSame(rows,f.loader.projectOwnedHistoryRows(second.facts().driver()));
            assertSame(rows.getFirst(),history(second).getFirst());
            var ordinary=f.loader.load(original.basis(),counted);
            assertEquals(first.semantic(),ordinary.semantic());assertEquals(first.fullBindingSha256(),ordinary.fullBindingSha256());
            assertSame(rows.getFirst(),OpportunityJson.array(ordinary.semantic().get("native_command_history"),"actual ordinary history").getFirst());
            assertEquals(6,materialLoads.get());assertEquals(3,nativeLoads.get());
            var replay=assertInstanceOf(DriverObservationAssembler.Complete.class,f.loader.replayCompleteOriginals(
                    original.manifestRef(),original.manifest(),original.driver(),original.packet(),original.nativeRef()));
            assertEquals(first.semantic(),replay.semantic());assertEquals(first.fullBindingSha256(),replay.fullBindingSha256());
            assertSame(rows.getFirst(),OpportunityJson.array(replay.semantic().get("native_command_history"),"actual public replay history").getFirst());
            assertEquals(6,materialLoads.get(),"raw replay consumes its explicit originals and adds no archive callback");assertEquals(3,nativeLoads.get());
            assertThrows(UnsupportedOperationException.class,rows::clear);
            byte[] returned=first.facts().driver().commandHistory().getFirst().originalRow().json();returned[0]='[';
            assertTrue(new String(first.facts().driver().commandHistory().getFirst().originalRow().json(),StandardCharsets.UTF_8).contains("1.00E+2"));
            var repeated=f.loader.loadFull(original.basis(),counted);assertFull(first,repeated);assertSame(rows.getFirst(),history(repeated).getFirst());
            assertEquals(8,materialLoads.get());assertEquals(4,nativeLoads.get());
            byte[] changed=original.driver().bytes();changed[0]='[';
            try { Files.write(Path.of(DriverObservationEvidenceReader.currentDriverReference(original.manifestRef(),original.manifest()).path()),changed); }
            catch(IOException failure) { throw new UncheckedIOException(failure); }
            assertThrows(UncheckedIOException.class,()->f.loader.loadFull(original.basis(),counted));
            return null;
        }));
    }

    @Test void differentOwnedDriverEvictionStrictFailureAndExplicitDiscardCannotBorrowOldRows() throws IOException {
        var f=new Fixture("invalidations");var original=originals(f,1);var mismatchedActor=originals(f,1,74);
        f.writer.locked(session->f.archive.inSession(session,bound->{
            var first=f.loader.loadFull(original.basis(),bound);var firstRows=f.loader.projectOwnedHistoryRows(first.facts().driver());
            var other=f.loader.decodeCompleteDriverBytes(driver(1));var otherRows=f.loader.projectOwnedHistoryRows(other);
            assertEquals(firstRows,otherRows);assertNotSame(firstRows.getFirst(),otherRows.getFirst());
            var returned=f.loader.projectOwnedHistoryRows(first.facts().driver());assertEquals(firstRows,returned);assertNotSame(firstRows.getFirst(),returned.getFirst());
            f.loader.discardHistoryProjection();var discarded=f.loader.projectOwnedHistoryRows(first.facts().driver());
            assertEquals(firstRows,discarded);assertNotSame(returned.getFirst(),discarded.getFirst());
            for(int i=2;i<=5;i++)f.loader.decodeCompleteDriverBytes(driver(i));
            var evicted=f.loader.loadFull(original.basis(),bound);assertFull(first,evicted);assertNotSame(first.facts().driver(),evicted.facts().driver());
            assertNotSame(firstRows.getFirst(),history(evicted).getFirst());
            var beforeFailure=history(evicted).getFirst();
            assertThrows(IllegalArgumentException.class,()->f.loader.decodeCompleteDriverBytes(bytes("{}")));
            var afterFailure=f.loader.loadFull(original.basis(),bound);assertFull(first,afterFailure);
            assertNotSame(evicted.facts().driver(),afterFailure.facts().driver());assertNotSame(beforeFailure,history(afterFailure).getFirst());
            var beforeIncomplete=history(afterFailure).getFirst();
            var incomplete=assertInstanceOf(DriverObservationAssembler.Incomplete.class,f.loader.replayCompleteOriginals(
                    mismatchedActor.manifestRef(),mismatchedActor.manifest(),mismatchedActor.driver(),mismatchedActor.packet(),mismatchedActor.nativeRef()));
            assertTrue(incomplete.reasons().getFirst().contains("unreconciled played-character/episode transition"));
            var afterIncomplete=f.loader.loadFull(original.basis(),bound);assertFull(first,afterIncomplete);
            assertNotSame(beforeIncomplete,history(afterIncomplete).getFirst(),"an actual Incomplete result clears the nominal projection memo");
            return null;
        }));
    }

    @Test void nestedSameSessionReusesButOtherThreadOuterExitAndNextScopeOnlyReceiveFreshProjectionData() throws IOException {
        var f=new Fixture("scope-boundaries");var original=originals(f,1);
        var escapedDriver=new AtomicReference<DriverStateSnapshot.Complete>();
        var escapedRows=new AtomicReference<List<?>>();
        f.writer.locked(session->f.archive.inSession(session,bound->{
            var full=f.loader.loadFull(original.basis(),bound);escapedDriver.set(full.facts().driver());
            var rows=f.loader.projectOwnedHistoryRows(full.facts().driver());escapedRows.set(rows);
            assertSame(rows,bound.inSession(session,nested->f.loader.projectOwnedHistoryRows(full.facts().driver())));
            var otherRows=new AtomicReference<List<?>>();var failure=new AtomicReference<Throwable>();
            var thread=new Thread(()->{try{otherRows.set(f.loader.projectOwnedHistoryRows(full.facts().driver()));}catch(Throwable problem){failure.set(problem);}});
            thread.start();try{thread.join(5000);}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new AssertionError(interrupted);}
            assertFalse(thread.isAlive());assertNull(failure.get());assertEquals(rows,otherRows.get());
            assertNotSame(rows.getFirst(),otherRows.get().getFirst(),"an external thread can parse DATA but never inherit the original owned memo");
            return null;
        }));
        var outside=f.loader.projectOwnedHistoryRows(escapedDriver.get());assertEquals(escapedRows.get(),outside);
        assertNotSame(escapedRows.get().getFirst(),outside.getFirst());
        f.writer.locked(session->f.archive.inSession(session,bound->{
            var full=f.loader.loadFull(original.basis(),bound);assertNotSame(escapedDriver.get(),full.facts().driver());
            assertEquals(escapedRows.get(),history(full));assertNotSame(escapedRows.get().getFirst(),history(full).getFirst());
            return null;
        }));
        var marker=new IOException("actual outer decode scope failed");var callbackFailure=new UncheckedIOException(marker);var failedRows=new AtomicReference<List<?>>();
        f.writer.locked(session->{
            var actual=assertThrows(UncheckedIOException.class,()->f.archive.inSession(session,bound->{
                var full=f.loader.loadFull(original.basis(),bound);failedRows.set(f.loader.projectOwnedHistoryRows(full.facts().driver()));throw callbackFailure;
            }));
            assertSame(callbackFailure,actual);assertSame(marker,actual.getCause());
            f.archive.inSession(session,bound->{var full=f.loader.loadFull(original.basis(),bound);
                assertEquals(failedRows.get(),history(full));assertNotSame(failedRows.get().getFirst(),history(full).getFirst());return null;});
            return null;
        });
    }

    @Test void publicExternalDriverAndForgedCompleteRemainStrictEvenWhileOwnedMemoIsWarm() throws IOException {
        var f=new Fixture("public-fallback");var original=originals(f,DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION);
        f.writer.locked(session->f.archive.inSession(session,bound->{
            var full=f.loader.loadFull(original.basis(),bound);var rows=f.loader.projectOwnedHistoryRows(full.facts().driver());
            var ordinary=f.loader.load(original.basis(),bound);assertEquals(full.semantic(),ordinary.semantic());
            var strict=new DriverObservationAssembler().projectFull(full.actual(),full.facts(),full.originalEvidence());
            assertFull(full,strict);assertNotSame(rows.getFirst(),history(strict).getFirst(),"public arbitrary facts cannot borrow the nominal owned memo");
            var external=DriverStateSnapshot.decodeComplete(original.driver().bytes());assertNotSame(full.facts().driver(),external);
            var externalRows=f.loader.projectOwnedHistoryRows(external);assertEquals(rows,externalRows);assertNotSame(rows.getFirst(),externalRows.getFirst());
            var forgedSemantic=full.semantic().with("post62_public_forgery",new OpportunityJson.Bool(true));
            var forgedDigest=DriverObservationAssembler.bindingSha256(forgedSemantic);
            var forged=new DriverObservationAssembler.FullSnapshot(full.actual(),full.facts(),forgedSemantic,full.originalEvidence(),forgedDigest);
            assertThrows(IllegalArgumentException.class,()->new DriverObservationAssembler.Complete(ordinary.identity(),ordinary.source(),ordinary.sessionId(),
                    ordinary.connectionGeneration(),forgedSemantic,ordinary.originalEvidence(),ordinary.observedAt(),forgedDigest,Optional.of(forged)));
            var after=f.loader.load(original.basis(),bound);
            assertEquals(ordinary.identity(),after.identity());assertEquals(ordinary.source(),after.source());assertEquals(ordinary.sessionId(),after.sessionId());
            assertEquals(ordinary.connectionGeneration(),after.connectionGeneration());assertEquals(ordinary.semantic(),after.semantic());
            assertEquals(ordinary.originalEvidence(),after.originalEvidence());assertEquals(ordinary.observedAt(),after.observedAt());
            assertEquals(ordinary.fullBindingSha256(),after.fullBindingSha256());
            assertFull(ordinary.originalProjection().orElseThrow(),after.originalProjection().orElseThrow());
            return null;
        }));
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
