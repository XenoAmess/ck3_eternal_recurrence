package org.xar.ck3.control.service.root;

import java.io.IOException;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import static org.junit.jupiter.api.Assertions.*;

/** Runs the production classifier over canonical producer receipts; creates no authority or receipt. */
public final class RootPublicPausePlanningAssertions {
    private RootPublicPausePlanningAssertions() { }

    public static void requireZeroBusiness(RootPlanningDomainCatalog catalog,Session same,
            OutcomeArchive originals,ActionReceipt actual)throws IOException {
        assertEquals(new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.PUBLIC_PAUSE_CONTROL),
                catalog.classify(actual,same,originals));
        RootPlanningInputsFactory.requireSettledControl(new RootPlanningInputsFactory.SystemControl(
                RootPlanningInputsFactory.ControlKind.PUBLIC_PAUSE_CONTROL),actual);
        assertFalse(actual.visibleGameplay());assertFalse(actual.eligibleAdvance());assertTrue(actual.applied().isEmpty());
    }

    public static void requireUnresolvedBlocked(ActionReceipt actual) {
        assertFalse(actual.settled());
        assertThrows(IllegalArgumentException.class,()->RootPlanningInputsFactory.requireSettledControl(
                new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.PUBLIC_PAUSE_CONTROL),actual));
    }
}
