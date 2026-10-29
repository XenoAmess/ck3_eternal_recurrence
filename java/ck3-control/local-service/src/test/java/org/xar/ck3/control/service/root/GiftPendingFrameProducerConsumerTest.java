package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.finance.GiftProcessIdentity;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.giftpending.*;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.*;
import org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy.Frame;

/** Finite software packet -> real transport/Driver/full source -> actual private Gift marker -> shared public retry.
 * Exercises the production consumeFresh boundary, not a copied Proof classifier. It grants no live Game/Core qualification. */
final class GiftPendingFrameProducerConsumerTest {
    @TempDir Path temporary;
    private static final String MACHINE="gift-frame-fixture",PIPE="\\\\.\\pipe\\gift-frame-fixture",SESSION="gift-frame-session",SHA="0".repeat(64);
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static BigInteger n(long value){return BigInteger.valueOf(value);}
    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static byte[] packet(String value)throws IOException{return NativeWire.packet(bytes(value));}
    private static String state(long player){return "{\"played_character\":{\"character_id\":"+player+",\"alive\":true},\"paused\":true,\"map_ready\":true,\"speed\":1,\"date_raw\":1000,\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"one_life_terminal\":false,\"succession_reconciliation\":null,\"one_life_settlement\":null,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{\"bridge_pid\":42,\"connection_generation\":5}}";}
    private static final class Packets implements NativePacketPort {
        final ArrayDeque<byte[]> incoming=new ArrayDeque<>();int reads,writes;boolean replaced;
        Packets()throws IOException {
            incoming.add(packet("{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":5,\"bridge_version\":\"gift-frame-fixture\",\"expected_ck3_sha256\":\""+SHA+"\",\"game_adapter_id\":\"gift-frame-fixture\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}"));
            incoming.add(packet("{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":1}"));publish(7,73);
        }
        void publish(int revision,long player)throws IOException{incoming.add(packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"gift-frame-"+revision+"\",\"revision\":"+revision+",\"state\":"+state(player)+"}"));}
        @Override public void awaitConnection(Instant deadline) { }
        @Override public void verify()throws IOException{if(replaced)throw new IOException("actual software process source replaced");}
        @Override public byte[] readPacket(Instant deadline)throws IOException{reads++;if(incoming.isEmpty())throw new IOException("finite original packet queue exhausted");return incoming.removeFirst();}
        @Override public NativePacketPort.WaitResult readPacketUntil(Instant wait,Instant capture)throws IOException {
            verify();return incoming.isEmpty()?new NativePacketPort.Elapsed(wait,Instant.now()):new NativePacketPort.Packet(readPacket(capture));
        }
        @Override public void writePacket(byte[] original,Instant deadline){writes++;throw new AssertionError("Gift pending frame WAIT cannot send any business or receipt-query request");}
        @Override public void close() { }
    }
    private static ExactRef ref(Path path)throws IOException{byte[] raw=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().toString(),raw.length,ActionCodec.sha256(raw));}
    private final class Fixture implements AutoCloseable {
        final Path sourceFile;final ExactRef reviewed;final G2Source source;final Packets packets;
        final NativeGameTransport transport;final ContinuityWriter writer;final NativeOutcomeArchive archive;
        final RootLifecycleAuthority physical;final StorageWriteGuardTestSupport storage;final PendingAction pending;
        final AtomicInteger sourceChecks=new AtomicInteger();
        Fixture(Path root)throws IOException {
            Files.createDirectory(root);sourceFile=root.resolve("source.java");Files.writeString(sourceFile,"finite reviewed Gift source",StandardOpenOption.CREATE_NEW);reviewed=ref(sourceFile);
            Path driverFile=root.resolve("driver.json");var driver=StrictJson.object();driver.put("format_version",2);driver.put("pipe_name",PIPE);driver.put("bridge_pid",42);driver.put("episode_character_id",73);driver.put("episode_run_id","gift-episode");driver.putNull("last_checkpoint");driver.putArray("command_history");
            for(String key:List.of("rollback_war_failure","managed_restore_transaction","succession_expectation","campaign_goal"))driver.putNull(key);
            Files.write(driverFile,StrictJson.canonical(driver,65536),StandardOpenOption.CREATE_NEW);ExactRef driverRef=ref(driverFile);
            var seed=StrictJson.object();seed.put("schema","root.ck3.continuity-window/v1");seed.put("machine_id",MACHINE);seed.put("sequence",0);seed.put("window_id",1);seed.put("status","running");seed.put("target_days",10958);seed.put("target_years",30);seed.put("calendar_year_days",365.25);seed.put("start_date_raw",1000);seed.put("target_date_raw",263992);seed.put("last_settled_date_raw",1000);seed.put("last_settled_cycles",0);seed.put("manual_repair_count",0);seed.put("automatic_recovery_count",0);seed.put("binding_lineage_count",0);var game=seed.putObject("game_binding");game.put("pid",42);game.put("creation_date","2026-10-24T00:00:00Z");seed.putNull("latest_binding");seed.putNull("pending_cycle");seed.put("NEXT",1);seed.set("java_driver_history_baseline",driverRef.toJson());
            byte[] initial=ContinuityJson.canonical(seed);Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");Files.write(snapshot,initial,StandardOpenOption.CREATE_NEW);Files.write(anchor,initial,StandardOpenOption.CREATE_NEW);Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0],StandardOpenOption.CREATE_NEW);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));Files.createDirectory(root.resolve("artifacts"));
            Baseline baseline=new Baseline(n(1),n(99),n(7),n(7),n(1000),n(73),n(100),n(0),n(1),n(1),List.of(n(99)),n(10),n(1));
            Ledger ledger=GiftPendingReducer.begin(Ledger.empty(),new BeginRequest("original-gift-1","gift-episode","R1",GiftProcessIdentity.actual(GAME),baseline,n(10),"a".repeat(64)));
            pending=GiftPendingCodec.decodeLedger(GiftPendingCodec.encodeLedger(ledger)).pending().orElseThrow();
            var registration=new DomainBodies.Registration(DomainBodies.Slot.FACTION,GiftPendingModel.SCHEMA,GiftPendingCodec.MAX_BYTES,List.of(reviewed),(head,previous,request,raw)->{
                assertTrue(previous.isEmpty());assertArrayEquals(GiftPendingCodec.encodeLedger(ledger),raw);assertArrayEquals(bytes("{\"actual_begin\":true}"),request.producerInput());return ActionCodec.sha256(raw);
            });
            var layout=new Layout(snapshot,ref(anchor),MACHINE);storage=StorageWriteGuardTestSupport.create(layout);
            var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"),layout.lock(),8<<20),storage);
            writer=new ContinuityWriter(layout,List.of(reviewed),new TransitionAuthority(){
                @Override public String revalidate(ContinuityState old,Request request){throw new AssertionError("Gift wait cannot write canonical business events");}
                @Override public ContinuityState reduce(ContinuityState old,Request request){throw new AssertionError("Gift wait cannot reduce canonical business events");}
            },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(registration),Optional.of(artifacts),Optional.empty()),storage);
            archive=new NativeOutcomeArchive(artifacts,writer);source=new G2Source(MACHINE,Instant.now().toString(),"software-fixture",reviewed);packets=new Packets();
            transport=NativeGoalObservationFixture.receive(packets,new NativePipeEndpoint.Config(PIPE,MACHINE,GAME,SESSION,"gift-frame-fixture",SHA,"gift-frame-fixture"),32,64);
            var repository=new DriverFactsRepository(DriverFactsRepository.imported(driverRef,Files.readAllBytes(driverFile),1,2,GAME,new OpportunityJson.Obj(Map.of())));
            var journal=new ContinuityActionJournal(writer,archive);var producer=new NativeDriverObservationProducer(repository,transport,source,raw->archive.preserveMaterial(new RawJson(raw)));
            var assembler=new DriverStateAssembler(new ActionSnapshotReader(journal),repository,producer);
            assembler.bindCapabilityObservation((actual,current)->{throw new AssertionError("Gift received-frame source cannot invoke capability/domain observation hooks");});
            physical=new RootLifecycleAuthority(writer,archive,transport,assembler,new DriverObservationAssembler(),source,(same,held,actual,origin,diagnostics,deadline)->{
                writer.requireSession(same);assertEquals(source,actual);assertEquals(held,diagnostics.session().orElseThrow());archive.readArtifact(same,origin,MAX_PIN_BYTES);
                var pin=same.capturePin(reviewed,65536);same.verifyPin(pin);ExactRef proof=archive.preserveArtifact(same,bytes("{\"scope\":\"finite-software-source-no-live-game-grant\"}"),65536);
                return new NativeReadinessCollector.SourceQualification(proof,current->{writer.requireSession(current);assertSame(same,current);current.verifyPin(pin);sourceChecks.incrementAndGet();});
            },Clock.systemUTC(),Duration.ofSeconds(30));
            writer.locked(same->{var body=archive.withSession(same).preserveMaterial(new RawJson(GiftPendingCodec.encodeLedger(ledger)));
                var request=new DomainBodies.ImportRequest(DomainBodies.Slot.FACTION,GiftPendingModel.SCHEMA,body,bytes("{\"actual_begin\":true}"),List.of(reviewed),"actual-software-original-gift-begin");same.commitImport(same.previewImport(request));return null;});
        }
        void requirePending(ContinuityStorePort.Session same,String head)throws IOException {
            writer.requireSession(same);assertEquals(head,same.head().digest());var actual=assertInstanceOf(DomainBodies.Available.class,same.readDomain(DomainBodies.Slot.FACTION));
            assertEquals(pending,GiftPendingCodec.decodeLedger(actual.canonicalBody()).pending().orElseThrow());same.verifyPin(same.capturePin(actual.reference().payload(),GiftPendingCodec.MAX_BYTES));
        }
        @Override public void close()throws IOException{try(storage){transport.close();}}
    }
    private record Captured(PlanningRequest request,Frame source,String head) { }
    private Captured capture(Fixture f)throws IOException {
        return f.writer.locked(same->f.physical.withSnapshot(same,Instant.now().plusSeconds(20),held->{
            var complete=held.ordinary().orElseThrow();var request=new PlanningRequest(complete.identity(),complete.source(),complete.sessionId(),Instant.now().plusSeconds(15),
                    new PlanningObservation(complete.semantic(),List.of(),Set.of(),Set.of("game.state.snapshot"),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
            Frame source=GiftPendingFrameWaitSource.frame(complete.semantic());org.xar.ck3.control.wave2.finance.giftpendingframe.GiftPendingFramePolicy.requireWaitSource(f.pending,source);
            return new Captured(request,source,same.head().digest());
        }));
    }
    @Test void originalPendingAndNativeWaitFullProducerReachThePrivateOneRetryConsumerWithoutAnyCommand()throws Exception {
        try(var f=new Fixture(temporary.resolve("actual-middle"))) {
            Captured captured=capture(f);f.packets.publish(8,73);AtomicInteger plans=new AtomicInteger();AtomicReference<RuntimeException> escaped=new AtomicReference<>();
            RawJson answer=ReadonlyPlanningRetry.plan(()->{
                if(plans.incrementAndGet()>1)return new RawJson(bytes("{\"snapshot_id\":\"fresh-whole-plan\",\"revision\":3}"));
                return f.writer.locked(same->{
                    f.requirePending(same,captured.head());NativeSnapshotWaitPort.WaitResult waited;
                    try{waited=f.transport.waitForSnapshot(Instant.now().plusSeconds(2),captured.request().deadline());}
                    catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                    assertInstanceOf(NativeSnapshotWaitPort.Received.class,waited);int reads=f.packets.reads;
                    return f.physical.withReceivedSnapshot(same,captured.request().deadline(),waited.frame(),fresh->{
                        assertEquals(reads,f.packets.reads,"received-frame qualification cannot consume another Native snapshot");
                        try{GiftPendingFrameWaitSource.consumeFresh(same,captured.request(),f.pending,captured.source(),fresh,()->f.requirePending(same,captured.head()));}
                        catch(RuntimeException actual){escaped.set(actual);throw actual;}
                        throw new AssertionError("real fresh pending frame must leave through its private marker");
                    });
                });
            });
            assertEquals(2,plans.get());assertEquals(0,f.packets.writes);assertTrue(f.sourceChecks.get()>0);
            var result=DriverJson.object(answer.bytes(),RawJson.MAXIMUM_BYTES);var marker=OpportunityJson.object(result.get("readonly_planning_replan_v1"),"actual retry marker");
            assertEquals(new OpportunityJson.IntegerValue(BigInteger.ONE),marker.get("fresh_replans"));
            var rejection=OpportunityJson.object(OpportunityJson.array(marker.get("original_rejections"),"rejections").getFirst(),"actual rejection");
            assertEquals(new OpportunityJson.Text("faction_pending_receipt_paused_frame_ready"),rejection.get("class"));
            assertEquals(new OpportunityJson.Bool(false),rejection.get("receipt_query_sent"));assertEquals(new OpportunityJson.Bool(false),rejection.get("gift_submission_replayed"));
            var failure=assertInstanceOf(GiftPendingFrameReadyFailure.class,escaped.get().getCause());
            assertThrows(IOException.class,failure::requireOriginal,"escaped or already consumed source failure cannot feed another budget");
            f.writer.locked(same->{f.requirePending(same,captured.head());return null;});
        }
    }
    @Test void detachedFreshLeaseAndChangedSourceCannotMintAnyRetry()throws Exception {
        try(var f=new Fixture(temporary.resolve("detached"))) {
            Captured captured=capture(f);f.packets.publish(8,73);AtomicReference<RootLifecycleAuthority.SnapshotLease> old=new AtomicReference<>();
            f.writer.locked(same->f.physical.withSnapshot(same,captured.request().deadline(),held->{old.set(held);return null;}));
            AtomicInteger calls=new AtomicInteger();assertThrows(IllegalArgumentException.class,()->ReadonlyPlanningRetry.plan(()->{
                calls.incrementAndGet();return f.writer.locked(same->{GiftPendingFrameWaitSource.consumeFresh(same,captured.request(),f.pending,captured.source(),old.get(),()->f.requirePending(same,captured.head()));return new RawJson(bytes("{}"));});
            }));assertEquals(1,calls.get());assertEquals(0,f.packets.writes);
        }
        try(var f=new Fixture(temporary.resolve("source-changed"))) {
            Captured captured=capture(f);Files.writeString(f.sourceFile,"changed exact original reviewed source");f.packets.publish(8,73);
            assertThrows(IOException.class,()->f.writer.locked(same->f.physical.withSnapshot(same,captured.request().deadline(),held->null)));assertEquals(0,f.packets.writes);
        }
    }
    @Test void missingForegroundAndBooleanRevisionNeverBecomeACompleteSourceFrame() {
        var valid=DriverJson.object(bytes("{\"revision\":1,\"native_revision\":7,\"date_raw\":1000,\"episode_run_id\":\"gift-episode\",\"played_character\":{\"character_id\":73,\"alive\":true},\"paused\":true,\"map_ready\":true,\"active_event\":null,\"pending_character_interaction\":null,\"diagnostics\":{\"bridge_pid\":42,\"connection_generation\":5}}"),65536);
        var fields=new java.util.LinkedHashMap<>(valid.members());fields.remove("active_event");assertThrows(IllegalArgumentException.class,()->GiftPendingFrameWaitSource.frame(new OpportunityJson.Obj(fields)));
        assertThrows(IllegalArgumentException.class,()->GiftPendingFrameWaitSource.frame(valid.with("native_revision",new OpportunityJson.Bool(true))));
        for(var constructor:GiftPendingFrameReadyFailure.class.getDeclaredConstructors())assertTrue(java.lang.reflect.Modifier.isPrivate(constructor.getModifiers()));
        assertTrue(Arrays.stream(GiftPendingFrameReadyFailure.class.getDeclaredMethods()).noneMatch(method->method.getName().equals("issue")&&java.lang.reflect.Modifier.isPublic(method.getModifiers())));
    }
}
