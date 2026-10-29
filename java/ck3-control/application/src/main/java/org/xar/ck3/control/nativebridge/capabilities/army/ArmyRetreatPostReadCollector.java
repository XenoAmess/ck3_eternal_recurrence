package org.xar.ck3.control.nativebridge.capabilities.army;

import java.util.List;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.effects.NativeEffectSnapshots;
import org.xar.ck3.control.application.planning.military.ActiveRetreatPost;

/** Observation only, inside the original primitive's actual reconciliation lease. No submit or parent identity is granted. */
public interface ArmyRetreatPostReadCollector {
    /** Transition is mandatory; terminal is added only when the original ActiveRetreatPost policy requests it. */
    List<PlanningReadReceipt> collect(ActionCommand originalChild, ActionState.Attempt originalAttempt,
            NativeEffectSnapshots.Pair actualFrames, OutcomeArchive sameArchive);
    /** Pure replay of the actual one/two post reads; absence or a pending lifecycle cannot authorize retreat Applied. */
    ActiveRetreatPost.Result verifyArchived(ActionCommand originalChild, ActionState.Attempt originalAttempt, NativeEffectSnapshots.Pair actualFrames,
            List<PlanningReadReceipt> originalPostReads, OutcomeArchive sameArchive);
}
