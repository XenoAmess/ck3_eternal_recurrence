package org.xar.ck3.control.service.root;

import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.PhysicalActionState;
import static org.junit.jupiter.api.Assertions.*;

/** Test-only consumer for the sole canonical physical producer fixture; this creates no permit or receipt. */
public final class RootGuiPhysicalControlAssertions {
    private RootGuiPhysicalControlAssertions(){ }
    public static void requireZeroBusiness(ActionReceipt actual) {
        assertInstanceOf(PhysicalActionState.class,actual.state());
        RootPlanningInputsFactory.requireSettledControl(new RootPlanningInputsFactory.SystemControl(
                RootPlanningInputsFactory.ControlKind.GUI_PHYSICAL_PRESENTATION),actual);
        assertEquals(ActionReceipt.Outcome.TERMINAL_WITHOUT_EFFECT,actual.outcome());
        assertFalse(actual.visibleGameplay());assertFalse(actual.eligibleAdvance());assertTrue(actual.applied().isEmpty());
    }
    public static void requireUnresolvedBlocked(ActionReceipt actual) {
        assertInstanceOf(PhysicalActionState.class,actual.state());assertFalse(actual.settled());
        assertThrows(IllegalArgumentException.class,()->RootPlanningInputsFactory.requireSettledControl(
                new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.GUI_PHYSICAL_PRESENTATION),actual));
    }
}
