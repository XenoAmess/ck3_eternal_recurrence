package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayDeque;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** NoGame wire DATA through the production transport, including refused original hello packets. */
final class NativeHelloCustodyTest {
    @TempDir Path temp;
    private static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    private static final String ADAPTER="ck3-1.21.0.3-26785313-msvc-x64";
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(BigInteger.valueOf(1234)));
    private static NativePipeEndpoint.Config config(){return new NativePipeEndpoint.Config("\\\\.\\pipe\\hello-custody-data","hello-custody-data",GAME,"hello-custody-session","hello-custody-data",BUILD.executableSha256(),ADAPTER);}
    private static com.fasterxml.jackson.databind.node.ObjectNode hello(){
        var row=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",GAME.pid()).put("connection_generation",1)
                .put("bridge_version","hello-custody-data").put("expected_ck3_version",BUILD.version()).put("expected_ck3_sha256",BUILD.executableSha256())
                .put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
        row.putArray("capabilities");return row;
    }
    @Test void rejectedStatusAndEveryExactIdentityMismatchRetainOriginalBeforeValidation()throws Exception {
        for(String changed:new String[]{"status","match","pid","bridge","hash","adapter"}) {
            var row=hello();
            switch(changed){
                case "status"->row.put("game_adapter_status","unsupported_build");
                case "match"->row.put("ck3_build_match",false);
                case "pid"->row.put("pid",43);
                case "bridge"->row.put("bridge_version","wrong");
                case "hash"->row.put("expected_ck3_sha256","0".repeat(64));
                case "adapter"->row.put("game_adapter_id","wrong");
                default->throw new AssertionError(changed);
            }
            byte[] packet=NativeWire.packet(StrictJson.canonical(row));var source=new Source(packet);Path target=temp.resolve(changed+".packet");
            try(var transport=new NativeGameTransport(source,config(),4,1)) {
                IOException refused=assertThrows(IOException.class,()->transport.awaitHello(Instant.now().plusSeconds(5),raw->{
                    Files.write(target,raw,StandardOpenOption.CREATE_NEW);
                    raw[0]^=1; // The observer receives a copy, never authority to mutate the validated packet.
                }));
                assertTrue(refused.getMessage().contains("exact Game/bridge binding"),changed);
                assertArrayEquals(packet,Files.readAllBytes(target));assertArrayEquals(packet,transport.lastOriginalPacket());
                assertEquals(0,source.writes);assertEquals(1,source.reads);
            }
        }
    }
    @Test void malformedOriginalIsRetainedBeforeDecoderRejects()throws Exception {
        byte[] packet=NativeWire.packet("{broken".getBytes(java.nio.charset.StandardCharsets.UTF_8));Path target=temp.resolve("malformed.packet");
        try(var actual=new NativeGameTransport(new Source(packet),config(),4,1)) {
            assertThrows(IOException.class,()->actual.awaitHello(Instant.now().plusSeconds(5),raw->Files.write(target,raw,StandardOpenOption.CREATE_NEW)));
            assertArrayEquals(packet,Files.readAllBytes(target));
        }
    }
    @Test void persistenceFailureCannotBecomeAcceptedAndDoesNotReadAgain()throws Exception {
        var source=new Source(NativeWire.packet(StrictJson.canonical(hello())));
        try(var actual=new NativeGameTransport(source,config(),4,1)) {
            assertThrows(IOException.class,()->actual.awaitHello(Instant.now().plusSeconds(5),raw->{throw new IOException("DATA disk failure");}));
            assertThrows(IOException.class,()->actual.awaitHello(Instant.now().plusSeconds(5)));
            assertEquals(1,source.reads);assertEquals(0,source.writes);
        }
    }
    @Test void acceptedHelloStillRequiresAllOriginalChecksAndCannotBeRecaptured()throws Exception {
        byte[] packet=NativeWire.packet(StrictJson.canonical(hello()));Path target=temp.resolve("accepted.packet");
        try(var actual=new NativeGameTransport(new Source(packet),config(),4,1)) {
            assertNotNull(actual.awaitHello(Instant.now().plusSeconds(5),raw->Files.write(target,raw,StandardOpenOption.CREATE_NEW)));
            assertArrayEquals(packet,Files.readAllBytes(target));
            assertThrows(IOException.class,()->actual.awaitHello(Instant.now().plusSeconds(5),raw->fail("no recapture")));
        }
    }
    private static final class Source implements NativePacketPort {
        final ArrayDeque<byte[]> packets=new ArrayDeque<>();int reads,writes;boolean closed;
        Source(byte[] packet){packets.add(packet.clone());}
        public void verify()throws IOException{if(closed)throw new IOException("DATA source closed");}
        public void awaitConnection(Instant until)throws IOException{verify();}
        public byte[] readPacket(Instant until)throws IOException{verify();reads++;if(packets.isEmpty())throw new IOException("no DATA packet");return packets.removeFirst();}
        public void writePacket(byte[] packet,Instant until){writes++;fail("Hello must never submit a command");}
        public void close(){closed=true;}
    }
}
