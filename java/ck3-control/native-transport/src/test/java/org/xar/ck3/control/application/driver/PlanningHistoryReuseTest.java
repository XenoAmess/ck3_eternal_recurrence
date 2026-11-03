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
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.nativebridge.*;

/** Real Collector/Driver producers with memory-only packet and storage edges; no Game or filesystem qualification. */
final class PlanningHistoryReuseTest {
    private static final String MACHINE="retained-driver-memory", SESSION="retained-driver-session";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final String WIRE="""
        {"format_version":2,"pipe_name":"test-pipe","bridge_pid":42,"episode_character_id":73,"episode_run_id":"episode-real-1",
        "last_checkpoint":null,"command_history":[{"index":1,"command":"fixture-read-only-history","ok":true,"nested":{"items":[{"n":9007199254740993,"d":-0.0000e+9}]}}],"rollback_war_failure":null,"managed_restore_transaction":null,
        "succession_expectation":null,"succession_lifecycle":null,"campaign_goal":{"campaign_id":"original","anchor":{"character_id":73}},
        "rollback_war_failures":[]}
        """;
    private static final String STATE="""
        {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,"played_character":{"character_id":73,"alive":true},
        "active_event":null,"pending_character_interaction":null,"one_life_terminal":false,"one_life_terminal_reason":null,
        "episode_identity_pending":false,"active_wars":[],"player_armies":[],"diagnostics":{"bridge_pid":42,"connection_generation":5}}
        """;

    @Test void originalProducerAndReadyConsumerShareStrictImmutableRowsOnlyInsideActualScope() throws Exception {
        try (var f=new Fixture()) {
            f.onInputs=(actual,known)->{
                var again=actual.collector.planningHistory(actual.store.session,known);
                assertSame(actual.firstParsed,again);
                assertThrows(UnsupportedOperationException.class,()->again.add(new Obj(Map.of())));
                var first=again.getFirst();
                assertThrows(UnsupportedOperationException.class,()->first.members().put("injected",new Bool(true)));
                var nested=(Obj)first.get("nested");var items=(Arr)nested.get("items");
                assertThrows(UnsupportedOperationException.class,()->items.items().clear());
                var detached=(com.fasterxml.jackson.databind.node.ObjectNode)OpportunityJson.toNode(first);
                detached.put("injected",true);
                byte[] writable=known.driver().commandHistory().getFirst().originalRow().json();writable[0]='[';
                assertFalse(first.members().containsKey("injected"));
                assertEquals(new BigInteger("9007199254740993"),((IntegerValue)((Obj)items.items().getFirst()).get("n")).value());
                assertEquals("-0.0000e+9",((DecimalValue)((Obj)items.items().getFirst()).get("d")).token());
            };
            var ready=f.round(f::ready);
            assertSame(f.firstParsed.getFirst(),ready.request().observations().history().getFirst());
            assertEquals(1,f.inputCalls);
            var outside=f.collector.planningHistory(f.store.session,f.inputKnown);
            assertEquals(f.firstParsed,outside);assertNotSame(f.firstParsed.getFirst(),outside.getFirst());
            assertEquals(0,f.packets.writes);
        }
    }

    @Test void foreignKnownSessionThreadAndNextScopeCannotBorrowAnEarlierParsedRow() throws Exception {
        try(var f=new Fixture()) {
            f.onInputs=(actual,known)->{
                var otherKnown=new DriverSnapshotFacts.Known(known.driver(),known.stamp(),known.originalHistoryBasis(),
                        known.actionRows(),known.auxiliary(),known.loop(),known.observation());
                assertEquals(known,otherKnown);assertNotSame(known,otherKnown);
                assertNotSame(actual.firstParsed.getFirst(),actual.collector.planningHistory(actual.store.session,otherKnown).getFirst());
                var foreign=new MemoryStore();
                assertNotSame(actual.firstParsed.getFirst(),actual.collector.planningHistory(foreign.session,known).getFirst());
                var result=new java.util.concurrent.atomic.AtomicReference<List<Obj>>();
                var failure=new java.util.concurrent.atomic.AtomicReference<Throwable>();
                Thread other=new Thread(()->{try{result.set(actual.collector.planningHistory(actual.store.session,known));}
                    catch(Throwable value){failure.set(value);}},"new-history-data-thread");
                other.start();try{other.join(3000);}catch(InterruptedException value){Thread.currentThread().interrupt();throw new AssertionError(value);}
                assertFalse(other.isAlive());assertNull(failure.get());
                assertEquals(actual.firstParsed,result.get());assertNotSame(actual.firstParsed.getFirst(),result.get().getFirst());
                assertSame(actual.firstParsed,actual.collector.planningHistory(actual.store.session,known));
            };
            var ready=f.round(f::ready);var original=f.firstParsed.getFirst();
            f.store.locked(same->f.collector.current(same,ready.request().before(),f.deadline,lease->{
                var first=f.collector.planningHistory(same,lease.driver());
                assertEquals(original,first.getFirst());assertNotSame(original,first.getFirst());
                assertSame(first,f.collector.planningHistory(same,lease.driver()));return null;
            }));
            assertEquals(0,f.packets.writes);
        }
    }

    @Test void legacyProxyDispatchAndCallbackFailureLeaveNoReusableScope() throws Exception {
        try(var f=new Fixture(true)) {
            var failure=new IllegalStateException("actual new offline callback failure");
            f.onInputs=(actual,known)->{throw failure;};
            var unavailable=assertInstanceOf(SessionPorts.ObservationUnavailable.class,f.round(f::observe));
            assertTrue(unavailable.reason().contains(failure.getMessage()));
            assertEquals(1,f.inputCalls);assertEquals(List.of("collect"),f.proxyMethods);
            var outside=f.collector.planningHistory(f.store.session,f.inputKnown);
            assertEquals(f.firstParsed,outside);assertNotSame(f.firstParsed.getFirst(),outside.getFirst());
            assertEquals(0,f.packets.writes);
        }
    }

    @Test void cachedDataDoesNotSkipTheExistingFreshCanonicalHeadCheck() throws Exception {
        try(var f=new Fixture()) {
            f.onInputs=(actual,known)->{actual.store.head=MemoryStore.head(2);};
            var unavailable=assertInstanceOf(SessionPorts.ObservationUnavailable.class,f.round(f::observe));
            assertTrue(unavailable.reason().contains("writer changed inside borrowed observation-only planning read"));
            assertEquals(1,f.inputCalls);
            var outside=f.collector.planningHistory(f.store.session,f.inputKnown);
            assertNotSame(f.firstParsed.getFirst(),outside.getFirst());
            assertEquals(0,f.packets.writes);
        }
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
        DriverSnapshotFacts.Known inputKnown;
        List<Obj> firstParsed;
        int inputCalls;
        final boolean legacyProxy;
        final java.util.List<String> proxyMethods=new java.util.ArrayList<>();
        java.util.function.BiConsumer<Fixture,DriverSnapshotFacts.Known> onInputs=(actual,known)->{};
        Fixture()throws IOException {this(false);}
        Fixture(boolean legacyProxy)throws IOException {
            this.legacyProxy=legacyProxy;
            Duration validity=Duration.ofSeconds(30);
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
                    inputsPort(),
                    new NativeReadiness.Policy(false,false,Optional.of(BigInteger.valueOf(73)),Duration.ZERO,false),validity,Clock.systemUTC());
            collector.bindObservationSession(store::requireSession);
            collector.bindReadyPublication((same,request,frame,current,sources)->{store.requireSession(same);published=current;});
            collector.bindPlanningEvidence((same,request,lease)->{store.requireSession(same);assertEquals(request.before(),lease.frame().identity());});
        }
        private NativeReadinessCollector.PlanningInputsPort inputsPort() {
            if (!legacyProxy) return (same,frame,current,received,until)->collectInputs(same,current);
            return (NativeReadinessCollector.PlanningInputsPort)java.lang.reflect.Proxy.newProxyInstance(
                    NativeReadinessCollector.PlanningInputsPort.class.getClassLoader(),
                    new Class<?>[]{NativeReadinessCollector.PlanningInputsPort.class},(proxy,method,args)->{
                        proxyMethods.add(method.getName());assertEquals("collect",method.getName());
                        return collectInputs((ContinuityStorePort.Session)args[0],(DriverSnapshotFacts.Known)args[2]);
                    });
        }
        private NativeReadinessCollector.PlanningInputs collectInputs(ContinuityStorePort.Session same,DriverSnapshotFacts.Known known) {
            store.requireSession(same);inputCalls++;inputKnown=known;
            firstParsed=collector.planningHistory(same,known);onInputs.accept(this,known);
            return new NativeReadinessCollector.PlanningInputs(Set.of(),Set.of(),Optional.empty(),List.of(),
                    Optional.empty(),Optional.empty(),false,Optional.empty());
        }
        SessionPorts.Observation observe()throws IOException,InterruptedException {
            return collector.observe(store.session,new SessionPorts.SessionIdentity(MACHINE,GAME,SESSION),deadline);
        }
        SessionPorts.Ready ready()throws IOException,InterruptedException {
            var observation=observe();
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
