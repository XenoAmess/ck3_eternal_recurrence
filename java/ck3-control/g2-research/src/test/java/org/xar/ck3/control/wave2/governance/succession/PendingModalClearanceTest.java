package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.GameIdentity;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.Session;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;

/** Software-only original native decoder -> complete SEM capture -> sole modal comparator.
 * Synthetic DATA deliberately cannot establish actual private Root/writer/loaded-source qualification.
 */
final class PendingModalClearanceTest {
    private static final int ACTOR=31254, DATE=53144328;

    @Test void newCapturedPlayerDecisionCanClearOnlyTheOldModalWithoutClaimingFinalUi() {
        BoundFrame before=binding("initial",1,31,"null","null",Optional.empty());
        Query initial=query(before,"initial",1,10,true,true);
        Close close=close(before,"close",11,true);
        BoundFrame event=binding("new-event",2,32,"{\"instance_id\":42,\"definition_id\":\"health.1015\"}","null",Optional.empty());
        Query later=query(event,"later",2,12,false,false);
        assertEquals(ClearanceState.FRAME_CHANGED,compareClearance(initial,close,later).state());
        var captured=capture(later,semantic(event));
        var result=PendingModalClearance.inspect(initial,close,List.of(captured));
        assertEquals(ClearanceState.CLEARED_OBSERVED,result.state());
        assertEquals(later,result.queries().getFirst().query());
        assertFalse(result.finalUiProven());assertFalse(result.dayAdvanceProven());
        assertFalse(result.naturalDeathProven());assertFalse(result.savedContinuationProven());assertFalse(result.submissionAuthorized());
        assertFalse(close.replayAuthorized());
        JsonNode wire=StrictJson.parse(result.originalProof());
        assertTrue(wire.get("modal_clear_observed").booleanValue());assertFalse(wire.get("final_ui_qualified").booleanValue());
        assertEquals(captured.fullSemantic(),ExactRef.fromJson(wire.get("subsequent_queries").get(0).get("full_semantic")));
        // The same retained native/SEM originals replay through the actual decoders, not a new proof decoder.
        Query replay=query(event,"later",2,12,false,false);
        assertEquals(ClearanceState.CLEARED_OBSERVED,PendingModalClearance.inspect(initial,close,List.of(capture(replay,semantic(event)))).state());
    }

    @Test void sceneDifferenceDoesNotPermitAnotherGameEpisodeDateActorTerminalOrRegressedVersion() {
        BoundFrame before=binding("initial",4,31,"null","null",Optional.empty());
        Query initial=query(before,"initial",1,10,true,true);Close close=close(before,"close",11,true);
        var normal=binding("later",5,32,"{\"instance_id\":42}","null",Optional.empty());var s=normal.session();var f=normal.frame();
        Session otherGame=new Session(s.machineId(),s.sessionId(),new GameIdentity(1234,"134056180000000002"),s.episodeRunId(),s.connectionGeneration(),s.executable(),s.executableFileId(),s.executableMtimeNs());
        Session otherRun=new Session(s.machineId(),s.sessionId(),s.game(),"other-run",s.connectionGeneration(),s.executable(),s.executableFileId(),s.executableMtimeNs());
        Session otherConnection=new Session(s.machineId(),s.sessionId(),s.game(),s.episodeRunId(),"3",s.executable(),s.executableFileId(),s.executableMtimeNs());
        List<BoundFrame> changed=List.of(new BoundFrame(otherGame,f,normal.scene()),new BoundFrame(otherRun,f,normal.scene()),
                new BoundFrame(otherConnection,f,normal.scene()),
                new BoundFrame(s,new Frame("day",f.publicRevision(),f.nativeRevision(),DATE+1,ACTOR,0),normal.scene()),
                new BoundFrame(s,new Frame("actor",f.publicRevision(),f.nativeRevision(),DATE,ACTOR+1,0),normal.scene()),
                new BoundFrame(s,new Frame("regressed",BigInteger.valueOf(3),f.nativeRevision(),DATE,ACTOR,0),normal.scene()),
                new BoundFrame(s,f,new Scene(normal.scene().activeEventJson(),"null",Optional.of("played_character_changed"))));
        for(BoundFrame changedFrame:changed){Query next=query(changedFrame,"later",2,12,false,false);
            assertEquals(ClearanceState.FRAME_CHANGED,PendingModalClearance.inspect(initial,close,List.of(capture(next,semantic(changedFrame)))).state());}
        Close changedPreparation=close(normal,"close",11,true);
        Query next=query(normal,"later",2,12,false,false);
        assertEquals(ClearanceState.FRAME_CHANGED,PendingModalClearance.inspect(initial,changedPreparation,List.of(capture(next,semantic(normal)))).state());
    }

    @Test void unknownAndAckAloneDoNotSettleAndBothModalPredicatesRemainNecessary() {
        BoundFrame before=binding("initial",1,31,"null","null",Optional.empty());Query initial=query(before,"initial",1,10,true,true);
        BoundFrame after=binding("after",2,32,"null","{\"instance_id\":91}",Optional.empty());
        Query clear=query(after,"clear",2,12,false,false);
        assertEquals(ClearanceState.SUBMISSION_UNKNOWN,PendingModalClearance.inspect(initial,close(before,"close",11,false),List.of(capture(clear,semantic(after)))).state());
        assertEquals(ClearanceState.OBSERVATION_REGRESSED,PendingModalClearance.inspect(initial,close(before,"close",9,true),List.of(capture(clear,semantic(after)))).state());
        for(boolean[] state:new boolean[][]{{true,false},{false,true},{true,true}}){
            Query blocked=query(after,"blocked",2,12,state[0],state[1]);
            assertEquals(ClearanceState.MODAL_OR_PREDICATES_UNCLEARED,PendingModalClearance.inspect(initial,close(before,"close",11,true),List.of(capture(blocked,semantic(after)))).state());
        }
        assertThrows(IllegalArgumentException.class,()->PendingModalClearance.inspect(initial,close(before,"close",11,true),List.of()));
    }

    @Test void everyIndependentReadMustBeAfterTheAckAndTheWholeRetainedSequence() {
        BoundFrame before=binding("initial",1,31,"null","null",Optional.empty());Query initial=query(before,"initial",1,10,true,true);Close close=close(before,"close",11,true);
        BoundFrame after=binding("after",2,32,"{\"instance_id\":42}","null",Optional.empty());
        Query first=query(after,"one",2,12,true,true);Query second=query(after,"two",3,13,false,false);
        assertEquals(ClearanceState.CLEARED_OBSERVED,PendingModalClearance.inspect(initial,close,List.of(capture(first,semantic(after)),capture(second,semantic(after)))).state());
        Query sameSequence=query(after,"two",2,13,false,false);Query staleAck=query(after,"two",3,11,false,false);Query sameRequest=query(after,"one",3,13,false,false);
        for(Query stale:List.of(sameSequence,staleAck,sameRequest))
            assertEquals(ClearanceState.POST_QUERY_NOT_NEWER,PendingModalClearance.inspect(initial,close,List.of(capture(first,semantic(after)),capture(stale,semantic(after)))).state());
    }

    @Test void completeSemanticAboveOneMiBIsRetainedWhileWrongTypesNullAndSceneMismatchAreRejected() {
        BoundFrame after=binding("after",2,32,"{\"instance_id\":42}","null",Optional.empty());Query query=query(after,"later",2,12,false,false);
        ObjectNode full=semantic(after);full.putArray("history").add("x".repeat(1_048_577));
        byte[] original=FullJsonTree.encode(full,FullJsonTree.MAXIMUM_BYTES);ExactRef fullRef=ref("full-semantic",original);
        var actual=PendingModalClearance.capture(query,ref("read",new byte[]{1}),fullRef,ref("native",new byte[]{2}),original,java.time.Instant.parse("2026-10-24T08:00:00Z"));
        assertTrue(actual.fullSemantic().bytes()>NativeTimelineBlocker12004.MAX_BYTES);assertEquals(fullRef,actual.fullSemantic());
        byte[] tampered=original.clone();tampered[tampered.length-2]=' ';
        assertThrows(IllegalArgumentException.class,()->PendingModalClearance.capture(query,actual.actualRead(),fullRef,actual.actualNative(),tampered,actual.observedAtUtc()));
        for(String field:List.of("snapshot_id","revision","native_revision","date_raw","local_player_id","paused","map_ready","active_event","pending_character_interaction","played_character")){
            ObjectNode missing=semantic(after);missing.remove(field);assertThrows(IllegalArgumentException.class,()->capture(query,missing));
            ObjectNode nil=semantic(after);nil.putNull(field);
            if(field.equals("pending_character_interaction"))assertDoesNotThrow(()->capture(query,nil));
            else assertThrows(IllegalArgumentException.class,()->capture(query,nil));
        }
        for(JsonNode invalid:List.of(StrictJson.object().booleanNode(true),StrictJson.object().numberNode(32.0),StrictJson.object().textNode("32"))){
            ObjectNode wrong=semantic(after);wrong.set("native_revision",invalid);assertThrows(IllegalArgumentException.class,()->capture(query,wrong));
        }
        ObjectNode differentScene=semantic(after);differentScene.putObject("active_event").put("instance_id",43);
        assertThrows(IllegalArgumentException.class,()->capture(query,differentScene));
        ObjectNode notPaused=semantic(after);notPaused.put("paused",false);assertThrows(IllegalArgumentException.class,()->capture(query,notPaused));
    }

    private static BoundFrame binding(String snapshot,long revision,long nativeRevision,String event,String interaction,Optional<String> terminal){
        Session session=new Session("synthetic-machine","fixture-session",new GameIdentity(1234,"134056180000000001"),"successor-run","2",
                new ExactRef("D:/fixtures/ck3.exe",101040248,NativePlayerHeirObservation12004.EXE_SHA256),"16888498602938861","1791307594040564100");
        return new BoundFrame(session,new Frame(snapshot,BigInteger.valueOf(revision),BigInteger.valueOf(nativeRevision),DATE,ACTOR,0),new Scene(event,interaction,terminal));
    }
    private static ObjectNode semantic(BoundFrame binding){
        var f=binding.frame();ObjectNode out=StrictJson.object().put("snapshot_id",f.snapshotId()).put("revision",f.publicRevision()).put("native_revision",f.nativeRevision()).put("date_raw",f.dateRaw()).put("local_player_id",f.localPlayerId()).put("paused",true).put("map_ready",true);
        out.putObject("played_character").put("character_id",f.actorCharacterId()).put("alive",true);
        out.set("active_event",json(binding.scene().activeEventJson()));out.set("pending_character_interaction",json(binding.scene().pendingInteractionJson()));
        if(binding.scene().terminalReason().isPresent())out.put("one_life_terminal_reason",binding.scene().terminalReason().orElseThrow());else out.putNull("one_life_terminal_reason");return out;
    }
    private static PendingModalClearance.SceneQuery capture(Query query,ObjectNode semantic){byte[] raw=FullJsonTree.encode(semantic,FullJsonTree.MAXIMUM_BYTES);return PendingModalClearance.capture(query,ref("read",StrictJson.canonical(query.original().toJson())),ref("semantic",raw),ref("native",new byte[]{2}),raw,java.time.Instant.parse("2026-10-24T08:00:00Z"));}
    private static Query query(BoundFrame binding,String request,long sequence,long observation,boolean blocks,boolean open){
        var frame=binding.frame();ObjectNode context=StrictJson.object().put("schema","current-timeline-blocker-context-v1").put("schema_version",1).put("status","available").put("snapshot_revision",frame.nativeRevision()).put("date_raw",frame.dateRaw()).put("identity",blocks&&open?"death_succession_modal":"none");
        context.set("blocks_simulation",typed(blocks));context.set("has_open_succession",typed(open));
        if(blocks&&open)context.set("can_continue",typed(true));else context.putObject("can_continue").put("status","unavailable").putNull("value").put("unavailable_reason","no_supported_timeline_surface_visible");
        context.putObject("evidence_source").put("kind","exact-build-stock-gui-plus-native-widget-state").put("path","game/gui/window_succession_event.gui").put("root_name",blocks&&open?"succession_event_window":"none").put("decisive_widget_name",blocks&&open?"close_button":"none");context.putNull("unavailable_reason");
        ObjectNode envelope=envelope(request);ObjectNode result=envelope.putObject("result").put("step",QUERY_STEP).put("accepted",true).put("status","available").put("query_sequence",sequence).put("observation_revision",observation).put("snapshot_revision",frame.nativeRevision()).put("private_build",true).put("read_only",true).put("advertised",false).put("backend_id","native-headless");result.set("current_timeline_blocker_context",context);
        byte[] raw=StrictJson.canonical(envelope);return parseQuery(raw,ref("query",raw),binding,request);
    }
    private static Close close(BoundFrame binding,String request,long observation,boolean known){
        ObjectNode envelope=envelope(request);
        if(!known)envelope.put("ok",false).put("error","original dispatch remains unknown");
        else{ObjectNode ack=envelope.putObject("result").put("step",CLOSE_STEP).put("status","submitted").put("snapshot_revision",binding.frame().nativeRevision()).put("date_raw",binding.frame().dateRaw()).put("played_character_id",binding.frame().actorCharacterId()).put("action_observation_revision",observation).put("close_invocations",1).put("material_result_verified",false).put("advertised",false).put("backend_id","native-headless");
            for(String field:List.of("accepted","identity_verified","can_continue_verified","paused_by_succession_verified","has_open_succession_verified","controller_vtable_verified","controller_open_verified","private_build"))ack.put(field,true);}
        byte[] raw=StrictJson.canonical(envelope);return parseClose(raw,ref("close",raw),binding,request);
    }
    private static ObjectNode typed(boolean value){return StrictJson.object().put("status","available").put("value",value).putNull("unavailable_reason");}
    private static ObjectNode envelope(String request){return StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request).put("ok",true);}
    private static JsonNode json(String value){return StrictJson.parse(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static ExactRef ref(String label,byte[] bytes){String sha=G2RetainedNativeSourceProvider.sha256(bytes);return new ExactRef("D:/fixtures/"+label+"-"+sha+".json",bytes.length,sha);}
}
