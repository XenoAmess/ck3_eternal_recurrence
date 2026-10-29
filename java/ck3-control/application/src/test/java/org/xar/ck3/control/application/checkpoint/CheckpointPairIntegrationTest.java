package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.application.action.*;

/** Actual temporary files through the production writer and consumer; no captured/live golden is invented. */
public class CheckpointPairIntegrationTest {
    @TempDir Path temporary;
    private static ProposalLifecycle.ObservationIdentity frame() {
        return new ProposalLifecycle.ObservationIdentity("test-machine-1", new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.ONE,BigInteger.valueOf(240)),"native:1",BigInteger.ONE,"episode-1"),1);
    }
    private static DriverStateSnapshot.Complete complete() {
        return DriverStateSnapshot.decodeComplete(("{\"format_version\":2,\"pipe_name\":\"test-pipe\",\"bridge_pid\":123,\"episode_character_id\":29829,\"episode_run_id\":\"episode-1\","
                + "\"last_checkpoint\":null,\"command_history\":[{\"index\":1,\"command\":\"query-unknown-retained\",\"ok\":true,\"result\":{\"pending\":[null,{\"unknown\":true}]}}],"
                + "\"rollback_war_failure\":null,\"managed_restore_transaction\":null,\"succession_expectation\":null,\"succession_lifecycle\":null,\"campaign_goal\":{\"pending\":null},\"rollback_war_failures\":[]}").getBytes(StandardCharsets.UTF_8));
    }
    private record Setup(NativeCheckpointFiles files,DriverCheckpointStore store,AtomicReference<DriverStateSnapshot.Complete> state,Path save) { }
    private Setup setup() throws Exception {
        NativeCheckpointFiles files = new NativeCheckpointFiles(); Path save = temporary.resolve("xar_checkpoint.ck3"); Files.writeString(save,"actual temporary save input");
        AtomicReference<DriverStateSnapshot.Complete> state = new AtomicReference<>(complete());
        DriverCheckpointStore store = new DriverCheckpointStore(files,temporary.resolve("native-driver-state.json"),"test-pipe",new DriverCheckpointStore.SnapshotSupplier() {
            public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) throws java.io.IOException {
                synchronized(state) { return work.run(state.get(),(expected,published) -> {
                    if (!state.compareAndSet(expected,published)) throw new IllegalStateException("snapshot CAS drift");
                }); }
            }
        }); return new Setup(files,store,state,save);
    }
    private CheckpointPair produce(Setup setup) throws Exception {
        var save = setup.files().observe(setup.save()).orElseThrow(); var anchor = setup.store().persist("save-test-1",save,frame(),"lineage-1");
        Path ack = temporary.resolve("native-ack.json"); Files.writeString(ack,"{\"native_ok\":true}");
        return new CheckpointPair(save,anchor.driver(),frame(),"lineage-1",anchor.historyIndex(),"save-test-1",setup.files().observe(ack).orElseThrow().reference(),Instant.parse("2026-10-23T15:00:00Z"));
    }
    @Test void completeProducerToPairConsumerAndRoundTripPreservesHistory() throws Exception {
        Setup setup = setup(); CheckpointPair pair = produce(setup); setup.store().verify(pair);
        assertEquals(pair,CheckpointPairCodec.decode(CheckpointPairCodec.encode(pair))); assertEquals(2,pair.historyIndex());
        String document = new String(setup.files().read(pair.driver(),DriverCheckpointStore.MAX_DRIVER_BYTES),StandardCharsets.UTF_8);
        assertTrue(document.contains("query-unknown-retained")); assertTrue(document.contains("\"pending\":[null,{\"unknown\":true}]"));
        var again = setup.store().persist("save-test-1",pair.save(),frame(),"lineage-1"); assertEquals(pair.driver(),again.driver());
        assertEquals(2,setup.state().get().commandHistory().size());
    }
    @Test void changedPhysicalSaveFailsExistingDriverPair() throws Exception {
        Setup setup = setup(); CheckpointPair pair = produce(setup); Files.writeString(setup.save(),"different temporary save");
        assertThrows(Exception.class,()->setup.store().verify(pair));
    }
    @Test void emptyPhysicalPrestateIsPresentButCannotQualifyAPair() throws Exception {
        Setup setup=setup(); Files.write(setup.save(),new byte[0]); var empty=setup.files().observe(setup.save()).orElseThrow();
        assertEquals(0,empty.reference().bytes());
        assertThrows(Exception.class,()->setup.store().persist("save-empty",empty,frame(),"lineage-1"));
    }
    @Test void pairIntegerAliasesAndUnavailableNativeAckAreRejected() throws Exception {
        Setup setup=setup(); CheckpointPair pair=produce(setup);
        String json=new String(CheckpointPairCodec.encode(pair),StandardCharsets.UTF_8);
        assertThrows(Exception.class,()->CheckpointPairCodec.decode(json.replace("\"history_index\":2","\"history_index\":true").getBytes(StandardCharsets.UTF_8)));
        assertThrows(Exception.class,()->CheckpointPairCodec.decode(json.replace("\"history_index\":2","\"history_index\":2.0").getBytes(StandardCharsets.UTF_8)));
        Files.delete(Path.of(pair.nativeAckRef().path())); assertThrows(Exception.class,()->setup.store().verify(pair));
    }
    @Test void immutableSeedCopyUsesActualSourceAndNeverOverwrites() throws Exception {
        Setup setup=setup(); CheckpointPair pair=produce(setup); Path seed=temporary.resolve("xar_episode_seed.ck3");
        var copy=setup.files().copyNew(pair.save(),seed); assertEquals(pair.save().reference().sha256(),copy.reference().sha256());
        assertNotEquals(pair.save().identity().fileId(),copy.identity().fileId());
        assertThrows(java.io.IOException.class,()->setup.files().copyNew(pair.save(),seed));
        setup.files().verify(pair.save()); setup.files().verify(copy);
    }
    @Test void incompleteSupplierCannotPublishDriverOrCreateHistory() throws Exception {
        Setup setup = setup(); Path target = temporary.resolve("unavailable-driver.json");
        var missing = new DriverCheckpointStore(setup.files(),target,"test-pipe",new DriverCheckpointStore.SnapshotSupplier() {
            public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) throws java.io.IOException {
                return work.run(new DriverStateSnapshot.Incomplete(List.of("command_history","campaign_goal")),(expected,published)->fail("incomplete snapshot must not publish"));
            }
        });
        assertThrows(Exception.class,()->missing.persist("save-missing",setup.files().observe(setup.save()).orElseThrow(),frame(),"lineage-1")); assertFalse(Files.exists(target));
    }
    @Test void failedStateCasNeverReturnsPairSuccess() throws Exception {
        Setup setup=setup(); var refusing=new DriverCheckpointStore(setup.files(),temporary.resolve("cas-driver.json"),"test-pipe",new DriverCheckpointStore.SnapshotSupplier(){
            public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) throws java.io.IOException {
                return work.run(complete(),(expected,published)->{throw new java.io.IOException("state changed");});
            }
        }); assertThrows(java.io.IOException.class,()->refusing.persist("save-cas",setup.files().observe(setup.save()).orElseThrow(),frame(),"lineage-1"));
    }
    @Test void newSaveClearsRollbackScopeAndMaterializesMissingPluralWithoutChangingCampaign() throws Exception {
        Setup setup=setup();var before=setup.state().get();
        var legacy=new DriverStateSnapshot.Complete(before.session(),before.commandHistory(),before.lastCheckpoint(),
                new DriverStateSnapshot.Value("{\"legacy_advisory\":true}".getBytes(StandardCharsets.UTF_8)),before.managedRestoreTransaction(),
                before.successionExpectation(),before.successionLifecycle(),before.campaignGoal(),new DriverStateSnapshot.Missing());
        setup.state().set(legacy);CheckpointPair pair=produce(setup);var saved=setup.store().readVerified(pair);
        assertInstanceOf(DriverStateSnapshot.NullValue.class,saved.rollbackWarFailure());
        var failures=assertInstanceOf(DriverStateSnapshot.Value.class,saved.rollbackWarFailures());assertEquals("[]",new String(failures.json(),StandardCharsets.UTF_8));
        assertArrayEquals(((DriverStateSnapshot.Value)legacy.campaignGoal()).json(),((DriverStateSnapshot.Value)saved.campaignGoal()).json());
        assertArrayEquals(legacy.commandHistory().getFirst().originalRow().json(),saved.commandHistory().getFirst().originalRow().json());
    }
    private static ContinuityState head() {
        return ContinuityState.fromJson(StrictJson.parse(("{\"schema\":\"root.ck3.continuity-window/v1\",\"machine_id\":\"test-machine-1\",\"sequence\":0,\"window_id\":1,\"start_date_raw\":0,\"target_date_raw\":240,\"target_days\":10,\"status\":\"running\",\"last_settled_cycles\":0,\"last_settled_date_raw\":0,\"pending_cycle\":{\"status\":\"unknown\",\"sequence\":5}}").getBytes(StandardCharsets.UTF_8)),"test-machine-1");
    }
    private static ContinuityStorePort noWriteWriter(ContinuityState state) {
        return new ContinuityStorePort() {
            public WriterContracts.Prepared preview(WriterContracts.Request request) { fail("invalid or unknown restore must not preview attachment"); return null; }
            public WriterContracts.Receipt commit(WriterContracts.Prepared prepared) { fail("invalid or unknown restore must not commit"); return null; }
            public ExactRef persistedHead() { throw new AssertionError("no physical ledger in this fixture"); }
            public <T>T locked(SessionWork<T> work) throws java.io.IOException {
                return work.run(new Session() {
                    public void requireWriter(Path originalWriterLock){throw new AssertionError("no writer qualification in this rejection fixture");}
                    public WriterContracts.Pin capturePin(ExactRef ref,int maximumBytes){throw new AssertionError("no pin qualification");}
                    public void verifyPin(WriterContracts.Pin pin){throw new AssertionError("no pin qualification");}
                    public WriterContracts.Head head(){return new WriterContracts.Head(state,List.of(),List.of(),List.of(),false);}
                    public WriterContracts.Prepared preview(WriterContracts.Request request){throw new AssertionError("no attach");}
                    public WriterContracts.Receipt commit(WriterContracts.Prepared prepared){throw new AssertionError("no commit");}
                    public ExactRef persistedHead(){throw new AssertionError("no ledger");}
                });
            }
        };
    }
    private static CheckpointRequest.Readiness ready(CheckpointPair pair) {
        return new CheckpointRequest.Readiness(pair.frame(),new G2Source("test-machine-1","2026-10-23T15:00:00Z","test-build",pair.nativeAckRef()),"old-session","lineage-1",true,true,true,"fixture_ready",pair.nativeAckRef(),Instant.now());
    }
    private static RestoreCheckpointService.PublicationPort refusingPublication() {
        return new RestoreCheckpointService.PublicationPort() {
            public RestoreCheckpointService.PublishedDriver publish(RestoreCheckpointService.Request request,
                    RestoreCheckpointService.NativeCandidate restored,DriverStateSnapshot.Complete saved,
                    WriterContracts.Prepared prepared,WriterContracts.Receipt committed,RestoreCheckpointService.ReadWindow reads) { throw new AssertionError("invalid restore must not publish Driver authority"); }
            public void requireCurrent(RestoreCheckpointService.PublishedDriver published,RestoreCheckpointService.NativeCandidate restored,
                    WriterContracts.Receipt committed,RestoreCheckpointService.ReadWindow reads) { throw new AssertionError("invalid restore cannot become current"); }
        };
    }
    private RestoreCheckpointService.NativeCandidate candidate(Setup setup,CheckpointPair pair,GameGeneration game,
            BigInteger actor,String sessionId) throws Exception {
        var state=StrictJson.object();state.put("paused",true);state.put("map_ready",true);state.put("date_raw",240);
        var player=state.putObject("played_character");player.put("character_id",actor);player.put("alive",true);
        byte[] stateBytes=StrictJson.canonical(state);var envelope=StrictJson.object();envelope.put("type","state_snapshot");
        envelope.put("protocol_version",1);envelope.put("snapshot_id","native:1");envelope.put("revision",1);envelope.set("state",state);
        byte[] json=StrictJson.canonical(envelope);byte[] packet=java.nio.ByteBuffer.allocate(json.length+4)
                .order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
        Path original=temporary.resolve(sessionId+"-raw.bin");Files.write(original,packet);
        var observed=new NativeObservationPort.ObservedFrame(new NativeObservationPort.TransportSession("test-machine-1",game,BigInteger.ONE,sessionId),
                "native:1",BigInteger.ONE,new RawJson(stateBytes),packet,Instant.now());
        return new RestoreCheckpointService.NativeCandidate(observed,ready(pair).source(),"lineage-1",setup.files().observe(original).orElseThrow().reference());
    }
    // Restore dispatch/UNKNOWN cases now use actual private material in local-service
    // CheckpointMaterialRestoreCompositionTest; a manual pair cannot construct that authority.
    @Test void positiveAckWithoutChangedSaveDoesNotConfirmOrResubmit() throws Exception {
        Setup setup=setup(); CheckpointPair baseline=produce(setup); var ready=ready(baseline);
        CheckpointService service=new CheckpointService(setup.files(),setup.store(),deadline->ready,temporary,java.time.Clock.systemUTC(),(pair,action)->{throw new AssertionError("ACK alone cannot freeze a seed");});
        AtomicInteger dispatches=new AtomicInteger(); AtomicReference<ActionReceipt> prior=new AtomicReference<>();
        service.bindActions(new ActionCoordinatorPort(){
            public ActionReceipt execute(ActionCommand command){
                if(prior.get()!=null)return prior.get(); dispatches.incrementAndGet(); Instant now=Instant.now();
                GuardEvidence guard=new GuardEvidence(command.before(),command.source(),command.sessionId(),BigInteger.ONE,command.operation(),baseline.nativeAckRef(),baseline.nativeAckRef(),"fixture-authority",now,command.deadline());
                var attempt=new ActionState.Attempt("native-test-request",now,guard,new NativeRequest("save-checkpoint","game.save-checkpoint",new RawJson("{}".getBytes(StandardCharsets.UTF_8))));
                var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(new RawJson("{}".getBytes(StandardCharsets.UTF_8))),new RawJson("{}".getBytes(StandardCharsets.UTF_8)),"{\"ok\":true}".getBytes(StandardCharsets.UTF_8));
                var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.AckReceived(attempt,ack)); prior.set(receipt); return receipt;
            }
            public ActionReceipt reconcile(String id){
                var original=prior.get(); var state=(ActionState.AckReceived)original.state();
                assertInstanceOf(ActionPorts.Pending.class,service.observe(original.command(),state.attempt(),state.dispatch())); return original;
            }
        });
        var factory=new CheckpointRequestFactory(setup.save(),deadline->ready);
        var request=factory.prepare(ready.observed(),ready.source(),ready.sessionId(),Optional.of(baseline),Instant.now().plusMillis(150));
        assertInstanceOf(CheckpointResult.Unknown.class,service.checkpoint(request));
        assertInstanceOf(CheckpointResult.Unknown.class,service.checkpoint(request)); assertEquals(1,dispatches.get());
        assertEquals(2,setup.state().get().commandHistory().size());
    }
}
