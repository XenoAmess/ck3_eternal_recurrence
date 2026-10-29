package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Actual collector and sole writer fixture: SAVE readiness borrows the active Session and never recursively locks it. */
final class NativeCheckpointBorrowedAdmissionTest {
    @TempDir Path temporary;

    @Test void checkpointInsideTheActualWriterScopeDoesNotOpenAnotherWriterLockOrPlanningQuery()throws Exception{
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("borrowed-checkpoint"),false)){
            var ready=actual.ready();int locks=actual.collectorLocks.get(),queries=actual.nativeReadWrites();
            actual.writer.locked(same->{
                String head=same.head().digest();
                var observed=assertDoesNotThrow(()->actual.collector.checkpoint("checkpoint-lineage").observe(Instant.now().plusSeconds(20)));
                assertEquals(ready.request().before(),observed.observed());
                assertEquals(ready.request().source(),observed.source());
                assertTrue(observed.paused());assertTrue(observed.mapReady());assertTrue(observed.saveEligible());
                assertEquals(locks,actual.collectorLocks.get(),"the original same-writer callback must not acquire another OS writer lock");
                assertEquals(queries,actual.nativeReadWrites(),"SAVE readiness must not start planning queries");
                assertEquals(head,same.head().digest());return null;
            });
        }
    }

    @Test void checkpointOutsideTheWriterScopeUsesExactlyOneOriginalWriterLock()throws Exception{
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("outside-checkpoint"),false)){
            actual.ready();int locks=actual.collectorLocks.get(),queries=actual.nativeReadWrites();
            var observed=actual.collector.checkpoint("checkpoint-lineage").observe(Instant.now().plusSeconds(20));
            assertTrue(observed.saveEligible());
            assertEquals(locks+1,actual.collectorLocks.get());
            assertEquals(queries,actual.nativeReadWrites());
            assertTrue(actual.writer.activeSession().isEmpty());
        }
    }

    @Test void checkpointCannotReplaceAFrozenOrdinaryReadOrRebindTheSoleActiveSessionGetter()throws Exception{
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("frozen-checkpoint"),false)){
            var ready=actual.ready();
            assertThrows(IllegalArgumentException.class,()->actual.collector.bindActiveObservationSession(actual.writer::activeSession));
            actual.writer.locked(same->actual.collector.current(same,ready.request().before(),Instant.now().plusSeconds(20),lease->{
                int reads=actual.nativePacketReads(),locks=actual.collectorLocks.get();
                assertThrows(IllegalArgumentException.class,()->actual.collector.checkpoint("checkpoint-lineage").observe(Instant.now().plusSeconds(10)));
                assertEquals(reads,actual.nativePacketReads());assertEquals(locks,actual.collectorLocks.get());return null;
            }));
        }
    }
}

