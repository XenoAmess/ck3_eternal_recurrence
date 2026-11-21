package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Actual C++ serializer resources; explicit mutations below are Java negative DATA, never Native execution. */
class NativeCurrentFullscreenEvent26785313ProducerTest {
    static byte[] raw(String role)throws IOException {
        try(var in=NativeCurrentFullscreenEvent26785313ProducerTest.class.getResourceAsStream("/current267-fullscreen-actual-cpp/"+role+".json")) {
            if(in==null)throw new IOException("Pinned genuine C++ resource absent: "+role);return in.readAllBytes();
        }
    }
    static ObjectNode envelope(String role)throws IOException{return NativeWire.object(NativeWire.parse(raw(role)));}
    static CurrentFullscreenEventResult frame(String role)throws IOException{return CurrentFullscreenEventResult.decode(new RawJson(StrictJson.canonical(envelope(role).get("result"))));}
    static CoreFrame.Partial actualCore()throws IOException{return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame("available").factsBefore().orElseThrow());}
    static CurrentFullscreenEventResult changed(ObjectNode token)throws IOException{return CurrentFullscreenEventResult.decode(new RawJson(StrictJson.canonical(token)));}
    @Test void actualQueryAndVoidAckRoundtripKeepExactBeforeSourceAndNoClosureClaim()throws Exception {
        for(String role:List.of("available","ack","empty","unknown","early","indeterminate","refused0","refused1","refused2","refused3")) {
            var original=frame(role);assertEquals(original,CurrentFullscreenEventResult.decode(original.encode()),role);
        }
        var query=frame("available");var ack=frame("ack");
        assertEquals(query,CurrentFullscreenEventResult.decode(query.encode()));assertEquals(ack,CurrentFullscreenEventResult.decode(ack.encode()));
        assertEquals(CurrentFullscreenEvent.Action.QUERY_FULLSCREEN,query.action());assertEquals(CurrentFullscreenEventResult.Status.ACK_DISPATCHED,ack.status());
        assertEquals(query.source(),ack.source());assertEquals(query.factsBefore(),ack.factsBefore());assertEquals(query.owner(),ack.owner());
        assertEquals(query.providerGeneration(),ack.providerGeneration());assertEquals(query.querySequence(),ack.querySequence());
        assertTrue(ack.effectAttempted());assertTrue(ack.nativeReturned());assertTrue(ack.cleanupKnown());
        var n=StrictJson.parse(ack.encode().bytes(),1<<20);assertEquals(24,n.size());
        for(String key:List.of("native_handled","fullscreen_closed","new_date_observed","physical_save_confirmed"))assertFalse(n.get(key).booleanValue(),key);
    }
    @Test void genuineRequestsAndJavaEncoderHaveOnlyTheFixedActionAndPrivateLeaseFields()throws Exception {
        for(var action:CurrentFullscreenEvent.Action.values()) {
            var n=envelope(action==CurrentFullscreenEvent.Action.QUERY_FULLSCREEN?"query-request":"ack-request");
            assertEquals(action.step(),n.get("step").textValue());assertEquals(8,n.size());
            assertTrue(n.get("arguments").isObject());assertEquals(0,n.get("arguments").size());assertEquals(0,n.get("expected_revision").intValue());
            var actual=frame("available");boolean query=action==CurrentFullscreenEvent.Action.QUERY_FULLSCREEN;
            var request=CurrentFullscreenEvent.request(actualCore(),action,query?BigInteger.ZERO:actual.providerGeneration(),query?BigInteger.ZERO:actual.querySequence(),query?Optional.empty():actual.source().orElseThrow().instanceId());
            var fields=NativeWire.object(NativeWire.parse(request.additionalFields().bytes()));assertEquals(Set.of("arguments","fullscreen_event"),fieldNames(fields));
            var claim=NativeWire.object(fields.get("fullscreen_event"));assertEquals(10,claim.size());assertEquals(action.wire(),claim.get("action").textValue());
            assertEquals(8,claim.get("expected_core").size());assertEquals(query,claim.get("instance_id").isNull());
            assertEquals(CurrentFullscreenEvent.SCHEMA,claim.get("schema").textValue());assertEquals(CurrentFullscreenEvent.BACKEND,claim.get("backend").textValue());
        }
        var q=frame("available");
        assertThrows(IllegalArgumentException.class,()->CurrentFullscreenEvent.request(actualCore(),CurrentFullscreenEvent.Action.QUERY_FULLSCREEN,q.providerGeneration(),q.querySequence(),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->CurrentFullscreenEvent.request(actualCore(),CurrentFullscreenEvent.Action.ACKNOWLEDGE_KNOWN,BigInteger.ZERO,BigInteger.ZERO,Optional.of(1)));
    }
    @Test void exactBuildSchemaAndAdditionalKeysCannotBuyObservationOrEffects()throws Exception {
        for(String key:List.of("schema","game_version","executable_sha256","backend","adapter_id")) {
            var n=NativeWire.object(envelope("available").get("result"));n.put(key,"wrong");reject(n,key);
        }
        for(String key:List.of("caller_can_select","selected_index","effect_confirmed")) {
            var n=NativeWire.object(envelope("available").get("result"));n.put(key,true);reject(n,key);
        }
        var n=NativeWire.object(envelope("available").get("result"));n.put("addresses_redacted",false);reject(n);
    }
    @Test void emptyCompleteSourceCannotBeRelabelledAsAMaterialCurrentItem()throws Exception {
        var empty=frame("empty").source().orElseThrow();assertEquals(0,empty.splashItemCount());assertFalse(empty.fullscreenFound());assertFalse(empty.knownAckAdmissible());assertTrue(empty.instanceId().isEmpty());
        var n=NativeWire.object(envelope("empty").get("result"));((ObjectNode)n.get("source")).put("splash_item_count",1);reject(n);
        n=NativeWire.object(envelope("available").get("result"));((ObjectNode)n.get("source")).put("splash_item_count",0);var invalid=n;assertThrows(IOException.class,()->changed(invalid));
    }
    @Test void MultipleItemsAndUnknownDefinitionsRemainReadonlyWithoutFixedAckAuthority()throws Exception {
        var n=NativeWire.object(envelope("available").get("result"));var s=(ObjectNode)n.get("source");s.put("splash_item_count",2).put("known_ack_admissible",false);
        assertFalse(changed(n).source().orElseThrow().knownAckAdmissible());s.put("known_ack_admissible",true);reject(n);
        n=NativeWire.object(envelope("available").get("result"));s=(ObjectNode)n.get("source");s.put("definition_key","java_data_unreviewed").put("known_ack_admissible",false);((ObjectNode)s.get("options").get(0)).putNull("source_bound_option_key");
        assertFalse(changed(n).source().orElseThrow().knownAckAdmissible());var altered=n;((ObjectNode)n.get("source")).put("known_ack_admissible",true);assertThrows(IOException.class,()->changed(altered));
    }
    @Test void CachedTextRetainsEmptyOpeningRichtextAndStockErrorWithoutInterpretation()throws Exception {
        var n=NativeWire.object(envelope("available").get("result"));var s=(ObjectNode)n.get("source");String text="ERROR:[pope_scope...] \u0015 actual rich text";
        s.put("opening","").put("description",text);((ObjectNode)s.get("options").get(0)).put("disabled_reason","");
        var decoded=changed(n);assertEquals("",decoded.source().orElseThrow().opening().orElseThrow());assertEquals(text,CurrentFullscreenEventResult.decode(decoded.encode()).source().orElseThrow().description().orElseThrow());
        s.put("description","x".repeat(16385));reject(n);
    }
    @Test void NativeCanMustBeActuallyBooleanAndTrueForTheOnlyAuthoredOption()throws Exception {
        var n=NativeWire.object(envelope("available").get("result"));((ObjectNode)n.get("source").get("options").get(0)).putNull("native_can_select");reject(n);
        n=NativeWire.object(envelope("available").get("result"));var s=(ObjectNode)n.get("source");((ObjectNode)s.get("options").get(0)).put("native_can_select",false);var invalid=n;assertThrows(IOException.class,()->changed(invalid));
        s.put("known_ack_admissible",false);assertFalse(changed(n).source().orElseThrow().knownAckAdmissible());
    }
    @Test void NativeLeaseMustBeCanonicalUint64StringsAndAckMustUseTheActualSourceInstance()throws Exception {
        var query=frame("available");assertTrue(query.providerGeneration().signum()>0);assertTrue(query.querySequence().signum()>0);
        for(String value:List.of("-1","01","18446744073709551616")) {
            var n=NativeWire.object(envelope("available").get("result"));n.put("provider_generation",value);reject(n);
        }
        var n=NativeWire.object(envelope("available").get("result"));n.put("query_sequence",1);reject(n);
        n=NativeWire.object(envelope("ack").get("result"));n.put("instance_id",Integer.MAX_VALUE);var wrong=n;assertThrows(IOException.class,()->changed(wrong));
    }
    @Test void KnownZeroEffectRefusalRetainsTheOriginalLeaseInstanceAndSpentClaim()throws Exception {
        var refused=frame("early");assertFalse(refused.successful());assertFalse(refused.effectAttempted());assertFalse(refused.nativeReturned());
        assertEquals(frame("ack").instanceId(),refused.instanceId());assertEquals(frame("available").providerGeneration(),refused.providerGeneration());assertEquals(frame("available").querySequence(),refused.querySequence());
        var n=NativeWire.object(envelope("early").get("result"));n.put("claim_sequence","1");assertEquals(BigInteger.ONE,changed(n).claimSequence());n.put("effect_attempted",true);reject(n);
    }
    @Test void CleanupUnknownCannotPretendToCarryACurrentObservedSourceOrAHandledVoidEffect()throws Exception {
        var n=NativeWire.object(envelope("available").get("result"));n.put("cleanup_known",false);reject(n);
        var uncertain=frame("indeterminate");assertEquals(CurrentFullscreenEventResult.Status.INDETERMINATE,uncertain.status());assertFalse(uncertain.successful());
        n=NativeWire.object(envelope("ack").get("result"));n.put("native_handled",true);var invalid=n;assertThrows(IOException.class,()->changed(invalid));
        n=NativeWire.object(envelope("available").get("result"));n.put("claim_sequence","1");var queryClaim=n;assertThrows(IOException.class,()->changed(queryClaim));
    }
    private static void reject(ObjectNode n){assertThrows(IOException.class,()->changed(n));}
    private static void reject(ObjectNode n,String message){assertThrows(IOException.class,()->changed(n),message);}
    private static Set<String> fieldNames(ObjectNode n){var names=new java.util.HashSet<String>();n.fieldNames().forEachRemaining(names::add);return Set.copyOf(names);}
}
