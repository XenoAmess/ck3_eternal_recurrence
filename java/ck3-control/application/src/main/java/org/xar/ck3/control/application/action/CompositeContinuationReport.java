package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Canonical attempts created by this continuation call; it does not infer physical writes from an ACK. */
public record CompositeContinuationReport(ActionReceipt parent, List<ActionReceipt> children, Disposition disposition) {
    public enum Disposition { NEW_CHILD_ATTEMPT, NO_NEW_CHILD_ATTEMPT }
    public CompositeContinuationReport {
        Objects.requireNonNull(parent); children = List.copyOf(children); Objects.requireNonNull(disposition);
        StrictJson.require(children.stream().map(value -> value.command().actionId()).distinct().count() == children.size(), "duplicate continuation child");
        StrictJson.require((disposition == Disposition.NEW_CHILD_ATTEMPT) == !children.isEmpty(), "continuation report must expose its actual new canonical attempts");
    }
}
