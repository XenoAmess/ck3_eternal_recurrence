package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.CompletedCycleProof;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.continuity.writer.NativeOutcomeArchive;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Software regression through actual assembler/stamp, semantic verifier, original writer and mandatory canonical SAVE refusal. */
public final class SavedAttachmentSourceStoreTest {
    @TempDir Path temporary;
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private record Fixture(NativeCheckpointFiles files,DriverCheckpointStore drivers,CheckpointPair pair,
            DriverStateSnapshot.Complete saved,CompletedCycleProof proof,SessionIdentity session,ContinuityWriter writer,
            CheckpointCommitVerifier verifier,SavedAttachmentSourceStore store,
            RestoreCheckpointService.NativeCandidate candidate,Path materialRoot) { }
    private Fixture fixture() throws Exception {
        var files=new NativeCheckpointFiles();var oldGame=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var newGame=new GameGeneration(124,new PythonOnlyUInt64(new BigInteger("9007199254740994")));
        var session=new SessionIdentity("test-machine-1",oldGame,"old-session");
        var before=DriverStateSnapshot.decodeComplete(bytes("""
            {"format_version":2,"pipe_name":"test-pipe","bridge_pid":123,"episode_character_id":29829,"episode_run_id":"episode-1",
            "command_history":[{"index":1,"command":"native-auto-run","ok":false,"result":{"status":"unknown","request_id":"old-unknown"}}],
            "last_checkpoint":null,"rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
            "succession_lifecycle":null,"campaign_goal":null,"rollback_war_failures":[]}
            """));
        byte[] state=bytes("""
            {"paused":true,"map_ready":true,"speed":3,"date_raw":240,"played_character":{"character_id":29829,"alive":true},
            "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
            "active_wars":[],"player_armies":[],
            "diagnostics":{"bridge_pid":123,"connection_generation":1}}
            """);
        var transport=new NativeObservationPort.TransportSession("test-machine-1",oldGame,BigInteger.ONE,"old-session");
        byte[] packet=packet(state);var nativeFrame=new NativeObservationPort.ObservedFrame(transport,"native:1",BigInteger.ONE,new RawJson(state),packet,AT);
        ExactRef rawRef=files.createNew(temporary.resolve("original-native.bin"),packet).reference();
        ExactRef sourceRef=files.createNew(temporary.resolve("source.txt"),bytes("software source provenance")).reference();
        var source=new G2Source("test-machine-1",AT.toString(),"test-build",sourceRef);
        var facts=new DriverObservationFacts(before,0,0,transport,"native:1",BigInteger.ONE,DriverJson.sha256(state),BigInteger.ONE,1,
                source,DriverJson.object(bytes("{}"),65536),sourceRef);
        var known=new DriverSnapshotFacts.Known(before,new DriverSnapshotFacts.Stamp(0,0,oldGame,"episode-1",DriverJson.sha256(before.encode())),
                sourceRef,List.of(),DriverJson.object(bytes("{}"),65536),Optional.empty(),Optional.of(facts));
        var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(nativeFrame,facts,rawRef));
        ExactRef semanticRef=files.createNew(temporary.resolve("original-semantic.json"),DriverJson.encode(complete.semantic())).reference();
        ExactRef driverRef=files.createNew(temporary.resolve("before-driver.json"),before.encode()).reference();
        ExactRef stampRef=files.createNew(temporary.resolve("original-stamp.json"),NativeDriverStamp.encode(complete,known)).reference();
        var semantic=new SemanticEvidence(complete.identity(),semanticRef,rawRef,stampRef,driverRef,AT);
        var stateRef=new AtomicReference<>(before);
        var drivers=new DriverCheckpointStore(files,temporary.resolve("saved-driver.json"),"test-pipe",new DriverCheckpointStore.SnapshotSupplier(){
            public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work)throws IOException {
                synchronized(stateRef){return work.run(stateRef.get(),(expected,published)->{
                    if(!stateRef.compareAndSet(expected,published))throw new IOException("fixture actual Driver CAS drift");
                });}
            }
        });
        var save=files.createNew(temporary.resolve("xar_checkpoint.ck3"),bytes("physical temporary SAVE")).reference();
        var saveWitness=files.observe(Path.of(save.path())).orElseThrow();var anchor=drivers.persist("save-1",saveWitness,complete.identity(),"lineage-1");
        ExactRef ack=files.createNew(temporary.resolve("save-ack.json"),bytes("{\"ok\":true}")).reference();
        var pair=new CheckpointPair(saveWitness,anchor.driver(),complete.identity(),"lineage-1",anchor.historyIndex(),"save-1",ack,AT);
        var cycleState=StrictJson.object();cycleState.put("schema","xar.java-ordinary-cycle-state/v1");cycleState.set("session",OrdinaryCycleTransitions.sessionToJson(session));
        cycleState.put("basis_cycles",0);cycleState.put("completed_cycles",0);cycleState.putNull("head");cycleState.putNull("pending_receipt");cycleState.putNull("retained_legacy_pending_digest");
        var proof=new CompletedCycleProof(0,semantic,ContinuityJson.digest(cycleState));
        var predecessor=StrictJson.object();predecessor.put("schema","root.ck3.continuity-window/v1");predecessor.put("machine_id","test-machine-1");
        predecessor.put("sequence",0);predecessor.put("window_id",1);predecessor.put("start_date_raw",0);predecessor.put("target_date_raw",480);predecessor.put("target_days",20);
        predecessor.put("status","running");predecessor.put("last_settled_cycles",0);predecessor.put("last_settled_date_raw",240);
        var latest=predecessor.putObject("latest_binding");latest.put("date_raw",240);latest.put("actor_character_id",29829);latest.put("episode_run_id","episode-1");
        latest.put("snapshot_id","native:1");latest.put("revision",1);latest.put("native_revision",1);
        predecessor.put("NEXT",11559);var unknown=predecessor.putArray("UNKNOWN").addObject();unknown.put("sequence",11558);unknown.put("status","unknown");unknown.put("replayed",false);
        Path ledger=temporary.resolve("ROOT-CONTINUITY-WINDOW.json");Files.write(ledger,StrictJson.canonical(predecessor));
        var origin=files.createNew(temporary.resolve("anchor.json"),StrictJson.canonical(predecessor)).reference();
        Path lock=temporary.resolve("ROOT-CONTINUITY-WINDOW.lock");Files.createFile(lock);Files.createDirectory(temporary.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        Path artifactsPath=Files.createDirectory(temporary.resolve("artifacts"));
        var storage=org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport.create(temporary,lock,64L*1024*1024);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifactsPath,lock,16*1024*1024),storage);
        var authority=new AtomicReference<SavedAttachmentAuthority>();
        var router=new WriterContracts.TransitionAuthority(){
            public String revalidate(ContinuityState head,WriterContracts.Request request)throws IOException{return authority.get().revalidate(head,request);}
            public ContinuityState reduce(ContinuityState head,WriterContracts.Request request)throws IOException{return authority.get().reduce(head,request);}
        };
        var writer=new ContinuityWriter(new WriterContracts.Layout(ledger,origin,"test-machine-1"),List.of(sourceRef),router,
                java.time.Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(artifacts),Optional.empty()),storage);
        var archive=new NativeOutcomeArchive(artifacts,writer);
        var semanticVerifier=new NativeSemanticEvidenceVerifier((borrowed,ref,limit)->{
            writer.requireSession(borrowed);var pin=borrowed.capturePin(ref,limit);var witness=files.observe(Path.of(ref.path())).orElseThrow();
            byte[] result=files.read(witness,limit);borrowed.verifyPin(pin);return result;
        });
        var verifier=new CheckpointCommitVerifier(files,drivers,(borrowed,owner,actual)->semanticVerifier.verify(borrowed,owner,actual).materialDigest(),lock,writer::requireSession,(borrowed,owner,actualPair,actualProof)->{throw new IOException("actual canonical SAVE authority is absent from this manual physical fixture");});
        var cycles=new OrdinaryCycleTransitions(archive,semanticVerifier,verifier::verify,new OriginalWindowReducer.Policy(20),writer::requireSession);
        Path materialRoot=temporary.resolve("checkpoint-material");
        var store=new SavedAttachmentSourceStore(files,drivers,verifier,writer::borrowedSession,materialRoot,cycles::verifyCompletedCycleProof,(same,owner,proofAtSource,captured)->{throw new IOException("manual fixture has no actual canonical SAVE history");});
        authority.set(new SavedAttachmentAuthority(drivers,store));
        var readiness=new CheckpointRequest.Readiness(complete.identity(),source,"old-session","lineage-1",true,true,true,"fixture_ready",ack,AT);
        byte[] newState=bytes(new String(state,StandardCharsets.UTF_8).replace("\"bridge_pid\":123","\"bridge_pid\":124"));byte[] newPacket=packet(newState);
        var newRaw=files.createNew(temporary.resolve("replacement-native.bin"),newPacket).reference();
        var candidate=new RestoreCheckpointService.NativeCandidate(new NativeObservationPort.ObservedFrame(
                new NativeObservationPort.TransportSession("test-machine-1",newGame,BigInteger.ONE,"new-session"),"native:1",BigInteger.ONE,new RawJson(newState),newPacket,AT),source,"lineage-1",newRaw);
        return new Fixture(files,drivers,pair,stateRef.get(),proof,session,writer,verifier,store,candidate,materialRoot);
    }
    @Test void manualPhysicalPairAndShapedAckCannotMintPersistentSavedSource() throws Exception {
        Fixture f=fixture();f.writer.locked(borrowed->{
            IOException refused=assertThrows(IOException.class,()->f.verifier.verifyCheckpoint(borrowed,f.session,f.pair,f.proof));
            assertTrue(refused.getMessage().contains("canonical SAVE"));
            assertFalse(Files.exists(f.materialRoot));assertEquals(0,borrowed.head().state().sequence());
            assertThrows(IOException.class,()->f.store.load(f.pair));return null;
        });
    }
    @Test void actualSemanticOriginalsStillRejectTamperingBeforeAnyMaterialCanBePublished() throws Exception {
        Fixture f=fixture();assertThrows(IOException.class,()->f.store.load(f.pair));
        f.writer.locked(borrowed->{
            Files.writeString(Path.of(f.proof.semantic().originalNativePacket().path()),"tampered actual semantic native original");
            assertThrows(Exception.class,()->f.verifier.verifyCheckpoint(borrowed,f.session,f.pair,f.proof));
            assertFalse(Files.exists(f.materialRoot));assertEquals(0,borrowed.head().state().sequence());return null;
        });
    }
    private static byte[] bytes(String text){return text.getBytes(StandardCharsets.UTF_8);}
    private static byte[] packet(byte[] state){
        byte[] json=bytes("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"native:1\",\"revision\":1,\"state\":"+new String(state,StandardCharsets.UTF_8)+"}");
        return ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();
    }
}
