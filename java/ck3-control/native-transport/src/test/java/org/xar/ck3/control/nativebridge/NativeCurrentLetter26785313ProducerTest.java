package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

class NativeCurrentLetter26785313ProducerTest {
    static ObjectNode envelope(String name)throws IOException {
        try(var in=NativeCurrentLetter26785313ProducerTest.class.getResourceAsStream("/current-letter26785313-cpp-v1/"+name+".json")) {
            if(in==null)throw new IOException("Actual C++ letter resource absent: "+name);return NativeWire.object(NativeWire.parse(in.readAllBytes()));
        }
    }
    static ObjectNode token(String name)throws IOException{return NativeWire.object(envelope(name).get("result"));}
    static CurrentLetterResult decode(ObjectNode node)throws IOException{return CurrentLetterResult.decode(new RawJson(StrictJson.canonical(node)));}
    @Test void allNineActualCppResultsRetainExactOkAndRoundtrip()throws Exception {
        for(String name:List.of("available.result","reply-dispatched.result","no-letter.result","unknown-letter.result","known-invalid.result","stale.result","expired.result","unavailable.result","indeterminate.result")) {
            var e=envelope(name);var r=decode(NativeWire.object(e.get("result")));assertEquals(e.get("ok").booleanValue(),r.successful(),name);
            assertEquals(NativeWire.parse(StrictJson.canonical(e.get("result"))),NativeWire.parse(r.encode().bytes()));
        }
    }
    @Test void unknownAndDisabledLettersAreReadonlyAvailableButNeverAdmissible()throws Exception {
        for(String name:List.of("unknown-letter.result","known-invalid.result")) {
            var r=decode(token(name));assertEquals(CurrentLetterResult.Status.AVAILABLE,r.status());assertFalse(r.source().orElseThrow().knownReplyAdmissible());assertFalse(r.effectAttempted());
        }
    }
    @Test void absentLetterUsesActualNullsRatherThanSyntheticInstance()throws Exception {
        var r=decode(token("no-letter.result"));var s=r.source().orElseThrow();assertFalse(s.letterFound());assertTrue(s.instanceId().isEmpty());assertTrue(s.options().isEmpty());
        var n=token("no-letter.result");((ObjectNode)n.get("source")).put("instance_id",123);assertThrows(IOException.class,()->decode(n));
    }
    @Test void knownReplyRequiresReviewedDefinitionSoleSourceMappedOptionAndRecipient()throws Exception {
        for(String field:List.of("definition_key","recipient_character_id")) {
            var n=token("available.result");var s=(ObjectNode)n.get("source");if(field.equals("definition_key"))s.put(field,"arbitrary.1");else s.put(field,888);
            assertThrows(IOException.class,()->decode(n));
        }
        var n=token("available.result");((ObjectNode)n.get("source").get("options").get(0)).put("source_bound_option_key","ep3_laamps.0003.b");assertThrows(IOException.class,()->decode(n));
    }
    @Test void voidReplyCannotClaimHandledClosedNewDateOrSave()throws Exception {
        for(String field:List.of("native_handled","letter_closed","new_date_observed","physical_save_confirmed")) {
            var n=token("reply-dispatched.result");n.put(field,true);assertThrows(IOException.class,()->decode(n),field);
        }
        var n=token("reply-dispatched.result");n.put("claim_sequence","0");assertThrows(IOException.class,()->decode(n));
    }
    @Test void canonicalUint64MaxIsExactAndMalformedLeaseRejects()throws Exception {
        assertEquals(NativeWire.UINT64_MAX,decode(token("available.result")).providerGeneration());
        for(String value:List.of("01","-1","18446744073709551616")){var n=token("available.result");n.put("provider_generation",value);assertThrows(IOException.class,()->decode(n));}
        var n=token("available.result");n.put("provider_generation",BigInteger.ONE);assertThrows(IOException.class,()->decode(n));
    }
    @Test void sourceAndCoreRolesCannotBeBoughtByPositiveStatus()throws Exception {
        var n=token("unavailable.result");n.put("status","available").putNull("unavailable_reason");assertThrows(IOException.class,()->decode(n));
        var m=token("available.result");m.put("source_available",false);assertThrows(IOException.class,()->decode(m));
        var x=token("available.result");x.put("configured_instance",123);assertThrows(IOException.class,()->decode(x));
    }
    @Test void observedSignedActorAndCachedEmptyStringsRetainExactDomains()throws Exception {
        var r=decode(token("available.result"));assertEquals(-16777215,r.factsBefore().orElseThrow().playedCharacterId());
        assertEquals(-16777215,r.source().orElseThrow().recipientCharacterId().orElseThrow());
        assertEquals("",r.source().orElseThrow().options().getFirst().disabledReason());
    }
}
