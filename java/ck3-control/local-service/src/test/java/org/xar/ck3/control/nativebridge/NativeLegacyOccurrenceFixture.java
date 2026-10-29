package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;

/** Test-only adapter of the existing software Win32 producer; never a native Game observation. */
public final class NativeLegacyOccurrenceFixture implements AutoCloseable {
    private final NativeSnapshotWaitReceiverFixture.Pipe pipe=new NativeSnapshotWaitReceiverFixture.Pipe();
    private final NativeGameTransport transport;
    private final byte[] originalA;
    public NativeLegacyOccurrenceFixture()throws Exception {
        pipe.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.HELLO));
        originalA=NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.snapshot("same",7,NativeSnapshotWaitReceiverFixture.STATE));
        var clock=Clock.fixed(Instant.parse("2026-10-25T00:00:00Z"),ZoneOffset.UTC);
        transport=new NativeGameTransport(NativeSnapshotWaitReceiverFixture.endpoint(pipe),
                NativeSnapshotWaitReceiverFixture.config(),16,16,List.of(),clock);
    }
    public NativeGameTransport transport(){return transport;}
    public ObservedFrame receiveA()throws InterruptedException {
        pipe.add(originalA);return transport.observe(deadline());
    }
    public ObservedFrame receiveB()throws IOException,InterruptedException {
        String changed=NativeSnapshotWaitReceiverFixture.STATE.replace("\"played_character_gold\":{\"raw\":0,\"scale\":100000}","\"played_character_gold\":{\"raw\":1,\"scale\":100000}");
        if(changed.equals(NativeSnapshotWaitReceiverFixture.STATE))
            throw new IOException("actual shared STATE gold raw replacement did not select the fixture source");
        pipe.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.snapshot("changed",7,changed)));
        return transport.observe(deadline());
    }
    public void disconnectOnNextPeek(){pipe.failPeek=true;}
    public int actualWriteCalls(){return pipe.writes;}
    public static Instant deadline(){return Instant.now().plusSeconds(5);}
    @Override public void close()throws IOException {transport.close();}
}
