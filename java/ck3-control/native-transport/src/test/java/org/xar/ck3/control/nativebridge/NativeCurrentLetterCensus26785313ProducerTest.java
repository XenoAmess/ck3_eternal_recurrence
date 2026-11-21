package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Genuine C++ serializer DATA. Mutations are explicit counterexamples, never Native positives. */
class NativeCurrentLetterCensus26785313ProducerTest {
    static final String ROOT="/current267-letter-set-a297/";
    static JsonNode index()throws IOException{return NativeWire.parse(resource("producer-index.json"));}
    static byte[] resource(String name)throws IOException {try(var in=NativeCurrentLetterCensus26785313ProducerTest.class.getResourceAsStream(ROOT+name)){if(in==null)throw new IOException("Pinned actual C++ resource absent: "+name);return in.readAllBytes();}}
    static ObjectNode envelope(String role)throws IOException {
        var path=index().get("result_roles").get(role);if(path==null||!path.isTextual())throw new IOException("Actual C++ result role absent: "+role);
        return NativeWire.object(NativeWire.parse(resource(path.textValue())));
    }
    static RawJson token(String role)throws IOException{return new RawJson(StrictJson.canonical(envelope(role).get("result")));}
    static CurrentLetterSetResult frame(String role)throws IOException{return CurrentLetterSetResult.decode(token(role));}
    static CoreFrame.Partial actualCore()throws IOException {return new CoreFrame.Partial(ExactCk3Build.CK3_121003_STEAM_26785313,frame("multiple").factsBefore().orElseThrow());}
    static ObjectNode result(String role)throws IOException{return NativeWire.object(NativeWire.parse(token(role).bytes()));}
    static CurrentLetterSetResult decode(ObjectNode value)throws IOException{return CurrentLetterSetResult.decode(new RawJson(StrictJson.canonical(value)));}
    @Test void everyOriginalFileMatchesFullHashAndEveryActualResultDecodes()throws Exception {
        int results=0;
        for(var row:index().get("files")) {
            byte[] bytes=resource(row.get("name").textValue());assertEquals(row.get("bytes").intValue(),bytes.length);
            assertEquals(row.get("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
            var object=NativeWire.parse(bytes);if(object.has("result")&&object.has("type")&&object.get("type").asText().equals("command_result")){var value=CurrentLetterSetResult.decode(new RawJson(StrictJson.canonical(object.get("result"))));assertEquals(object.get("ok").booleanValue(),value.successful());results++;}
        }
        assertTrue(results>=5);
    }
    @Test void fullCensusRetainsThreeDistinctActualInstancesRatherThanFirstOrLast()throws Exception {
        var source=frame("multiple").source().orElseThrow();assertTrue(source.censusComplete());assertEquals(3,source.namedRootCount());assertEquals(3,source.letters().size());
        assertEquals(3,source.letters().stream().map(row->row.instanceId().orElseThrow()).distinct().count());
        for(var row:source.letters()){assertTrue(row.letterFound());assertTrue(row.namedRootBound());assertEquals(source.residentCount(),row.residentCount());assertEquals(row,source.exactInstance(row.instanceId().orElseThrow()));}
    }
    @Test void emptyCompleteObservationIsAvailableWithoutAnyReplyAuthority()throws Exception {
        var empty=frame("empty");assertEquals(CurrentLetterSetResult.Status.AVAILABLE,empty.status());assertTrue(empty.source().orElseThrow().letters().isEmpty());assertEquals(0,empty.source().orElseThrow().namedRootCount());
        assertThrows(IOException.class,()->empty.source().orElseThrow().exactInstance(1));assertTrue(empty.instanceId().isEmpty());
    }
    @Test void queryAndReplyEncodingUseNewFamilyAndExplicitInstanceRole()throws Exception {
        var core=actualCore();var query=CurrentLetterSet.request(core,CurrentLetterSet.Action.QUERY_LETTERS,BigInteger.ZERO,BigInteger.ZERO,Optional.empty());
        var q=NativeWire.object(NativeWire.parse(query.additionalFields().bytes()));assertEquals(2,q.size());assertTrue(q.get("arguments").isEmpty());assertEquals(10,q.get("letter_set").size());assertTrue(q.get("letter_set").get("instance_id").isNull());
        var reply=frame("reply");var request=CurrentLetterSet.request(core,CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE,reply.providerGeneration(),reply.querySequence(),reply.instanceId());
        assertEquals("reply-known-current-letter-instance-v1",request.step());assertEquals("game.command.reply-known-current-letter-instance.v1",request.requiredCapability().orElseThrow());
        assertEquals(reply.instanceId().orElseThrow(),NativeWire.parse(request.additionalFields().bytes()).get("letter_set").get("instance_id").intValue());
    }
    @Test void actualVoidReplyRetainsFullBeforeCensusAndCannotClaimPoststate()throws Exception {
        var reply=frame("reply");assertEquals(CurrentLetterSetResult.Status.REPLY_DISPATCHED,reply.status());assertTrue(reply.effectAttempted());assertTrue(reply.nativeReturned());assertTrue(reply.claimSequence().signum()>0);
        assertTrue(reply.source().orElseThrow().exactInstance(reply.instanceId().orElseThrow()).knownReplyAdmissible());
        var raw=NativeWire.parse(reply.encode().bytes());for(String key:new String[]{"native_handled","letter_closed","new_date_observed","physical_save_confirmed"})assertFalse(raw.get(key).booleanValue());
        assertEquals(reply,CurrentLetterSetResult.decode(reply.encode()));
    }
    @Test void incompleteCountOmittedRowAndDuplicateInstanceCounterexamplesReject()throws Exception {
        var incomplete=result("multiple");((ObjectNode)incomplete.get("source")).put("census_complete",false);assertThrows(IOException.class,()->decode(incomplete));
        var omitted=result("multiple");((com.fasterxml.jackson.databind.node.ArrayNode)omitted.get("source").get("letters")).remove(0);assertThrows(IOException.class,()->decode(omitted));
        var duplicate=result("multiple");var rows=duplicate.get("source").get("letters");((ObjectNode)rows.get(1)).put("instance_id",rows.get(0).get("instance_id").intValue());assertThrows(IOException.class,()->decode(duplicate));
    }
    @Test void crossedResidentRecipientAndUnreviewedOptionCounterexamplesReject()throws Exception {
        var resident=result("multiple");((ObjectNode)resident.get("source").get("letters").get(0)).put("resident_count",0);assertThrows(IOException.class,()->decode(resident));
        var recipient=result("multiple");((ObjectNode)recipient.get("source").get("letters").get(0)).put("recipient_character_id",-1);assertThrows(IOException.class,()->decode(recipient));
        var option=result("reply");int id=option.get("instance_id").intValue();for(var row:option.get("source").get("letters"))if(row.get("instance_id").intValue()==id)((ObjectNode)row.get("options").get(0)).put("source_bound_option_key","unreviewed.option");assertThrows(IOException.class,()->decode(option));
    }
    @Test void extraMissingOldFamilyAndFalsePoststateFieldsReject()throws Exception {
        for(String mutation:new String[]{"extra","missing","old","closed"}) {
            var object=result("multiple");switch(mutation){case "extra"->object.put("permission",true);case "missing"->object.remove("instance_id");case "old"->object.put("schema",CurrentLetter.RESULT_SCHEMA);default->object.put("letter_closed",true);}
            assertThrows(IOException.class,()->decode(object));
        }
    }
    @Test void queryAndReplyNullLeaseAndInstanceRolesAreStrict()throws Exception {
        var core=actualCore();assertThrows(IllegalArgumentException.class,()->CurrentLetterSet.request(core,CurrentLetterSet.Action.QUERY_LETTERS,BigInteger.ZERO,BigInteger.ZERO,Optional.of(2)));
        assertThrows(IllegalArgumentException.class,()->CurrentLetterSet.request(core,CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE,BigInteger.ONE,BigInteger.ONE,Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->CurrentLetterSet.request(core,CurrentLetterSet.Action.REPLY_KNOWN_INSTANCE,BigInteger.ZERO,BigInteger.ONE,Optional.of(2)));
        var wrong=result("multiple");wrong.put("instance_id",2);assertThrows(IOException.class,()->decode(wrong));
    }
    @Test void canonicalUnsignedLeaseAndActualSignedInstanceDomainsRejectCounterexamples()throws Exception {
        for(String value:new String[]{"01","-1","18446744073709551616"}){var raw=result("multiple");raw.put("query_sequence",value);assertThrows(IOException.class,()->decode(raw));}
        var instance=result("reply");instance.put("instance_id",0);assertThrows(IOException.class,()->decode(instance));
        var outside=result("reply");outside.put("instance_id",BigInteger.ONE.shiftLeft(31));assertThrows(IOException.class,()->decode(outside));
    }
}
