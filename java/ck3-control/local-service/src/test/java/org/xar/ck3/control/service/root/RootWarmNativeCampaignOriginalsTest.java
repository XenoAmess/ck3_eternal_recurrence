package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real physical archive/lock + sole manifest/stamp/assembler producers -> actual warm DATA consumer. No Managed Game. */
final class RootWarmNativeCampaignOriginalsTest {
    @TempDir Path temporary;
    private static final String MACHINE="xenoamess-full-tower-eb9d2c1186";
    private static final int LIMIT=1<<20;
    private static final String STATE="""
            {"paused":true,"map_ready":true,"speed":3,"date_raw":53144328,
             "played_character":{"character_id":73,"alive":true},"active_event":null,
             "pending_character_interaction":null,"active_wars":[],"player_armies":[],
             "diagnostics":{"bridge_pid":42,"connection_generation":5}}
            """;
    private record Originals(DriverStateSnapshot.Complete driver,SessionPorts.SessionIdentity owner,
            SessionPorts.SemanticEvidence evidence,ExactRef manifest) { }

    @Test void soleProducerArchiveRoundTripFeedsTheActualWarmSavedOriginalsConsumer()throws Exception {
        var archive=archive();archive.writer().locked(same->{
            var original=originals(same,archive);String head=same.head().digest();
            var decoded=DriverStateSnapshot.decodeComplete(original.driver().encode());
            assertArrayEquals(original.driver().encode(),decoded.encode());
            assertInstanceOf(DriverStateSnapshot.NullValue.class,decoded.successionLifecycle());
            RootRestoreMaterials.requireNativeCampaignSavedOriginals(same,archive,original.owner(),original.evidence(),decoded);
            assertEquals(head,same.head().digest());return null;
        });
    }
    @Test void originalMissingAndBoundLifecyclesCannotBorrowTheSavedNativeProjection()throws Exception {
        var archive=archive();archive.writer().locked(same->{
            var original=originals(same,archive);String head=same.head().digest();
            for(DriverStateSnapshot.Slot slot:List.of(new DriverStateSnapshot.Missing(),
                    new DriverStateSnapshot.Value("{\"lifecycle\":\"rogue_one_life\"}".getBytes(StandardCharsets.UTF_8)))) {
                var d=original.driver();var changed=new DriverStateSnapshot.Complete(d.session(),d.commandHistory(),d.lastCheckpoint(),
                        d.rollbackWarFailure(),d.managedRestoreTransaction(),d.successionExpectation(),slot,d.campaignGoal(),d.rollbackWarFailures());
                assertThrows(IllegalArgumentException.class,()->RootRestoreMaterials.requireNativeCampaignSavedOriginals(
                        same,archive,original.owner(),original.evidence(),changed));
            }
            assertEquals(head,same.head().digest());return null;
        });
    }
    @Test void changedObservationVersionAndWrongSavedOwnerCannotPassByKeepingTheSameNullDriver()throws Exception {
        var archive=archive();archive.writer().locked(same->{
            var original=originals(same,archive);var e=original.evidence();var f=e.frame();
            var oldFrame=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity(f.machineId(),f.game(),f.frame(),
                    DriverObservationAssembler.CANONICAL_OBSERVATION_VERSION);
            var old=new SessionPorts.SemanticEvidence(oldFrame,e.semantic(),e.originalNativePacket(),e.driverStamp(),e.originalDriver(),e.observedAt());
            assertThrows(IllegalArgumentException.class,()->RootRestoreMaterials.requireNativeCampaignSavedOriginals(
                    same,archive,original.owner(),old,original.driver()));
            var foreign=new SessionPorts.SessionIdentity(MACHINE,original.owner().game(),"foreign-saved-session");
            assertThrows(IOException.class,()->RootRestoreMaterials.requireNativeCampaignSavedOriginals(
                    same,archive,foreign,e,original.driver()));return null;
        });
    }
    @Test void sameBytesReplacedManifestFileIdIsRejectedByTheOriginalWriterPin()throws Exception {
        var archive=archive();archive.writer().locked(same->{
            var original=originals(same,archive);var pin=same.capturePin(original.manifest(),LIMIT);
            Path path=Path.of(original.manifest().path()),copy=temporary.resolve("same-bytes-new-manifest.json");
            Files.write(copy,Files.readAllBytes(path));Files.move(copy,path,java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            assertThrows(IOException.class,()->same.verifyPin(pin));return null;
        });
    }
    private Originals originals(ContinuityStorePort.Session same,NativeOutcomeArchive archive)throws IOException {
        var game=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("134373229053165471")));
        var session=new NativeObservationPort.TransportSession(MACHINE,game,BigInteger.valueOf(5),"original-saved-session");
        var nil=new DriverStateSnapshot.NullValue();
        var driver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("original-saved-pipe",42,BigInteger.valueOf(73),"saved-episode"),
                List.of(),nil,nil,nil,nil,nil,nil,nil);
        var driverRef=archive.preserveArtifact(same,driver.encode(),LIMIT);
        var stamp=new DriverSnapshotFacts.Stamp(3,7,game,driver.session().episodeRunId(),DriverJson.sha256(driver.encode()));
        var auxiliary=new OpportunityJson.Obj(Map.of("episode_projection",new OpportunityJson.Text("native_campaign")));
        var known=new DriverSnapshotFacts.Known(driver,stamp,driverRef,List.of(),auxiliary,Optional.empty(),Optional.empty());
        byte[] state=STATE.strip().getBytes(StandardCharsets.UTF_8);
        byte[] message=("{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"saved-frame\",\"revision\":9,\"state\":"
                +new String(state,StandardCharsets.UTF_8)+"}").getBytes(StandardCharsets.UTF_8);
        byte[] packet=ByteBuffer.allocate(message.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(message.length).put(message).array();
        var actual=new NativeObservationPort.ObservedFrame(session,"saved-frame",BigInteger.valueOf(9),new RawJson(state),packet,
                Instant.parse("2026-10-25T01:30:00Z"));
        ExactRef sourceRef=archive.preserveArtifact(same,"software-only-source".getBytes(StandardCharsets.UTF_8),LIMIT);
        var source=new G2Source(MACHINE,"2026-10-25T01:30:00Z","software-only",sourceRef);
        var manifest=DriverObservationEvidenceReader.encode(known,actual,BigInteger.TWO,
                DriverObservationAssembler.NATIVE_CAMPAIGN_OBSERVATION_VERSION,source,auxiliary,driverRef);
        ExactRef manifestRef=archive.preserveArtifact(same,manifest.bytes(),LIMIT);
        var facts=DriverObservationEvidenceReader.decode(manifestRef,manifest,RawJson.fullMaterial(driver.encode()),actual);
        ExactRef nativeRef=archive.preserveArtifact(same,packet,LIMIT);
        var complete=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(actual,facts,nativeRef));
        var observed=new DriverSnapshotFacts.Known(driver,stamp,driverRef,List.of(),auxiliary,Optional.empty(),Optional.of(facts));
        ExactRef semantic=archive.preserveArtifact(same,DriverJson.encode(complete.semantic()),LIMIT);
        ExactRef stampRef=archive.preserveArtifact(same,NativeDriverStamp.encode(complete,observed),LIMIT);
        var evidence=new SessionPorts.SemanticEvidence(complete.identity(),semantic,nativeRef,stampRef,driverRef,actual.observedAt());
        return new Originals(driver,new SessionPorts.SessionIdentity(MACHINE,game,session.sessionId()),evidence,manifestRef);
    }
    private NativeOutcomeArchive archive()throws IOException {
        Path root=temporary.resolve("writer");Files.createDirectory(root);
        Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");
        var state=StrictJson.object();state.put("schema","root.ck3.continuity-window/v1");state.put("machine_id",MACHINE);
        state.put("sequence",0);state.put("window_id",1);state.put("status","running");state.put("target_days",1);
        state.put("start_date_raw",0);state.put("target_date_raw",24);state.put("last_settled_date_raw",0);state.put("last_settled_cycles",0);
        byte[] bytes=ContinuityJson.canonical(state);Files.write(snapshot,bytes);Files.write(anchor,bytes);
        Path lock=root.resolve("ROOT-CONTINUITY-WINDOW.lock");Files.createFile(lock);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        var files=new NativeCheckpointFiles();ExactRef anchored=files.observe(anchor).orElseThrow().reference();
        Path source=root.resolve("reviewed-source.txt");Files.writeString(source,"software-only warm archive regression");
        var layout=new WriterContracts.Layout(snapshot,anchored,MACHINE);Path artifactRoot=root.resolve("artifacts");Files.createDirectory(artifactRoot);
        var storage=StorageWriteGuardTestSupport.create(layout);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifactRoot,lock,LIMIT),storage);
        var writer=new ContinuityWriter(layout,List.of(files.observe(source).orElseThrow().reference()),new WriterContracts.TransitionAuthority(){
            @Override public String revalidate(ContinuityState predecessor,WriterContracts.Request request){return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState predecessor,WriterContracts.Request request){return OriginalWindowReducer.reduce(predecessor,request);}
        },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(artifacts),Optional.empty()),storage);
        return new NativeOutcomeArchive(artifacts,writer);
    }
}
