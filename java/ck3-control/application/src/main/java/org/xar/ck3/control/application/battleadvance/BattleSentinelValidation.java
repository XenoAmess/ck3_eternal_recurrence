package org.xar.ck3.control.application.battleadvance;

import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Port of native_driver.py:29965-30207; consumes the single shared strict Status contract. */
public final class BattleSentinelValidation {
    private BattleSentinelValidation() { }
    public static void arm(Status status, int start, int target, int speed, Mode mode, List<Integer> watch, BattleAdvanceStep.Scope scope) {
        boolean combat = scope == BattleAdvanceStep.Scope.ACTIVE_BATTLE ? status.combatCount() > 0
                : scope == BattleAdvanceStep.Scope.ROUTE_CONTACT_WINDOW || status.combatCount() == 0;
        StrictJson.require(status.state() == State.ARMED && !status.generation().decimal().equals("0")
                && status.startingDateRaw() == start && status.targetDateRaw() == target
                && status.lastObservedDateRaw() == start && status.triggerDateRaw() == 0
                && status.speed() == speed && status.mode() == mode && status.armyCount() == watch.size()
                && combat && status.completedDailyTicks() == 0 && status.intermediatePauseCount() == 0
                && status.triggerFlags() == 0 && status.triggerReasons().isEmpty()
                && status.signedDateDeltaFromTargetRaw() == 0 && status.overshootDays() == -1
                && !status.pauseWrapperCalled() && !status.pauseObserved() && !status.terminalObserved() && !status.abnormal(),
                "native tactical sentinel arm acknowledgement is inconsistent");
    }
    private static boolean sameArm(Status status, Status arm, int start, int target, int speed, Mode mode, List<Integer> watch) {
        return status.generation().equals(arm.generation()) && status.startingDateRaw() == start
                && status.targetDateRaw() == target && status.speed() == speed && status.mode() == mode
                && status.armyCount() == watch.size() && status.combatCount() == arm.combatCount();
    }
    public static void stop(Status status, Status arm, int start, int target, int end, int speed, Mode mode, List<Integer> watch) {
        long delta = (long) end - start;
        StrictJson.require(status.state() == State.TRIGGERED && !status.abnormal()
                && sameArm(status, arm, start, target, speed, mode, watch)
                && status.lastObservedDateRaw() == end && status.triggerDateRaw() == end
                && !status.triggerReasons().isEmpty() && status.triggerFlags() != 0 && status.pauseObserved()
                && status.signedDateDeltaFromTargetRaw() == (long) end - target && status.overshootDays() == 0
                && delta > 0 && delta % 24 == 0 && status.completedDailyTicks() == delta / 24,
                "native tactical sentinel stop failed generation/date/tick postcondition");
        StrictJson.require(status.triggerReasons().contains("date_deadline") == (end == target),
                "sentinel deadline reason disagrees with dates");
        boolean nativePause = status.triggerReasons().contains("native_pause");
        StrictJson.require(status.intermediatePauseCount() == (nativePause ? 1 : 0) && status.pauseWrapperCalled() == !nativePause,
                "sentinel pause ownership disagrees with trigger reasons");
    }
    public static void decision(Status status, Status arm, int start, int target, int end, int speed, Mode mode,
            List<Integer> watch, BattleAdvanceFrame.Boundary boundary, boolean canceled) {
        long delta = (long) end - start;
        StrictJson.require(boundary.validIdentity() && boundary.owner().dateRaw() == end && delta >= 0 && delta % 24 == 0 && end <= target,
                "sentinel decision boundary identity/date postcondition failed");
        if (status.state() == State.TRIGGERED) {
            StrictJson.require(!canceled, "normally triggered sentinel must not be canceled");
            stop(status, arm, start, target, end, speed, mode, watch); return;
        }
        StrictJson.require(status.state() == State.IDLE && !status.abnormal() && canceled
                && sameArm(status, arm, start, target, speed, mode, watch)
                && status.completedDailyTicks() <= delta / 24
                && status.lastObservedDateRaw() == start + status.completedDailyTicks() * 24
                && status.triggerDateRaw() == 0 && status.intermediatePauseCount() == 0 && status.triggerFlags() == 0
                && status.triggerReasons().isEmpty() && status.signedDateDeltaFromTargetRaw() == 0 && status.overshootDays() == -1
                && !status.pauseWrapperCalled() && !status.pauseObserved() && !status.terminalObserved(),
                "sentinel decision boundary generation/date/status postcondition failed");
    }
}
