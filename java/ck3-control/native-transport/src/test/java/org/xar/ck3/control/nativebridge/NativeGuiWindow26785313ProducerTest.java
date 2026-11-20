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
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFramePublicCodec;

/** Actual C++ producer DATA plus authored transport. Never queries Game or grants activation. */
final class NativeGuiWindow26785313ProducerTest {
    static final String ROOT="/newnative/gui-window26785313-v1/";
    static final ExactCk3Build BUILD=GuiWindowFrame.BUILD;
    static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(999)));
    static byte[] cpp(String name)throws Exception {
        byte[] bytes;
        try(var in=NativeGuiWindow26785313ProducerTest.class.getResourceAsStream(ROOT+name)){if(in==null)throw new IOException("actual C++ golden required: "+name);bytes=in.readNBytes(16385);assertTrue(bytes.length<=16384);}
        try(var in=NativeGuiWindow26785313ProducerTest.class.getResourceAsStream(ROOT+"producer-pins.json")){
            if(in==null)throw new IOException("actual producer pins required");var p=StrictJson.parse(in.readNBytes(16384)).get(name);assertNotNull(p);
            assertEquals(p.path("bytes").intValue(),bytes.length);assertEquals(p.path("sha256").textValue(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        }return bytes;
    }
    static ObjectNode envelope(String file)throws Exception{return (ObjectNode)StrictJson.parse(cpp(file));}
    static ObjectNode result()throws Exception{return (ObjectNode)envelope("partial-SYNTHETIC-DATA.json").get("result");}
    static RawJson raw(JsonNode node){return new RawJson(StrictJson.canonical(node));}
    static CoreFrame.Partial core()throws Exception{return (CoreFrame.Partial)GuiWindowFrame.decode(raw(result())).coreFrame();}
    static void reject(ObjectNode value){assertThrows(IllegalArgumentException.class,()->GuiWindowFrame.decode(raw(value)));}
    @Test void actualCppGoldenRoundTripsWithoutAddressesActionsOrFullClaims()throws Exception {
        var request=GuiWindowFramePublicCodec.decodeRequestPacket(NativeWire.packet(cpp("request-v1.json")));
        assertEquals("rite_creation_window",request.windowName());assertEquals(-16777215,request.expectedCore().prefix().playedCharacterId());
        assertEquals(request,GuiWindowFramePublicCodec.decodeRequestPacket(NativeWire.execute("java-window-1",GuiWindowFrame.STEP,BigInteger.ZERO,GuiWindowFramePublicCodec.additionalFields(request).bytes())));
        var frame=assertInstanceOf(GuiWindowFrame.Partial.class,GuiWindowFramePublicCodec.decodePacket(new RawJson(cpp("partial-SYNTHETIC-DATA.json")),"root-qa-1"));
        assertTrue(frame.windowAvailable());assertEquals(frame,GuiWindowFrame.decode(GuiWindowFramePublicCodec.encode(frame)));
        var out=StrictJson.parse(GuiWindowFramePublicCodec.encode(frame).bytes());
        for(String key:List.of("activation_available","control_actions_available","complete_gui_tree","complete_snapshot","native_findtop_semantics_verified"))assertFalse(out.path(key).booleanValue());
        assertTrue(out.path("addresses_redacted").booleanValue());assertEquals("0",out.path("window").path("nodes").get(0).path("node_id").textValue());
    }
    @Test void actualCppNoGameUnavailableAndMissingWindowAreDifferentObservedStates()throws Exception {
        for(String file:List.of("unavailable-NoGame.json","wrong-tuple-unavailable.json","missing-owner-unavailable.json")){
            var frame=assertInstanceOf(GuiWindowFrame.Unavailable.class,GuiWindowFramePublicCodec.decodePacket(new RawJson(cpp(file)),"root-qa-1"));
            assertFalse(frame.windowAvailable());assertEquals(frame,GuiWindowFrame.decode(GuiWindowFramePublicCodec.encode(frame)));
            var row=StrictJson.parse(GuiWindowFramePublicCodec.encode(frame).bytes());for(String key:List.of("top_level","window","requested_window","owner_witness"))assertTrue(row.path(key).isNull());
        }
        var missing=assertInstanceOf(GuiWindowFrame.Partial.class,GuiWindowFramePublicCodec.decodePacket(new RawJson(cpp("missing-window-SYNTHETIC-DATA.json")),"root-qa-1"));
        assertFalse(missing.windowAvailable());assertTrue(missing.window().isEmpty());assertEquals(missing,GuiWindowFrame.decode(GuiWindowFramePublicCodec.encode(missing)));
    }
    @Test void everyFieldTypesTupleUnknownFieldsAndDuplicatesAreStrict()throws Exception {
        for(String field:GuiWindowFrame.FIELDS){var r=result();r.remove(field);reject(r);}
        for(String field:List.of("tree_source_available","window_available","complete_window_tree","activation_available")){var r=result();r.put(field,1);reject(r);}
        for(String field:List.of("activation_available","control_actions_available","complete_gui_tree","complete_snapshot","native_findtop_semantics_verified")){var r=result();r.put(field,true);reject(r);}
        var extra=result();extra.put("widget_address","1");reject(extra);var tuple=result();tuple.put("executable_sha256",ExactCk3Build.CK3_1210.executableSha256());reject(tuple);
        var duplicate=new String(cpp("partial-SYNTHETIC-DATA.json"),StandardCharsets.UTF_8).replace("\"window_available\":true","\"window_available\":true,\"window_available\":true");
        assertThrows(IllegalArgumentException.class,()->GuiWindowFramePublicCodec.decodePacket(new RawJson(duplicate.getBytes(StandardCharsets.UTF_8)),"root-qa-1"));
    }
    @Test void treeIdsParentsDepthChildrenAndRequestedOccurrenceCannotDrift()throws Exception {
        for(String value:List.of("01","-1","4096","1.0","18446744073709551615")){var r=result();((ObjectNode)r.path("window").path("nodes").get(0)).put("node_id",value);reject(r);}
        for(String field:List.of("node_id","parent_id")){var r=result();((ObjectNode)r.path("window").path("nodes").get(0)).put(field,0);reject(r);}
        var child=result();var nodes=(com.fasterxml.jackson.databind.node.ArrayNode)child.path("window").path("nodes");
        ((ObjectNode)nodes.get(0)).put("child_count",1);var n=((ObjectNode)nodes.get(0)).deepCopy();n.put("node_id","1").put("parent_id","0").put("sibling_index",0).put("depth",1).put("name","").put("child_count",0);nodes.add(n);
        assertInstanceOf(GuiWindowFrame.Partial.class,GuiWindowFrame.decode(raw(child)));
        for(String field:List.of("depth","sibling_index","child_count")){var altered=child.deepCopy();((ObjectNode)altered.path("window").path("nodes").get(1)).put(field,2);reject(altered);}
        var cycle=child.deepCopy();((ObjectNode)cycle.path("window").path("nodes").get(1)).put("parent_id","1");reject(cycle);
        var inherited=child.deepCopy();((ObjectNode)inherited.path("window").path("nodes").get(0)).put("visible",false);((ObjectNode)inherited.path("top_level").get(0)).put("visible",false);reject(inherited);
        var wrongName=result();wrongName.put("requested_window","faith_window");reject(wrongName);
        var duplicateTop=result();((com.fasterxml.jackson.databind.node.ArrayNode)duplicateTop.path("top_level")).add(duplicateTop.path("top_level").get(0).deepCopy());reject(duplicateTop);
        var missingTree=result();missingTree.put("window_available",false).put("complete_window_tree",false).putNull("window");reject(missingTree);
        var first=((GuiWindowFrame.Partial)GuiWindowFrame.decode(raw(result()))).window().orElseThrow().nodes().getFirst();
        assertThrows(IllegalArgumentException.class,()->new GuiWindowFrame.Window(java.util.Collections.nCopies(4097,first)));
        assertThrows(IllegalArgumentException.class,()->new GuiWindowFrame.Node(1,java.util.OptionalInt.of(0),0,65,"",0,true,true));
    }
    @Test void utf8NamesWitnessAndNumericBoundariesDoNotCoerce()throws Exception {
        assertEquals("",GuiWindowFrame.nodeName(""));assertEquals("汉".repeat(64),GuiWindowFrame.nodeName("汉".repeat(64)));
        for(String bad:List.of("汉".repeat(65),"a".repeat(193),"x"+(char)0)){assertThrows(IllegalArgumentException.class,()->GuiWindowFrame.nodeName(bad));}
        assertThrows(IllegalArgumentException.class,()->GuiWindowFrame.nodeName(String.valueOf((char)0xd800)));
        var max=result();var witness=(ObjectNode)max.path("owner_witness");for(String k:List.of("connection_generation","ticket_sequence","pump_epoch"))witness.put(k,"18446744073709551615");witness.put("thread_id",4294967295L);
        assertEquals(new BigInteger("18446744073709551615"),((GuiWindowFrame.Partial)GuiWindowFrame.decode(raw(max))).ownerWitness().connectionGeneration());
        for(String value:List.of("0","01","+1","18446744073709551616")){var r=result();((ObjectNode)r.path("owner_witness")).put("pump_epoch",value);reject(r);}
        var r=result();((ObjectNode)r.path("owner_witness")).put("thread_id",true);reject(r);
        var floatDepth=result();((ObjectNode)floatDepth.path("window").path("nodes").get(0)).put("depth",0.0);reject(floatDepth);
        var oversized=new RawJson(("{\"padding\":\""+"x".repeat(GuiWindowFrame.MAXIMUM_BYTES)+"\"}").getBytes(StandardCharsets.UTF_8));
        assertThrows(IllegalArgumentException.class,()->GuiWindowFrame.decode(oversized));
    }
    @Test void requestRequiresExactWindowNameOriginalCoreAndNativeLexicalDomain()throws Exception {
        for(String name:List.of("","x y","x/y","汉","x".repeat(97))){assertThrows(IllegalArgumentException.class,()->GuiWindowFramePublicCodec.request(core(),Instant.now().plusSeconds(1),name));}
        for(String extra:List.of("connection_generation","widget_address")){var r=envelope("request-v1.json");((ObjectNode)r.path("gui_window")).put(extra,"1");assertThrows(IllegalArgumentException.class,()->GuiWindowFramePublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(r))));}
        var core=envelope("request-v1.json");((ObjectNode)core.path("gui_window").path("expected_core")).put("paused",false);assertThrows(IllegalArgumentException.class,()->GuiWindowFramePublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(core))));
        var zero=new String(cpp("request-v1.json"),StandardCharsets.UTF_8).replace("\"expected_revision\":0","\"expected_revision\":-0");assertThrows(IllegalArgumentException.class,()->GuiWindowFramePublicCodec.decodeRequestPacket(NativeWire.packet(zero.getBytes(StandardCharsets.UTF_8))));
        var deadline=envelope("request-v1.json");((ObjectNode)deadline.path("gui_window")).put("deadline_unix_ms",true);assertThrows(IllegalArgumentException.class,()->GuiWindowFramePublicCodec.decodeRequestPacket(NativeWire.packet(StrictJson.canonical(deadline))));
    }
    static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\gui-window-DATA","gui-window-data",GAME,"gui-window-session","gui-window-bridge",BUILD.executableSha256(),BUILD.coreFrameAdapterId());}
    static NativeGameTransport transport(Replay port){return new NativeGameTransport(port,config(),16,3);}
    @Test void identicalTransportCoreSendsOneNamedQueryPreservingActualCustody()throws Exception {
        var source=new Replay(result());try(var actual=transport(source)){
            var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            var read=assertInstanceOf(NativeGameTransport.GuiWindowReceived.class,actual.readGuiWindowReceived(before,"rite_creation_window",before.validUntil()));
            read.requireOriginal(actual,read.validUntil());assertEquals(2,source.writes);read.original().custody().orElseThrow().verify(read.original());
            var request=GuiWindowFramePublicCodec.decodeRequestPacket(read.original().outbound().orElseThrow().originalPacket());assertEquals(before.frame(),request.expectedCore());assertEquals("rite_creation_window",request.windowName());
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.readGuiWindowReceived(before,"faith_window",before.validUntil()).original());assertEquals(2,source.writes);
            assertThrows(IOException.class,()->read.requireOriginal(actual,read.validUntil().plusNanos(1)));assertTrue(actual.latestObservedSnapshot().isEmpty());
        }
    }
    @Test void wrongIssuerWindowConnectionAndUnknownNeverBorrowFreshnessOrReplay()throws Exception {
        var source=new Replay(result());var other=new Replay(result());try(var actual=transport(source);var foreign=transport(other)){
            var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,foreign.readGuiWindowReceived(before,"rite_creation_window",before.validUntil()).original());assertEquals(0,other.writes);
            assertInstanceOf(NativeActionPort.RejectedBeforeDispatch.class,actual.readGuiWindowReceived(before,"rite_creation_window",before.validUntil().plusNanos(1)).original());assertEquals(1,source.writes);
            ((ObjectNode)source.reply.path("owner_witness")).put("connection_generation","8");var failed=assertInstanceOf(NativeGameTransport.GuiWindowReadUnavailable.class,actual.readGuiWindowReceived(before,"rite_creation_window",before.validUntil()));
            assertInstanceOf(NativeActionPort.AckReceived.class,failed.original());assertEquals(2,source.writes);
        }
        var changed=result();changed.put("requested_window","faith_window");((ObjectNode)changed.path("top_level").get(0)).put("name","faith_window");((ObjectNode)changed.path("window").path("nodes").get(0)).put("name","faith_window");
        var wrongWindow=new Replay(changed);try(var actual=transport(wrongWindow)){
            var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            var failed=assertInstanceOf(NativeGameTransport.GuiWindowReadUnavailable.class,actual.readGuiWindowReceived(before,"rite_creation_window",before.validUntil()));
            assertInstanceOf(NativeActionPort.AckReceived.class,failed.original());assertEquals(2,wrongWindow.writes);
        }
        var missing=new Replay(result());missing.dropReply=true;try(var actual=transport(missing)){
            var before=assertInstanceOf(NativeGameTransport.CoreReceived.class,actual.readCoreFrameReceived(Instant.now().plusSeconds(30)));
            var unknown=actual.readGuiWindowReceived(before,"rite_creation_window",before.validUntil());assertInstanceOf(NativeActionPort.Unknown.class,unknown.original());
            assertSame(unknown,actual.readGuiWindowReceived(before,"rite_creation_window",before.validUntil()));assertEquals(2,missing.writes);
        }
    }
    static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> incoming=new ArrayDeque<>();final ObjectNode reply;boolean closed,dropReply;int writes;
        Replay(ObjectNode reply)throws IOException{this.reply=reply;var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",7)
                .put("bridge_version","gui-window-bridge").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256()).put("game_adapter_id",BUILD.coreFrameAdapterId()).put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add(CoreFrame.CAPABILITY);incoming.add(NativeWire.packet(StrictJson.canonical(hello)));}
        public void verify()throws IOException{if(closed)throw new IOException("authored source closed");}
        public void verifyCoreControlWindowPolicy(){/* No real window qualification from authored source. */}
        public void awaitConnection(Instant deadline)throws IOException{verify();}
        public byte[] readPacket(Instant deadline)throws IOException{verify();if(incoming.isEmpty())throw new IOException("authored missing reply");return incoming.removeFirst();}
        public void writePacket(byte[] packet,Instant deadline)throws IOException{
            verify();writes++;var request=NativeWire.decodeExecuteRequest(packet);ObjectNode data;
            if(request.step().equals(CoreFrame.STEP)){try{data=(ObjectNode)result().get("core_frame");}catch(Exception failure){throw new IOException(failure);}}
            else{assertEquals(GuiWindowFrame.STEP,request.step());GuiWindowFramePublicCodec.decodeRequestPacket(packet);if(dropReply)return;data=reply;}
            var envelope=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",request.requestId()).put("ok",true);envelope.set("result",data);incoming.add(NativeWire.packet(StrictJson.canonical(envelope)));
        }
        public void close(){closed=true;}
    }
}
