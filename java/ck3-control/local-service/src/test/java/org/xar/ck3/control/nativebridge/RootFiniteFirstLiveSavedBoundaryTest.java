package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.service.root.RootFiniteFirstLiveWork;

/** Actual SAVE/service/journal/material composition; zero-day fixture is not a completed live batch. */
public final class RootFiniteFirstLiveSavedBoundaryTest {
    @TempDir Path temporary;

    @Test public void canonicalSaveAndRealJournalFrontierFeedTheProductionFiniteCaller()throws Exception {
        try(var fixture=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("saved"),false)) {
            var confirmed=assertInstanceOf(org.xar.ck3.control.application.checkpoint.CheckpointResult.Confirmed.class,
                    fixture.service.checkpoint(fixture.request));
            assertEquals(1,fixture.actual.nativeActionWrites());
            var committed=fixture.saveBoundary(confirmed.pair());
            assertEquals(0,committed.committedSavedDays(),"this fixture does not fabricate forward game days");
            fixture.actual.ready();
            fixture.actual.writer.locked(same->{
                long sequence=same.head().state().sequence();
                var actual=RootFiniteFirstLiveWork.requireSavedBoundary(same,fixture.owner,
                        confirmed.pair(),fixture.materials,fixture.batch);
                var original=fixture.materials.currentPhysical(same,confirmed.pair());
                original.requirePhysical(same);
                assertEquals(confirmed.pair(),actual.pair());
                assertEquals(original.reference(),actual.materialReference());
                assertEquals(confirmed.pair().driver().reference(),actual.driverReference());
                assertEquals(sequence,same.head().state().sequence(),"consumer reads the original committed boundary");
                return null;
            });
            assertEquals(1,fixture.actual.nativeActionWrites(),"boundary consumption does not submit another SAVE");
        }
    }

    @Test public void physicalConfirmedPairAloneDoesNotReplaceTheJournalSavedBoundary()throws Exception {
        try(var fixture=new CheckpointSourceCompositionTest.Fixture(temporary.resolve("uncommitted"),false)) {
            var confirmed=assertInstanceOf(org.xar.ck3.control.application.checkpoint.CheckpointResult.Confirmed.class,
                    fixture.service.checkpoint(fixture.request));
            fixture.actual.writer.locked(same->{
                long sequence=same.head().state().sequence();
                assertThrows(IOException.class,()->RootFiniteFirstLiveWork.requireSavedBoundary(
                        same,fixture.owner,confirmed.pair(),fixture.materials,fixture.batch));
                assertEquals(sequence,same.head().state().sequence());
                return null;
            });
            assertEquals(1,fixture.actual.nativeActionWrites());
        }
    }
}
