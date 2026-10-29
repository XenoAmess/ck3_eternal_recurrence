package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeLegacyOccurrenceFixture;

/** Actual Endpoint -> NGT accepted occurrence -> the Legacy producer's shared native guard. */
final class RootLegacyResumeNativeOccurrenceTest {
    @Test void fixedClockABARejectsOldADespiteIdenticalPacketTimeAndState()throws Exception {
        try(var fixture=new NativeLegacyOccurrenceFixture()) {
            var transport=fixture.transport();var a1=fixture.receiveA();
            var held=RootLegacyResumeRuntime.NativeOccurrence.capture(transport,a1);
            held.requireCurrent(transport);
            var b=fixture.receiveB();assertFalse(java.util.Arrays.equals(a1.state().bytes(),b.state().bytes()));
            assertThrows(IOException.class,()->held.requireCurrent(transport));
            var a2=fixture.receiveA();
            assertNotSame(a1,a2);assertEquals(a1.session(),a2.session());
            assertEquals(a1.snapshotId(),a2.snapshotId());assertEquals(a1.nativeRevision(),a2.nativeRevision());
            assertEquals(a1.observedAt(),a2.observedAt());assertArrayEquals(a1.originalPacket(),a2.originalPacket());
            assertArrayEquals(a1.state().bytes(),a2.state().bytes());
            // Historical accepted DATA remains readable, but cannot qualify the old original for resume.
            transport.acceptedSnapshotRevision(a1).requireOriginal(a1);
            assertThrows(IOException.class,()->held.requireCurrent(transport));
            assertThrows(IOException.class,()->RootLegacyResumeRuntime.NativeOccurrence.capture(transport,a1));
            var fresh=RootLegacyResumeRuntime.NativeOccurrence.capture(transport,a2);fresh.requireCurrent(transport);
            assertEquals(0,fixture.actualWriteCalls());
        }
    }
    @Test void identicalConsecutivePacketRejectsOldOccurrenceWithoutSemanticRevisionChange()throws Exception {
        try(var fixture=new NativeLegacyOccurrenceFixture()) {
            var transport=fixture.transport();var first=fixture.receiveA();
            var held=RootLegacyResumeRuntime.NativeOccurrence.capture(transport,first);
            var duplicate=fixture.receiveA();
            assertEquals(first.observedAt(),duplicate.observedAt());
            assertArrayEquals(first.originalPacket(),duplicate.originalPacket());
            var oldRevision=transport.acceptedSnapshotRevision(first);var currentRevision=transport.acceptedSnapshotRevision(duplicate);
            assertEquals(oldRevision.publicRevision(),currentRevision.publicRevision());
            assertNotEquals(oldRevision.received().order(),currentRevision.received().order());
            assertThrows(IOException.class,()->held.requireCurrent(transport));
            RootLegacyResumeRuntime.NativeOccurrence.capture(transport,duplicate).requireCurrent(transport);
            assertEquals(0,fixture.actualWriteCalls());
        }
    }
    @Test void reconstructedEqualFrameAndAnotherReceiverCannotAcquireCurrentLegacyOccurrence()throws Exception {
        try(var fixture=new NativeLegacyOccurrenceFixture();var another=new NativeLegacyOccurrenceFixture()) {
            var transport=fixture.transport();var first=fixture.receiveA();another.receiveA();
            var held=RootLegacyResumeRuntime.NativeOccurrence.capture(transport,first);
            var reconstructed=new ObservedFrame(first.session(),first.snapshotId(),first.nativeRevision(),first.state(),
                    first.originalPacket(),first.observedAt());
            assertThrows(IOException.class,()->RootLegacyResumeRuntime.NativeOccurrence.capture(transport,reconstructed));
            assertThrows(IOException.class,()->RootLegacyResumeRuntime.NativeOccurrence.capture(another.transport(),first));
            assertThrows(IOException.class,()->held.requireCurrent(another.transport()));
            held.requireCurrent(transport);
            assertEquals(0,fixture.actualWriteCalls());assertEquals(0,another.actualWriteCalls());
        }
    }
    @Test void actualNativeDisconnectInvalidatesHeldLegacyOccurrenceWhileHistoricalDataRemains()throws Exception {
        try(var fixture=new NativeLegacyOccurrenceFixture()) {
            var transport=fixture.transport();var first=fixture.receiveA();
            var held=RootLegacyResumeRuntime.NativeOccurrence.capture(transport,first);
            fixture.disconnectOnNextPeek();
            assertThrows(UncheckedIOException.class,()->transport.observe(NativeLegacyOccurrenceFixture.deadline()));
            var disconnected=transport.latestStateRevision().orElseThrow();
            assertEquals(NativeGameTransport.StateRevisionKind.DISCONNECTED,disconnected.kind());
            assertEquals(109,disconnected.disconnection().orElseThrow().win32Code());
            transport.acceptedSnapshotRevision(first).requireOriginal(first);
            assertThrows(IOException.class,()->held.requireCurrent(transport));
            assertThrows(IOException.class,()->RootLegacyResumeRuntime.NativeOccurrence.capture(transport,first));
            assertEquals(0,fixture.actualWriteCalls());
        }
    }
    @Test void actualCloseCannotPromoteHistoricalAcceptedDataToCurrentLegacyOccurrence()throws Exception {
        try(var fixture=new NativeLegacyOccurrenceFixture()) {
            var transport=fixture.transport();var first=fixture.receiveA();
            var held=RootLegacyResumeRuntime.NativeOccurrence.capture(transport,first);transport.close();
            var closed=transport.latestStateRevision().orElseThrow();
            assertEquals(NativeGameTransport.StateRevisionKind.DISCONNECTED,closed.kind());
            assertTrue(closed.disconnection().orElseThrow().nativeDisconnectSucceeded());
            transport.acceptedSnapshotRevision(first).requireOriginal(first);
            assertThrows(IOException.class,()->held.requireCurrent(transport));
            assertThrows(IOException.class,()->RootLegacyResumeRuntime.NativeOccurrence.capture(transport,first));
            assertEquals(0,fixture.actualWriteCalls());
        }
    }
}
