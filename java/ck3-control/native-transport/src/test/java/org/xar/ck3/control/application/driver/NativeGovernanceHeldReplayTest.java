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
import org.xar.ck3.control.application.effects.RootPlanningReadGuard;
import org.xar.ck3.control.application.planning.governance.*;
import org.xar.ck3.control.nativebridge.capabilities.governance.*;
import java.util.concurrent.atomic.AtomicReference;
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
final class NativeGovernanceHeldReplayTest {
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

    private static final String EXE="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    @Test void actualFormalReturnedFailureKeepsItsHeldOriginalFailureObservation() throws Exception {
        try(var f=new Fixture()) { f.round(()->{
            var ready=f.ready();var definitions=new GovernancePlanningReads(new GovernancePlanningReads.Sources(
                    f.material(bytes("actual LIFE source")),f.material(bytes("actual Crown source"))),"1.20.0.4",EXE);
            var catalog=RootReadContractCatalog.staticOnly(definitions.all());var seen=new AtomicReference<PlanningReadResult<?>>();
            var heldFailure=new AtomicReference<RuntimeException>();var heldChecks=new AtomicInteger();
            var root=new RootPlanningReadGuard(f.collector,()->f.store.session,f.archive,ready.request().source(),Clock.systemUTC(),
                    "governance-memory-root",(same,ref,maximum)->{f.store.requireSession(same);return f.original(ref,maximum);},catalog);
            PlanningReadCoordinator.ReadGuardPort guards=new PlanningReadCoordinator.ReadGuardPort(){
                @Override public PlanningReadGuard verify(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract){return root.verify(head,request,contract);}
                @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract){
                    heldChecks.incrementAndGet();try{return root.verifyOriginalCurrent(head,request,contract);}
                    catch(RuntimeException failure){heldFailure.set(failure);throw failure;}
                }
            };
            var coordinator=new PlanningReadCoordinator(catalog,f.journal,guards,f.transport,f.archive,Clock.systemUTC());
            PlanningReadPort observed=new PlanningReadPort(){
                @Override public <T>PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("must use original Session");}
                @Override public <T>PlanningReadResult<T> read(ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest request){
                    assertSame(definitions.formal(),contract);var result=coordinator.read(same,contract,request);seen.set(result);return result;
                }
            };
            var borrowed=new GovernanceBorrowedSession(f.store.session,Path.of("D:/test-memory/governance-writer.lock"),f.store::requireSession);
            var port=new NativeLifestyleReadPort(observed,definitions,f.archive,borrowed);
            int packets=f.packets.reads;String head=f.store.session.head().digest();
            var result=port.formal(ready.request());
            if(heldFailure.get()!=null)throw new AssertionError("actual Root held original guard rejected returned LIFE failure",heldFailure.get());
            assertInstanceOf(GovernanceObservationSupplier.Unavailable.class,result);
            var failed=assertInstanceOf(PlanningReadResult.Unavailable.class,seen.get());
            assertEquals(1,heldChecks.get());assertTrue(failed.observedFailure().isPresent(),()->"actual returned failure observation missing: "+failed.reason());
            var original=assertInstanceOf(NativeActionPort.AckReceived.class,failed.original().orElseThrow());assertFalse(original.nativeOk());
            assertTrue(original.outbound().isPresent());assertTrue(original.custody().isPresent());
            assertEquals(1,f.packets.writes);assertEquals(packets+1,f.packets.reads);assertEquals(head,f.store.session.head().digest());return null;
        }); }
    }
    @Test void actualFormalOriginalHasIdenticalLiveAndPureReplayDecoderAndRejectsNativeDrift() throws Exception {
        try(var f=new Fixture()) { f.round(()->{
            var ready=f.ready();var definitions=new GovernancePlanningReads(new GovernancePlanningReads.Sources(
                    f.material(bytes("actual LIFE source")),f.material(bytes("actual Crown source"))),"1.20.0.4",EXE);
            var catalog=RootReadContractCatalog.staticOnly(definitions.all());
            var root=new RootPlanningReadGuard(f.collector,()->f.store.session,f.archive,ready.request().source(),Clock.systemUTC(),
                    "governance-memory-root",(same,ref,maximum)->{f.store.requireSession(same);return f.original(ref,maximum);},catalog);
            var coordinator=new PlanningReadCoordinator(catalog,f.journal,root,f.transport,f.archive,Clock.systemUTC());
            var contract=definitions.formal();var request=new PlanningReadRequest(ready.request().before(),ready.request().source(),SESSION,
                    contract.operation(),new Obj(Map.of()),f.deadline);
            f.packets.positiveFormal=true;
            var result=coordinator.read(f.store.session,contract,request);
            var actual=assertInstanceOf(PlanningReadResult.Known.class,result,()->"actual formal decode: "+result);
            var receipt=actual.receipt();assertEquals(actual.value(),contract.replay(receipt));
            for(var installed:definitions.all())assertTrue(installed.hasPureReplay(),installed.contractId());
            var bad=com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode();
            bad.setAll((com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(receipt.original().originalFrame().bytes()));
            ((com.fasterxml.jackson.databind.node.ObjectNode)bad.get("result").get("snapshot")).put("player_character_id",74);
            var tampered=new NativeActionPort.AckReceived(receipt.requestId(),true,Optional.of(new RawJson(StrictJson.canonical(bad.get("result")))),
                    new RawJson(StrictJson.canonical(bad)),NativeWire.packet(StrictJson.canonical(bad)));
            var wrong=new PlanningReadReceipt(request,contract.contractId(),receipt.requestId(),receipt.before(),receipt.after(),tampered);
            assertThrows(IllegalArgumentException.class,()->contract.replay(wrong));assertEquals(1,f.packets.writes);return null;
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
            @Override public void requireWriter(Path lock){requireSession(this);assertEquals(Path.of("D:/test-memory/governance-writer.lock"),lock);}
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
        private final Fixture fixture;private final Map<ExactRef,NativeActionPort.DispatchOutcome> outcomes=new HashMap<>();
        private final Map<ExactRef,NativeRequest> requests=new HashMap<>();private final Map<ExactRef,PlanningReadReceipt> reads=new HashMap<>();
        Archive(Fixture fixture){this.fixture=fixture;}
        @Override public ActionPorts.OutcomeArchive withSession(ContinuityStorePort.Session same){fixture.store.requireSession(same);return this;}
        @Override public <T>T inSession(ContinuityStorePort.Session same,Function<ActionPorts.OutcomeArchive,T> work){fixture.store.requireSession(same);return work.apply(this);}
        @Override public ExactRef preserveMaterial(RawJson raw){return fixture.material(raw.bytes());}
        @Override public RawJson loadMaterial(ExactRef ref){return new RawJson(fixture.original(ref,DriverJson.MAX_NATIVE_BYTES));}
        @Override public RawJson loadFullMaterial(ExactRef ref){return loadMaterial(ref);}
        @Override public ExactRef materialReferenceOf(RawJson raw){var ref=new ExactRef("D:/test-memory/retained-driver/"+DriverJson.sha256(raw.bytes())+".json",raw.bytes().length,DriverJson.sha256(raw.bytes()));assertArrayEquals(raw.bytes(),fixture.original(ref,DriverJson.MAX_NATIVE_BYTES));return ref;}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame actual){return fixture.material(actual.originalPacket());}
        @Override public byte[] loadNativeFrame(ExactRef ref){return fixture.original(ref,DriverJson.MAX_NATIVE_BYTES);}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){for(var e:outcomes.entrySet())if(e.getValue().equals(value))return e.getKey();var ref=fixture.material(bytes("{\"memory_outcome\":"+outcomes.size()+"}"));outcomes.put(ref,value);return ref;}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){return outcomes.get(ref);}
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){return outcomes.entrySet().stream().filter(e->e.getValue().equals(value)).findFirst().orElseThrow().getKey();}
        @Override public ExactRef preserveRequest(NativeRequest value){for(var e:requests.entrySet())if(e.getValue().equals(value))return e.getKey();var ref=fixture.material(bytes("{\"memory_request\":"+requests.size()+"}"));requests.put(ref,value);return ref;}
        @Override public NativeRequest loadRequest(ExactRef ref){return requests.get(ref);}
        @Override public ExactRef requestReferenceOf(NativeRequest value){return requests.entrySet().stream().filter(e->e.getValue().equals(value)).findFirst().orElseThrow().getKey();}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){for(var e:reads.entrySet())if(e.getValue().equals(value))return e.getKey();var ref=fixture.material(bytes("{\"memory_read\":"+reads.size()+"}"));reads.put(ref,value);return ref;}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){return reads.get(ref);}
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){return reads.entrySet().stream().filter(e->e.getValue().equals(value)).findFirst().orElseThrow().getKey();}
        private AssertionError unused(){return new AssertionError("memory read cannot write an action or ledger");}
        @Override public ExactRef preserveRecord(ActionRecord value){throw unused();}
        @Override public ActionRecord loadRecord(ExactRef ref){throw unused();}
        @Override public ExactRef recordReferenceOf(ActionRecord value){throw unused();}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw unused();}
        @Override public ActionReceipt loadReceipt(ExactRef ref){throw unused();}
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){throw unused();}
    }

    private static final class Packets implements NativePacketPort {
        final ArrayDeque<byte[]> queue=new ArrayDeque<>();int reads,writes;boolean closed,positiveFormal;
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
        @Override public void writePacket(byte[] packet,Instant until)throws IOException {
            writes++;var command=StrictJson.parse(java.util.Arrays.copyOfRange(packet,4,packet.length));
            String id=StrictJson.text(command.get("request_id"));
            assertEquals(GovernancePlanningReads.FORMAL,StrictJson.text(command.get("step")));
            var reply=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",positiveFormal);
            if(!positiveFormal)reply.put("error","actual controlled LIFE response unavailable");
            else reply.set("result",StrictJson.parse(bytes("{\"step\":\"private-query-player-lifestyle-formal-v1\",\"private_build\":true,\"advertised\":false,\"status\":\"available\",\"episode_run_id\":\"episode-real-1\",\"formal_precondition_status\":\"not_ready\",\"snapshot\":{\"private_build\":true,\"advertised\":false,\"status\":\"available\",\"snapshot_id\":\"native:9\",\"public_revision\":9,\"native_revision\":9,\"proof_epoch\":9,\"date_raw\":53144328,\"player_character_id\":73,\"current_focus\":{\"presence\":\"absent\"},\"current_lifestyle_progress\":{\"presence\":\"absent\"},\"owned_perk_keys\":[],\"actor_traits\":{\"status\":\"available\",\"observed_keys\":[]},\"legal_focus_candidates\":{\"status\":\"unavailable\",\"reason\":\"not_requested\",\"items\":[]},\"legal_perk_candidates\":{\"status\":\"unavailable\",\"reason\":\"not_requested\",\"items\":[]},\"readiness\":{\"current_focus_ready\":true,\"lifestyle_progress_ready\":true,\"owned_perks_ready\":true,\"legal_focus_candidates_ready\":false,\"legal_perk_candidates_ready\":false,\"same_frame_ready\":true}}}")));
            queue.add(NativeWire.packet(StrictJson.canonical(reply)));
        }
        @Override public void close(){closed=true;}
    }
}
