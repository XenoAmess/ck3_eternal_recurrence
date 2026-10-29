package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionSnapshotReader;

/** The existing software Driver/journal seam checks rejection before the observation producer can run. */
final class DriverFreshObservationScopeTest {
    @Test void immutableFactsRejectEveryFreshObservationEntryBeforeProducerAndReleaseTheGuardOnExit() throws Exception {
        var fixture=DriverCapabilityStateProducerTest.fresh();
        var known=DriverCapabilityStateProducerTest.published(fixture);
        var repository=new DriverFactsRepository(known);
        var journal=new DriverStateAssemblerTest.Journal(DriverStateAssemblerTest.snapshot(known,List.of()));
        var calls=new AtomicInteger();
        var assembler=new DriverStateAssembler(new ActionSnapshotReader(journal),repository,actual->{
            assertSame(fixture.actual(),actual);calls.incrementAndGet();
            return new DriverObservationFacts.Known(known.observation().orElseThrow());
        });
        var same=DriverCapabilityStateProducerTest.nullSession();
        assembler.withFrozenFacts(frozen->{
            assertSame(known,frozen.state());
            assertThrows(IllegalArgumentException.class,()->assembler.read(fixture.actual()));
            assertThrows(IllegalArgumentException.class,()->assembler.withFrozenObservation(fixture.actual(),same,observed->{
                fail("nested observation callback must not run");return null;
            }));
            assertThrows(IllegalArgumentException.class,()->assembler.withFrozenRawObservation(fixture.actual(),same,observed->{
                fail("nested raw observation callback must not run");return null;
            }));
            assembler.withFrozenFacts(nested->{
                assertSame(known,nested.state());
                assertThrows(IllegalArgumentException.class,()->assembler.read(fixture.actual()));return null;
            });
            assertEquals(0,calls.get());assertSame(known,repository.locked(current->current));return null;
        });
        assertEquals(0,journal.active);
        var actual=assertInstanceOf(DriverObservationFacts.Known.class,assembler.read(fixture.actual()));
        assertEquals(known.observation().orElseThrow(),actual.facts());
        assertEquals(1,calls.get());assertEquals(0,journal.active);
        var after=repository.locked(current->(DriverSnapshotFacts.Known)current);
        assertEquals(known.stamp(),after.stamp());assertEquals(known.auxiliary(),after.auxiliary());
        assertArrayEquals(known.driver().encode(),after.driver().encode());
    }
}
