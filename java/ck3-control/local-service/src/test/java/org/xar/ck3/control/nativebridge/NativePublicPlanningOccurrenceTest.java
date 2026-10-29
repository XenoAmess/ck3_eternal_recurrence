package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual public producer and consumer; software packet/Clock control grants no native/Game qualification. */
final class NativePublicPlanningOccurrenceTest {
    @TempDir Path temporary;
    private static final String SHA="ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d";
    private ActionWriterIntegrationFixture fixture(String name) throws IOException {
        var scene=new ActionWriterIntegrationFixture.SoftwareReadScenario(SHA,"public-occurrence-software",
                ignored->List.of(),ignored->new RawJson(new byte[]{'{','}'}),Optional.empty(),Set.of());
        return new ActionWriterIntegrationFixture(temporary.resolve(name),false,scene,Clock.fixed(Instant.now(),ZoneOffset.UTC));
    }
    private static Instant deadline() { return Instant.now().plusSeconds(10); }
    private static ObservedFrame receive(NativeGameTransport transport) throws IOException {
        try { return transport.observe(deadline()); }
        catch(InterruptedException failure) { Thread.currentThread().interrupt();throw new IOException(failure); }
    }
    private static ObjectNode packet(ObservedFrame frame) {
        byte[] bytes=frame.originalPacket();return (ObjectNode)StrictJson.parse(Arrays.copyOfRange(bytes,4,bytes.length));
    }
    private static void prime(ActionWriterIntegrationFixture actual,boolean ready) throws Exception {
        actual.ready();
        if(!ready) {
            var transport=actual.physicalInputs().transport();var first=transport.currentSnapshot(deadline());
            var body=packet(first);body.put("snapshot_id",first.snapshotId()+"-unpaused");
            ((ObjectNode)body.get("state")).put("paused",false);
            actual.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(body)));receive(transport);
        }
        NativePublicPlanningProducerConsumerTest.bindSoftwareSource(actual);
    }
    private static void requireMode(NativeReadinessCollector.PublicPlanningObservation union,boolean ready) {
        if(ready)assertInstanceOf(NativeReadinessCollector.PublicReady.class,union);
        else assertInstanceOf(NativeReadinessCollector.PublicObserved.class,union);
    }
    @Test void bothBranchesKeepTheActualOccurrenceWithoutExtraReadAndCannotEscape() throws Exception {
        for(boolean ready:List.of(true,false))try(var actual=fixture("same-"+ready)) {
            prime(actual,ready);var escaped=new AtomicReference<NativeReadinessCollector.PublicPlanningFrame>();
            actual.writer.locked(same->actual.collector.withOwnedPublicPlanning(same,actual.observationIdentity(),deadline(),union->{
                requireMode(union,ready);escaped.set(union.frame());
                int reads=actual.nativeReadWrites(),packets=actual.nativePacketReads();
                var first=union.frame().snapshot().actual();var transport=actual.physicalInputs().transport();
                assertSame(first,transport.currentSnapshot(deadline()));
                union.assertCurrent(same);union.frame().assertCurrent(same);
                transport.acceptedSnapshotRevision(first).requireOriginal(transport.currentSnapshot(deadline()));
                assertEquals(reads,actual.nativeReadWrites());assertEquals(packets,actual.nativePacketReads());return null;
            }));
            actual.writer.locked(same->{assertThrows(RuntimeException.class,()->escaped.get().assertCurrent(same));return null;});
            assertEquals(0,actual.nativeActionWrites());
        }
    }
    @Test void bothBranchesRejectFixedClockAbaWithIdenticalRawTimeAndRevision() throws Exception {
        for(boolean ready:List.of(true,false))try(var actual=fixture("aba-"+ready)) {
            prime(actual,ready);var rejected=new AtomicBoolean();var reads=new AtomicInteger(-1);
            assertThrows(IOException.class,()->actual.writer.locked(same->actual.collector.withOwnedPublicPlanning(
                    same,actual.observationIdentity(),deadline(),union->{
                requireMode(union,ready);union.assertCurrent(same);
                // Ready's legitimate ordinary QUERY completed before the consumer count boundary.
                reads.set(actual.nativeReadWrites());var transport=actual.physicalInputs().transport();
                var first=union.frame().snapshot().actual();var token=transport.acceptedSnapshotRevision(first);
                var middle=packet(first);middle.put("snapshot_id",first.snapshotId()+"-middle");
                ((ObjectNode)middle.get("state")).putObject("played_character_gold").put("raw",1).put("scale",100000);
                // Equal native revision permits legal A/B/A without regressing the native counter.
                actual.enqueueSoftwareNativePacket(NativeWire.packet(StrictJson.canonical(middle)));
                var changed=receive(transport);assertNotSame(first,changed);
                assertEquals(first.snapshotId()+"-middle",changed.snapshotId(),"the actual legal B packet must be accepted");
                assertEquals(first.nativeRevision(),changed.nativeRevision());actual.enqueueSoftwareNativePacket(first.originalPacket());
                var last=receive(transport);assertNotSame(first,last);assertEquals(first.session(),last.session());
                assertEquals(first.snapshotId(),last.snapshotId());assertEquals(first.nativeRevision(),last.nativeRevision());
                assertEquals(first.observedAt(),last.observedAt());assertArrayEquals(first.originalPacket(),last.originalPacket());
                assertTrue(transport.acceptedSnapshotRevision(last).received().order().compareTo(token.received().order())>0);
                assertThrows(IOException.class,()->union.assertCurrent(same));rejected.set(true);return null;
            })));
            assertTrue(rejected.get());assertEquals(reads.get(),actual.nativeReadWrites());
            assertEquals(0,actual.nativeActionWrites());assertTrue(actual.physicalInputs().transport().mailboxDiagnostics().poison().isEmpty());
        }
    }
}
