package org.xar.ck3.control.wave3.governance.lifestylehistory;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.Field;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.PendingAction;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.Request;
import org.xar.ck3.control.wave3.governance.lifestylehistory.LifestyleHistory.Selection;

/** One typed consumer port. It gates selection; it never sends, retries, or marks a saved checkpoint. */
public final class LifestyleHistoryConsumer {
    private LifestyleHistoryConsumer() { }
    public static Request applyPendingGuard(Request current, Selection selection) {
        Objects.requireNonNull(current); Objects.requireNonNull(selection);
        StrictJson.require(!current.pendingAction().present(), "a second pending source cannot override an existing observation");
        if (selection.status() != LifestyleHistory.Status.EPISODE_UNAVAILABLE) {
            StrictJson.require(current.snapshot().present() && current.snapshot().value().episodeRunId().is(selection.episodeRunId()),
                    "history selection must bind the current actual episode before it can guard a consumer");
        }
        Field<PendingAction> pending = pendingGuard(selection);
        return new Request(current.snapshot(), current.feudalScopeAdmitted(), current.atPeace(), current.collectTaxesActive(),
                current.allowWartimePerk(), current.allowWartimeInitialFocus(), current.preferredFocusTargetKey(), pending, current.focusScopeAdmitted());
    }
    /** The single pending-state projection shared by typed and legacy mechanical consumers. */
    public static Field<PendingAction> pendingGuard(Selection selection) {
        Objects.requireNonNull(selection);
        return switch (selection.status()) {
            case CLEAR -> Field.nullValue();
            case VERIFY_ORIGINAL_RECEIPT -> Field.of(new PendingAction(Field.of(selection.pendingActions().getFirst().status())));
            case HOLD_UNKNOWN, CONFLICT, EPISODE_UNAVAILABLE -> Field.of(new PendingAction(Field.of("action_state_unknown")));
        };
    }
    public static LifestyleMinPolicy.Decision chooseMinimum(Request current, Selection selection) {
        return LifestyleMinPolicy.choose(applyPendingGuard(current, selection));
    }
}
