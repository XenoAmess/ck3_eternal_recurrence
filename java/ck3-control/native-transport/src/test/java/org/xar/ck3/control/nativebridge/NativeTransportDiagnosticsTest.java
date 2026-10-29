package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.Callable;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** Actual software endpoint -> sole NGT read/strict shared parser -> immutable diagnostic consumers. */
final class NativeTransportDiagnosticsTest {
    private static final String SHA="a".repeat(64);
    private static final String STATE="{\"date_raw\":1234,\"speed\":1,\"paused\":true,\"map_ready\":true,\"played_character\":{\"character_id\":31254,\"alive\":true},\"active_event\":null,\"pending_character_interaction\":null,\"one_life_settlement\":null,\"played_character_gold\":0,\"played_character_prestige\":0,\"played_character_piety\":0,\"history\":[],\"active_wars\":[],\"player_armies\":[]}";
    @Test void everyRealRejectedReceiveAndPublishIsCountedWithoutReplacingAcceptedStateOrRefreshingDiagnostics()throws Exception {
        Replay replay=new Replay();replay.add(hello());replay.add(snapshot("accepted",7,STATE));
        var transport=transport(replay,16);transport.awaitHello(deadline());var accepted=transport.observe(deadline());
        assertEquals("accepted",accepted.snapshotId());var initial=production(transport);
        assertEquals(BigInteger.ONE,initial.receivedSnapshotCount());assertEquals(BigInteger.ZERO,initial.rejectedSnapshotCount());assertTrue(initial.lastRejectedSnapshot().isEmpty());
        replay.add(publish("one","begin"));replay.add(publish("one","end"));
        byte[] bad=snapshot("rejected",8,STATE.replace("\"active_wars\":[]","\"active_wars\":true"));replay.add(bad);
        assertThrows(UncheckedIOException.class,()->transport.observe(deadline()),"bounded software queue ends after real semantic rejection");
        var captured=transport.diagnostics();var data=captured.production().orElseThrow();
        assertEquals(BigInteger.TWO,data.receivedSnapshotCount());assertEquals(BigInteger.ONE,data.rejectedSnapshotCount());assertEquals(BigInteger.TWO,data.snapshotPublishDiagnosticCount());
        assertEquals(BigInteger.TWO,data.lastReceivedSnapshot().orElseThrow().ordinal());
        assertArrayEquals(bad,data.lastRejectedSnapshot().orElseThrow().original().originalPacket().value());
        assertEquals("accepted",transport.latestObservedSnapshot().orElseThrow().snapshotId(),"semantic rejection must preserve the earlier accepted source");
        assertEquals(NativeGameTransport.ReceivedState.HELLO_VERIFIED,captured.receivedState(),"semantic rejection is not a terminal transport failure");
        int reads=replay.reads.get(),writes=replay.writes.get();for(int i=0;i<100;i++)transport.diagnostics();
        assertEquals(reads,replay.reads.get());assertEquals(writes,replay.writes.get());
        replay.add(snapshot("next",9,STATE));assertEquals("next",transport.observe(deadline()).snapshotId());
        assertEquals(BigInteger.ONE,production(transport).rejectedSnapshotCount());assertEquals(BigInteger.TWO,data.receivedSnapshotCount(),"captured diagnostic values are immutable");
        assertEquals(transport.awaitHello(deadline()),data.session().orElseThrow());assertEquals(initial.custodyEpoch(),data.custodyEpoch());
        byte[] altered=data.lastRejectedSnapshot().orElseThrow().original().originalPacket().value();altered[altered.length-1]^=1;
        assertEquals(NativeRequestChronology.PacketIdentity.of(bad),NativeRequestChronology.PacketIdentity.of(data.lastRejectedSnapshot().orElseThrow().original().originalPacket().value()));
    }
    @Test void repeatedMalformedSnapshotEnvelopeCountsEachActualReceiveAndKeepsOriginalMissingNullBoolAndFloatTokens()throws Exception {
        Replay replay=new Replay();replay.add(hello());var transport=transport(replay,8);transport.awaitHello(deadline());
        byte[] malformed=packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":null,\"revision\":1.0,\"state\":{\"date_raw\":true,\"speed\":null,\"paused\":false}}");
        replay.add(malformed);replay.add(malformed);assertThrows(UncheckedIOException.class,()->transport.observe(deadline()));
        var production=production(transport);assertEquals(BigInteger.TWO,production.rejectedSnapshotCount());assertEquals(BigInteger.TWO,production.receivedSnapshotCount());
        var fields=production.lastRejectedSnapshot().orElseThrow().original().fields();
        assertEquals(NativeWire.Presence.NULL,fields.snapshotId().presence());assertEquals(NativeWire.Presence.ABSENT,fields.mapReady().presence());assertEquals(NativeWire.Presence.NULL,fields.speed().presence());
        assertTrue(NativeWire.parse(fields.revision().token().orElseThrow().value()).isFloatingPointNumber());assertTrue(NativeWire.parse(fields.dateRaw().token().orElseThrow().value()).isBoolean());
        assertTrue(transport.latestObservedSnapshot().isEmpty());assertEquals(NativeGameTransport.ReceivedState.HELLO_VERIFIED,transport.diagnostics().receivedState());
        assertArrayEquals(malformed,transport.lastOriginalPacket());
    }
    @Test void realConcurrentCaptureReadsOneCoherentLifetimeWithoutAdditionalEndpointOperations()throws Exception {
        Replay replay=new Replay();replay.add(hello());var transport=transport(replay,512);transport.awaitHello(deadline());
        for(int index=0;index<256;index++)replay.add(publish("publish-"+index,"end"));replay.add(snapshot("accepted",7,STATE));
        var pool=Executors.newFixedThreadPool(5);
        try {
            var ingestion=pool.submit(()->transport.observe(deadline()));var readers=new ArrayList<Callable<Boolean>>();
            for(int worker=0;worker<4;worker++)readers.add(()->{BigInteger previous=BigInteger.ZERO;for(int index=0;index<128;index++){
                var data=production(transport);assertTrue(data.snapshotPublishDiagnosticCount().compareTo(previous)>=0);previous=data.snapshotPublishDiagnosticCount();
                assertEquals(data.receivedSnapshotCount().signum()==0,data.lastReceivedSnapshot().isEmpty());assertEquals(BigInteger.ZERO,data.rejectedSnapshotCount());
            }return true;});
            for(var result:pool.invokeAll(readers,10,TimeUnit.SECONDS))assertTrue(result.get(10,TimeUnit.SECONDS));assertEquals("accepted",ingestion.get(10,TimeUnit.SECONDS).snapshotId());
        }finally{pool.shutdownNow();assertTrue(pool.awaitTermination(10,TimeUnit.SECONDS));}
        assertEquals(BigInteger.valueOf(256),production(transport).snapshotPublishDiagnosticCount());assertEquals(258,replay.reads.get());assertEquals(0,replay.writes.get());
    }
    @Test void actualTypedAdoptionEventsDistinguishUnavailableKnownNullAndFirstTerminalRefusal()throws Exception {
        Replay replay=new Replay();replay.add(hello());var transport=transport(replay,8);
        assertInstanceOf(NativeTransportDiagnostics.Unobserved.class,production(transport).adoption());
        assertThrows(IOException.class,transport::recordAdoptionObserved);transport.awaitHello(deadline());
        assertInstanceOf(NativeTransportDiagnostics.Unobserved.class,production(transport).adoption(),"HELLO is not Driver adoption");
        transport.recordAdoptionObserved();assertTrue(((NativeTransportDiagnostics.Observed)production(transport).adoption()).refusal().isEmpty());
        transport.recordAdoptionRefused(NativeTransportDiagnostics.AdoptionRefusalReason.PERSISTED_LIFECYCLE_MISMATCH,"ActualTypedRefusal","original lifecycle mismatch");
        var refusal=((NativeTransportDiagnostics.Observed)production(transport).adoption()).refusal().orElseThrow();
        assertEquals("persisted_lifecycle_mismatch",refusal.reason().wire());assertEquals("hello_adoption",refusal.stage());assertEquals("original lifecycle mismatch",refusal.message());
        assertArrayEquals(hello(),refusal.originalHello().original().packet().value());assertEquals(production(transport).session().orElseThrow(),refusal.session());
        transport.recordAdoptionRefused(NativeTransportDiagnostics.AdoptionRefusalReason.INVALID_DRIVER_JOURNAL,"OtherRefusal","other failure");
        assertEquals(refusal,((NativeTransportDiagnostics.Observed)production(transport).adoption()).refusal().orElseThrow());assertThrows(IOException.class,transport::recordAdoptionObserved);
        assertEquals(NativeGameTransport.ReceivedState.TERMINAL,transport.diagnostics().receivedState());
        var historical=new NativeGameTransport.TransportDiagnostics(transport.diagnostics().receivedState(),transport.diagnostics().session(),transport.diagnostics().originalHello(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),new NativeWire.Bytes(new byte[0]));
        assertTrue(historical.production().isEmpty(),"legacy constructor cannot claim zero/null original production");
    }
    @Test void malformedProtocolAndReadIoDoNotBecomeSemanticRejectionOrInventAnAdoptionRefusal()throws Exception {
        Replay replay=new Replay();replay.add(hello());var transport=transport(replay,8);transport.awaitHello(deadline());
        replay.add(packet("{\"type\":\"state_snapshot\",\"protocol_version\":true,\"revision\":1}"));assertThrows(UncheckedIOException.class,()->transport.observe(deadline()));
        assertEquals(BigInteger.ZERO,production(transport).rejectedSnapshotCount());assertInstanceOf(NativeTransportDiagnostics.Unobserved.class,production(transport).adoption());
        assertEquals(NativeGameTransport.ReceivedState.TERMINAL,transport.diagnostics().receivedState());
        BigInteger exact=new BigInteger("9007199254740993");var captured=production(transport);
        var large=new NativeTransportDiagnostics.Production(captured.custodyEpoch(),captured.session(),BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),exact,Optional.empty(),captured.adoption());
        assertEquals(exact,large.snapshotPublishDiagnosticCount());assertThrows(IllegalArgumentException.class,()->new NativeTransportDiagnostics.Production(captured.custodyEpoch(),captured.session(),BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),NativeWire.UINT64_MAX.add(BigInteger.ONE),Optional.empty(),captured.adoption()));
    }
    private static NativeTransportDiagnostics.Production production(NativeGameTransport transport){return transport.diagnostics().production().orElseThrow();}
    private static Instant deadline(){return Instant.now().plusSeconds(20);}
    private static NativeGameTransport transport(Replay replay,int frames){return new NativeGameTransport(replay,new NativePipeEndpoint.Config("\\\\.\\pipe\\diagnostic-fixture","fixture-machine",new GameGeneration(12700,new PythonOnlyUInt64(BigInteger.ONE)),"diagnostic-session","fixture-bridge",SHA,"fixture-adapter"),frames,16);}
    private static byte[] hello()throws IOException{return packet("{\"type\":\"hello\",\"protocol_version\":1,\"pid\":12700,\"connection_generation\":1,\"bridge_version\":\"fixture-bridge\",\"expected_ck3_sha256\":\""+SHA+"\",\"game_adapter_id\":\"fixture-adapter\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}");}
    private static byte[] snapshot(String id,long revision,String state)throws IOException{return packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\""+id+"\",\"revision\":"+revision+",\"state\":"+state+"}");}
    private static byte[] publish(String id,String phase)throws IOException{return packet("{\"type\":\"snapshot_publish_diagnostic\",\"protocol_version\":1,\"request_id\":\""+id+"\",\"phase\":\""+phase+"\",\"status\":\"actual\",\"revision\":7,\"payload_bytes\":1}");}
    private static byte[] packet(String json)throws IOException{return NativeWire.packet(json.getBytes(StandardCharsets.UTF_8));}
    private static final class Replay implements NativePacketPort {
        private final ArrayDeque<byte[]> queued=new ArrayDeque<>();final AtomicInteger reads=new AtomicInteger();final AtomicInteger writes=new AtomicInteger();
        synchronized void add(byte[] packet){queued.add(packet.clone());}
        @Override public void verify(){ }
        @Override public void awaitConnection(Instant deadline){ }
        @Override public synchronized byte[] readPacket(Instant deadline)throws IOException {reads.incrementAndGet();if(queued.isEmpty())throw new IOException("software fixture has no further received packet");return queued.remove().clone();}
        @Override public void writePacket(byte[] packet,Instant deadline){writes.incrementAndGet();}
        @Override public void close(){ }
    }
}
