package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame;

/** Actual shared software Win32 source -> Endpoint -> sole accepted-receive producer. No Game qualification. */
final class NativeAcceptedSnapshotRevisionTest {
    @Test void receivesAdvanceBeforeProjectionAndEquivalentCanonicalStateDoesNot()throws Exception {
        try(var fixture=new NativeSnapshotWaitReceiverFixture(NativeSnapshotWaitReceiverFixture.STATE
                .replace("\"date_raw\":1234","\"fixture_numeric\":0,\"date_raw\":1234").getBytes(StandardCharsets.UTF_8))) {
            var transport=fixture.transport();
            assertTrue(transport.latestAcceptedSnapshotRevision().isEmpty());
            assertTrue(transport.latestStateRevision().isEmpty());
            transport.awaitHello(NativeSnapshotWaitReceiverFixture.deadline());
            var hello=transport.latestStateRevision().orElseThrow();
            assertEquals(NativeGameTransport.StateRevisionKind.HELLO,hello.kind());
            assertEquals(BigInteger.ONE,hello.publicRevision());assertTrue(hello.disconnection().isEmpty());
            var first=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            var original=transport.acceptedSnapshotRevision(first);
            assertEquals(BigInteger.TWO,original.publicRevision());original.requireOriginal(first);
            var firstState=transport.latestStateRevision().orElseThrow();
            assertEquals(NativeGameTransport.StateRevisionKind.SNAPSHOT,firstState.kind());
            assertEquals(original.session(),firstState.session());assertEquals(original.received(),firstState.received());
            assertEquals(original.publicRevision(),firstState.publicRevision());
            assertTrue(firstState.received().order().compareTo(hello.received().order())>0);
            assertSame(first,transport.currentSnapshot(NativeSnapshotWaitReceiverFixture.deadline()));
            fixture.publishSnapshot("first",7,NativeSnapshotWaitReceiverFixture.STATE
                    .replace("\"date_raw\":1234","\"fixture_numeric\":0.0,\"date_raw\":1234").getBytes(StandardCharsets.UTF_8));
            var same=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            var unchanged=transport.acceptedSnapshotRevision(same);
            assertEquals(BigInteger.TWO,unchanged.publicRevision());
            assertTrue(unchanged.received().order().compareTo(original.received().order())>0);
            assertEquals(unchanged.received(),transport.latestStateRevision().orElseThrow().received());
            assertThrows(IOException.class,()->original.requireOriginal(same));
            fixture.publishSnapshot("changed",9,NativeSnapshotWaitReceiverFixture.STATE
                    .replace("\"played_character_gold\":{\"raw\":0,\"scale\":100000}",
                            "\"played_character_gold\":{\"raw\":1,\"scale\":100000}").getBytes(StandardCharsets.UTF_8));
            var changed=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            var latest=transport.acceptedSnapshotRevision(changed);
            assertEquals(BigInteger.valueOf(3),latest.publicRevision());
            assertSame(latest,transport.latestAcceptedSnapshotRevision().orElseThrow());
            assertSame(changed,transport.latestObservedSnapshot().orElseThrow());
            assertSame(latest,transport.acceptedSnapshotRevision(transport.latestObservedSnapshot().orElseThrow()));
            assertSame(original,transport.acceptedSnapshotRevision(first));
            transport.close();
            assertSame(latest,transport.latestAcceptedSnapshotRevision().orElseThrow());
            assertSame(original,transport.acceptedSnapshotRevision(first));
            var disconnected=transport.latestStateRevision().orElseThrow();
            assertEquals(NativeGameTransport.StateRevisionKind.DISCONNECTED,disconnected.kind());
            assertEquals(BigInteger.valueOf(4),disconnected.publicRevision());
            assertTrue(disconnected.disconnection().orElseThrow().nativeDisconnectSucceeded());
            assertEquals("DisconnectNamedPipe",disconnected.disconnection().orElseThrow().operation());
            transport.close();
            assertSame(disconnected,transport.latestStateRevision().orElseThrow());
        }
    }
    @Test void equalDataCannotCreateReceiverOccurrenceAndRejectedSnapshotDoesNotAdvance()throws Exception {
        try(var fixture=new NativeSnapshotWaitReceiverFixture()) {
            var transport=fixture.transport();var first=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            var original=transport.acceptedSnapshotRevision(first);
            var reconstructed=new ObservedFrame(first.session(),first.snapshotId(),first.nativeRevision(),first.state(),
                    first.originalPacket(),first.observedAt());
            assertThrows(IOException.class,()->original.requireOriginal(reconstructed));
            assertThrows(IOException.class,()->transport.acceptedSnapshotRevision(reconstructed));
            fixture.publishSnapshot("rejected",8,NativeSnapshotWaitReceiverFixture.STATE
                    .replace("\"date_raw\":1234","\"date_raw\":true").getBytes(StandardCharsets.UTF_8));
            fixture.publishSnapshot("accepted-again",9);
            var next=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            assertEquals(BigInteger.valueOf(3),transport.acceptedSnapshotRevision(next).publicRevision());
        }
    }
    @Test void secondHelloIsTerminalAndCannotForgeAnotherConnectedTransition()throws Exception {
        var api=new NativeSnapshotWaitReceiverFixture.Pipe();
        api.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.HELLO));
        try(var transport=NativeSnapshotWaitReceiverFixture.transport(api,16)) {
            transport.awaitHello(NativeSnapshotWaitReceiverFixture.deadline());
            var original=transport.latestStateRevision().orElseThrow();
            api.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.HELLO));
            assertThrows(java.io.UncheckedIOException.class,()->transport.observe(NativeSnapshotWaitReceiverFixture.deadline()));
            assertSame(original,transport.latestStateRevision().orElseThrow());
            assertEquals(NativeGameTransport.ReceivedState.TERMINAL,transport.diagnostics().receivedState());
            assertTrue(transport.latestAcceptedSnapshotRevision().isEmpty());
            assertEquals(0,api.writes);
        }
    }
    @Test void regressedActualChronologyRejectsReceiveWithoutInventingAnAcceptedRevision()throws Exception {
        var api=new NativeSnapshotWaitReceiverFixture.Pipe();
        api.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.HELLO));
        var time=new java.util.concurrent.atomic.AtomicReference<>(Instant.parse("2026-10-25T12:00:00Z"));
        Clock clock=new Clock() {
            @Override public java.time.ZoneId getZone(){return ZoneOffset.UTC;}
            @Override public Clock withZone(java.time.ZoneId zone){return Clock.fixed(time.get(),zone);}
            @Override public Instant instant(){return time.get();}
        };
        try(var transport=new NativeGameTransport(NativeSnapshotWaitReceiverFixture.endpoint(api),
                NativeSnapshotWaitReceiverFixture.config(),16,16,List.of(),clock)) {
            transport.awaitHello(NativeSnapshotWaitReceiverFixture.deadline());
            var hello=transport.latestStateRevision().orElseThrow();
            byte[] original=NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.snapshot("first",7,NativeSnapshotWaitReceiverFixture.STATE));
            api.add(original);time.set(time.get().minusSeconds(1));
            assertThrows(java.io.UncheckedIOException.class,()->transport.observe(NativeSnapshotWaitReceiverFixture.deadline()));
            assertSame(hello,transport.latestStateRevision().orElseThrow());
            assertTrue(transport.latestAcceptedSnapshotRevision().isEmpty());
            assertArrayEquals(original,transport.lastOriginalPacket());
            assertEquals(NativeGameTransport.ReceivedState.TERMINAL,transport.diagnostics().receivedState());
            assertEquals(0,api.writes);
        }
    }
    @Test void invalidDateCannotMintOccurrenceOrStateRevisionAndLegalSameRevisionStillArrives()throws Exception {
        String sourceState=NativeSnapshotWaitReceiverFixture.STATE.replace("\"date_raw\":1234","\"date_raw\":1");
        for(String token:new String[]{"true","false","1.0","1e0","null","\"1\"","<missing>"}) {
            var api=new NativeSnapshotWaitReceiverFixture.Pipe();
            api.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.HELLO));
            api.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.snapshot("first",7,sourceState)));
            try(var transport=NativeSnapshotWaitReceiverFixture.transport(api,1)) {
                var first=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
                var accepted=transport.acceptedSnapshotRevision(first);
                var state=transport.latestStateRevision().orElseThrow();
                String invalid=token.equals("<missing>")?sourceState.replace("\"date_raw\":1,","")
                        :sourceState.replace("\"date_raw\":1","\"date_raw\":"+token);
                byte[] original=NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.snapshot("next",8,invalid));
                api.add(original);
                assertThrows(java.io.UncheckedIOException.class,()->transport.observe(NativeSnapshotWaitReceiverFixture.deadline()));
                assertSame(accepted,transport.latestAcceptedSnapshotRevision().orElseThrow());
                assertSame(state,transport.latestStateRevision().orElseThrow());
                assertSame(first,transport.latestObservedSnapshot().orElseThrow());
                assertSame(first,transport.currentSnapshot(NativeSnapshotWaitReceiverFixture.deadline()));
                assertArrayEquals(original,transport.lastOriginalPacket());
                assertEquals(NativeGameTransport.ReceivedState.HELLO_VERIFIED,transport.diagnostics().receivedState());
                // Rejected native revision 8 never replaced accepted revision 7; a valid original 8 remains admissible.
                api.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.snapshot("next",8,sourceState)));
                var legal=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
                var next=transport.acceptedSnapshotRevision(legal);
                assertEquals(BigInteger.valueOf(8),legal.nativeRevision());
                // Native identity changed from first/7 to next/8, which changes the original Python semantic dict.
                assertEquals(accepted.publicRevision().add(BigInteger.ONE),next.publicRevision());
                assertTrue(next.received().order().compareTo(accepted.received().order().add(BigInteger.ONE))>0);
                assertEquals(next.received(),transport.latestStateRevision().orElseThrow().received());
                assertEquals(BigInteger.ONE,org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(
                        org.xar.ck3.control.application.driver.DriverObservationAssembler.originalNativeState(legal).get("date_raw"),"date_raw"));
                assertThrows(IOException.class,()->accepted.requireOriginal(legal));assertEquals(0,api.writes);
            }
        }
    }
    @Test void nativeIdentityRemainsPartOfOriginalPythonCanonicalRevisionComparison()throws Exception {
        try(var fixture=new NativeSnapshotWaitReceiverFixture()) {
            var transport=fixture.transport();
            var first=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            assertEquals(BigInteger.TWO,transport.acceptedSnapshotRevision(first).publicRevision());
            fixture.publishSnapshot("second",7);
            var changedId=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            assertEquals(BigInteger.valueOf(3),transport.acceptedSnapshotRevision(changedId).publicRevision());
            fixture.publishSnapshot("second",8);
            var changedRevision=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            var original=transport.acceptedSnapshotRevision(changedRevision);
            assertEquals(BigInteger.valueOf(4),original.publicRevision());
            fixture.publishSnapshot("second",8);
            var repeated=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            var next=transport.acceptedSnapshotRevision(repeated);
            assertEquals(original.publicRevision(),next.publicRevision());
            assertNotSame(changedRevision,repeated);
            assertTrue(next.received().order().compareTo(original.received().order())>0);
            assertThrows(IOException.class,()->original.requireOriginal(repeated));
        }
    }
    @Test void fixedClockABAWithIdenticalPacketsRetainsDifferentActualOccurrenceRevisions()throws Exception {
        var api=new NativeSnapshotWaitReceiverFixture.Pipe();
        api.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.HELLO));
        byte[] a=NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.snapshot("same",7,NativeSnapshotWaitReceiverFixture.STATE));
        api.add(a);
        var clock=Clock.fixed(Instant.parse("2026-10-25T00:00:00Z"),ZoneOffset.UTC);
        try(var transport=new NativeGameTransport(NativeSnapshotWaitReceiverFixture.endpoint(api),
                NativeSnapshotWaitReceiverFixture.config(),16,16,List.of(),clock)) {
            var first=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            var firstRevision=transport.acceptedSnapshotRevision(first);
            api.add(NativeSnapshotWaitReceiverFixture.packet(NativeSnapshotWaitReceiverFixture.snapshot("changed",7,
                    NativeSnapshotWaitReceiverFixture.STATE.replace("\"played_character_gold\":{\"raw\":0,\"scale\":100000}",
                            "\"played_character_gold\":{\"raw\":1,\"scale\":100000}"))));
            var middle=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            api.add(a);
            var last=transport.observe(NativeSnapshotWaitReceiverFixture.deadline());
            var lastRevision=transport.acceptedSnapshotRevision(last);
            assertNotSame(first,last);assertArrayEquals(first.originalPacket(),last.originalPacket());
            assertEquals(first.observedAt(),last.observedAt());
            assertEquals(BigInteger.TWO,firstRevision.publicRevision());
            assertEquals(BigInteger.valueOf(3),transport.acceptedSnapshotRevision(middle).publicRevision());
            assertEquals(BigInteger.valueOf(4),lastRevision.publicRevision());
            assertTrue(lastRevision.received().order().compareTo(firstRevision.received().order())>0);
            assertSame(firstRevision,transport.acceptedSnapshotRevision(first));
            assertThrows(IOException.class,()->lastRevision.requireOriginal(first));
        }
    }
}
