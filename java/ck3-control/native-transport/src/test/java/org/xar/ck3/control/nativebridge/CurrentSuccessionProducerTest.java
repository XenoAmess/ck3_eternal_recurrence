package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

final class CurrentSuccessionProducerTest {
    private static ObjectNode positive()throws Exception{return NativeWire.object(NativeWire.parse(CurrentSuccessionCppFrames.result("dead")));}
    private static CurrentSuccessionLifecycleResult decode(ObjectNode n)throws IOException{return CurrentSuccessionLifecycleResult.decode(new RawJson(StrictJson.canonical(n)));}
    @Test void actualCppSevenResultsRoundTripWithoutLivingCoreOrInheritanceCredit()throws Exception {
        for(String name:new String[]{"dead","assigned","unassigned","dispatched","indeterminate","incoherent","unavailable"}) {
            var original=CurrentSuccessionCppFrames.response(name);var d=CurrentSuccessionCppFrames.frame(name);assertEquals(original.nativeOk(),d.nativeOk());assertEquals(d,CurrentSuccessionLifecycleResult.decode(d.encode()));assertEquals(NativeWire.parse(original.result().token().orElseThrow().value()),NativeWire.parse(d.encode().bytes()));
        }
        var dead=CurrentSuccessionCppFrames.frame("dead");assertFalse(dead.worldBefore().orElseThrow().playedCharacterAlive());assertEquals(CurrentSuccessionLifecycle.PlayerRelation.PENDING_PREDECESSOR,dead.source().orElseThrow().playerRelation());
        var assigned=CurrentSuccessionCppFrames.frame("assigned");assertTrue(assigned.worldBefore().orElseThrow().playedCharacterAlive());
        var unassigned=CurrentSuccessionCppFrames.frame("unassigned");var w=unassigned.worldBefore().orElseThrow();assertFalse(w.mapReady());assertFalse(w.hasPlayedCharacter());assertTrue(w.playedCharacter().isEmpty());assertEquals(0,w.speed());assertEquals(-1,w.localPlayerId());
        var dispatch=NativeWire.object(NativeWire.parse(CurrentSuccessionCppFrames.result("dispatched")));assertFalse(dispatch.get("native_handled").booleanValue());assertFalse(dispatch.get("continuation_confirmed").booleanValue());assertFalse(dispatch.get("physical_save_confirmed").booleanValue());
    }
    @Test void genuineSourceCreatesExactJavaRequestsForReverseCppParser()throws Exception {
        var source=CurrentSuccessionCppFrames.frame("dead");var s=source.source().orElseThrow();
        var requests=new org.xar.ck3.control.application.action.NativeRequest[]{CurrentSuccessionLifecycle.queryRequest(),CurrentSuccessionLifecycle.continueRequest(source.providerGeneration(),source.querySequence(),s.deadCharacter().orElseThrow(),s.continueCharacter().orElseThrow())};
        for(int i=0;i<requests.length;i++) {
            var r=requests[i];var f=NativeWire.object(NativeWire.parse(r.additionalFields().bytes()));assertEquals(2,f.size());assertEquals(10,f.get("succession_lifecycle").size());assertEquals(0,f.get("arguments").size());assertFalse(f.has("expected_core"));
            f.put("core_control_deadline_unix_ms",2800000000000L);byte[] packet=NativeWire.execute("succession-java-"+i,r.step(),BigInteger.ZERO,StrictJson.canonical(f));assertEquals(BigInteger.ZERO,NativeWire.decodeExecuteRequest(packet).expectedRevision().orElseThrow());
            String dir=System.getProperty("xar.current267.succession.java.requests");if(dir!=null){Files.createDirectories(Path.of(dir));Files.write(Path.of(dir).resolve(i==0?"succession-query-request.json":"succession-continue-request.json"),Arrays.copyOfRange(packet,4,packet.length));}
        }
    }
    @Test void changedTypedRelationNativeSourceGuardOrWorldCannotMintAvailable()throws Exception {
        for(String k:new String[]{"dead_character_dead","continue_character_alive","handler_source_verified","named_root_bound","window_visible","window_enabled","default_button_admissible","default_native_route","stable_two_pass_verified"}){var n=positive();((ObjectNode)n.get("source")).put(k,false);assertThrows(IOException.class,()->decode(n),k);}
        var n=positive();((ObjectNode)n.get("source")).put("player_relation","heir_already_assigned");assertThrows(IOException.class,()->decode(n));
        var bad=positive();((ObjectNode)bad.get("world_before")).put("paused",false);assertThrows(IOException.class,()->decode(bad));
        assertThrows(IOException.class,()->decode(positive().putNull("source")));assertThrows(IOException.class,()->decode(positive().putNull("owner_witness")));
    }
    @Test void onlyPositivePrivateLeaseCanonicalStringsAndSignedIdsAreAccepted()throws Exception {
        for(String s:new String[]{"0","+1","01","-0","-1","18446744073709551616"})assertThrows(IOException.class,()->decode(positive().put("provider_generation",s)),s);
        assertThrows(IOException.class,()->decode(positive().put("query_sequence",1)));var n=positive();((ObjectNode)n.get("source")).put("dead_character_id",2147483648L);assertThrows(IOException.class,()->decode(n));
        var w=positive();((ObjectNode)w.get("owner_witness")).put("thread_id",4294967296L);assertThrows(IOException.class,()->decode(w));
        var signed=positive();((ObjectNode)signed.get("source")).put("dead_character_id",Integer.MIN_VALUE);((ObjectNode)signed.get("world_before")).put("played_character_id",Integer.MIN_VALUE);assertEquals(Integer.MIN_VALUE,decode(signed).worldBefore().orElseThrow().playedCharacter().orElseThrow().value());
    }
    @Test void voidDispatchedNeverBecomesHandledConfirmedOrPhysicalSave()throws Exception {
        for(String k:new String[]{"native_handled","continuation_confirmed","physical_save_confirmed"}){var n=NativeWire.object(NativeWire.parse(CurrentSuccessionCppFrames.result("dispatched"))).put(k,true);assertThrows(IOException.class,()->decode(n),k);}
        for(String k:new String[]{"effect_attempted","native_returned","source_available"}){var n=NativeWire.object(NativeWire.parse(CurrentSuccessionCppFrames.result("dispatched"))).put(k,false);assertThrows(IOException.class,()->decode(n),k);}
        var n=positive().put("claim_sequence","1");assertThrows(IOException.class,()->decode(n));
    }
    @Test void lifecycleCannotAliasOldCoreFullMenuTupleOrArbitraryWidget()throws Exception {
        for(String k:new String[]{"schema","game_version","executable_sha256","adapter_id","backend","step","action","status"})assertThrows(IOException.class,()->decode(positive().put(k,"wrong")),k);
        for(String k:new String[]{"widget","selector","expected_core","owner_verified"})assertThrows(IOException.class,()->decode(positive().put(k,"forged")),k);
        var n=positive();((ObjectNode)n.get("world_before")).put("schema","ck3_1210_core_frame_v1");assertThrows(IOException.class,()->decode(n));
        var upper=positive().put("status","AVAILABLE");assertThrows(IOException.class,()->decode(upper));
    }
}
