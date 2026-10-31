package org.xar.ck3.control.application.action;

import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Immutable DATA binding current canonical original parent action/body and complete original execution (handler/start/guard/empty child vector). */
public record CompositeNoGameplayWriteObservation(String actionId, String bodySha256, CompositeExecution execution) {
    public CompositeNoGameplayWriteObservation {
        StrictJson.text(actionId);
        StrictJson.require(bodySha256 != null && bodySha256.matches("[0-9a-f]{64}"), "complete original parent body SHA required");
        Objects.requireNonNull(execution);
        StrictJson.require(execution.children().isEmpty(), "no-gameplay-write observation requires no reserved child");
    }

    public void validate(ActionCommand parent, CompositeExecution retained) {
        Objects.requireNonNull(parent); Objects.requireNonNull(retained);
        StrictJson.require(actionId.equals(parent.actionId()), "observation action ID differs from parent");
        StrictJson.require(bodySha256.equals(ActionCodec.bodySha256(parent)), "observation body SHA differs from parent");
        StrictJson.require(execution.equals(retained), "observation execution differs from retained");
        StrictJson.require(execution.children().isEmpty(), "observation execution must have empty child vector");
        GuardEvidence guard = retained.guard();
        StrictJson.require(parent.origin() instanceof CommandOrigin.Gameplay && parent.origin().acceptsGuard(guard.origin())
                && guard.observed().equals(parent.before()) && guard.source().equals(parent.source())
                && guard.sessionId().equals(parent.sessionId()) && guard.operation().equals(parent.operation()),
                "no-gameplay-write observation crossed its original gameplay command guard");
    }
}
