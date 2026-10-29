package org.xar.ck3.control.application.action;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** A read's data result and, only after the actual UNKNOWN, its privately minted original custody. */
public record PlanningReadAttempt<T>(PlanningReadResult<T> result,
        Optional<PlanningReadCoordinator.OriginalRead<T>> original) {
    public PlanningReadAttempt {
        Objects.requireNonNull(result); original = Objects.requireNonNull(original);
        if (original.isPresent()) {
            if (!(result instanceof PlanningReadResult.Unavailable<T> unavailable))
                throw new IllegalArgumentException("only an unavailable original read retains a late-read ticket");
            StrictJson.require(unavailable.original().filter(original.orElseThrow().original()::equals).isPresent(),
                    "ticket must retain the exact actual unavailable UNKNOWN");
        }
    }
}
