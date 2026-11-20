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
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiRootIndexFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiRootIndexFramePublicCodec;

/** Genuine C++ golden DATA through Java codec/transport. No actual Game, main owner, GUI or action credit. */
final class NativeGuiRootIndex26785313ProducerTest {
    private static final ExactCk3Build BUILD=GuiRootIndexFrame.BUILD;
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static byte[] cpp(String name)throws Exception {
        String sha=switch(name) {
            case "request-v1.json"->"3726e73185e77197d79f8575cb16326a5bc95031e621228aeca467198df5bc02";
            case "partial-SYNTHETIC-DATA.json"->"3eb3daa81afaf3ed86078e306353e4a991327a7d5632a16a6a6d3b247b956f85";
            case "unavailable-NoGame.json"->"5a8adcc195fa84c20f31fbfc80bd5c8f552bd3b4590ed6cb82416bf2339460f9";
            case "missing-owner-unavailable.json"->"e4066a4fe445b3945a3059c872fcd8a47d842ca222ec6d8984812a631a630375";
            case "wrong-tuple-unavailable.json"->"ebda0d0cfbecc312676f6a66409a83f9d52d6a1ebb05f953e65bf65e70d4604b";
            default->throw new IllegalArgumentException(name);
        };
        try(var input=NativeGuiRootIndex26785313ProducerTest.class.getResourceAsStream("/newnative/gui-root-index26785313-v1/"+name)) {
            if(input==null)throw new IOException("actual C++ fixture missing: "+name);
            byte[] bytes=input.readNBytes(4097);assertTrue(bytes.length<=4096);
            assertEquals(sha,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));return bytes;
        }
    }
    private static ObjectNode envelope(String name)throws Exception{return NativeWire.object(NativeWire.parse(cpp(name)));}
    private static ObjectNode result()throws Exception{return (ObjectNode)envelope("partial-SYNTHETIC-DATA.json").get("result");}
    private static RawJson raw(ObjectNode node){return new RawJson(StrictJson.canonical(node));}
    private static CoreFrame.Partial core()throws Exception{return (CoreFrame.Partial)CoreFrame.decode(raw((ObjectNode)result().get("core_frame")));}
    private static void reject(ObjectNode altered){assertThrows(IllegalArgumentException.class,()->GuiRootIndexFrame.decode(raw(altered)));}

    @Test void genuineCppRequestAndPartialRoundtripWithoutExpandingTheRole()throws Exception {
        var request=GuiRootIndexFramePublicCodec.decodeRequestPacket(NativeWire.packet(cpp("request-v1.json")));
        assertEquals(-16777215,request.expectedCore().prefix().playedCharacterId());assertEquals(new BigInteger("4102444800000"),request.deadlineUnixMs());
        byte[] generated=NativeWire.execute("root-qa-1",GuiRootIndexFrame.STEP,BigInteger.ZERO,GuiRootIndexFramePublicCodec.additionalFields(request).bytes());
        assertEquals(request,GuiRootIndexFramePublicCodec.decodeRequestPacket(generated));
        assertEquals(envelope("request-v1.json"),NativeWire.parse(java.util.Arrays.copyOfRange(generated,4,generated.length)));
        var frame=assertInstanceOf(GuiRootIndexFrame.Partial.class,GuiRootIndexFramePublicCodec.decodePacket(new RawJson(cpp("partial-SYNTHETIC-DATA.json")),"root-qa-1"));
        assertEquals(2,frame.rootIndex().entryCount());assertEquals(1,frame.rootIndex().emptyEntryCount());assertEquals(BigInteger.valueOf(7),frame.ownerWitness().connectionGeneration());
        assertEquals(frame,GuiRootIndexFrame.decode(GuiRootIndexFramePublicCodec.encode(frame)));
        var encoded=NativeWire.object(NativeWire.parse(GuiRootIndexFramePublicCodec.encode(frame).bytes()));
        assertTrue(encoded.path("addresses_redacted").booleanValue());assertFalse(encoded.path("complete_gui_tree").booleanValue());assertFalse(encoded.path("control_actions_available").booleanValue());
    }
    @Test void genuineNoGameMissingOwnerAndWrongProfileRemainUnavailableData()throws Exception {
        for(String name:List.of("unavailable-NoGame.json","missing-owner-unavailable.json","wrong-tuple-unavailable.json")) {
            var frame=assertInstanceOf(GuiRootIndexFrame.Unavailable.class,GuiRootIndexFramePublicCodec.decodePacket(new RawJson(cpp(name)),"root-qa-1"));
            assertEquals(frame,GuiRootIndexFrame.decode(GuiRootIndexFramePublicCodec.encode(frame)));
            var encoded=NativeWire.object(NativeWire.parse(GuiRootIndexFramePublicCodec.encode(frame).bytes()));
            assertTrue(encoded.get("root_index").isNull());assertTrue(encoded.get("owner_witness").isNull());
            assertTrue(encoded.path("core_frame").path("date_raw").isNull());
        }
        var mainObserved=envelope("unavailable-NoGame.json");var r=(ObjectNode)mainObserved.get("result");
        r.put("application_main_observed",true);((ObjectNode)r.get("core_frame")).put("application_main_observed",true);
        assertTrue(assertInstanceOf(GuiRootIndexFrame.Unavailable.class,GuiRootIndexFramePublicCodec.decodePacket(raw(mainObserved),"root-qa-1")).coreFrame().applicationMainObserved());
    }
    @Test void fullUint64WitnessStringsAndSignedActorBoundsRemainExact()throws Exception {
        var r=result();var owner=(ObjectNode)r.get("owner_witness");owner.put("connection_generation","18446744073709551615").put("ticket_sequence","9223372036854775808").put("pump_epoch","9007199254740993").put("thread_id",4294967295L);
        var p=assertInstanceOf(GuiRootIndexFrame.Partial.class,GuiRootIndexFrame.decode(raw(r)));
        assertEquals(new BigInteger("18446744073709551615"),p.ownerWitness().connectionGeneration());assertEquals(p,GuiRootIndexFrame.decode(GuiRootIndexFramePublicCodec.encode(p)));
        for(int id:new int[]{Integer.MIN_VALUE,0,Integer.MAX_VALUE}) {
            var prefix=core().prefix();var expected=new CoreFrame.Partial(BUILD,new CoreFrame.Prefix(prefix.dateRaw(),1,true,0,true,true,id,true));
            var request=new GuiRootIndexFramePublicCodec.Request(expected,new BigInteger("18446744073709551615"));
            assertEquals(request,GuiRootIndexFramePublicCodec.decodeRequestPacket(NativeWire.execute("root-id-"+id,GuiRootIndexFrame.STEP,BigInteger.ZERO,GuiRootIndexFramePublicCodec.additionalFields(request).bytes())));
        }
    }
    @Test void wrongTypesMissingExtraDuplicatesAndMixedTupleAreRejected()throws Exception {
        for(String field:List.of("addresses_redacted","complete_snapshot","complete_gui_tree","control_actions_available","root_index_available","application_main_observed","source_abi_pins_verified")) {
            var r=result();r.put(field,1);reject(r);
        }
        for(String field:GuiRootIndexFrame.FIELDS){var r=result();r.remove(field);reject(r);}
        var extra=result();extra.put("application_address","1");reject(extra);
        var tuple=result();tuple.put("executable_sha256",ExactCk3Build.CK3_1210.executableSha256());reject(tuple);
        var duplicate=new String(cpp("partial-SYNTHETIC-DATA.json"),StandardCharsets.UTF_8).replace("\"root_index_available\":true","\"root_index_available\":true,\"root_index_available\":true");
        assertThrows(IllegalArgumentException.class,()->GuiRootIndexFramePublicCodec.decodePacket(new RawJson(duplicate.getBytes(StandardCharsets.UTF_8)),"root-qa-1"));
    }
    @Test void countCoherenceForeignContextAndNonCanonicalWitnessCannotPass()throws Exception {
        for(int value:new int[]{-1,4097}){var r=result();((ObjectNode)r.get("root_index")).put("entry_count",value);reject(r);}
        var sum=result();((ObjectNode)sum.get("root_index")).put("empty_entry_count",0);reject(sum);
        var context=result();((ObjectNode)context.get("root_index")).put("all_entries_current_context",false);reject(context);
        var floating=result();((ObjectNode)floating.get("root_index")).put("entry_count",2.0);reject(floating);
        for(String bad:List.of("0","01","-1","+1","1.0","18446744073709551616")) {var r=result();((ObjectNode)r.get("owner_witness")).put("ticket_sequence",bad);reject(r);}
        var number=result();((ObjectNode)number.get("owner_witness")).put("connection_generation",7);reject(number);
        for(long thread:new long[]{0,4294967296L}){var r=result();((ObjectNode)r.get("owner_witness")).put("thread_id",thread);reject(r);}
        var booleanThread=result();((ObjectNode)booleanThread.get("owner_witness")).put("thread_id",true);reject(booleanThread);
        var nullCore=result();nullCore.putNull("core_frame");reject(nullCore);
    }
    @Test void requestCannotCarryConfigConnectionAddressesFloatsOrInvalidPausedActor()throws Exception {
        var r=envelope("request-v1.json");((ObjectNode)r.get("gui_root_index")).put("connection_generation","7");
        assertThrows(IllegalArgumentException.class,()->GuiRootIndexFramePublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(r))));
        for(String field:List.of("paused","map_ready","has_played_character","played_character_alive")){
            var request=envelope("request-v1.json");((ObjectNode)request.path("gui_root_index").path("expected_core")).put(field,false);
            assertThrows(IllegalArgumentException.class,()->GuiRootIndexFramePublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(request))));
        }
        var request=envelope("request-v1.json");((ObjectNode)request.get("gui_root_index")).put("deadline_unix_ms",1.0);
        assertThrows(IllegalArgumentException.class,()->GuiRootIndexFramePublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(request))));
        String negativeZero=new String(cpp("request-v1.json"),StandardCharsets.UTF_8).replace("\"expected_revision\":0","\"expected_revision\":-0");
        assertThrows(IllegalArgumentException.class,()->GuiRootIndexFramePublicCodec.decodeRequestPacket(NativeWire.packet(negativeZero.getBytes(StandardCharsets.UTF_8))));
        var missing=envelope("request-v1.json");((ObjectNode)missing.path("gui_root_index").path("expected_core")).remove("date_raw");
        assertThrows(IllegalArgumentException.class,()->GuiRootIndexFramePublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(missing))));
        var extra=envelope("request-v1.json");((ObjectNode)extra.get("arguments")).put("address","1");
        assertThrows(IllegalArgumentException.class,()->GuiRootIndexFramePublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(extra))));
        var sentinel=envelope("request-v1.json");((ObjectNode)sentinel.path("gui_root_index").path("expected_core")).put("played_character_id",-1);
        assertThrows(IllegalArgumentException.class,()->GuiRootIndexFramePublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(sentinel))));
    }
    private static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\root-index-software","root-index-software",GAME,"root-index-session","root-index-bridge",BUILD.executableSha256(),BUILD.coreFrameAdapterId());}
    private static NativeGameTransport transport(Replay port){return new NativeGameTransport(port,config(),16,3);}
    @Test void sameTransportOriginalCoreSendsExactlyOneQueryAndPreservesCustody()throws Exception {
        var port=new Replay(result());try(var transport=transport(port)) {
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,transport.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            var read=assertInstanceOf(NativeGameTransport.GuiRootIndexReceived.class,transport.readGuiRootIndexReceived(core,core.validUntil()));
            assertEquals(2,port.writes);read.requireOriginal(transport,read.validUntil());
            var request=GuiRootIndexFramePublicCodec.decodeRequestPacket(read.original().outbound().orElseThrow().originalPacket());
            assertEquals(core.frame(),request.expectedCore());assertEquals(read.validUntil().toEpochMilli(),request.deadlineUnixMs().longValueExact());
            var ack=read.original();ack.custody().orElseThrow().verify(ack);
            assertArrayEquals(port.lastPacket,ack.originalPacket());assertTrue(transport.latestObservedSnapshot().isEmpty());
            assertThrows(IOException.class,()->read.requireOriginal(transport,read.validUntil().plusNanos(1)));
            var second=transport.readGuiRootIndexReceived(core,core.validUntil());assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,second.original());assertEquals(2,port.writes);
        }
    }
    @Test void foreignCoreAndExtendedDeadlineNeverWriteAndBadAckIsNotRelabelledZero()throws Exception {
        var first=new Replay(result());var other=new Replay(result());
        try(var transport=transport(first);var foreign=transport(other)) {
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,transport.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,foreign.readGuiRootIndexReceived(core,core.validUntil()).original());assertEquals(0,other.writes);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,transport.readGuiRootIndexReceived(core,core.validUntil().plusNanos(1)).original());assertEquals(1,first.writes);
            first.reply.put("complete_gui_tree",true);
            var invalid=transport.readGuiRootIndexReceived(core,core.validUntil());var ack=assertInstanceOf(NativeActionPort.AckReceived.class,invalid.original());
            assertTrue(ack.nativeOk());ack.custody().orElseThrow().verify(ack);assertEquals(2,first.writes);assertInstanceOf(NativeGameTransport.GuiRootIndexReadUnavailable.class,invalid);
        }
        var stale=new Replay(result());((ObjectNode)stale.reply.get("owner_witness")).put("connection_generation","8");
        try(var transport=transport(stale)) {
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,transport.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            var rejected=assertInstanceOf(NativeGameTransport.GuiRootIndexReadUnavailable.class,transport.readGuiRootIndexReceived(core,core.validUntil()));
            assertInstanceOf(NativeActionPort.AckReceived.class,rejected.original());assertEquals(2,stale.writes);
        }
    }
    @Test void unavailableNativeDataAndUnknownRemainOriginalWithoutReplay()throws Exception {
        var unavailable=(ObjectNode)envelope("unavailable-NoGame.json").get("result");var port=new Replay(unavailable);
        try(var transport=transport(port)) {
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,transport.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            var received=assertInstanceOf(NativeGameTransport.GuiRootIndexReceived.class,transport.readGuiRootIndexReceived(core,core.validUntil()));
            assertInstanceOf(GuiRootIndexFrame.Unavailable.class,received.frame());assertTrue(received.original().nativeOk());
        }
        var missing=new Replay(result());missing.dropReply=true;
        try(var transport=transport(missing)) {
            var core=assertInstanceOf(NativeGameTransport.CoreReceived.class,transport.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            var first=transport.readGuiRootIndexReceived(core,core.validUntil());assertInstanceOf(NativeActionPort.Unknown.class,first.original());
            assertSame(first,transport.readGuiRootIndexReceived(core,core.validUntil()));assertEquals(2,missing.writes);
        }
    }
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> incoming=new ArrayDeque<>();final ObjectNode reply;int writes;boolean closed,dropReply;byte[] lastPacket;
        Replay(ObjectNode reply) throws Exception {
            this.reply=reply.deepCopy();var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",7)
                    .put("bridge_version","root-index-bridge").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                    .put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add(CoreFrame.CAPABILITY);incoming.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        public void verify()throws IOException {if(closed)throw new IOException("software port closed");}
        public void verifyCoreControlWindowPolicy(){ /* Authored software guard, not a real window observation. */ }
        public void awaitConnection(Instant deadline)throws IOException{verify();}
        public byte[] readPacket(Instant deadline)throws IOException {verify();if(incoming.isEmpty())throw new IOException("authored missing reply");return incoming.removeFirst();}
        public void writePacket(byte[] packet,Instant deadline)throws IOException {
            verify();var request=NativeWire.decodeExecuteRequest(packet);writes++;
            ObjectNode data;
            if(request.step().equals(CoreFrame.STEP)) {try{data=(ObjectNode)result().get("core_frame");}catch(Exception failure){throw new IOException(failure);}}
            else {assertEquals(GuiRootIndexFrame.STEP,request.step());GuiRootIndexFramePublicCodec.decodeRequestPacket(packet);if(dropReply)return;data=reply;}
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);envelope.set("result",data);
            lastPacket=NativeWire.packet(StrictJson.canonical(envelope));incoming.add(lastPacket.clone());
        }
        public void close(){closed=true;}
    }
}
