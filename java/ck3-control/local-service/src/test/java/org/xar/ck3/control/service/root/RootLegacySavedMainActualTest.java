package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;

/** Real Main exact6 -> explicit Saved producer -> held writer Prepared/commit -> full cold postbind.
 * Missing admitted startup originals is RED. Historical inspection below never claims committed recovery. */
final class RootLegacySavedMainActualTest {
    @Test void actualSavedMainCommitsLegacyAndPreservesItsOriginalAcrossTwoRealWriterScopes()throws Exception {
        RootStartupLegacyActualInputs.executeFromEnvironment(input->{
            var core=input.core();var root=input.original();var reads=input.readInputs();
            assertSame(root,reads.current());assertSame(core,reads.core());
            var context=reads.catalog().context();
            assertSame(core,context.core());assertSame(root,context.actions());
            assertSame(core.writer(),context.writer());assertSame(core.archive(),context.archive());
            assertSame(root.driver(),context.adopted());assertTrue(root.hasInstalledHost());
            assertSame(input.host(),root.hostForPublication());
            ContinuityStorePort.Session[] firstSession=new ContinuityStorePort.Session[1];
            var original=core.withBorrowed(()->{
                var same=core.writer().borrowedSession();firstSession[0]=same;
                assertSame(same,core.activeBorrowedSession());core.writer().requireSession(same);
                var before=same.head();var cold=context.requireColdReboundOrigin(same);cold.requireOriginal(same);
                var data=cold.data();
                assertEquals(data,RootColdReboundRuntime.Data.decode(data.encode()));
                assertSame(context,cold.context());assertEquals(context.source(),data.source());
                assertEquals(root.identity().game(),data.owner().game());
                assertEquals(root.identity().sessionId(),data.owner().sessionId());
                assertNotEquals(data.pair().frame().game(),data.owner().game(),"Saved Main must use its actual new physical creator");
                same.verifyPin(data.migrationEvent());same.verifyPin(data.bootstrapEvidence());
                same.requireHistoricalState(data.captureSequence(),data.captureHeadDigest());
                assertEquals(0,cold.newSavedDayCredit());assertEquals(0,cold.newCycleCredit());
                assertEquals(before,same.head(),"actual original inspection must neither commit nor adopt again");
                return cold;
            });
            core.withBorrowed(()->{
                var same=core.writer().borrowedSession();core.writer().requireSession(same);
                assertSame(same,core.activeBorrowedSession());assertNotSame(firstSession[0],same);
                var before=same.head();var retained=context.requireColdReboundOrigin(same);
                assertSame(original,retained);retained.requireOriginal(same);
                assertEquals(original.data(),RootColdReboundRuntime.Data.decode(retained.data().encode()));
                same.verifyPin(retained.data().migrationEvent());
                assertEquals(before,same.head(),"a second borrowed scope is a historical read, never a migration replay");
                return null;
            });
            assertSame(root,core.sessionAccess().current());assertFalse(root.isRetired());
        });
    }
}
