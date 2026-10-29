package org.xar.ck3.control.application.planning;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * Online model decision provider interface for the ordinary planner.
 * It selects between an existing proposal and waiting; it never creates commands.
 */
@FunctionalInterface
public interface OrdinaryDecisionSelector {

    enum Choice {
        ACCEPT,
        WAIT
    }

    record Selection(Choice choice, String reason, Optional<ExactRef> evidence) {
        public Selection {
            Objects.requireNonNull(choice);
            StrictJson.text(reason);
            Objects.requireNonNull(evidence);
        }
    }

    Selection select(PlanningRequest request, PlanningResult.ActionSelected proposal);
}
