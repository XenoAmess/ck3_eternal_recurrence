package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeRequestChronologyCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual C++ software producer -> exact original outbound -> sole Java receive/custody path.
 * The child uses its retained owned-memory .4 raw readers and real mailbox executor/formatter.
 * It does not open CK3 or grant actual Native/HELLO/Root gameplay qualification. Required inputs
 * are explicit; absence fails this regression and never becomes a skipped/pass result. */
final class NativeFresh12004CppProducerTest {
    private static final String SHA="98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final String ADAPTER="ck3-1.20.0.4-msvc-x64";
    private static String required(String name){String value=System.getProperty(name);if(value==null||value.isBlank())throw new IllegalStateException("required actual C++ fixture input: "+name);return value;}
    @Test void actualCppFullReaderAndFormatterProduceBothOriginalPacketsForTwoJavaRequests()throws Exception {
        Path executable=Path.of(required("xar.native.fresh12004.fixtureExecutable")).toRealPath();
        String expectedBytes=required("xar.native.fresh12004.fixtureBytes"),expectedSha=required("xar.native.fresh12004.fixtureSha256");
        assertTrue(expectedBytes.matches("[1-9][0-9]*"));assertTrue(expectedSha.matches("[0-9a-f]{64}"));
        assertEquals(new BigInteger(expectedBytes),BigInteger.valueOf(Files.size(executable)));
        assertEquals(expectedSha,DriverJson.sha256(Files.readAllBytes(executable)));
        Path workRoot=Path.of(required("xar.native.fresh12004.workRoot")).toRealPath();
        assertTrue(Files.isDirectory(workRoot));Path work=Files.createTempDirectory(workRoot,"fresh12004-cpp-");
        try(var port=new CppPort(executable,work)){
            String slash=Character.toString(92);
            var config=new NativePipeEndpoint.Config(slash+slash+"."+slash+"pipe"+slash+"fresh12004-cpp-software",
                    "cpp-owned-memory-fixture",new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),
                    "same-software-session","source-test",SHA,ADAPTER);
            try(var transport=new NativeGameTransport(port,config,16,64)){
                var first=assertInstanceOf(NativeFreshSnapshotPort.Received.class,transport.readFreshFullState(deadline()));
                assertArrayEquals(port.originalState,first.originalFrame().originalPacket());
                assertArrayEquals(port.originalAck,first.acknowledgement().originalPacket());
                var second=assertInstanceOf(NativeFreshSnapshotPort.Received.class,transport.readFreshFullState(deadline()));
                NativeFreshSnapshotPort.verifyAfter(first.acknowledgement(),second);
                assertEquals(first.originalFrame().state(),second.originalFrame().state());
                assertEquals(first.originalFrame().nativeRevision(),second.originalFrame().nativeRevision());
                assertNotEquals(first.acknowledgement().requestId(),second.acknowledgement().requestId());
                var custody=second.acknowledgement().custody().orElseThrow();
                assertEquals(custody,NativeRequestChronologyCodec.decode(NativeRequestChronologyCodec.encode(custody)));
                NativeFreshSnapshotPort.verifyAfterOriginal(first.acknowledgement(),second.acknowledgement(),second.originalFrame(),second.snapshotReceived());
                assertEquals(2,port.writes);
            }
        }
    }
    private static Instant deadline(){return Instant.now().plusSeconds(30);}
    private static final class CppPort implements NativePacketPort {
        private final Path executable,work;private final ArrayDeque<byte[]> received=new ArrayDeque<>();
        private int writes;private byte[] originalState,originalAck;
        CppPort(Path executable,Path work)throws IOException{
            this.executable=executable;this.work=work;
            // Software HELLO selects the actual .4 tuple/capability. Live bridge
            // HELLO/ENV qualification remains a separate Root Native test.
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",42)
                    .put("connection_generation",1).put("bridge_version","source-test").put("expected_ck3_sha256",SHA)
                    .put("expected_ck3_version","1.20.0.4").put("game_adapter_id",ADAPTER).put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY);
            received.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify(){}
        @Override public void awaitConnection(Instant deadline){}
        @Override public byte[] readPacket(Instant deadline)throws IOException{
            if(received.isEmpty())throw new IOException("actual C++ producer has no retained packet");return received.remove();
        }
        @Override public void writePacket(byte[] packet,Instant deadline)throws IOException{
            writes++;Path output=Files.createDirectory(work.resolve("original-read-"+writes));Path request=output.resolve("original-request.json");
            Files.write(request,Arrays.copyOfRange(packet,4,packet.length));Path log=output.resolve("cpp-producer.log");
            Process child=new ProcessBuilder(executable.toString(),output.toString(),request.toString()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
            try{
                if(!child.waitFor(20,TimeUnit.SECONDS)){child.destroyForcibly();throw new IOException("actual C++ fresh full-state fixture timed out; original request must not replay");}
                if(child.exitValue()!=0)throw new IOException("actual C++ fresh full-state fixture failed: "+Files.readString(log));
            }catch(InterruptedException interrupted){Thread.currentThread().interrupt();child.destroyForcibly();throw new IOException("actual C++ producer wait interrupted",interrupted);}
            byte[] stream=Files.readAllBytes(output.resolve("state-snapshot-fresh-four-packets.bin"));
            if(stream.length<10)throw new IOException("actual C++ protocol stream lacks its two original frames");
            int stateBytes=ByteBuffer.wrap(stream,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
            if(stateBytes<=0||stateBytes>stream.length-9)throw new IOException("actual C++ state frame length differs");
            int ackOffset=4+stateBytes,ackBytes=ByteBuffer.wrap(stream,ackOffset,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
            if(ackBytes<=0||(long)ackOffset+4+ackBytes!=stream.length)throw new IOException("actual C++ ACK frame length differs");
            originalState=Arrays.copyOfRange(stream,0,ackOffset);originalAck=Arrays.copyOfRange(stream,ackOffset,stream.length);
            if(!(NativeWire.decode(originalState) instanceof NativeWire.Snapshot)||!(NativeWire.decode(originalAck) instanceof NativeWire.CommandResult))
                throw new IOException("actual C++ producer stream did not preserve state then ACK");
            received.add(originalState);received.add(originalAck);
        }
        @Override public void close(){}
    }
}
