package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.CheckpointResult;
import static org.junit.jupiter.api.Assertions.*;

/** Actual public SAVE -> warm LOAD -> later READ -> repeat LOAD assertion helper.
 * Called by the existing explicit RootPrivateBootstrapActualRegression after its real cold checks.
 * This is not a default no-Game JUnit test. Its one qualified caller supplies the same private Root
 * and real Confirmed SAVE; missing input fails at that actual acceptance entry, never as a skip. */
public final class RootWarmNativeCampaignRestoreCheck {
    private RootWarmNativeCampaignRestoreCheck(){ }
    public interface ActualInput extends AutoCloseable {
        RootApplicationSession originalRoot()throws IOException;
        RootSessionAccess actualAccess()throws IOException;
        CheckpointResult.Confirmed actualPublicSave()throws IOException;
        RootCheckpointPublicCalls.Request request()throws IOException;
        Instant firstDeadline();
        Instant secondDeadline();
        RootFrozenRunProfile.FrozenRunProfile originalFrozen()throws IOException;
        /** The identical installed catalog retained by this actual returned Root; never reconstructed from DATA. */
        RootInstalledCatalog actualCatalog(RootApplicationSession actualRestored)throws IOException;
        @Override void close()throws IOException;
    }
    /** The outer qualified actual fixture owns and closes this original input lifetime. */
    public static RootOrdinaryRestoreCustodyAssertions.Published requireActual(ActualInput input)throws Exception {
            Objects.requireNonNull(input,"MISSING_ACTUAL_WARM_ROOT_INPUT: original qualified Root and actual public SAVE required");
            var original=input.originalRoot();var access=input.actualAccess();var frozen=input.originalFrozen();
            var published=RootOrdinaryRestoreCustodyAssertions.restorePublicSaveTwice(original,access,input.actualPublicSave(),input.request(),
                    input.firstDeadline(),input.secondDeadline(),(actual,binding,deadline)->
                        RootWarmNativeCampaignRestoreAssertions.requireActualRoot(actual,binding,input.actualCatalog(actual),frozen,deadline));
            assertSame(published.second(),access.current());assertTrue(published.first().isRetired());assertFalse(published.second().isRetired());
            assertEquals(0,published.firstBinding().newSavedDayCredit());assertEquals(0,published.secondBinding().newSavedDayCredit());
            return published;
    }
}
