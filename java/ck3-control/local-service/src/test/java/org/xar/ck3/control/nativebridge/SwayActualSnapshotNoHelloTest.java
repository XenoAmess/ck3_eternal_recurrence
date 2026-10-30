package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Base64;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.planning.sway.SwayNativeWire;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual standalone Native snapshot frames are never substituted for a missing original HELLO. */
final class SwayActualSnapshotNoHelloTest {
    @Test void actualSnapshotWithoutOriginalHelloCannotMintAHeldSessionOrAcceptedOccurrence() throws Exception {
        int count=0;
        try(var in=getClass().getResourceAsStream("/sway/m6-native-resource-receiver-originals.json")) {
            assertNotNull(in,"mandatory actual resource-reader Native originals");
            for(var row:StrictJson.parse(in.readAllBytes())) {
                byte[] original=Base64.getDecoder().decode(row.get("frame_base64").textValue());
                assertEquals(row.get("frame_sha256").textValue(),ActionCodec.sha256(original));
                var port=new OnlyOriginal(original);String slash=Character.toString(92);
                var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"no-hello-software-originals","xenoamess-full-tower-eb9d2c1186",
                        new GameGeneration(73,new PythonOnlyUInt64(BigInteger.ONE)),"software-no-original-hello","software-only",SwayNativeWire.EXE,"software-only");
                try(var transport=new NativeGameTransport(port,config,4,4)) {
                    assertEquals(NativeGameTransport.ReceivedState.NO_HELLO,transport.diagnostics().receivedState());
                    var rejected=assertThrows(UncheckedIOException.class,()->transport.observe(Instant.now().plusSeconds(5)));
                    assertEquals("Native frame arrived before original hello",rejected.getCause().getMessage());
                    var diagnostic=transport.diagnostics();
                    assertEquals(NativeGameTransport.ReceivedState.TERMINAL,diagnostic.receivedState());
                    assertTrue(diagnostic.session().isEmpty());assertTrue(diagnostic.originalHello().isEmpty());
                    assertArrayEquals(original,diagnostic.lastOriginalPacket().value());
                    assertThrows(IOException.class,transport::latestObservedSnapshot);
                    assertThrows(UncheckedIOException.class,()->transport.observe(Instant.now().plusSeconds(5)));
                    assertEquals(1,port.reads);assertEquals(0,port.writes);
                }
                count++;
            }
        }
        assertEquals(2,count);
    }
    private static final class OnlyOriginal implements NativePacketPort {
        private final byte[] original;int reads,writes;
        OnlyOriginal(byte[] packet) {original=packet.clone();}
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) { }
        @Override public byte[] readPacket(Instant deadline) throws IOException {if(reads++!=0)throw new IOException("original snapshot already read; no fallback HELLO");return original.clone();}
        @Override public void writePacket(byte[] packet,Instant deadline) {writes++;throw new AssertionError("missing HELLO never permits outbound writes");}
        @Override public void close() { }
    }
}
