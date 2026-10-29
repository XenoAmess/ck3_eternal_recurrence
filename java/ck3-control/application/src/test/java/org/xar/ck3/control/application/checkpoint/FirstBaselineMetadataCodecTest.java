package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Pure archived DATA contract only; this fixture cannot mint private material, physical permission or a Root. */
final class FirstBaselineMetadataCodecTest {
    private static final String MACHINE="baseline-metadata-data-fixture";
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private record Data(ObjectNode metadata,EpisodeWindow.CommittedBaseline baseline,SemanticEvidence semantic){}
    private static ExactRef ref(String name,long bytes,char digest){
        return new ExactRef(Path.of("fixture-data-"+name).toAbsolutePath().toString(),bytes,String.valueOf(digest).repeat(64));
    }
    private static WriterContracts.Pin pin(String name){
        var ref=ref(name,7,'e');
        return new WriterContracts.Pin(ref,new WriterContracts.FileIdentity("1","9007199254740993","134000000000000001",AT.toString(),ref.bytes()));
    }
    private static ContinuityState projected(ContinuityState state,long sequence,String event){
        var row=state.toJson();row.put("sequence",sequence);row.put("last_event_identity",event);return ContinuityState.fromJson(row,MACHINE);
    }
    private static Data data(){
        var oldGame=new GameGeneration(31,new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var newGame=new GameGeneration(32,new PythonOnlyUInt64(new BigInteger("134000000000000002")));
        var old=new EpisodeWindow.Identity(MACHINE,oldGame,"old-session","old-episode",0,28,480);
        var next=new EpisodeWindow.Identity(MACHINE,newGame,"next-session","next-episode",1,29,240);
        var row=StrictJson.object();row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id",MACHINE);row.put("sequence",1);
        row.put("window_id",1);row.put("status","running");row.put("target_days",20);row.put("start_date_raw",480);row.put("target_date_raw",960);
        row.put("last_settled_cycles",1);row.put("last_settled_date_raw",480);row.put("retained_original","q".repeat(90000));row.set("game_binding",oldGame.toJson());
        var begin=new EpisodeWindow.Begin("data-begin",old,next,1,2,"data-parent",1,"a".repeat(64),ref("lifecycle",7,'a'),ref("adopted-driver",7,'b'),List.of());
        var waiting=projected(EpisodeWindow.reduce(ContinuityState.fromJson(row,MACHINE),begin.request()),2,begin.request().identity());
        var committedBegin=new EpisodeWindow.CommittedBegin(begin,2,begin.request().identity(),ContinuityJson.digest(waiting.toJson()),pin("begin"));
        var identity=new FileStatIdentity(BigInteger.valueOf(7),"9007199254740993","1792800000000000001");
        var frame=new ObservationIdentity(MACHINE,newGame,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29),StrictJson.UINT64_MAX,BigInteger.valueOf(240)),
                "actual-data-snapshot",StrictJson.UINT64_MAX,"next-episode"),1);
        var pair=new CheckpointPair(new CheckpointPair.FileWitness(ref("save",7,'c'),identity),
                new CheckpointPair.FileWitness(ref("saved-driver",7,'d'),identity),frame,"data-lineage",2,"data-save",ref("ack",7,'a'),AT);
        byte[] pairRaw=CheckpointPairCodec.encode(pair);
        var pairRef=new ExactRef(ref("pair",7,'a').path(),pairRaw.length,DriverCheckpointStore.sha256(pairRaw));
        var baseline=new EpisodeWindow.Baseline(committedBegin,pair.saveActionId(),pairRef,pairRef.sha256(),ref("receipt",7,'b'),"f".repeat(64),next);
        var active=projected(EpisodeWindow.reduce(waiting,baseline.request()),3,baseline.request().identity());
        var committed=new EpisodeWindow.CommittedBaseline(baseline,3,baseline.request().identity(),ContinuityJson.digest(active.toJson()),pin("baseline"));
        var semantic=new SemanticEvidence(frame,ref("semantic",7,'a'),ref("native-packet",7,'b'),ref("driver-stamp",7,'c'),ref("archived-saved-driver",7,'d'),AT);
        var metadata=StrictJson.object();metadata.put("schema",SavedFirstCheckpointMaterialStore.BASELINED_SCHEMA);metadata.set("pair",StrictJson.parse(pairRaw));
        metadata.set("first_material_witness",CheckpointPairCodec.fileWitnessToJson(new CheckpointPair.FileWitness(ref("first-material",7,'a'),identity)));
        metadata.set("committed_baseline",committed.toJson());metadata.set("saved_semantic",OrdinaryCycleTransitions.semanticToJson(semantic));
        metadata.put("saved_semantic_verifier_sha256","9".repeat(64));metadata.set("original_writer_head",active.toJson());
        return new Data(metadata,committed,semantic);
    }
    private static void verify(ObjectNode row,Data expected){
        SavedFirstCheckpointMaterialStore.verifyArchivedBaselineMetadata(StrictJson.canonical(row,1048576),expected.baseline,expected.semantic);
    }
    @Test void sharedPureDecoderPreservesFullUint64PairAndOriginalWitnessInRoundTrip(){
        var f=data();assertTrue(StrictJson.canonical(f.metadata,1048576).length>65536);assertDoesNotThrow(()->verify(f.metadata,f));
        assertDoesNotThrow(()->SavedFirstCheckpointMaterialStore.verifyArchivedBaselineMetadata(
                StrictJson.canonical(StrictJson.parse(StrictJson.canonical(f.metadata,1048576),1048576),1048576),f.baseline,f.semantic));
        assertEquals("18446744073709551615",f.metadata.at("/pair/frame/frame/revision").textValue());
        assertEquals("9007199254740993",f.metadata.at("/first_material_witness/identity/file_id").textValue());
    }
    @Test void strictSingleFieldTableRejectsMissingNullWrongSchemaAndInventedPermissionFields(){
        var f=data();
        for(String key:List.of("schema","pair","first_material_witness","committed_baseline","saved_semantic","saved_semantic_verifier_sha256","original_writer_head")){
            var missing=f.metadata.deepCopy();missing.remove(key);assertThrows(Exception.class,()->verify(missing,f),key);
            var nul=f.metadata.deepCopy();nul.putNull(key);assertThrows(Exception.class,()->verify(nul,f),key);
        }
        var wrong=f.metadata.deepCopy();wrong.put("schema",SavedFirstCheckpointMaterialStore.SCHEMA);assertThrows(Exception.class,()->verify(wrong,f));
        var extra=f.metadata.deepCopy();extra.put("qualified",true);assertThrows(Exception.class,()->verify(extra,f));
        var numeric=f.metadata.deepCopy();((ObjectNode)numeric.at("/first_material_witness/identity")).put("file_id",9007199254740993L);
        assertThrows(Exception.class,()->verify(numeric,f));
    }
    @Test void pairHeadAndSavedDriverBindingsCannotBeChangedWhileRetainingTheExpectedBaseline(){
        var f=data();
        var pair=f.metadata.deepCopy();((ObjectNode)pair.get("pair")).put("save_action_id","other-save");assertThrows(Exception.class,()->verify(pair,f));
        var head=f.metadata.deepCopy();((ObjectNode)head.get("original_writer_head")).put("last_settled_cycles",1);assertThrows(Exception.class,()->verify(head,f));
        var driver=f.metadata.deepCopy();((ObjectNode)driver.at("/saved_semantic/original_driver")).put("sha256","0".repeat(64));
        assertThrows(Exception.class,()->verify(driver,f));
        var numeric=f.metadata.deepCopy();((ObjectNode)numeric.at("/pair/frame/frame")).put("revision",9007199254740993L);
        assertThrows(Exception.class,()->verify(numeric,f));
    }
    @Test void anExpectedBaselineOrSemanticFromAnotherOriginalCannotBeAccepted(){
        var f=data();var changed=new EpisodeWindow.CommittedBaseline(f.baseline.baseline(),f.baseline.sequence(),f.baseline.eventIdentity(),"0".repeat(64),f.baseline.eventPin());
        assertThrows(Exception.class,()->SavedFirstCheckpointMaterialStore.verifyArchivedBaselineMetadata(StrictJson.canonical(f.metadata,1048576),changed,f.semantic));
        var other=new SemanticEvidence(f.semantic.frame(),f.semantic.semantic(),f.semantic.originalNativePacket(),f.semantic.driverStamp(),
                f.semantic.originalDriver(),f.semantic.observedAt().plusSeconds(1));
        assertThrows(Exception.class,()->SavedFirstCheckpointMaterialStore.verifyArchivedBaselineMetadata(StrictJson.canonical(f.metadata,1048576),f.baseline,other));
    }
}
