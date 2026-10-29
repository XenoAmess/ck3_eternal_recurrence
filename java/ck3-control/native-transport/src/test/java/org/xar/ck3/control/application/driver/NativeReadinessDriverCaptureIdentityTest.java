package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.readiness.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.nativebridge.*;

/** Real Collector/Driver producers with memory-only packet and storage edges; no Game or filesystem qualification. */
final class NativeReadinessDriverCaptureIdentityTest {
    private static final String MACHINE="retained-driver-memory", SESSION="retained-driver-session";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String WIRE="""
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
        "last_checkpoint":null,"command_history":[],"rollback_war_failure":null,"managed_restore_transaction":null,
        "succession_expectation":null,"succession_lifecycle":null,"campaign_goal":{"campaign_id":"original","anchor":{"character_id":73}},
        "rollback_war_failures":[]}
        """;
    private static final String STATE="""
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
        "active_event":null,"pending_character_interaction":null,"one_life_terminal":false,"one_life_terminal_reason":null,
        "episode_identity_pending":false,"active_wars":[],"player_armies":[],"diagnostics":{"bridge_pid":42,"connection_generation":5}}
        """;

    @Test void actualAssemblerReadRepackagesSameDriverWithoutInvalidatingItsRetainedPlanningRound() throws Exception {
        try(var f=new Fixture()) { f.round(()->{
            var ready=f.ready();var captured=f.published;
            int nativeReads=f.packets.reads;
            assertInstanceOf(DriverObservationFacts.Known.class,f.driver.read(f.transport.currentSnapshot(f.deadline)));
            var current=f.driver.withFrozenFacts(f.store.session,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
            assertNotSame(captured,current,"real replaceObservation must produce the counterexample wrapper");
            assertEquals(captured.stamp(),current.stamp());assertArrayEquals(captured.driver().encode(),current.driver().encode());
            assertEquals(captured.originalHistoryBasis(),current.originalHistoryBasis());assertEquals(captured.actionRows(),current.actionRows());
            assertEquals(captured.auxiliary(),current.auxiliary());assertEquals(captured.loop(),current.loop());assertEquals(captured.observation(),current.observation());
            String head=f.store.session.head().digest();var calls=new AtomicInteger();
            f.collector.current(f.store.session,ready.request().before(),f.deadline,lease->{
                calls.incrementAndGet();assertSame(captured,lease.driver());assertEquals(ready.request().before(),lease.frame().identity());return null;
            });
            assertEquals(1,calls.get());assertEquals(nativeReads,f.packets.reads,"retained reuse must not receive another packet");
            assertEquals(head,f.store.session.head().digest());assertEquals(0,f.packets.writes);return null;
        }); }
    }

    @Test void actualCapabilityProducerPublicationKeepsTheSameDriverRetainedRound() throws Exception {
        try(var f=new Fixture()) { f.round(()->{
            var ready=f.ready();var captured=f.published;
            var frame=f.collector.current(f.store.session,ready.request().before(),f.deadline,lease->lease.frame());
            int nativeReads=f.packets.reads;String head=f.store.session.head().digest();
            var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
            var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
            var policy=f.material(bytes("{\"schema\":\"test.actual-new-entry-policy\"}"));
            var publication=DriverCapabilityStateProducer.initializeNewEpisode(frame,captured,configuration,presentation,policy,f.archive);
            var current=f.driver.publishCapabilityInputs(f.store.session,publication.expectedStamp(),publication.expectedAuxiliarySha256(),publication);
            assertNotSame(captured,current);assertNotEquals(captured.auxiliary(),current.auxiliary());
            assertEquals(publication.auxiliary(),current.auxiliary());
            assertEquals(captured.stamp(),current.stamp());assertArrayEquals(captured.driver().encode(),current.driver().encode());
            assertEquals(captured.originalHistoryBasis(),current.originalHistoryBasis());assertEquals(captured.actionRows(),current.actionRows());
            assertEquals(captured.loop(),current.loop());assertEquals(captured.observation(),current.observation());
            var calls=new AtomicInteger();
            f.collector.current(f.store.session,ready.request().before(),f.deadline,lease->{
                calls.incrementAndGet();assertSame(captured,lease.driver());assertSame(frame,lease.frame());return null;
            });
            assertEquals(1,calls.get());assertEquals(nativeReads,f.packets.reads);
            assertEquals(head,f.store.session.head().digest());assertEquals(0,f.packets.writes);return null;
        }); }
    }

    @Test void actualDriverCasChangeCannotReuseTheOldCapturedLease() throws Exception {
        try(var f=new Fixture()) { f.round(()->{
            var ready=f.ready();var captured=f.published;
            f.repository.locked(state->{
                var before=(DriverSnapshotFacts.Known)state;
                var changed=DriverStateSnapshot.decodeComplete(bytes(WIRE.replace("\"original\"","\"changed\"")));
                var stamp=new DriverSnapshotFacts.Stamp(before.stamp().driverVersion()+1,before.stamp().episodeEpoch(),GAME,
                        changed.session().episodeRunId(),DriverJson.sha256(changed.encode()));
                f.repository.compareAndSet(before.stamp(),new DriverSnapshotFacts.Known(changed,stamp,before.originalHistoryBasis(),
                        before.actionRows(),before.auxiliary(),before.loop(),Optional.empty()));return null;
            });
            assertNotEquals(captured.stamp(),f.driver.withFrozenFacts(f.store.session,frozen->((DriverSnapshotFacts.Known)frozen.state()).stamp()));
            var calls=new AtomicInteger();assertThrows(IllegalArgumentException.class,()->f.collector.current(f.store.session,
                    ready.request().before(),f.deadline,lease->{calls.incrementAndGet();return null;}));
            assertEquals(0,calls.get());return null;
        }); }
    }

    @Test void changedCanonicalHeadAndForeignBorrowedSessionStillRejectBeforeConsumer() throws Exception {
        try(var f=new Fixture()) { f.round(()->{
            var ready=f.ready();var calls=new AtomicInteger();
            var foreign=new MemoryStore();
            assertThrows(IllegalArgumentException.class,()->f.collector.current(foreign.session,ready.request().before(),f.deadline,
                    lease->{calls.incrementAndGet();return null;}));
            f.store.head=MemoryStore.head(2);
            assertThrows(IllegalArgumentException.class,()->f.collector.current(f.store.session,ready.request().before(),f.deadline,
                    lease->{calls.incrementAndGet();return null;}));
            assertEquals(0,calls.get());return null;
        }); }
    }

    @Test void unknownCanonicalActionCannotBecomeAnOrdinaryRetainedLease() throws Exception {
        try(var f=new Fixture()) { f.round(()->{
            var ready=f.ready();var request=ready.request();
            var expected=new ProposalLifecycle.ExpectedPostcondition(1,request.before(),request.source(),"memory-retained/v1",
                    List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"),true)));
            var command=new ActionCommand("memory-unresolved",request.before(),request.source(),SESSION,new OperationKey("memory-action"),
                    new Obj(Map.of()),expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),f.deadline);
            f.journal.actions=List.of(new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Unknown(Optional.empty(),
                    Optional.empty(),"actual unresolved memory snapshot",List.of(f.material(bytes("unknown original"))))));
            var calls=new AtomicInteger();var failure=assertThrows(IllegalArgumentException.class,()->f.collector.current(f.store.session,
                    request.before(),f.deadline,lease->{calls.incrementAndGet();return null;}));
            assertTrue(failure.getMessage().contains("unresolved actions"));assertEquals(0,calls.get());assertEquals(0,f.packets.writes);return null;
        }); }
    }

    private static byte[] bytes(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static final class Fixture implements AutoCloseable {
        final Instant deadline=Instant.now().plusSeconds(20);
        final MemoryStore store=new MemoryStore();final Packets packets=new Packets();
        final Map<ExactRef,byte[]> originals=new HashMap<>();
        final Archive archive=new Archive(this);
        final DriverFactsRepository repository;final Journal journal;final DriverStateAssembler driver;
        final NativeGameTransport transport;final NativeReadinessCollector collector;
        DriverSnapshotFacts.Known published;
        Fixture()throws IOException {
            var config=new NativePipeEndpoint.Config("\\\\.\\pipe\\pure-retained-driver-memory",MACHINE,GAME,SESSION,"memory","0".repeat(64),"memory");
            transport=NativeTransportReplayTestFactory.create(packets,config,32,16);
            var auxiliary=new Obj(Map.of("capability_session_paths",new Obj(Map.of("queue_dir",Nil.INSTANCE,"driver_state_path",Nil.INSTANCE)),
                    "driver_state_restored",new Bool(false),"driver_state_error",Nil.INSTANCE,"restore_kind",new Text("new_episode"),
                    "episode_binding_state",new Text("active_new"),"cold_candidate_rejection",Nil.INSTANCE,"episode_transition_error",Nil.INSTANCE));
            var known=DriverFactsRepository.imported(material(bytes(WIRE)),bytes(WIRE),3,7,GAME,auxiliary);
            repository=new DriverFactsRepository(known);journal=new Journal(store,known.originalHistoryBasis());
            var source=new G2Source(MACHINE,"2026-10-29T18:00:00Z","retained-memory",material(bytes("memory source")));
            driver=new DriverStateAssembler(new ActionSnapshotReader(journal),repository,actual->repository.locked(state->{
                var current=(DriverSnapshotFacts.Known)state;
                var extra=new Obj(Map.of("backend_id",new Text("native-headless"),"source",new Text("injected-dll-named-pipe"),
                        "diagnostics",DriverJson.object(actual.state().bytes(),65536).get("diagnostics")));
                var full=material(current.driver().encode());
                var manifest=DriverObservationEvidenceReader.encode(current,actual,BigInteger.TWO,1,source,extra,full);
                var original=material(manifest.bytes());
                return new DriverObservationFacts.Known(DriverObservationEvidenceReader.decode(original,manifest,new RawJson(current.driver().encode()),actual));
            }));
            var identity=new SessionPorts.SessionIdentity(MACHINE,GAME,SESSION);
            var verifier=new NativeSemanticEvidenceVerifier((same,reference,maximum)->{store.requireSession(same);return original(reference,maximum);});
            collector=new NativeReadinessCollector(identity,store,transport,driver,new DriverObservationAssembler(),
                    (game,until)->new GameLifecycle.Running(game,source.sourceRef()),
                    (same,role,raw)->{store.requireSession(same);return material(raw);},verifier,
                    (same,owner,frame,current,received,process,until)->NativeReadinessCollector.SourceQualification.none(),
                    (same,frame,current,received,until)->new NativeReadinessCollector.ExecutableCapabilities(Set.of(),Set.of(),Optional.empty()),
                    (same,frame,current,received,until)->new NativeReadinessCollector.PlanningInputs(Set.of(),Set.of(),Optional.empty(),List.of(),
                            Optional.empty(),Optional.empty(),false,Optional.empty()),
                    new NativeReadiness.Policy(false,false,Optional.of(BigInteger.valueOf(73)),Duration.ZERO,false),Duration.ofSeconds(30),Clock.systemUTC());
            collector.bindObservationSession(store::requireSession);
            collector.bindReadyPublication((same,request,frame,current,sources)->{store.requireSession(same);published=current;});
            collector.bindPlanningEvidence((same,request,lease)->{store.requireSession(same);assertEquals(request.before(),lease.frame().identity());});
        }
        SessionPorts.Ready ready()throws IOException,InterruptedException {
            var observation=collector.observe(store.session,new SessionPorts.SessionIdentity(MACHINE,GAME,SESSION),deadline);
            return assertInstanceOf(SessionPorts.Ready.class,observation,()->"actual memory producer: "+observation);
        }
        <T>T round(NativeReadinessCollector.PlanningRoundWork<T> work)throws IOException {
            return store.locked(same->{try{return collector.withPlanningRound(same,work);}catch(InterruptedException failure){
                Thread.currentThread().interrupt();throw new IOException(failure);}});
        }
        ExactRef material(byte[] raw){String sha=DriverJson.sha256(raw);var ref=new ExactRef("D:/test-memory/retained-driver/"+sha+".json",raw.length,sha);originals.putIfAbsent(ref,raw.clone());return ref;}
        byte[] original(ExactRef ref,int maximum){assertTrue(ref.bytes()<=maximum);return originals.get(ref).clone();}
        @Override public void close()throws IOException {transport.close();}
    }

    private static final class MemoryStore implements ContinuityStorePort {
        WriterContracts.Head head=head(1);Thread owner;boolean active;
        final Session session=new Session(){
            @Override public WriterContracts.Head head(){requireSession(this);return head;}
            @Override public void requireWriter(Path lock){throw new AssertionError("no physical writer in memory fixture");}
            @Override public WriterContracts.Pin capturePin(ExactRef ref,int maximum){throw new AssertionError("no physical pin in memory fixture");}
            @Override public void verifyPin(WriterContracts.Pin pin){throw new AssertionError("no physical pin in memory fixture");}
            @Override public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("READ cannot preview");}
            @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("READ cannot commit");}
            @Override public ExactRef persistedHead(){throw new AssertionError("no persisted memory head");}
        };
        static WriterContracts.Head head(int window){
            String raw="{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\""+MACHINE+"\",\"sequence\":0,\"window_id\":"+window
                    +",\"start_date_raw\":53144328,\"target_date_raw\":53144352,\"target_days\":1,\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":53144328}";
            return new WriterContracts.Head(ContinuityState.fromJson(ContinuityJson.parseObject(bytes(raw),65536),MACHINE),List.of(),List.of(),List.of(),false);
        }
        @Override public void requireSession(Session same){StrictJson.require(active&&owner==Thread.currentThread()&&same==session,"actual original memory writer Session required");}
        @Override public <T>T locked(SessionWork<T> work)throws IOException {assertFalse(active);active=true;owner=Thread.currentThread();try{return work.run(session);}finally{active=false;owner=null;}}
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("no preview");}
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("no commit");}
        @Override public ExactRef persistedHead(){throw new AssertionError("no persisted memory head");}
    }
    private static final class Journal implements ActionJournal {
        final MemoryStore store;final ExactRef basis;List<ActionReceipt> actions=List.of();
        Journal(MemoryStore store,ExactRef basis){this.store=store;this.basis=basis;}
        @Override public <T>T locked(Function<LockedJournal,T> work){return locked(store.session,work);}
        @Override public <T>T locked(ContinuityStorePort.Session same,Function<LockedJournal,T> work){
            store.requireSession(same);return work.apply(new LockedJournal(){
                @Override public ContinuityStorePort.Session writerSession(){return same;}
                @Override public Optional<ActionReceipt> find(String id){return actions.stream().filter(row->row.command().actionId().equals(id)).findFirst();}
                @Override public List<ActionReceipt> unresolved(){return actions.stream().filter(row->!row.settled()).toList();}
                @Override public ActionReceipt append(ActionCommand command,String sha,ActionState state){throw new AssertionError("no action write");}
                @Override public Snapshot snapshot(){return new Snapshot(store.head.state().sequence(),store.head.digest(),actions,new BoundHistoryBasis(basis));}
            });
        }
    }
    private static final class Archive implements ActionPorts.OutcomeArchive {
        private final Fixture fixture;
        Archive(Fixture fixture){this.fixture=fixture;}
        @Override public ExactRef preserveMaterial(RawJson raw){return fixture.material(raw.bytes());}
        @Override public RawJson loadMaterial(ExactRef ref){return new RawJson(fixture.original(ref,DriverJson.MAX_NATIVE_BYTES));}
        @Override public ExactRef materialReferenceOf(RawJson raw){var ref=fixture.material(raw.bytes());return ref;}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame actual){return fixture.material(actual.originalPacket());}
        @Override public byte[] loadNativeFrame(ExactRef ref){return fixture.original(ref,DriverJson.MAX_NATIVE_BYTES);}
        private AssertionError unused(){return new AssertionError("capability publication fixture cannot dispatch, act or write a ledger");}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw unused();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){throw unused();}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){throw unused();}
        @Override public ExactRef preserveRequest(NativeRequest value){throw unused();}
        @Override public NativeRequest loadRequest(ExactRef ref){throw unused();}
        @Override public ExactRef requestReferenceOf(NativeRequest value){throw unused();}
        @Override public ExactRef preserveRecord(ActionRecord value){throw unused();}
        @Override public ActionRecord loadRecord(ExactRef ref){throw unused();}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw unused();}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw unused();}
        @Override public ActionReceipt loadReceipt(ExactRef ref){throw unused();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw unused();}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw unused();}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){throw unused();}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){throw unused();}
    }

    private static final class Packets implements NativePacketPort {
        final ArrayDeque<byte[]> queue=new ArrayDeque<>();int reads,writes;boolean closed;
        Packets()throws IOException {
            queue.add(NativeWire.packet(bytes("{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":5,\"bridge_version\":\"memory\",\"expected_ck3_sha256\":\""+"0".repeat(64)
                    +"\",\"game_adapter_id\":\"memory\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}")));
            queue.add(NativeWire.packet(bytes("{\"type\":\"heartbeat\",\"protocol_version\":1,\"pid\":42,\"monotonic_ms\":1,\"sequence\":1,\"startup_failure_containment_enabled\":false,\"startup_particle2_stage_recorder_enabled\":false,"
                    +"\"main_thread_query_mailbox_v1\":{\"installed\":true,\"stop\":false,\"failure\":0,\"ready\":true,\"executor_submission_enabled\":true,\"date_raw\":53144328,\"paused\":true,\"pump_epochs\":9}}")));
            queue.add(NativeWire.packet(bytes("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"memory-snapshot\",\"revision\":9,\"state\":"+STATE+"}")));
        }
        @Override public void verify()throws IOException {if(closed)throw new IOException("memory packet source closed");}
        @Override public void awaitConnection(Instant until)throws IOException {verify();}
        @Override public byte[] readPacket(Instant until)throws IOException {verify();reads++;if(queue.isEmpty())throw new IOException("unexpected extra Native receive");return queue.removeFirst();}
        @Override public WaitResult readPacketUntil(Instant waitUntil,Instant captureUntil)throws IOException {return new Packet(readPacket(captureUntil));}
        @Override public void writePacket(byte[] packet,Instant until){writes++;throw new AssertionError("memory READ cannot dispatch Native command");}
        @Override public void close(){closed=true;}
    }
}
