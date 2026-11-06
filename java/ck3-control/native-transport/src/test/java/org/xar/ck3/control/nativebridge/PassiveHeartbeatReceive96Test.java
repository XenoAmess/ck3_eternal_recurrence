package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;

/** Original-producer replay DATA only. No Win32 process, real endpoint, LoadedCustody or permission is fabricated. */
final class PassiveHeartbeatReceive96Test {
    @Test void onePassivePacketRetainsHeartbeatWithoutAnyWriteAndPreservesReadFailure() throws Exception {
        byte[] hello=packet("{\"type\":\"hello\",\"protocol_version\":1,\"pid\":1,\"connection_generation\":1,\"bridge_version\":\"0.1.0\",\"expected_ck3_sha256\":\""+"a".repeat(64)+"\",\"game_adapter_id\":\"DATA_ONLY\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}");
        byte[] heartbeat=packet("{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":7,\"main_thread_query_mailbox_v1\":{\"DATA_ONLY\":true}}");
        var game=GameGeneration.fromJson(StrictJson.object().put("pid",1).put("creation_filetime","1"));
        var config=new NativePipeEndpoint.Config("\\\\.\\pipe\\UNISSUED_PASSIVE_DATA_ONLY","unissued-data",game,"UNISSUED_PASSIVE_DATA_ONLY","0.1.0","a".repeat(64),"DATA_ONLY");
        var endpoint=new Packets(hello,heartbeat,packet("{\"type\":\"error\",\"protocol_version\":1}"));
        try(var transport=new NativeGameTransport(endpoint,config,1,1,List.of(),Clock.systemUTC())) {
            Instant deadline=Instant.now().plusSeconds(10);transport.awaitHello(deadline);
            UncheckedIOException budget=assertThrows(UncheckedIOException.class,()->transport.observe(deadline));
            assertTrue(budget.getCause().getMessage().contains("snapshot frame budget exhausted"));
            var actual=transport.diagnostics().latestHeartbeat().orElseThrow();
            assertEquals(NativeWire.NoticeKind.HEARTBEAT,actual.original().kind());
            assertArrayEquals(heartbeat,actual.original().packet().value());assertNotNull(actual.observedAt());
            assertEquals(2,endpoint.reads);assertEquals(1,endpoint.queue.size());assertEquals(0,endpoint.writes);
        }
        assertEquals(1,endpoint.closes);assertEquals(0,endpoint.writes);
        IOException original=new IOException("original passive provider failure");
        var failing=new Packets(hello);failing.failure=original;
        try(var transport=new NativeGameTransport(failing,config,1,1,List.of(),Clock.systemUTC())) {
            Instant deadline=Instant.now().plusSeconds(10);transport.awaitHello(deadline);
            UncheckedIOException actual=assertThrows(UncheckedIOException.class,()->transport.observe(deadline));
            assertSame(original,actual.getCause());assertTrue(transport.diagnostics().latestHeartbeat().isEmpty());
            assertEquals(0,failing.writes);
        }
        assertEquals(1,failing.closes);assertEquals(0,failing.writes);
        System.out.println("PASSIVE_HEARTBEAT_DATA_PASS onepostHELLO/actualreceiver/rawHB/zeroWrites/readFailureIdentity");
    }
    private static byte[] packet(String body) {
        byte[] raw=body.getBytes(StandardCharsets.UTF_8);
        return ByteBuffer.allocate(raw.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(raw.length).put(raw).array();
    }
    private static final class Packets implements NativePacketPort {
        private final ArrayDeque<byte[]> queue=new ArrayDeque<>();
        private int reads,writes,closes;private IOException failure;
        Packets(byte[]... packets){for(byte[] packet:packets)queue.add(packet.clone());}
        @Override public void verify(){ }
        @Override public void awaitConnection(Instant deadline){ }
        @Override public byte[] readPacket(Instant deadline)throws IOException {
            reads++;if(queue.isEmpty()){if(failure!=null)throw failure;throw new IOException("bounded replay exhausted");}
            return queue.removeFirst().clone();
        }
        @Override public void writePacket(byte[] packet,Instant deadline){writes++;throw new AssertionError("passive receive must never write");}
        @Override public void close(){closes++;}
    }
}
