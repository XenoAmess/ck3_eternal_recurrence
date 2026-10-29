package org.xar.ck3.control.service.root;

import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import static org.junit.jupiter.api.Assertions.*;

/** Consumes an actual canonical military receipt; creates no Root, permit, action or proof. */
public final class RootMilitaryControlAssertions {
    private RootMilitaryControlAssertions(){ }
    public static void requireZeroBusiness(ActionReceipt actual) {
        RootPlanningInputsFactory.requireSettledControl(new RootPlanningInputsFactory.SystemControl(
                RootPlanningInputsFactory.ControlKind.MILITARY_UI_CONTROL),actual);
        if(actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED) {
            var settled=assertInstanceOf(ActionState.Settled.class,actual.state());
            assertInstanceOf(ActionState.ControlApplied.class,settled.settlement());
        }
        assertFalse(actual.visibleGameplay());assertFalse(actual.eligibleAdvance());assertTrue(actual.applied().isEmpty());
    }
    public static void requireUnresolvedBlocked(ActionReceipt actual) {
        assertFalse(actual.settled());
        assertThrows(IllegalArgumentException.class,()->RootPlanningInputsFactory.requireSettledControl(
                new RootPlanningInputsFactory.SystemControl(RootPlanningInputsFactory.ControlKind.MILITARY_UI_CONTROL),actual));
    }
}

