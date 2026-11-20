package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiControlsFrameV2;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiControlsFrameV2PublicCodec;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2;

/** Actual C++ SYNTHETIC DATA/NoGame and authored transport only. No runtime row selector is inferred. */
final class NativeGuiControls26785313V2ProducerTest {
    static final String ROOT="/newnative/gui-controls26785313-v2/";
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(999)));
    static byte[] cpp(String name)throws Exception{
        byte[] raw;try(var in=NativeGuiControls26785313V2ProducerTest.class.getResourceAsStream(ROOT+name)){if(in==null)throw new IOException("actual C++ producer required: "+name);raw=in.readNBytes(16385);assertTrue(raw.length<=16384);}
        try(var in=NativeGuiControls26785313V2ProducerTest.class.getResourceAsStream(ROOT+"producer-pins.json")){if(in==null)throw new IOException("actual producer pins required");var p=StrictJson.parse(in.readNBytes(16384)).get(name);assertNotNull(p);assertEquals(p.path("bytes").intValue(),raw.length);assertEquals(p.path("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));}return raw;
    }
    static ObjectNode result(String name)throws Exception{return (ObjectNode)StrictJson.parse(cpp(name)).get("result");}
    static ObjectNode query()throws Exception{return result("available-query-SYNTHETIC-DATA.json");}
    static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value));}
    static void reject(ObjectNode value){assertThrows(IllegalArgumentException.class,()->GuiControlsFrameV2.decode(raw(value)));}
    @Test void actualCppQueryActivationAndNoGameRoundTripWithoutEffectOrSaveCredit()throws Exception{
        for(String name:List.of("available-query-SYNTHETIC-DATA.json","submitted-SYNTHETIC-DATA.json","disabled-SYNTHETIC-DATA.json","indeterminate-SYNTHETIC-DATA.json","unavailable-NoGame.json","wrong-tuple-unavailable.json")){
            var frame=GuiControlsFrameV2.decode(raw(result(name)));assertEquals(frame,GuiControlsFrameV2.decode(GuiControlsFrameV2PublicCodec.encode(frame)));var normalized=StrictJson.parse(GuiControlsFrameV2PublicCodec.encode(frame).bytes());
            for(String key:List.of("effect_confirmed","physical_save_confirmed","complete_snapshot","full_snapshot_before_verified","complete_gui_tree"))assertFalse(normalized.path(key).booleanValue());
        }
        var submitted=GuiControlsFrameV2.decode(raw(result("submitted-SYNTHETIC-DATA.json")));assertTrue(submitted.effectAttempted());assertTrue(submitted.verificationPending());assertTrue(submitted.nativeHandled());assertFalse(submitted.queryAvailable());
        var available=GuiControlsFrameV2.decode(raw(query()));assertEquals(new BigInteger("18446744073709551615"),available.queryGeneration().orElseThrow());assertEquals(152,available.sourceRiteId().orElseThrow());
    }
    @Test void requestsHaveStrictCoreSourceAndStringTokenDiscriminators()throws Exception{
        for(String name:List.of("query-request-v2.json","activate-request-v2.json")){var request=GuiControlsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(cpp(name)));assertEquals(request,GuiControlsFrameV2PublicCodec.decodeRequestPacket(NativeWire.execute("java-controls-1",request.operation().step(),BigInteger.ZERO,GuiControlsFrameV2PublicCodec.additionalFields(request).bytes())));}
        for(String key:List.of("query_generation","widget_id"))for(String bad:List.of("0","01","+1","-1","18446744073709551616")){var row=(ObjectNode)StrictJson.parse(cpp("activate-request-v2.json"));((ObjectNode)row.path("gui_control")).put(key,bad);assertThrows(IllegalArgumentException.class,()->GuiControlsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(row))));}
        var numeric=(ObjectNode)StrictJson.parse(cpp("activate-request-v2.json"));((ObjectNode)numeric.path("gui_control")).put("widget_id",2);assertThrows(IllegalArgumentException.class,()->GuiControlsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(numeric))));
        var faith=(ObjectNode)StrictJson.parse(cpp("activate-request-v2.json"));((ObjectNode)faith.path("gui_control")).put("window_name","faith_window").remove("expected_source_rite_id");assertThrows(IllegalArgumentException.class,()->GuiControlsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(faith))));
        var missing=(ObjectNode)StrictJson.parse(cpp("query-request-v2.json"));((ObjectNode)missing.path("gui_control")).remove("expected_source_rite_id");assertThrows(IllegalArgumentException.class,()->GuiControlsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(missing))));
    }
    @Test void fieldTypesRowsSourceCoreAndPendingFlagsCannotBeRelaxed()throws Exception{
        for(String key:GuiControlsFrameV2.FIELDS){var row=query();row.remove(key);reject(row);}
        for(String key:List.of("effect_confirmed","physical_save_confirmed","complete_snapshot","full_snapshot_before_verified","complete_gui_tree")){var row=query();row.put(key,true);reject(row);}
        var pointer=query();pointer.put("widget_address","1");reject(pointer);var source=query();source.put("source_rite_id",4294967295L);reject(source);
        var typed=query();typed.put("query_generation",1);reject(typed);var callback=query();((ObjectNode)callback.path("widgets").get(1)).put("enabled",false);reject(callback);
        var duplicate=query();((ObjectNode)duplicate.path("widgets").get(1)).put("widget_id","1");reject(duplicate);var path=query();((ObjectNode)path.path("widgets").get(1)).put("child_path","01");reject(path);
        var pending=result("submitted-SYNTHETIC-DATA.json");pending.put("verification_pending",false);reject(pending);
        var noCore=query();noCore.put("core_before_verified",false);reject(noCore);
        var zeroActor=query();((ObjectNode)zeroActor.path("core_frame")).put("played_character_id",0);reject(zeroActor);
        var dup=new String(cpp("available-query-SYNTHETIC-DATA.json"),StandardCharsets.UTF_8).replace("\"query_available\":true","\"query_available\":true,\"query_available\":true");assertThrows(IllegalArgumentException.class,()->GuiControlsFrameV2PublicCodec.decodePacket(new RawJson(dup.getBytes(StandardCharsets.UTF_8)),"controls-qa-1"));
    }
    static NativePipeEndpoint.Config config(){var b=GuiControlsFrameV2.BUILD;return new NativePipeEndpoint.Config("\\\\.\\pipe\\controls-data","controls-data",GAME,"controls-session","controls-bridge",b.executableSha256(),b.coreFrameAdapterId());}
    static NativeGameTransport transport(Replay port){return new NativeGameTransport(port,config(),16,8);}
    static NativeGameTransport.CoreReceived core(NativeGameTransport actual)throws Exception{return assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));}
    static NativeGameTransport.RiteDraftCostsReceived draft(NativeGameTransport actual,NativeGameTransport.CoreReceived before)throws Exception{return assertInstanceOf(NativeGameTransport.RiteDraftCostsReceived.class,actual.readRiteDraftCostsReceived(before,152,before.validUntil()));}
    @Test void sameActualDraftThenQueryThenOneObservedTokenActivationKeepsCustody()throws Exception{
        var source=new Replay(query(),result("submitted-SYNTHETIC-DATA.json"));try(var actual=transport(source)){
            var before=core(actual);var sourceRite=draft(actual,before);var query=assertInstanceOf(NativeGameTransport.GuiControlsReceivedV2.class,actual.readRiteGuiControlsV2(sourceRite,sourceRite.validUntil()));query.requireOriginal(actual,query.validUntil());
            var selected=query.frame().widgets().orElseThrow().get(1); // The actual C++ synthetic fixture's known callback row, never a runtime/Dynastic selector.
            var ack=assertInstanceOf(NativeActionPort.AckReceived.class,actual.submitGuiControlsActivationV2(query,selected,query.validUntil()));ack.custody().orElseThrow().verify(ack);assertEquals(1,source.activationWrites);
            var sent=GuiControlsFrameV2PublicCodec.decodeRequestPacket(ack.outbound().orElseThrow().originalPacket());assertEquals(152,sent.expectedSourceRiteId().orElseThrow());assertEquals(query.frame().queryGeneration().orElseThrow(),sent.selection().orElseThrow().queryGeneration());assertEquals(selected.widgetId(),sent.selection().orElseThrow().widgetId());
            assertEquals(GuiControlsFrameV2.Status.SUBMITTED,GuiControlsFrameV2PublicCodec.decodeOutcome(ack).status());assertTrue(actual.latestObservedSnapshot().isEmpty());assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitGuiControlsActivationV2(query,selected,query.validUntil()));assertEquals(1,source.activationWrites);
        }
    }
    @Test void faithCannotActivateAndForgedForeignOrStaleRowsCannotWrite()throws Exception{
        var faith=query();faith.put("window_name","faith_window").put("rite_source_verified",false).putNull("source_rite_id");for(var n:faith.path("widgets"))((ObjectNode)n).put("native_callback_admissible",false);
        var source=new Replay(faith,result("submitted-SYNTHETIC-DATA.json"));try(var actual=transport(source)){var before=core(actual);var read=assertInstanceOf(NativeGameTransport.GuiControlsReceivedV2.class,actual.readFaithGuiControlsV2(before,before.validUntil()));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitGuiControlsActivationV2(read,read.frame().widgets().orElseThrow().get(0),read.validUntil()));assertEquals(0,source.activationWrites);}
        var ownerPort=new Replay(query(),result("disabled-SYNTHETIC-DATA.json"));var foreignPort=new Replay(query(),result("submitted-SYNTHETIC-DATA.json"));try(var actual=transport(ownerPort);var other=transport(foreignPort)){
            var before=core(actual);var d=draft(actual,before);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,other.readRiteGuiControlsV2(d,d.validUntil()).original());assertEquals(0,foreignPort.writes);
            var read=assertInstanceOf(NativeGameTransport.GuiControlsReceivedV2.class,actual.readRiteGuiControlsV2(d,d.validUntil()));var selected=read.frame().widgets().orElseThrow().get(1);
            var forged=new GuiControlsFrameV2.Widget(BigInteger.valueOf(3),selected.runtimeName(),selected.childPath(),true,true,true);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitGuiControlsActivationV2(read,forged,read.validUntil()));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitGuiControlsActivationV2(read,selected,read.validUntil().plusNanos(1)));assertEquals(0,ownerPort.activationWrites);
            var rejected=assertInstanceOf(NativeActionPort.AckReceived.class,actual.submitGuiControlsActivationV2(read,selected,read.validUntil()));assertEquals(GuiControlsFrameV2.Status.DISABLED,GuiControlsFrameV2PublicCodec.decodeOutcome(rejected).status());assertEquals(1,ownerPort.activationWrites);
        }
    }
    @Test void indeterminateAndMissingReplyRetainOriginalIdBodyAndStopAllReplay()throws Exception{
        for(boolean missing:List.of(false,true)){var source=new Replay(query(),result("indeterminate-SYNTHETIC-DATA.json"));source.dropActivation=missing;try(var actual=transport(source)){var before=core(actual);var d=draft(actual,before);var read=assertInstanceOf(NativeGameTransport.GuiControlsReceivedV2.class,actual.readRiteGuiControlsV2(d,d.validUntil()));var selected=read.frame().widgets().orElseThrow().get(1);var unknown=assertInstanceOf(NativeActionPort.Unknown.class,actual.submitGuiControlsActivationV2(read,selected,read.validUntil()));assertEquals(1,source.activationWrites);assertArrayEquals(source.activationPacket,unknown.originalRequestPacket());if(!missing)assertTrue(actual.originalIndeterminateCoreAcknowledgement(unknown.requestId()).isPresent());assertSame(unknown,actual.submitGuiControlsActivationV2(read,selected,read.validUntil()));assertSame(unknown,actual.submitCoreNormalExit(before,before.validUntil()));assertEquals(1,source.activationWrites);}}
    }
    @Test void unavailableMayRetainPartialBeforeCoreAndAnIdenticalOldGenerationIsNotNewAuthority()throws Exception{
        var unavailable=query();unavailable.put("query_available",false).put("status","unavailable").put("source_abi_pins_verified",false).put("rite_source_verified",false).putNull("source_rite_id").putNull("query_generation").putNull("widgets").put("unavailable_reason","selected_rite_source_changed");
        var frame=GuiControlsFrameV2.decode(raw(unavailable));assertTrue(frame.coreBeforeVerified());assertTrue(frame.ownerWitness().isPresent());assertFalse(frame.queryAvailable());assertEquals(frame,GuiControlsFrameV2.decode(GuiControlsFrameV2PublicCodec.encode(frame)));
        var source=new Replay(query(),result("submitted-SYNTHETIC-DATA.json"));try(var actual=transport(source)){
            var c1=core(actual);var d1=draft(actual,c1);var q1=assertInstanceOf(NativeGameTransport.GuiControlsReceivedV2.class,actual.readRiteGuiControlsV2(d1,d1.validUntil()));
            var c2=core(actual);var d2=draft(actual,c2);var q2=assertInstanceOf(NativeGameTransport.GuiControlsReceivedV2.class,actual.readRiteGuiControlsV2(d2,d2.validUntil()));
            assertEquals(q1.frame().queryGeneration(),q2.frame().queryGeneration());assertNotEquals(q1.original().requestId(),q2.original().requestId());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitGuiControlsActivationV2(q1,q1.frame().widgets().orElseThrow().get(1),q1.validUntil()));assertEquals(0,source.activationWrites);
        }
    }
    @Test void missingCapabilitiesWrongSourceAndUncertainQueryNeverWriteAnActivation()throws Exception{
        var noQuery=new Replay(query(),result("submitted-SYNTHETIC-DATA.json"),false,true);try(var actual=transport(noQuery)){var before=core(actual);var d=draft(actual,before);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.readRiteGuiControlsV2(d,d.validUntil()).original());assertEquals(2,noQuery.writes);assertEquals(0,noQuery.activationWrites);}
        var noActivate=new Replay(query(),result("submitted-SYNTHETIC-DATA.json"),true,false);try(var actual=transport(noActivate)){var before=core(actual);var d=draft(actual,before);var read=assertInstanceOf(NativeGameTransport.GuiControlsReceivedV2.class,actual.readRiteGuiControlsV2(d,d.validUntil()));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.submitGuiControlsActivationV2(read,read.frame().widgets().orElseThrow().get(1),read.validUntil()));assertEquals(0,noActivate.activationWrites);}
        var wrong=query();wrong.put("source_rite_id",153);var drift=new Replay(wrong,result("submitted-SYNTHETIC-DATA.json"));try(var actual=transport(drift)){var before=core(actual);var d=draft(actual,before);var read=assertInstanceOf(NativeGameTransport.GuiControlsReadUnavailableV2.class,actual.readRiteGuiControlsV2(d,d.validUntil()));assertInstanceOf(NativeActionPort.AckReceived.class,read.original());assertEquals(0,drift.activationWrites);}
        var missing=new Replay(query(),result("submitted-SYNTHETIC-DATA.json"));missing.dropQuery=true;try(var actual=transport(missing)){var before=core(actual);var d=draft(actual,before);var unknown=actual.readRiteGuiControlsV2(d,d.validUntil());assertInstanceOf(NativeActionPort.Unknown.class,unknown.original());assertSame(unknown,actual.readRiteGuiControlsV2(d,d.validUntil()));assertEquals(3,missing.writes);assertEquals(0,missing.activationWrites);}
    }
    static final class Replay implements NativePacketPort{
        final ArrayDeque<byte[]> incoming=new ArrayDeque<>();final ObjectNode query,activation;boolean closed,dropActivation,dropQuery;int writes,activationWrites;byte[] activationPacket;
        Replay(ObjectNode query,ObjectNode activation)throws IOException{this(query,activation,true,true);}
        Replay(ObjectNode query,ObjectNode activation,boolean queryCapability,boolean activationCapability)throws IOException{this.query=query;this.activation=activation;var b=GuiControlsFrameV2.BUILD;var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",7).put("bridge_version","controls-bridge").put("expected_ck3_version",b.version()).put("expected_ck3_sha256",b.executableSha256()).put("game_adapter_id",b.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);var capabilities=hello.putArray("capabilities").add(CoreFrame.CAPABILITY);if(queryCapability)capabilities.add(GuiControlsFrameV2.QUERY_CAPABILITY);if(activationCapability)capabilities.add(GuiControlsFrameV2.ACTIVATE_CAPABILITY);incoming.add(NativeWire.packet(StrictJson.canonical(hello)));}
        public void verify()throws IOException{if(closed)throw new IOException("authored source closed");}public void verifyCoreControlWindowPolicy(){/* Authored only; no live window or input qualification. */}public void awaitConnection(Instant deadline)throws IOException{verify();}public byte[] readPacket(Instant deadline)throws IOException{verify();if(incoming.isEmpty())throw new IOException("authored missing reply");return incoming.removeFirst();}
        public void writePacket(byte[] packet,Instant deadline)throws IOException{
            verify();writes++;var request=NativeWire.decodeExecuteRequest(packet);ObjectNode value;
            try{
                if(request.step().equals(CoreFrame.STEP))value=(ObjectNode)NativeGuiControls26785313V2ProducerTest.query().get("core_frame");
                else if(request.step().equals(RiteDraftCostsFrameV2.STEP)){try(var in=getClass().getResourceAsStream("/newnative/rite-draft-costs26785313-v2/partial-native-false-SYNTHETIC-DATA.json")){if(in==null)throw new IOException("sealed a30 actual source resource absent");value=(ObjectNode)StrictJson.parse(in.readNBytes(16384)).get("result");}}
                else {var typed=GuiControlsFrameV2PublicCodec.decodeRequestPacket(packet);if(typed.operation()==GuiControlsFrameV2.Operation.ACTIVATE){activationWrites++;activationPacket=packet.clone();if(dropActivation)return;value=activation;}else {if(dropQuery)return;value=query;}}
            }catch(Exception invalid){throw new IOException(invalid);}
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);envelope.set("result",value);incoming.add(NativeWire.packet(StrictJson.canonical(envelope)));
        }
        public void close(){closed=true;}
    }
}
