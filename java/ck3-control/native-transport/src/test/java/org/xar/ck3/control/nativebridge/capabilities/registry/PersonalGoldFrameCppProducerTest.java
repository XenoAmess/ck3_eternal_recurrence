package org.xar.ck3.control.nativebridge.capabilities.registry;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.*;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.semantic.NativePlayedResources;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Exact C++ command_result originals -> public DATA codecs only; no fake custody, Received, Full, Root or action role. */
final class PersonalGoldFrameCppProducerTest {
    private record Original(String name,int bytes,String sha256){ }
    private static final Original NORMAL=new Original("personal-gold-producer-partial01.json",1233,"06fcc7b418e46dff6a27ab72533ca7b8444077d33ccc7aaeadd07cfbc93d208f");
    private static final Original MINIMUM=new Original("personal-gold-producer-minimum01.json",1245,"a7eb0f993a1093a10951145a9e7d2404be90ccfb9b26ecb8bb1a85cf7d54da87");
    private static final Original UNAVAILABLE=new Original("personal-gold-producer-unavailable01.json",1262,"a8d48e467883f294799909a81951e77fee43797113e9c2fd1a65f0b4c12fe942");
    private static byte[] original(Original input)throws Exception {
        String directory=System.getProperty("xar.native.personalGold1210.fixtures");byte[] body;
        if(directory==null||directory.isBlank()) {
            try(var stream=PersonalGoldFrameCppProducerTest.class.getResourceAsStream("/newnative/personal-gold1210/"+input.name())) {
                if(stream==null)throw new IOException("exact native personal-gold resource missing: "+input.name());body=stream.readNBytes(input.bytes()+1);
            }
        }else {
            var root=Path.of(directory);if(!root.isAbsolute())throw new IOException("absolute actual personal-gold fixture directory required");
            try(var stream=Files.newInputStream(root.resolve(input.name()))){body=stream.readNBytes(input.bytes()+1);}
        }
        assertEquals(input.bytes(),body.length);assertEquals(input.sha256(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body)));return body;
    }
    /** Public outcome DATA assembled from actual C++ bytes and the real Java outbound encoder, never a receiver/chronology oracle. */
    private static NativeActionPort.AckReceived outcome(byte[] body)throws Exception {
        byte[] packet=NativeWire.packet(body);assertArrayEquals(body,Arrays.copyOfRange(packet,4,packet.length));
        var result=assertInstanceOf(NativeWire.CommandResult.class,NativeWire.decode(packet));
        var outbound=NativeWire.execute(result.requestId(),PersonalGoldFrame.STEP,BigInteger.ZERO,utf8("{}"));
        return new NativeActionPort.AckReceived(result.requestId(),result.nativeOk(),result.result().token().map(value->new RawJson(value.value())),
                new RawJson(result.payload().value()),packet,Optional.of(new NativeActionPort.OutboundPacket(result.requestId(),outbound)));
    }
    private static ObjectNode result(Original source)throws Exception {return RegistryJson.object(outcome(original(source)).originalResultToken().orElseThrow());}
    private static byte[] utf8(String value){return value.getBytes(StandardCharsets.UTF_8);}
    private static void denied(ObjectNode row){assertThrows(IllegalArgumentException.class,()->PersonalGoldFrame.decode(RegistryJson.encode(row)));}

    @Test void exactCppNormalMinimumAndUnavailablePreserveTheirNativeDataAndNarrowClaims()throws Exception {
        for(var source:List.of(NORMAL,MINIMUM,UNAVAILABLE)) {
            var ack=outcome(original(source));assertTrue(ack.custody().isEmpty(),"public DATA does not invent real receive custody");
            var actual=PersonalGoldFramePublicCodec.decodeOutcome(ack);assertEquals(ExactCk3Build.CK3_1210,actual.build());
            var nativeValue=RegistryJson.object(ack.originalResultToken().orElseThrow());var publicValue=RegistryJson.object(PersonalGoldFramePublicCodec.encode(actual));
            assertEquals(nativeValue,publicValue);assertFalse(publicValue.get("complete_snapshot").booleanValue());
            assertFalse(publicValue.get("treasury_observed").booleanValue());assertFalse(publicValue.get("monthly_flow_observed").booleanValue());
            assertEquals(actual,PersonalGoldFrame.decode(PersonalGoldFramePublicCodec.encode(actual)));
            if(source==UNAVAILABLE) {
                var missing=assertInstanceOf(PersonalGoldFrame.Unavailable.class,actual);assertFalse(missing.applicationMainObserved());
                assertEquals("personal_gold_not_read",missing.reason());assertInstanceOf(CoreFrame.Unavailable.class,missing.coreFrame());
                assertTrue(publicValue.get("personal_gold").isNull());assertEquals(nativeValue.get("core_frame"),publicValue.get("core_frame"));
            }else {
                var partial=assertInstanceOf(PersonalGoldFrame.Partial.class,actual);assertTrue(partial.applicationMainObserved());
                assertEquals(source==NORMAL?12345000L:Long.MIN_VALUE,partial.personalGold().raw());assertEquals(100000,partial.personalGold().scale());
                var core=partial.coreFrame().prefix();assertEquals(123456,core.dateRaw());assertEquals(5,core.speed());assertEquals(7,core.localPlayerId());
                assertEquals(16777217,core.playedCharacterId());assertTrue(core.mapReady()&&core.paused()&&core.hasPlayedCharacter()&&core.playedCharacterAlive());
            }
        }
    }

    @Test void everyMixedBuildAndBroaderSnapshotClaimIsRejected()throws Exception {
        var original=result(NORMAL);
        for(String field:List.of("step","schema","game_version","executable_sha256","adapter_id","backend")) {
            var changed=original.deepCopy();String wrong=switch(field) {
                case "step"->CoreFrame.STEP;case "schema"->"ck3_12004_personal_gold_frame_v1";case "game_version"->"1.21.0.0";
                case "executable_sha256"->ExactCk3Build.CK3_12004.executableSha256();case "adapter_id"->"ck3-1.20.0.4-msvc-x64";
                case "backend"->"ck3-1.20.0.4-native-headless-main-thread";default->throw new AssertionError(field);};
            changed.put(field,wrong);denied(changed);
        }
        for(String field:List.of("complete_snapshot","treasury_observed","monthly_flow_observed")){var changed=original.deepCopy();changed.put(field,true);denied(changed);}
        var nested=original.deepCopy();((ObjectNode)nested.get("core_frame")).put("complete_snapshot",true);denied(nested);
        var actual=assertInstanceOf(PersonalGoldFrame.Partial.class,PersonalGoldFrame.decode(RegistryJson.encode(original)));
        var old=original.deepCopy();old.set("core_frame",RegistryJson.object(CoreFramePublicCodec.encode(new CoreFrame.Partial(ExactCk3Build.CK3_12004,actual.coreFrame().prefix()))));denied(old);
        for(String field:List.of("map_ready","paused","has_played_character","played_character_alive")) {
            var changed=original.deepCopy();((ObjectNode)changed.get("core_frame")).put(field,false);denied(changed);
        }
    }

    @Test void allBooleanAndIntegerFieldsRejectCoercionMissingAndOverflow()throws Exception {
        var original=result(NORMAL);var factory=JsonNodeFactory.instance;
        var badBooleans=List.of(factory.numberNode(1),factory.textNode("true"),factory.nullNode(),factory.numberNode(new BigDecimal("1.0")));
        for(String field:List.of("complete_snapshot","treasury_observed","monthly_flow_observed","personal_gold_available","application_main_observed")) {
            for(var token:badBooleans){var changed=original.deepCopy();changed.set(field,token);denied(changed);}
            var missing=original.deepCopy();missing.remove(field);denied(missing);
        }
        for(String field:List.of("complete_snapshot","core_available","application_main_observed","paused","map_ready","has_played_character","played_character_alive")) {
            for(var token:badBooleans){var changed=original.deepCopy();((ObjectNode)changed.get("core_frame")).set(field,token);denied(changed);}
            var missing=original.deepCopy();((ObjectNode)missing.get("core_frame")).remove(field);denied(missing);
        }
        var badIntegers=List.of(factory.booleanNode(true),factory.textNode("1"),factory.nullNode(),factory.numberNode(new BigDecimal("1.0")));
        for(String field:List.of("date_raw","speed","local_player_id","played_character_id")) {
            for(var token:badIntegers){var changed=original.deepCopy();((ObjectNode)changed.get("core_frame")).set(field,token);denied(changed);}
            for(var overflow:List.of(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE),BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE))) {
                var changed=original.deepCopy();((ObjectNode)changed.get("core_frame")).put(field,overflow);denied(changed);
            }
            var missing=original.deepCopy();((ObjectNode)missing.get("core_frame")).remove(field);denied(missing);
        }
        for(String field:List.of("raw","scale")) {
            for(var token:badIntegers){var changed=original.deepCopy();((ObjectNode)changed.get("personal_gold")).set(field,token);denied(changed);}
            var missing=original.deepCopy();((ObjectNode)missing.get("personal_gold")).remove(field);denied(missing);
        }
        for(var overflow:List.of(BigInteger.valueOf(Long.MIN_VALUE).subtract(BigInteger.ONE),BigInteger.valueOf(Long.MAX_VALUE).add(BigInteger.ONE))) {
            var changed=original.deepCopy();((ObjectNode)changed.get("personal_gold")).put("raw",overflow);denied(changed);
        }
        for(int scale:List.of(99999,100001)){var changed=original.deepCopy();((ObjectNode)changed.get("personal_gold")).put("scale",scale);denied(changed);}
        var extra=original.deepCopy();((ObjectNode)extra.get("personal_gold")).put("monthly_income",0);denied(extra);
    }

    @Test void unavailableRetainsNullReasonAndNestedCoreWithoutInventingZeroOrApplicationMain()throws Exception {
        var unavailable=result(UNAVAILABLE);var available=result(NORMAL);
        for(String field:List.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive")) {
            var changed=unavailable.deepCopy();((ObjectNode)changed.get("core_frame")).set(field,available.get("core_frame").get(field));denied(changed);
        }
        var zero=unavailable.deepCopy();zero.set("personal_gold",NativePlayedResources.encode(new NativePlayedResources.Amount(0)));denied(zero);
        var absent=available.deepCopy();absent.putNull("personal_gold");denied(absent);
        var outer=unavailable.deepCopy();outer.put("application_main_observed",true);denied(outer);
        var nested=unavailable.deepCopy();((ObjectNode)nested.get("core_frame")).put("application_main_observed",true);denied(nested);
        for(var reason:List.of(JsonNodeFactory.instance.nullNode(),JsonNodeFactory.instance.textNode(""),JsonNodeFactory.instance.numberNode(1))) {
            var changed=unavailable.deepCopy();changed.set("unavailable_reason",reason);denied(changed);
        }
        // A public DTO composition, not a new native oracle: a genuine core may survive a failed gold read.
        var core=assertInstanceOf(PersonalGoldFrame.Partial.class,PersonalGoldFrame.decode(RegistryJson.encode(available))).coreFrame();
        var reason=assertInstanceOf(PersonalGoldFrame.Unavailable.class,PersonalGoldFrame.decode(RegistryJson.encode(unavailable))).reason();
        var retained=new PersonalGoldFrame.Unavailable(core,true,reason);var row=RegistryJson.object(PersonalGoldFramePublicCodec.encode(retained));
        assertTrue(row.get("personal_gold").isNull());assertEquals(available.get("core_frame"),row.get("core_frame"));assertEquals(retained,PersonalGoldFrame.decode(RegistryJson.encode(row)));
        assertThrows(IllegalArgumentException.class,()->new PersonalGoldFrame.Unavailable(core,false,reason));
    }

    @Test void outcomeRequiresExactOriginalOutboundEnvelopeAndResultToken()throws Exception {
        var ack=outcome(original(NORMAL));String id=ack.requestId();byte[] empty=utf8("{}");
        for(byte[] request:List.of(NativeWire.execute(id,CoreFrame.STEP,BigInteger.ZERO,empty),
                NativeWire.execute(id,PersonalGoldFrame.STEP,BigInteger.ONE,empty),
                NativeWire.executePrivateQuery(id,PersonalGoldFrame.STEP,BigInteger.ZERO,empty),
                NativeWire.executeSnapshotRevisionOnly(id,PersonalGoldFrame.STEP,BigInteger.ZERO,empty),
                NativeWire.execute(id,PersonalGoldFrame.STEP,BigInteger.ZERO,RegistryJson.encode(JsonNodeFactory.instance.objectNode().put("actor_id",7)).bytes()),
                NativeWire.execute("foreign-request",PersonalGoldFrame.STEP,BigInteger.ZERO,empty))) {
            var changed=new NativeActionPort.AckReceived(id,ack.nativeOk(),ack.originalResultToken(),ack.originalFrame(),ack.originalPacket(),
                    Optional.of(new NativeActionPort.OutboundPacket(id,request)));
            assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(changed));
        }
        var missingOutbound=new NativeActionPort.AckReceived(id,ack.nativeOk(),ack.originalResultToken(),ack.originalFrame(),ack.originalPacket());
        assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(missingOutbound));
        for(var token:List.<Optional<RawJson>>of(Optional.empty(),Optional.of(new RawJson(utf8("{}"))))) {
            var changed=new NativeActionPort.AckReceived(id,ack.nativeOk(),token,ack.originalFrame(),ack.originalPacket(),ack.outbound());
            assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(changed));
        }
        var wrongFrame=new NativeActionPort.AckReceived(id,ack.nativeOk(),ack.originalResultToken(),new RawJson(utf8("{}")),ack.originalPacket(),ack.outbound());
        assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(wrongFrame));
        var wrongOk=new NativeActionPort.AckReceived(id,false,ack.originalResultToken(),ack.originalFrame(),ack.originalPacket(),ack.outbound());
        assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(wrongOk));
        var shifted=RegistryJson.object(ack.originalFrame()).deepCopy();shifted.put("request_id","foreign-request");
        var wrongPacket=new NativeActionPort.AckReceived(id,ack.nativeOk(),ack.originalResultToken(),ack.originalFrame(),NativeWire.packet(RegistryJson.encode(shifted).bytes()),ack.outbound());
        assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(wrongPacket));
        var unknown=new NativeActionPort.Unknown(id,"software result unresolved",ack.outbound().orElseThrow().originalPacket(),Optional.empty());
        assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(unknown));
        var rejected=new NativeActionPort.RejectedBeforeDispatch(id,new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,0,"software source missing",Optional.empty()));
        assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(rejected));
        assertTrue(ack.custody().isEmpty(),"this codec tested public DATA only, no private source/read role");
    }

    @Test void closedEnvelopeAndNoArgumentContractRejectWrongShapesAndTypedAliases()throws Exception {
        for(var arguments:List.<PublicBindings.Arguments>of(new PublicBindings.Missing(),new PublicBindings.Null(),new PublicBindings.Value(new RawJson(utf8("{}")))))
            assertEquals(PersonalGoldFramePublicCodec.Request.INSTANCE,PersonalGoldFramePublicCodec.decodeArguments(arguments));
        for(var json:List.of("null","[]","0","false"))
            assertThrows(IllegalArgumentException.class,()->PersonalGoldFramePublicCodec.decodeArguments(new PublicBindings.Value(new RawJson(utf8(json)))));
        var named=JsonNodeFactory.instance.objectNode().put("personal_gold",false);
        assertThrows(IllegalArgumentException.class,()->PersonalGoldFramePublicCodec.decodeArguments(new PublicBindings.Value(RegistryJson.encode(named))));
        var actual=outcome(original(NORMAL));var originalEnvelope=RegistryJson.object(actual.originalFrame());
        for(String changed:List.of("missing","null","extra","protocol_boolean","ok_integer","negative")) {
            var envelope=originalEnvelope.deepCopy();
            switch(changed) {
                case "missing"->envelope.remove("result");case "null"->envelope.putNull("result");case "extra"->envelope.put("treasury_observed",false);
                case "protocol_boolean"->envelope.put("protocol_version",true);case "ok_integer"->envelope.put("ok",1);case "negative"->envelope.put("ok",false);
                default->throw new AssertionError(changed);
            }
            assertThrows(IOException.class,()->PersonalGoldFramePublicCodec.decodeOutcome(outcome(RegistryJson.encode(envelope).bytes())),changed);
        }
        var extra=result(NORMAL);extra.put("treasury",0);denied(extra);
        var missing=result(NORMAL);missing.remove("core_frame");denied(missing);
        var nullCore=result(NORMAL);nullCore.putNull("core_frame");denied(nullCore);
        // Duplicate detection is exercised on the genuine token bytes, without making a new positive oracle.
        String originalToken=new String(actual.originalResultToken().orElseThrow().bytes(),StandardCharsets.UTF_8);
        String key=Character.toString(34)+"step"+Character.toString(34)+":";
        String duplicate=originalToken.replace(key,key+Character.toString(34)+PersonalGoldFrame.STEP+Character.toString(34)+","+key);
        assertNotEquals(originalToken,duplicate);
        assertThrows(IllegalArgumentException.class,()->PersonalGoldFrame.decode(new RawJson(utf8(duplicate))));
    }
}
