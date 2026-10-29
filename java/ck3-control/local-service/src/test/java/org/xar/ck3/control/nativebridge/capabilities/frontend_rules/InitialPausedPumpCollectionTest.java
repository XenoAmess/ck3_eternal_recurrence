package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeSnapshotWaitPort;
import org.xar.ck3.control.application.driver.InitialDriverBootstrap;
import org.xar.ck3.control.nativebridge.InitialPausedPumpIoFixture;

/**
 * Actual endpoint byte I/O and the existing receiver plus the real Bootstrap collection helper.
 * Software packets prove no managed Game, full Staged qualification, Entry commit or Admitted.
 */
final class InitialPausedPumpCollectionTest {
    private static final BigInteger DATE=BigInteger.valueOf(InitialPausedPumpIoFixture.DATE);
    private static Instant deadline(){return Instant.now().plusSeconds(5);}
    private static byte[] latestHeartbeat(InitialPausedPumpIoFixture input){
        return input.transport().diagnostics().latestHeartbeat().orElseThrow().original().packet().value();
    }
    @Test void oldSnapshotOnlyObserveConsumesAnActualPumpHeartbeatButStillReachesItsOriginalDeadline()throws Exception {
        try(var input=new InitialPausedPumpIoFixture()){
            byte[] advanced=input.publishHeartbeat(2,"2",true,InitialPausedPumpIoFixture.DATE);
            Instant originalDeadline=Instant.now().plusMillis(120);
            assertThrows(UncheckedIOException.class,()->input.transport().observe(originalDeadline));
            assertFalse(Instant.now().isBefore(originalDeadline));
            assertArrayEquals(advanced,latestHeartbeat(input));
            assertEquals(BigInteger.ONE,input.transport().diagnostics().production().orElseThrow().receivedSnapshotCount());
            assertDoesNotThrow(()->GameplayStartEffects.verifyPump(input.firstHeartbeat(),latestHeartbeat(input),DATE),
                    "actual heartbeat progress was already received, but the old consumer still waited for another Snapshot");
            assertEquals(0,input.writeCalls());
        }
    }
    @Test void boundedRealWaitCollectsHeartbeatAndRetainsTheExactOriginalSnapshotWithoutACommand()throws Exception {
        try(var input=new InitialPausedPumpIoFixture()){
            byte[] advanced=input.publishHeartbeat(2,"2",true,InitialPausedPumpIoFixture.DATE);
            var actual=InitialDriverBootstrap.collectPausedPump(input.transport(),deadline(),Clock.systemUTC());
            assertSame(input.first(),actual);
            assertArrayEquals(input.first().originalPacket(),actual.originalPacket());
            assertEquals(input.first().snapshotId(),actual.snapshotId());
            assertEquals(input.first().nativeRevision(),actual.nativeRevision());
            assertEquals(input.first().observedAt(),actual.observedAt());
            assertArrayEquals(advanced,latestHeartbeat(input));
            assertEquals(BigInteger.ONE,input.transport().diagnostics().production().orElseThrow().receivedSnapshotCount());
            assertDoesNotThrow(()->GameplayStartEffects.verifyPump(input.firstHeartbeat(),latestHeartbeat(input),DATE));
            assertEquals(0,input.writeCalls());
        }
    }
    @Test void elapsedAloneCannotProveAnyPausedPumpProgress()throws Exception {
        try(var input=new InitialPausedPumpIoFixture()){
            var actual=InitialDriverBootstrap.collectPausedPump(input.transport(),deadline(),Clock.systemUTC());
            assertSame(input.first(),actual);
            assertArrayEquals(input.firstHeartbeat(),latestHeartbeat(input));
            assertThrows(IllegalArgumentException.class,
                    ()->GameplayStartEffects.verifyPump(input.firstHeartbeat(),latestHeartbeat(input),DATE));
            assertEquals(BigInteger.ONE,input.transport().diagnostics().production().orElseThrow().receivedSnapshotCount());
            assertEquals(0,input.writeCalls());
        }
    }
    private record BadPump(String pump,boolean paused,int date){}
    @Test void ingestedSamePumpWrongDateUnpausedAndBooleanPumpStillFailTheOriginalVerifier()throws Exception {
        for(var bad:List.of(new BadPump("1",true,InitialPausedPumpIoFixture.DATE),
                new BadPump("2",true,InitialPausedPumpIoFixture.DATE+24),
                new BadPump("2",false,InitialPausedPumpIoFixture.DATE),
                new BadPump("true",true,InitialPausedPumpIoFixture.DATE))){
            try(var input=new InitialPausedPumpIoFixture()){
                byte[] original=input.publishHeartbeat(2,bad.pump(),bad.paused(),bad.date());
                assertSame(input.first(),InitialDriverBootstrap.collectPausedPump(input.transport(),deadline(),Clock.systemUTC()));
                assertArrayEquals(original,latestHeartbeat(input));
                assertThrows(IllegalArgumentException.class,
                        ()->GameplayStartEffects.verifyPump(input.firstHeartbeat(),latestHeartbeat(input),DATE));
                assertEquals(0,input.writeCalls());
            }
        }
    }
    @Test void actualSourceFailureAndForeignClientRemainFailuresRatherThanElapsedSuccess()throws Exception {
        for(boolean foreign:List.of(false,true)){
            try(var input=new InitialPausedPumpIoFixture()){
                input.publishHeartbeat(2,"2",true,InitialPausedPumpIoFixture.DATE);
                if(foreign)input.foreignPid();else input.failSource("Native transport deadline expired");
                assertThrows(IOException.class,
                        ()->InitialDriverBootstrap.collectPausedPump(input.transport(),deadline(),Clock.systemUTC()));
                assertEquals(0,input.writeCalls());
            }
        }
    }
    @Test void expiredDeadlineDoesNoIoAndClippedTypedWaitRetainsTheOriginalCaptureDeadline()throws Exception {
        try(var input=new InitialPausedPumpIoFixture()){
            int reads=input.readCalls();
            assertThrows(IOException.class,()->InitialDriverBootstrap.collectPausedPump(input.transport(),
                    Instant.now().minusNanos(1),Clock.systemUTC()));
            assertEquals(reads,input.readCalls());
            var recording=new RecordingPort(input.transport());
            Instant originalDeadline=Instant.now().plusMillis(120);
            Clock nearDeadline=Clock.fixed(originalDeadline.minusMillis(1),ZoneOffset.UTC);
            try{
                InitialDriverBootstrap.collectPausedPump(recording,originalDeadline,nearDeadline);
            }catch(IOException actualDeadline){
                // A zero-prefix wait may finish too late for the final original capture check.
                // The original deadline remains binding; no retry or later deadline is supplied.
            }
            assertEquals(originalDeadline,recording.captureUntil);
            assertNotNull(recording.waitUntil);
            assertTrue(recording.waitUntil.isBefore(originalDeadline));
            assertFalse(recording.waitUntil.isAfter(nearDeadline.instant().plusMillis(50)));
            assertThrows(IllegalArgumentException.class,
                    ()->GameplayStartEffects.verifyPump(input.firstHeartbeat(),latestHeartbeat(input),DATE));
            assertEquals(0,input.writeCalls());
        }
    }
    @Test void startedPartialPacketFailureCannotBecomeElapsedOrRetainedFrameSuccess()throws Exception {
        try(var input=new InitialPausedPumpIoFixture()){
            byte[] partial={1,0};input.publishPartial(partial);
            assertThrows(IOException.class,()->InitialDriverBootstrap.collectPausedPump(input.transport(),
                    Instant.now().plusMillis(120),Clock.systemUTC()));
            assertArrayEquals(partial,input.retainedFailureBytes());
            assertEquals(0,input.writeCalls());
        }
    }
    @Test void anActualNewSnapshotKeepsNormalReceiveAccountingAndIsNotPumpEvidence()throws Exception {
        try(var input=new InitialPausedPumpIoFixture()){
            byte[] original=input.publishSnapshot("paused-next",8);
            var actual=InitialDriverBootstrap.collectPausedPump(input.transport(),deadline(),Clock.systemUTC());
            assertNotSame(input.first(),actual);
            assertArrayEquals(original,actual.originalPacket());
            assertEquals("paused-next",actual.snapshotId());
            assertEquals(BigInteger.valueOf(8),actual.nativeRevision());
            assertEquals(BigInteger.TWO,input.transport().diagnostics().production().orElseThrow().receivedSnapshotCount());
            assertThrows(IllegalArgumentException.class,
                    ()->GameplayStartEffects.verifyPump(input.firstHeartbeat(),latestHeartbeat(input),DATE));
            assertEquals(0,input.writeCalls());
        }
    }
    /** Only records arguments before forwarding to the identical real receiver; issues no source authority. */
    private static final class RecordingPort implements NativeSnapshotWaitPort {
        private final NativeSnapshotWaitPort actual;
        private Instant waitUntil,captureUntil;
        private RecordingPort(NativeSnapshotWaitPort actual){this.actual=actual;}
        public NativeObservationPort.ObservedFrame observe(Instant deadline)throws InterruptedException{return actual.observe(deadline);}
        public NativeObservationPort.ObservedFrame currentSnapshot(Instant deadline)throws IOException{return actual.currentSnapshot(deadline);}
        public WaitResult waitForSnapshot(Instant waitUntil,Instant captureUntil)throws IOException,InterruptedException{
            this.waitUntil=waitUntil;this.captureUntil=captureUntil;
            return actual.waitForSnapshot(waitUntil,captureUntil);
        }
    }
}
