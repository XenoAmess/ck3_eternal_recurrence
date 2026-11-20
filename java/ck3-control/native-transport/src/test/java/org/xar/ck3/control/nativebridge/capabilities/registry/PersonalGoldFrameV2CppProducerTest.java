package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.semantic.NativePlayedResources;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Pinned actual production C++ serializer output from hand-authored NoGame DATA; no live owner or MCP admission. */
final class PersonalGoldFrameV2CppProducerTest {
    private record Input(String name,int bytes,String sha256,Long raw) { }
    private static final List<Input> INPUTS=List.of(
            new Input("personal-gold-v2-partial.json",1266,"e30ac0ef6e1bcf50e7d56597d661546700757ce126c3ee44d93856848e6ccadf",-12345L),
            new Input("personal-gold-v2-raw--1.json",1262,"7f3b213e5c238513b2a5f68267d6cbdb14ee9fb0c390700d7b31876ba0ee8a01",-1L),
            new Input("personal-gold-v2-raw--9223372036854775808.json",1280,"a95e473c44ab9aa87ff4566d392a582ec4f58dedf18397e8fe1022112cb33eb2",Long.MIN_VALUE),
            new Input("personal-gold-v2-raw-0.json",1261,"011321e6310f5082a902cdf66fa1288185def30bf6f08569b49ffc7962b15d70",0L),
            new Input("personal-gold-v2-raw-1.json",1261,"abae321994ed4c4e61765fd145a8539d58e3ccc328ffd7362ec7b894dd94b140",1L),
            new Input("personal-gold-v2-raw-9223372036854775807.json",1279,"ac05befbb8365d22281f22799be3982ecbf94dfe5b45475e992997d726ad830c",Long.MAX_VALUE),
            new Input("personal-gold-v2-unavailable.json",1302,"160b17627c72376e62451bbcb450749a29fecf640c93882449c0dbbbc2beb912",null));
    private static byte[] original(Input input)throws Exception {
        try(var stream=PersonalGoldFrameV2CppProducerTest.class.getResourceAsStream("/newnative/personal-gold121003-v2/"+input.name())) {
            if(stream==null)throw new IOException("actual C++ Gold V2 fixture missing: "+input.name());
            byte[] raw=stream.readNBytes(input.bytes()+1);assertEquals(input.bytes(),raw.length);
            assertEquals(input.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));return raw;
        }
    }
    private static NativeActionPort.AckReceived ack(byte[] envelope,String step)throws IOException {
        byte[] packet=NativeWire.packet(envelope);var decoded=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        return new NativeActionPort.AckReceived(decoded.requestId(),decoded.nativeOk(),
                decoded.result().token().map(value->new RawJson(value.value())),new RawJson(envelope),packet,
                Optional.of(new NativeActionPort.OutboundPacket(decoded.requestId(),NativeWire.execute(decoded.requestId(),step,BigInteger.ZERO,new byte[]{'{','}'}))));
    }
    private static ObjectNode result(Input input)throws Exception {
        return RegistryJson.object(RegistryJson.object(new RawJson(original(input))).get("result"));
    }
    private static void denied(ObjectNode changed){assertThrows(IllegalArgumentException.class,()->PersonalGoldFrame.decodeV2(RegistryJson.encode(changed)));}

    @Test void allSevenActualCppResultsRoundTripWithoutNumericCoercionOrCompleteSnapshotClaims()throws Exception {
        for(var input:INPUTS){
            var value=PersonalGoldFramePublicCodec.decodeOutcome(ack(original(input),PersonalGoldFrame.Version.V2.step()));
            assertEquals(PersonalGoldFrame.Version.V2,value.version());assertEquals(ExactCk3Build.CK3_121003_STEAM_26785313,value.build());
            assertEquals(value.build(),value.coreFrame().build());
            var encoded=PersonalGoldFramePublicCodec.encode(value);assertEquals(result(input),RegistryJson.object(encoded));
            assertEquals(value,PersonalGoldFrame.decodeV2(encoded));assertEquals(value,PersonalGoldFrame.decode(encoded));
            var row=RegistryJson.object(encoded);assertEquals(15,row.size());
            assertFalse(row.get("complete_snapshot").booleanValue());assertFalse(row.get("treasury_observed").booleanValue());assertFalse(row.get("monthly_flow_observed").booleanValue());
            if(input.raw()!=null){
                var partial=assertInstanceOf(PersonalGoldFrame.Partial.class,value);assertEquals(input.raw().longValue(),partial.personalGold().raw());
                assertTrue(row.get("personal_gold").get("raw").isTextual());assertEquals(Long.toString(input.raw()),row.get("personal_gold").get("raw").textValue());
            }else{
                var unavailable=assertInstanceOf(PersonalGoldFrame.Unavailable.class,value);assertFalse(unavailable.applicationMainObserved());
                assertTrue(row.get("personal_gold").isNull());assertEquals("application_main_not_observed",unavailable.reason());
            }
        }
    }

    @Test void noncanonicalOverflowAndWrongJsonKindsOrScaleAreRejected()throws Exception {
        var base=result(INPUTS.getFirst());
        for(String raw:List.of("+1","01","-0","-01","9223372036854775808","-9223372036854775809","1.0","1e5"," 1","1 ","","--1")){
            var changed=base.deepCopy();((ObjectNode)changed.get("personal_gold")).put("raw",raw);denied(changed);
        }
        for(var raw:List.of(JsonNodeFactory.instance.numberNode(1),JsonNodeFactory.instance.numberNode(1.0),JsonNodeFactory.instance.booleanNode(true),JsonNodeFactory.instance.nullNode())){
            var changed=base.deepCopy();((ObjectNode)changed.get("personal_gold")).set("raw",raw);denied(changed);
        }
        for(var scale:List.of(JsonNodeFactory.instance.numberNode(1000),JsonNodeFactory.instance.numberNode(100000.0),JsonNodeFactory.instance.textNode("100000"),JsonNodeFactory.instance.booleanNode(true))){
            var changed=base.deepCopy();((ObjectNode)changed.get("personal_gold")).set("scale",scale);denied(changed);
        }
        var missing=base.deepCopy();((ObjectNode)missing.get("personal_gold")).remove("raw");denied(missing);
        var extra=base.deepCopy();((ObjectNode)extra.get("personal_gold")).put("treasury",0);denied(extra);
        assertInstanceOf(NativePlayedResources.Amount.class,NativePlayedResources.decode(NativePlayedResources.encode(new NativePlayedResources.Amount(1))));
        assertThrows(IllegalArgumentException.class,()->NativePlayedResources.decode(base.get("personal_gold")),"shared old numeric contract remains unchanged");
    }

    @Test void exactOuterNestedCorePausedAndLivingOwnerContextCannotCrossVersions()throws Exception {
        var base=result(INPUTS.getFirst());
        for(String field:List.of("game_version","executable_sha256","adapter_id","backend","schema","step")){
            var changed=base.deepCopy();changed.put(field,"wrong");denied(changed);
            if(!field.equals("step")){var nested=base.deepCopy();((ObjectNode)nested.get("core_frame")).put(field,"wrong");denied(nested);}
        }
        for(String field:List.of("paused","map_ready","played_character_alive")){
            var changed=base.deepCopy();((ObjectNode)changed.get("core_frame")).put(field,false);denied(changed);
        }
        var absent=base.deepCopy();var core=(ObjectNode)absent.get("core_frame");core.put("has_played_character",false).put("played_character_id",-1).put("played_character_alive",false);denied(absent);
        for(String field:List.of("complete_snapshot","treasury_observed","monthly_flow_observed")){var changed=base.deepCopy();changed.put(field,true);denied(changed);}
        var noMain=base.deepCopy();noMain.put("application_main_observed",false);denied(noMain);
        var unavailable=result(INPUTS.getLast());var invented=unavailable.deepCopy();invented.set("personal_gold",base.get("personal_gold"));denied(invented);
        var wrongReason=unavailable.deepCopy();wrongReason.putNull("unavailable_reason");denied(wrongReason);
        var mixedMain=unavailable.deepCopy();mixedMain.put("application_main_observed",true);denied(mixedMain);
        assertThrows(IllegalArgumentException.class,()->PersonalGoldFrame.decode(RegistryJson.encode(base),PersonalGoldFrame.Version.V1));
        var partial=assertInstanceOf(PersonalGoldFrame.Partial.class,PersonalGoldFrame.decodeV2(RegistryJson.encode(base)));
        assertThrows(IllegalArgumentException.class,()->new PersonalGoldFrame.Partial(partial.coreFrame(),partial.personalGold()),"old constructor retains V1 qualification");
    }

    @Test void originalOutboundVersionAndReturnedVersionMustAgreeBeforeCodecCanProduceTypedData()throws Exception {
        var cpp=original(INPUTS.getFirst());
        assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(ack(cpp,PersonalGoldFrame.STEP)));
        assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(ack(cpp,CoreFrame.STEP)));
        var correct=ack(cpp,PersonalGoldFrame.Version.V2.step());
        var missing=new NativeActionPort.AckReceived(correct.requestId(),true,correct.originalResultToken(),correct.originalFrame(),correct.originalPacket());
        assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(missing));
        var tokenChanged=new NativeActionPort.AckReceived(correct.requestId(),true,Optional.of(new RawJson("{}".getBytes(StandardCharsets.UTF_8))),correct.originalFrame(),correct.originalPacket(),correct.outbound());
        assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(tokenChanged));
        assertTrue(correct.custody().isEmpty(),"codec DATA does not fabricate private receiver custody or owner");
    }
}
