package org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContext.Build;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionDoctrineDraftReads.*;

/** Original retained C++ packets plus executed Python oracle; this is software parity, never game evidence. */
final class ReligionDoctrineDataPythonParityTest {
    @Test void originalCompletePacketsPassNativeParserNormalizerAndExactPublicWidths()throws Exception{
        byte[] bytes;try(InputStream input=getClass().getResourceAsStream("/org/xar/ck3/control/religion/religion-doctrine-data-parity37.json")){assertNotNull(input);bytes=input.readAllBytes();}
        assertEquals("e67e022ffc24043cde6414f9c49138c26d20f5296069ac3ac554f97e9ec235be",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        JsonNode corpus=StrictJson.parse(bytes);int accepted=0,rejected=0;
        for(JsonNode row:corpus.path("cases")){
            var selected=Selection.fixed(Kind.valueOf(row.path("kind").textValue()));var frame=new ReligionTemporalFinance.Frame(Build.CROZIER2,BigInteger.valueOf(702),new BigInteger(row.path("native_revision").textValue()),new BigInteger(row.path("date").textValue()),new BigInteger(row.path("actor").textValue()),1234L,BigInteger.ONE,"original:retained-cpp","original:doctrine-parity");
            if(row.path("accepted").booleanValue()){
                byte[] original=Base64.getDecoder().decode(row.path("wire_base64").textValue());var packet=NativeWire.decode(NativeWire.packet(original));assertInstanceOf(NativeWire.CommandResult.class,packet);var result=(NativeWire.CommandResult)packet;assertTrue(result.nativeOk());var token=result.result().token().orElseThrow();
                ObjectNode envelope=ReligionCodec.object(new RawJson(token.value()));var before=envelope.deepCopy();var observed=ReligionDoctrineDraftReads.normalizeEnvelope(selected,frame,envelope);
                assertEquals(row.path("expected"),ReligionCodec.object(observed.nativeEnvelope()).get(selected.kind().nested()));assertEquals(before,envelope);
                var output=observed.publicResult();assertTrue(output.get("capture_epoch").isTextual());assertEquals("701",output.get("snapshot_revision").textValue());assertEquals("702",output.get("queried_revision").textValue());assertEquals(output,StrictJson.parse(ReligionCodec.raw(output).bytes()));
                assertTrue(ReligionCodec.object(observed.nativeEnvelope()).get("snapshot_revision").isIntegralNumber());accepted++;
            }else{var input=(ObjectNode)row.path("value");var before=input.deepCopy();assertThrows(IllegalArgumentException.class,()->ReligionDoctrineDataValidation.normalize(selected,input,frame),row.path("name").textValue());assertEquals(before,input);rejected++;}
        }assertEquals(5,accepted);assertEquals(20,rejected);
    }
    @Test void originalOptionalSelectorPresenceAndSafeRequestRoundTripAreDistinct(){
        String knowledge=Kind.DOCTRINE_KNOWLEDGE.method();var missing=StrictJson.object().put("expected_revision","18446744073709551615");var nil=missing.deepCopy().putNull("doctrine_key");var named=missing.deepCopy().put("doctrine_key","doctrine_礼");
        var a=Selection.from(ReligionCodec.decode(knowledge,ReligionCodec.raw(missing)));var b=Selection.from(ReligionCodec.decode(knowledge,ReligionCodec.raw(nil)));var c=Selection.from(ReligionCodec.decode(knowledge,ReligionCodec.raw(named)));
        assertNotEquals(a,b);assertEquals(ReligionDoctrineDraftReads.nativeArguments(a),ReligionDoctrineDraftReads.nativeArguments(b));assertFalse(ReligionDoctrineDraftReads.selectionArguments(a).has("doctrine_key"));assertTrue(ReligionDoctrineDraftReads.selectionArguments(b).get("doctrine_key").isNull());assertEquals("doctrine_礼",ReligionDoctrineDraftReads.nativeArguments(c).get("doctrine_key").textValue());
        for(ObjectNode input:List.of(missing,nil,named)){var request=ReligionCodec.decode(knowledge,ReligionCodec.raw(input));assertEquals(request,ReligionCodec.decode(knowledge,ReligionCodec.encode(request)));}
        var tenets=StrictJson.object().put("expected_revision",1).put("target_rite_id",4294967295L).put("tenet_key","tenet_0").put("include_knowledge_catalogue",false);var selected=Selection.from(ReligionCodec.decode(Kind.TENETS.method(),ReligionCodec.raw(tenets)));assertEquals(new BigInteger("4294967295"),selected.target().orElseThrow());assertFalse(ReligionDoctrineDraftReads.nativeArguments(selected).has("include_knowledge_catalogue"));
        for(ObjectNode bad:List.of(tenets.deepCopy().put("target_rite_id",true),tenets.deepCopy().put("target_rite_id",1.0),tenets.deepCopy().put("include_knowledge_catalogue",1),tenets.deepCopy().putNull("tenet_key"),tenets.deepCopy().put("unknown",true)))assertThrows(IllegalArgumentException.class,()->Selection.from(ReligionCodec.decode(Kind.TENETS.method(),ReligionCodec.raw(bad))));
        assertEquals(13,Arrays.stream(Kind.values()).map(Kind::method).distinct().count());
    }
    @Test void resourceSidecarAbsenceAndNullKeepOriginalPresenceWhileUnsupportedContentRejects()throws Exception{
        JsonNode cases;try(InputStream input=getClass().getResourceAsStream("/org/xar/ck3/control/religion/religion-reform-draft-parity14.json")){assertNotNull(input);cases=StrictJson.parse(input.readAllBytes(),262144).path("cases");}
        for(Kind kind:List.of(Kind.DRAFT_RESOURCE_COSTS,Kind.REFORM_CONTEXT)){
            JsonNode row=null;for(JsonNode candidate:cases)if(candidate.path("accepted").booleanValue()&&candidate.path("kind").textValue().equals(kind.name())){row=candidate;break;}assertNotNull(row);
            var frame=new ReligionTemporalFinance.Frame(Build.CROZIER2,BigInteger.valueOf(702),BigInteger.valueOf(701),new BigInteger(row.path("date").textValue()),new BigInteger(row.path("actor").textValue()),1234L,BigInteger.ONE,"offline:composed-normalizer","offline:presence");
            var body=(ObjectNode)row.path("value");var envelope=StrictJson.object().put("step",kind.step()).put("accepted",true).put("status",body.path("available").booleanValue()?"observed":"unavailable").put("private_build",true).put("read_only",true).put("advertised",false).put("game_version",frame.build().version()).put("executable_sha256",frame.build().sha256()).put("backend_id","ck3-"+frame.build().version()+"-native-"+kind.suffix()).put("domain_key",kind.domain()).put("snapshot_revision",701).put("date_raw",frame.date());envelope.set(kind.nested(),body);
            var selected=Selection.fixed(kind);var output=ReligionDoctrineDraftReads.normalizeEnvelope(selected,frame,envelope).publicResult();
            if(kind==Kind.DRAFT_RESOURCE_COSTS){String wire="religion_rite_dynamic_term_observations_12004",facts="religion_rite_dynamic_term_observation_facts_12004";assertFalse(output.has(facts));var nil=envelope.deepCopy().putNull(wire).putNull("religion_creation_price_source_12004");var result=ReligionDoctrineDraftReads.normalizeEnvelope(selected,frame,nil).publicResult();assertEquals("absent",result.get(facts).get("status").textValue());assertFalse(result.has("religion_creation_price_source_facts_12004"));var unsupported=envelope.deepCopy();unsupported.putObject(wire);assertThrows(IllegalArgumentException.class,()->ReligionDoctrineDraftReads.normalizeEnvelope(selected,frame,unsupported));}
            else{for(String scope:List.of("current_context","current_rite_model","current_draft_costs"))for(String key:switch(scope){case "current_context"->List.of("faith_fervor_raw","spiritual_fulfillment_raw");case "current_rite_model"->List.of("divergence_to_main_raw","faith_heresy_threshold_raw");default->List.of("piety_cost_raw","piety_missing_signed_raw");})if(body.path(scope).hasNonNull(key))assertTrue(output.get(scope).get(key).isTextual(),scope+"/"+key);}
        }
    }
}
