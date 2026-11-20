package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
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
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2;
import org.xar.ck3.control.nativebridge.capabilities.registry.RiteDraftCostsFrameV2PublicCodec;

/** Exact C++ Can/cost DATA plus authored source. Never evaluates a live observer or edits/saves. */
final class NativeRiteDraftCosts26785313ProducerTest {
    static final String ROOT="/newnative/rite-draft-costs26785313-v2/";
    static final String FALSE="partial-native-false-SYNTHETIC-DATA.json",TRUE="partial-native-true-missing-piety-SYNTHETIC-DATA.json";
    static final ExactCk3Build BUILD=RiteDraftCostsFrameV2.BUILD;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(999)));
    static byte[] cpp(String name)throws Exception{
        byte[] bytes;try(var in=NativeRiteDraftCosts26785313ProducerTest.class.getResourceAsStream(ROOT+name)){if(in==null)throw new IOException("actual C++ golden required: "+name);bytes=in.readNBytes(16385);assertTrue(bytes.length<=16384);}
        try(var in=NativeRiteDraftCosts26785313ProducerTest.class.getResourceAsStream(ROOT+"producer-pins.json")){if(in==null)throw new IOException("actual source pins required");var pin=StrictJson.parse(in.readNBytes(16384)).get(name);assertNotNull(pin);assertEquals(pin.path("bytes").intValue(),bytes.length);assertEquals(pin.path("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));}return bytes;
    }
    static ObjectNode envelope(String file)throws Exception{return (ObjectNode)StrictJson.parse(cpp(file));}
    static ObjectNode result()throws Exception{return (ObjectNode)envelope(FALSE).get("result");}
    static RawJson raw(ObjectNode value){return new RawJson(StrictJson.canonical(value));}
    static CoreFrame.Partial core()throws Exception{return (CoreFrame.Partial)RiteDraftCostsFrameV2.decode(raw(result())).coreFrame();}
    static void reject(ObjectNode value){assertThrows(IllegalArgumentException.class,()->RiteDraftCostsFrameV2.decode(raw(value)));}
    @Test void exactCppNativeFalseAndTrueWithoutPietyRemainAvailableIndependentFacts()throws Exception{
        var no=assertInstanceOf(RiteDraftCostsFrameV2.Partial.class,RiteDraftCostsFrameV2PublicCodec.decodePacket(new RawJson(cpp(FALSE)),"rite-qa-1"));
        assertFalse(no.draft().canEditRiteNative());assertTrue(no.draft().hasEnoughPiety());assertEquals(Long.MAX_VALUE,no.draft().pietyCostRaw());assertEquals(Long.MIN_VALUE,no.draft().pietyMissingSignedRaw());
        var yes=assertInstanceOf(RiteDraftCostsFrameV2.Partial.class,RiteDraftCostsFrameV2PublicCodec.decodePacket(new RawJson(cpp(TRUE)),"rite-qa-1"));
        assertTrue(yes.draft().canEditRiteNative());assertFalse(yes.draft().hasEnoughPiety());assertEquals(1,yes.draft().pietyMissingSignedRaw());
        for(var frame:List.of(no,yes)){assertEquals(frame,RiteDraftCostsFrameV2.decode(RiteDraftCostsFrameV2PublicCodec.encode(frame)));var row=StrictJson.parse(RiteDraftCostsFrameV2PublicCodec.encode(frame).bytes());assertTrue(row.path("draft_available").booleanValue());assertTrue(row.path("full_native_can_edit_evaluated").booleanValue());for(String key:List.of("observer_guard_evaluated","control_actions_available","complete_snapshot","complete_gui_tree","physical_save_confirmed"))assertFalse(row.path(key).booleanValue());}
    }
    @Test void actualCppNoGameAndWrongProfileNeverBecomeZeroOrUnavailableCanFalse()throws Exception{
        for(String name:List.of("unavailable-NoGame.json","wrong-tuple-unavailable.json")){var frame=assertInstanceOf(RiteDraftCostsFrameV2.Unavailable.class,RiteDraftCostsFrameV2PublicCodec.decodePacket(new RawJson(cpp(name)),"rite-qa-1"));assertEquals(frame,RiteDraftCostsFrameV2.decode(RiteDraftCostsFrameV2PublicCodec.encode(frame)));var row=StrictJson.parse(RiteDraftCostsFrameV2PublicCodec.encode(frame).bytes());assertTrue(row.path("draft").isNull());assertTrue(row.path("owner_witness").isNull());assertFalse(row.path("full_native_can_edit_evaluated").booleanValue());}
    }
    @Test void signed64StringsScaleTypesAndEnoughPredicateAreExact()throws Exception{
        for(String field:List.of("piety_cost_raw","piety_missing_signed_raw"))for(String bad:List.of("-0","01","+1","1.0","9223372036854775808","-9223372036854775809")){var r=result();((ObjectNode)r.path("draft")).put(field,bad);reject(r);}
        for(String field:List.of("piety_cost_raw","piety_missing_signed_raw")){var r=result();((ObjectNode)r.path("draft")).put(field,1);reject(r);}
        for(long missing:new long[]{Long.MIN_VALUE,-1,0,1,Long.MAX_VALUE}){var r=result();((ObjectNode)r.path("draft")).put("piety_missing_signed_raw",Long.toString(missing)).put("has_enough_piety",missing<=0);assertEquals(missing,((RiteDraftCostsFrameV2.Partial)RiteDraftCostsFrameV2.decode(raw(r))).draft().pietyMissingSignedRaw());}
        var lie=result();((ObjectNode)lie.path("draft")).put("has_enough_piety",false);reject(lie);
        var scale=result();((ObjectNode)scale.path("draft")).put("raw_scale",100000.0);reject(scale);var bool=result();((ObjectNode)bool.path("draft")).put("can_edit_rite_native",1);reject(bool);
    }
    @Test void allSourceFieldsActorRiteWitnessAndFixedNoActionsRemainStrict()throws Exception{
        for(String field:RiteDraftCostsFrameV2.FIELDS){var r=result();r.remove(field);reject(r);}
        for(String field:List.of("complete_snapshot","complete_gui_tree","control_actions_available","observer_guard_evaluated","physical_save_confirmed")){var r=result();r.put(field,true);reject(r);}
        var extra=result();extra.put("handler_address","1");reject(extra);var tuple=result();tuple.put("executable_sha256",ExactCk3Build.CK3_1210.executableSha256());reject(tuple);
        for(long id:new long[]{-1,4294967295L,4294967296L}){var r=result();((ObjectNode)r.path("draft")).put("source_rite_id",id);reject(r);}
        var actor=result();((ObjectNode)actor.path("draft")).put("played_character_id",1);reject(actor);var window=result();((ObjectNode)window.path("draft")).put("window_name","faith_window");reject(window);
        for(String value:List.of("0","01","18446744073709551616")){var r=result();((ObjectNode)r.path("owner_witness")).put("ticket_sequence",value);reject(r);}
        var duplicate=new String(cpp(FALSE),StandardCharsets.UTF_8).replace("\"draft_available\":true","\"draft_available\":true,\"draft_available\":true");assertThrows(IllegalArgumentException.class,()->RiteDraftCostsFrameV2PublicCodec.decodePacket(new RawJson(duplicate.getBytes(StandardCharsets.UTF_8)),"rite-qa-1"));
    }
    @Test void actualCppRequestRoundTripsOnlyItsUint32SourceAndOriginalCore()throws Exception{
        var request=RiteDraftCostsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(cpp("request-v2.json")));assertEquals(152,request.expectedSourceRiteId());assertEquals(-16777215,request.expectedCore().prefix().playedCharacterId());
        for(long id:new long[]{0,152,4294967294L}){var r=new RiteDraftCostsFrameV2PublicCodec.Request(request.expectedCore(),request.deadlineUnixMs(),id);assertEquals(r,RiteDraftCostsFrameV2PublicCodec.decodeRequestPacket(NativeWire.execute("rite-java-1",RiteDraftCostsFrameV2.STEP,BigInteger.ZERO,RiteDraftCostsFrameV2PublicCodec.additionalFields(r).bytes())));}
        for(String field:List.of("window_name","connection_generation","controller_address")){var r=envelope("request-v2.json");((ObjectNode)r.path("rite_draft")).put(field,"1");assertThrows(IllegalArgumentException.class,()->RiteDraftCostsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(r))));}
        for(long id:new long[]{-1,4294967295L}){assertThrows(IllegalArgumentException.class,()->new RiteDraftCostsFrameV2PublicCodec.Request(request.expectedCore(),request.deadlineUnixMs(),id));}
        var bool=envelope("request-v2.json");((ObjectNode)bool.path("rite_draft")).put("expected_source_rite_id",true);assertThrows(IllegalArgumentException.class,()->RiteDraftCostsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(bool))));
        var zero=new String(cpp("request-v2.json"),StandardCharsets.UTF_8).replace("\"expected_revision\":0","\"expected_revision\":-0");assertThrows(IllegalArgumentException.class,()->RiteDraftCostsFrameV2PublicCodec.decodeRequestPacket(NativeWire.packet(zero.getBytes(StandardCharsets.UTF_8))));
    }
    static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\rite-cost-DATA","rite-cost-data",GAME,"rite-cost-session","rite-cost-bridge",BUILD.executableSha256(),BUILD.coreFrameAdapterId());}
    static NativeGameTransport transport(Replay port){return new NativeGameTransport(port,config(),16,3);}
    @Test void identicalPrivateCoreSendsOneQueryAndPreservesOriginalCostAckCustody()throws Exception{
        var source=new Replay(result());try(var actual=transport(source)){var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));var read=assertInstanceOf(NativeGameTransport.RiteDraftCostsReceived.class,actual.readRiteDraftCostsReceived(before,152,before.validUntil()));read.requireOriginal(actual,read.validUntil());read.original().custody().orElseThrow().verify(read.original());assertFalse(((RiteDraftCostsFrameV2.Partial)read.frame()).draft().canEditRiteNative());var request=RiteDraftCostsFrameV2PublicCodec.decodeRequestPacket(read.original().outbound().orElseThrow().originalPacket());assertEquals(before.frame(),request.expectedCore());assertEquals(152,request.expectedSourceRiteId());assertEquals(2,source.writes);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.readRiteDraftCostsReceived(before,153,before.validUntil()).original());assertEquals(2,source.writes);assertTrue(actual.latestObservedSnapshot().isEmpty());}
    }
    @Test void foreignCoreSourceMismatchDeadlineAndUnknownCannotBorrowOrReplay()throws Exception{
        var source=new Replay(result());var other=new Replay(result());try(var actual=transport(source);var foreign=transport(other)){var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,foreign.readRiteDraftCostsReceived(before,152,before.validUntil()).original());assertEquals(0,other.writes);assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.readRiteDraftCostsReceived(before,152,before.validUntil().plusNanos(1)).original());assertEquals(1,source.writes);var mismatch=assertInstanceOf(NativeGameTransport.RiteDraftCostsReadUnavailable.class,actual.readRiteDraftCostsReceived(before,153,before.validUntil()));assertInstanceOf(NativeActionPort.AckReceived.class,mismatch.original());assertEquals(2,source.writes);}
        var missing=new Replay(result());missing.dropReply=true;try(var actual=transport(missing)){var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));var unknown=actual.readRiteDraftCostsReceived(before,152,before.validUntil());assertInstanceOf(NativeActionPort.Unknown.class,unknown.original());assertSame(unknown,actual.readRiteDraftCostsReceived(before,152,before.validUntil()));assertEquals(2,missing.writes);}
    }
    static final class Replay implements NativePacketPort{
        final ArrayDeque<byte[]> incoming=new ArrayDeque<>();final ObjectNode reply;boolean closed,dropReply;int writes;
        Replay(ObjectNode reply)throws IOException{this.reply=reply;var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",7).put("bridge_version","rite-cost-bridge").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);hello.putArray("capabilities").add(CoreFrame.CAPABILITY);incoming.add(NativeWire.packet(StrictJson.canonical(hello)));}
        public void verify()throws IOException{if(closed)throw new IOException("authored source closed");}public void verifyCoreControlWindowPolicy(){/* Authored only: no real window qualification. */}public void awaitConnection(Instant deadline)throws IOException{verify();}
        public byte[] readPacket(Instant deadline)throws IOException{verify();if(incoming.isEmpty())throw new IOException("authored missing reply");return incoming.removeFirst();}
        public void writePacket(byte[] packet,Instant deadline)throws IOException{verify();writes++;var request=NativeWire.decodeExecuteRequest(packet);ObjectNode data;if(request.step().equals(CoreFrame.STEP)){try{data=(ObjectNode)result().get("core_frame");}catch(Exception failure){throw new IOException(failure);}}else{assertEquals(RiteDraftCostsFrameV2.STEP,request.step());RiteDraftCostsFrameV2PublicCodec.decodeRequestPacket(packet);if(dropReply)return;data=reply;}var env=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);env.set("result",data);incoming.add(NativeWire.packet(StrictJson.canonical(env)));}
        public void close(){closed=true;}
    }
}
