package org.xar.ck3.control.nativebridge.capabilities.religion;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HexFormat;
import java.security.MessageDigest;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionCodec;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionContract;
import static org.xar.ck3.control.nativebridge.capabilities.religion.ReligionConversionRead.*;

/** Real captured mailbox fixtures feed the actual strict producer and public serde. No Game qualification. */
final class ReligionConversionBoundaryTest {
    private static String required(String name){String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("NOT_RUN: required original input "+name);return value;}
    private static byte[] exact(ExactRef ref)throws Exception {byte[] bytes=Files.readAllBytes(Path.of(ref.path()));assertEquals(ref.bytes(),bytes.length);assertEquals(ref.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));return bytes;}
    private static JsonNode manifest()throws Exception {byte[] bytes=Files.readAllBytes(Path.of(required("xar.religionConversion.sourceMap")));assertEquals(required("xar.religionConversion.sourceMapSha256"),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));return NativeWire.parse(bytes);}
    private static ObjectNode packet(Kind kind,String name)throws Exception {
        for(JsonNode fixture:manifest().get("original_fixture_inputs"))if(fixture.get("kind").textValue().equals(kind.name())&&fixture.get("name").textValue().equals(name))return (ObjectNode)NativeWire.parse(exact(ExactRef.fromJson(fixture.get("ref"))));
        throw new IllegalStateException("NOT_RUN: exact captured fixture missing "+kind+"/"+name);
    }
    private static ObjectNode payload(Kind kind,ObjectNode packet){return ((ObjectNode)packet.get("result").get(kind.key())).deepCopy();}
    private static BoundFrame frame(ObjectNode payload){JsonNode build=payload.has("game_version")?payload:payload.get("predicted_base_fulfillment");return new BoundFrame(PlayerReligionContext.Build.exact(build.get("game_version").textValue(),build.get("executable_sha256").textValue()),payload.get("date_raw").bigIntegerValue(),payload.get("played_character_id").bigIntegerValue());}
    private static View value(Kind kind,ObjectNode data){return normalize(kind,ReligionCodec.raw(data),frame(data),kind==Kind.CHOICES?null:data.get("target_rite_id").bigIntegerValue());}
    @Test void allThirtyOneOriginalCapturedPacketsRetainRawTokensAndPublicSerde()throws Exception {
        int count=0;for(JsonNode fixture:manifest().get("original_fixture_inputs")) {
            Kind kind=Kind.valueOf(fixture.get("kind").textValue());byte[] bytes=exact(ExactRef.fromJson(fixture.get("ref")));ObjectNode packet=(ObjectNode)NativeWire.parse(bytes);ObjectNode e=(ObjectNode)packet.get("result"),data=payload(kind,packet);View v=value(kind,data);
            assertEquals(data,ReligionCodec.object(v.nativeData()));ObjectNode result=present(v,frame(data).build(),"captured-mailbox-software-frame",BigInteger.valueOf(15),e.get("snapshot_revision").bigIntegerValue(),e);
            var response=new ReligionContract.Response(ReligionCodec.method(kind.method()),ReligionCodec.raw(result));assertEquals(result,ReligionCodec.object(ReligionCodec.encode(response)));
            assertTrue(result.get("capture_epoch").isTextual());assertTrue(result.get("queried_revision").isTextual());assertArrayEquals(bytes,exact(ExactRef.fromJson(fixture.get("ref"))));count++;
        }assertEquals(31,count,"do not silently drop unavailable or nontrivial original fixtures");
    }
    @Test void runtimeBoundaryRejectsUnknownMissingBooleanFloatAndExplicitNull()throws Exception {
        ObjectNode choices=payload(Kind.CHOICES,packet(Kind.CHOICES,"choices.json"));
        ObjectNode unknown=choices.deepCopy();unknown.put("constructor_qualification",true);assertThrows(IllegalArgumentException.class,()->value(Kind.CHOICES,unknown));
        ObjectNode missing=choices.deepCopy();missing.remove("available");assertThrows(IllegalArgumentException.class,()->value(Kind.CHOICES,missing));
        ObjectNode bool=choices.deepCopy();bool.put("capture_epoch",true);assertThrows(IllegalArgumentException.class,()->value(Kind.CHOICES,bool));
        ObjectNode floating=choices.deepCopy();floating.put("capture_epoch",9.0);assertThrows(IllegalArgumentException.class,()->value(Kind.CHOICES,floating));
        ObjectNode nul=choices.deepCopy();nul.putNull("read_only");assertThrows(IllegalArgumentException.class,()->value(Kind.CHOICES,nul));
    }
    @Test void availableComponentsMustShareActualActorDateAndOwnerPump()throws Exception {
        ObjectNode data=payload(Kind.CHOICES,packet(Kind.CHOICES,"choices.json"));
        for(String field:List.of("capture_epoch","date_raw","played_character_id")){ObjectNode copy=data.deepCopy();ObjectNode child=(ObjectNode)copy.get("faith_choices");child.put(field,child.get(field).bigIntegerValue().add(BigInteger.ONE));assertThrows(IllegalArgumentException.class,()->value(Kind.CHOICES,copy),field);}
    }
    @Test void optionalFervorMissingIsRetainedAndNullIsRejected()throws Exception {
        ObjectNode inputs=payload(Kind.INPUTS,packet(Kind.INPUTS,"signed-prediction.json"));assertFalse(inputs.has("conversion_fervor"));View missing=value(Kind.INPUTS,inputs);assertFalse(publicData(missing).has("conversion_fervor"));
        ObjectNode explicitNull=inputs.deepCopy();explicitNull.putNull("conversion_fervor");assertThrows(IllegalArgumentException.class,()->value(Kind.INPUTS,explicitNull));
    }
    @Test void fullUint64OwnerCountersNeverPassThroughDouble()throws Exception {
        BigInteger max=new BigInteger("18446744073709551615");ObjectNode data=payload(Kind.CHOICES,packet(Kind.CHOICES,"choices.json"));data.put("capture_epoch",max);((ObjectNode)data.get("faith_choices")).put("capture_epoch",max);((ObjectNode)data.get("current_faith_rites")).put("capture_epoch",max);
        View v=value(Kind.CHOICES,data);ObjectNode result=publicData(v);assertEquals(max.toString(),result.get("capture_epoch").textValue());assertEquals(max.toString(),result.get("faith_choices").get("capture_epoch").textValue());assertEquals(max,ReligionCodec.object(v.nativeData()).get("capture_epoch").bigIntegerValue());
        data.put("capture_epoch",max.add(BigInteger.ONE));assertThrows(IllegalArgumentException.class,()->value(Kind.CHOICES,data));
    }
    @Test void signedResourcesAndFulfillmentKeepExactPublicDecimalStrings()throws Exception {
        ObjectNode data=payload(Kind.OUTCOME,packet(Kind.OUTCOME,"current.json"));ObjectNode actor=(ObjectNode)data.get("actor"),state=(ObjectNode)data.get("state");actor.put("piety_raw",BigInteger.valueOf(Long.MIN_VALUE));state.put("knowledge_level_raw",BigInteger.valueOf(Long.MAX_VALUE));
        ObjectNode result=publicData(value(Kind.OUTCOME,data));assertEquals(Long.toString(Long.MIN_VALUE),result.get("actor").get("piety_raw").textValue());assertEquals(Long.toString(Long.MAX_VALUE),result.get("state").get("knowledge_level_raw").textValue());
    }
    @Test void sourcePayloadBuildAndTargetCannotBeReinterpreted()throws Exception {
        ObjectNode data=payload(Kind.TERMS,packet(Kind.TERMS,"permitted.json"));BoundFrame before=frame(data);BigInteger target=data.get("target_rite_id").bigIntegerValue();
        assertThrows(IllegalArgumentException.class,()->normalize(Kind.TERMS,ReligionCodec.raw(data),new BoundFrame(PlayerReligionContext.Build.CROZIER4,before.dateRaw(),before.player()),target));
        assertThrows(IllegalArgumentException.class,()->normalize(Kind.TERMS,ReligionCodec.raw(data),before,target.add(BigInteger.ONE)));
    }
    @Test void unavailableCostMayKeepItsActualZeroEpochWithoutGrantingConvert()throws Exception {
        ObjectNode data=payload(Kind.TERMS,packet(Kind.TERMS,"cost-unavailable.json"));Terms v=(Terms)value(Kind.TERMS,data);assertFalse(v.source().available());assertFalse(v.cost().source().available());
        assertEquals(v.cost().source().captureEpoch().toString(),publicData(v).get("cost").get("capture_epoch").textValue());
    }
    @Test void emptyNativeReasonTextIsDifferentFromUnavailableOrNull()throws Exception {
        Reasons value=(Reasons)value(Kind.REASONS,payload(Kind.REASONS,packet(Kind.REASONS,"native-allowed-empty.json")));assertTrue(value.source().available());assertEquals("",value.rawText());assertEquals("",publicData(value).get("raw_native_text").textValue());
    }
}
