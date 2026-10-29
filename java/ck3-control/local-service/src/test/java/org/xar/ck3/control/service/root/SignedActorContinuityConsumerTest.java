package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.presentation.PresentationRequest;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionConversionRead;
import org.xar.ck3.control.recovery.*;

/** Java signed-actor correction. Controlled values are not Python public parity or negative-ID Game evidence. */
final class SignedActorContinuityConsumerTest {
    private static final BigInteger MAX_U64=new BigInteger("18446744073709551615");
    private static final String EPISODE="signed-actor-controlled-episode";
    private static final GameGeneration GAME=new GameGeneration(7,new PythonOnlyUInt64(BigInteger.ONE));
    @Test void actualConsumerConstructorsAndSerdeKeepSignedIntegersWithoutAliases(){
        for(int actor:new int[]{Integer.MIN_VALUE,-2147483647,-2,0,Integer.MAX_VALUE}) {
            var window=new EpisodeWindow.Identity("software-signed-actor",GAME,"actual-session",EPISODE,0,actor,100);
            assertEquals(window,EpisodeWindow.Identity.fromJson(window.toJson()));assertEquals(BigInteger.valueOf(actor),window.toJson().get("actor_id").bigIntegerValue());
            var saved=new SavedFrame("native:8",7,8,100,actor,EPISODE);assertEquals(saved,SavedFrame.fromJson(saved.toJson()));
            var first=new SavedContinuityAttachment.FirstBasis.Frame("first-snapshot",MAX_U64,MAX_U64,100,actor,EPISODE);assertEquals(first,SavedContinuityAttachment.FirstBasis.Frame.fromJson(first.toJson()));
            assertEquals(MAX_U64.toString(),first.toJson().get("native_revision").textValue());assertEquals(BigInteger.valueOf(actor),first.toJson().get("actor_character_id").bigIntegerValue());
            var request=new PresentationRequest.Frame("snapshot","7","8",actor,100);assertEquals(request,PresentationRequest.Frame.fromJson(request.toJson()));
            var religion=new ReligionConversionRead.BoundFrame(PlayerReligionContext.Build.CROZIER3,BigInteger.valueOf(100),BigInteger.valueOf(actor));assertEquals(BigInteger.valueOf(actor),religion.player());
        }
    }
    @Test void missingMarkerOverflowBooleanFloatStringAndNullRemainInvalid(){
        assertThrows(IllegalArgumentException.class,()->new EpisodeWindow.Identity("software-signed-actor",GAME,"session",EPISODE,0,-1,100));
        assertThrows(IllegalArgumentException.class,()->new EpisodeWindow.Identity("software-signed-actor",GAME,"session",EPISODE,0,2147483648L,100));
        assertThrows(IllegalArgumentException.class,()->new SavedContinuityAttachment.FirstBasis.Frame("snapshot",MAX_U64,MAX_U64,100,-1,EPISODE));
        assertThrows(IllegalArgumentException.class,()->new PresentationRequest.Frame("snapshot","7","8",-1,100));
        assertThrows(IllegalArgumentException.class,()->new ReligionConversionRead.BoundFrame(PlayerReligionContext.Build.CROZIER3,BigInteger.ONE,BigInteger.valueOf(2147483648L)));
        var identity=new EpisodeWindow.Identity("software-signed-actor",GAME,"session",EPISODE,0,-2,100);
        for(JsonNode bad:List.of(StrictJson.object().put("v",true).get("v"),StrictJson.object().put("v",-2.0).get("v"),StrictJson.object().put("v","-2").get("v"),com.fasterxml.jackson.databind.node.NullNode.instance)) {
            ObjectNode row=identity.toJson();row.set("actor_id",bad);assertThrows(IllegalArgumentException.class,()->EpisodeWindow.Identity.fromJson(row));
        }
        assertThrows(IllegalArgumentException.class,()->new SavedContinuityAttachment.FirstBasis.Frame("snapshot",MAX_U64.add(BigInteger.ONE),MAX_U64,100,-2,EPISODE));
        assertThrows(IllegalArgumentException.class,()->new EpisodeWindow.Identity("software-signed-actor",GAME,"session",EPISODE,-1,-2,100));
    }
    @Test void originalReducerPreservesSignedActorAndExistingOpaqueUnknown(){
        ObjectNode detail=StrictJson.object().put("machine_id","software-signed-actor").put("evidence_id","controlled-in-memory-source").put("source","controlled-original-source").put("reason","controlled-repair").put("completed_cycles",0);
        detail.set("game",GAME.toJson());ObjectNode frame=detail.putObject("frame");frame.put("date_raw",100).put("actor_character_id",Integer.MIN_VALUE).put("episode_run_id",EPISODE).put("snapshot_id","original-frame").put("revision",7).put("native_revision",8);
        ObjectNode initial=OriginalWindowReducer.reduce(null,"repair_required",detail);ObjectNode unknown=StrictJson.object().put("do_not_replay",true);initial.set("opaque_unknown",unknown);
        ObjectNode attached=OriginalWindowReducer.reduce(initial,"attach_verified",detail);assertEquals(BigInteger.valueOf(Integer.MIN_VALUE),attached.get("latest_binding").get("actor_character_id").bigIntegerValue());assertEquals(unknown,attached.get("opaque_unknown"));
        ((ObjectNode)detail.get("frame")).put("actor_character_id",-1);assertThrows(IllegalArgumentException.class,()->OriginalWindowReducer.reduce(initial,"attach_verified",detail));
    }
    @Test void coldReaderAcceptsSignedFactsButStillRequiresTheRealPrerequisiteProvider()throws Exception {
        for(int actor:new int[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE}) {
            AtomicBoolean reached=new AtomicBoolean();RecoveryPreview result=ClosedFailureRecoveryReducer.preview(input(actor),(in,digest)->{reached.set(true);return new RecoveryPrerequisiteVerifier.Unavailable("actual closed-prefix/original-SDK authority intentionally not supplied");});
            assertTrue(reached.get(),"signed actor must pass the pure input boundary");assertInstanceOf(RecoveryPreview.Unavailable.class,result,"data does not mint restoration authority");
        }
        AtomicBoolean reached=new AtomicBoolean();assertInstanceOf(RecoveryPreview.Rejected.class,ClosedFailureRecoveryReducer.preview(input(-1),(in,digest)->{reached.set(true);return new RecoveryPrerequisiteVerifier.Unavailable("must not reach");}));assertFalse(reached.get());
    }
    private static ClosedFailureRecoveryInput input(int actor)throws Exception {
        Map<String,ObjectNode> docs=new HashMap<>();for(JsonNode source:manifest().get("recovery_inputs")){ExactRef ref=ExactRef.fromJson(source.get("ref"));docs.put(source.get("name").textValue(),(ObjectNode)NativeWire.parse(exact(ref)));}
        ObjectNode basis=docs.get("n46-prior-basis.actual.json"),raw=docs.get("n46-raw-state.actual.json"),governance=docs.get("n46-raw-governance.actual.json");
        ((ObjectNode)basis.get("frame")).put("actor_character_id",actor);((ObjectNode)basis.get("campaign_goal_anchor")).put("current_character_id",actor);
        ((ObjectNode)raw.get("before")).put("actor_character_id",actor);((ObjectNode)raw.get("actual_saved_checkpoint")).put("episode_character_id",actor);
        ((ObjectNode)raw.get("pending_cycle").get("before")).put("actor_character_id",actor);((ObjectNode)governance.get("pending_cycle").get("before")).put("actor_character_id",actor);
        RecoveryEvidence saved=software("n46-prior-basis.actual.json",basis);
        docs.get("n46-prior-qualification.actual.json").set("basis_ref",saved.reference().toJson());
        docs.get("n46-full-failure11543.actual.json").put("original_response",software("n46-auto-failure11558.actual.json",docs.get("n46-auto-failure11558.actual.json")).reference().path());
        ObjectNode refs=(ObjectNode)basis.get("refs");return new ClosedFailureRecoveryInput(basis.get("machine_id").textValue(),"2026-10-24T05:00:00Z",
                software("n46-head240.actual.json",docs.get("n46-head240.actual.json")),saved,software("n46-prior-qualification.actual.json",docs.get("n46-prior-qualification.actual.json")),
                software("n46-full-request11543.actual.json",docs.get("n46-full-request11543.actual.json")),software("n46-full-failure11543.actual.json",docs.get("n46-full-failure11543.actual.json")),
                software("n46-auto-request11558.actual.json",docs.get("n46-auto-request11558.actual.json")),software("n46-auto-failure11558.actual.json",docs.get("n46-auto-failure11558.actual.json")),
                software("n46-raw-state.actual.json",raw),software("n46-raw-governance.actual.json",governance),software("n46-next11559.actual.json",docs.get("n46-next11559.actual.json")),
                ExactRef.fromJson(refs.get("driver")),FileStatIdentity.fromJson(basis.get("driver_identity"),FileStatIdentity.SCHEMA),ExactRef.fromJson(refs.get("save")),FileStatIdentity.fromJson(basis.get("save_identity"),FileStatIdentity.SCHEMA));
    }
    private static RecoveryEvidence software(String name,ObjectNode value){byte[] bytes=ContinuityJson.canonical(value,ContinuityJson.TRANSPORT_MAX_BYTES);return new RecoveryEvidence(new ExactRef("/software-signed-actor/"+name,bytes.length,RecoveryEvidence.sha256(bytes)),bytes);}
    private static byte[] exact(ExactRef ref)throws Exception{byte[] bytes=Files.readAllBytes(Path.of(ref.path()));assertEquals(ref.bytes(),bytes.length);assertEquals(ref.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));return bytes;}
    private static JsonNode manifest()throws Exception{String path=System.getProperty("xar.signedActor.sourceMap"),sha=System.getProperty("xar.signedActor.sourceMapSha256");if(path==null||sha==null)throw new IllegalStateException("NOT_RUN: exact signed actor source-map properties are required");byte[] bytes=Files.readAllBytes(Path.of(path));assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));return NativeWire.parse(bytes);}
}
