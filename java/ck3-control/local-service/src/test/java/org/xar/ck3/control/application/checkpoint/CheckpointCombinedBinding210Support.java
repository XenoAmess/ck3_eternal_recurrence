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
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;

/** Unit callback scope with real temporary files/Driver anchors. Stub Session grants no live/canonical qualification. */
final class CheckpointCombinedBinding210Support {
    static final String SEMANTIC_DIGEST="a".repeat(64),SAVE_DIGEST="b".repeat(64);
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private CheckpointCombinedBinding210Support() { }
    record Fixture(NativeCheckpointFiles files,DriverCheckpointStore drivers,CheckpointPair pair,
            DriverStateSnapshot.Complete saved,CompletedCycleProof proof,SessionIdentity owner,Scope same,
            CheckpointCommitVerifier verifier,SavedAttachmentSourceStore store,byte[] archivedDriver) {
        Fixture { archivedDriver=archivedDriver.clone(); }
        @Override public byte[] archivedDriver(){return archivedDriver.clone();}
        String cycleAuthority(){return CheckpointCombinedBinding210Support.cycleAuthority(owner,proof);}
    }
    static final class Scope implements ContinuityStorePort.Session {
        private final Path lock;private WriterContracts.Head actual;
        Scope(Path lock,ContinuityState state){this.lock=lock;actual=new WriterContracts.Head(state,List.of(),List.of(),List.of(),false);}
        @Override public void requireWriter(Path expected)throws IOException {if(!lock.equals(expected))throw new IOException("foreign unit writer");}
        @Override public WriterContracts.Head head(){return actual;}
        void changeHead(){var row=actual.state().toJson();row.put("last_settled_cycles",1);actual=new WriterContracts.Head(ContinuityState.fromJson(row,actual.state().machineId()),List.of(),List.of(),List.of(),false);}
        @Override public ContinuityState requireHistoricalState(long sequence,String digest)throws IOException {
            if(sequence!=actual.state().sequence()||!digest.equals(actual.digest()))throw new IOException("unit historical state mismatch");return actual.state();
        }
        @Override public WriterContracts.Pin capturePin(ExactRef ref,int max)throws IOException {throw new IOException("not a pin unit");}
        @Override public void verifyPin(WriterContracts.Pin pin)throws IOException {throw new IOException("not a pin unit");}
        @Override public WriterContracts.Prepared preview(WriterContracts.Request request)throws IOException {throw new IOException("unit cannot preview");}
        @Override public WriterContracts.Receipt commit(WriterContracts.Prepared prepared)throws IOException {throw new IOException("unit cannot commit");}
        @Override public ExactRef persistedHead()throws IOException {throw new IOException("unit cannot persist");}
    }
    static Fixture fixture(Path root,CheckpointCommitVerifier.SaveReceiptVerifier saves)throws Exception {
        Files.createDirectories(root);
        var files=new NativeCheckpointFiles();var oldGame=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var newGame=new GameGeneration(124,new PythonOnlyUInt64(new BigInteger("9007199254740994")));
        var session=new SessionIdentity("test-machine-1",oldGame,"old-session");
        var before=DriverStateSnapshot.decodeComplete(bytes("""
            {"format_version":2,"pipe_name":"test-pipe","bridge_pid":123,"episode_character_id":29829,"episode_run_id":"episode-1",
            "command_history":[{"index":1,"command":"native-auto-run","ok":false,"result":{"status":"unknown","request_id":"old-unknown"}}],
            "last_checkpoint":null,"rollback_war_failure":null,"managed_restore_transaction":null,"succession_expectation":null,
            "succession_lifecycle":null,"campaign_goal":null,"rollback_war_failures":[]}
            """));
        int rawDate=org.xar.ck3.control.planning.campaigncadence.CampaignCalendar.dateToRaw("1066.1.1");
        byte[] state=bytes("""
            {"paused":true,"map_ready":true,"speed":3,"date_raw":240,"played_character":{"character_id":29829,"alive":true},
            "active_event":null,"pending_character_interaction":null,"one_life_terminal_reason":null,
            "active_wars":[],"player_armies":[],
            "diagnostics":{"bridge_pid":123,"connection_generation":1}}
            """.replace("\"date_raw\":240","\"date_raw\":"+rawDate));
        var transport=new NativeObservationPort.TransportSession("test-machine-1",oldGame,BigInteger.ONE,"old-session");
        byte[] packet=packet(state);var nativeFrame=new NativeObservationPort.ObservedFrame(transport,"native:1",BigInteger.ONE,new RawJson(state),packet,AT);
        ExactRef rawRef=files.createNew(root.resolve("original-native.bin"),packet).reference();
        ExactRef sourceRef=files.createNew(root.resolve("source.txt"),bytes("software source provenance")).reference();
        var source=new G2Source("test-machine-1",AT.toString(),"test-build",sourceRef);
        var facts=new DriverObservationFacts(before,0,0,transport,"native:1",BigInteger.ONE,DriverJson.sha256(state),BigInteger.ONE,1,
                source,DriverJson.object(bytes("{}"),65536),sourceRef);
        var known=new DriverSnapshotFacts.Known(before,new DriverSnapshotFacts.Stamp(0,0,oldGame,"episode-1",DriverJson.sha256(before.encode())),
                sourceRef,List.of(),DriverJson.object(bytes("{}"),65536),Optional.empty(),Optional.of(facts));
        var assembled=new DriverObservationAssembler().assemble(nativeFrame,facts,rawRef);
        var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,assembled,assembled.toString());
        ExactRef semanticRef=files.createNew(root.resolve("original-semantic.json"),DriverJson.encode(complete.semantic())).reference();
        ExactRef driverRef=files.createNew(root.resolve("before-driver.json"),before.encode()).reference();
        ExactRef stampRef=files.createNew(root.resolve("original-stamp.json"),NativeDriverStamp.encode(complete,known)).reference();
        var semantic=new SemanticEvidence(complete.identity(),semanticRef,rawRef,stampRef,driverRef,AT);
        var stateRef=new AtomicReference<>(before);
        var drivers=new DriverCheckpointStore(files,root.resolve("saved-driver.json"),"test-pipe",new DriverCheckpointStore.SnapshotSupplier(){
            public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work)throws IOException {
                synchronized(stateRef){return work.run(stateRef.get(),(expected,published)->{
                    if(!stateRef.compareAndSet(expected,published))throw new IOException("fixture actual Driver CAS drift");
                });}
            }
        });
        var save=files.createNew(root.resolve("xar_checkpoint.ck3"),bytes("physical temporary SAVE")).reference();
        var saveWitness=files.observe(Path.of(save.path())).orElseThrow();var anchor=drivers.persist("save-1",saveWitness,complete.identity(),"lineage-1");
        ExactRef ack=files.createNew(root.resolve("save-ack.json"),bytes("{\"ok\":true}")).reference();
        var pair=new CheckpointPair(saveWitness,anchor.driver(),complete.identity(),"lineage-1",anchor.historyIndex(),"save-1",ack,AT);
        var cycleState=StrictJson.object();cycleState.put("schema","xar.java-ordinary-cycle-state/v1");cycleState.set("session",OrdinaryCycleTransitions.sessionToJson(session));
        cycleState.put("basis_cycles",0);cycleState.put("completed_cycles",0);cycleState.putNull("head");cycleState.putNull("pending_receipt");cycleState.putNull("retained_legacy_pending_digest");
        var proof=new CompletedCycleProof(0,semantic,ContinuityJson.digest(cycleState));

        var headRow=StrictJson.object();headRow.put("schema","root.ck3.continuity-window/v1");headRow.put("machine_id","test-machine-1");
        headRow.put("sequence",0);headRow.put("window_id",1);headRow.put("start_date_raw",rawDate-240);headRow.put("target_date_raw",rawDate+240);headRow.put("target_days",20);
        headRow.put("status","running");headRow.put("last_settled_cycles",0);headRow.put("last_settled_date_raw",rawDate);headRow.put("NEXT",1);
        var same=new Scope(root.resolve("unit.lock"),ContinuityState.fromJson(headRow,"test-machine-1"));
        var verifier=new CheckpointCommitVerifier(files,drivers,(borrowed,owner,actual)->SEMANTIC_DIGEST,root.resolve("unit.lock"),
                borrowed->{if(borrowed!=same)throw new IOException("foreign unit scope");},saves);
        Path materialRoot=root.resolve("saved-material");Files.createDirectories(materialRoot.resolve("checkpoints"));
        var store=new SavedAttachmentSourceStore(files,drivers,verifier,()->same,materialRoot,
                (borrowed,owner,actual)->cycleAuthority(owner,actual),(borrowed,owner,actual,captured)->cycleAuthority(owner,actual));
        return new Fixture(files,drivers,pair,stateRef.get(),proof,session,same,verifier,store,files.read(pair.driver(),DriverCheckpointStore.MAX_DRIVER_BYTES));
    }
    static String cycleAuthority(SessionIdentity owner,CompletedCycleProof proof){
        var row=StrictJson.object();row.put("cycle_state_digest",proof.cycleStateDigest());row.put("semantic_digest",SEMANTIC_DIGEST);
        row.set("session",OrdinaryCycleTransitions.sessionToJson(owner));return ContinuityJson.digest(row);
    }
    private static byte[] bytes(String s){return s.getBytes(StandardCharsets.UTF_8);}
    private static byte[] packet(byte[] state){byte[] json=bytes("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"native:1\",\"revision\":1,\"state\":"+new String(state,StandardCharsets.UTF_8)+"}");return ByteBuffer.allocate(json.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();}
}
