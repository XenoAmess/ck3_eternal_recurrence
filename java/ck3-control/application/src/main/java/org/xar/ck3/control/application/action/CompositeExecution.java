package org.xar.ck3.control.application.action;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Durable child identities and exact bodies; never an opaque runner state or replay instruction. */
public record CompositeExecution(String handlerId, Instant startedAt, GuardEvidence guard, List<Child> children) {
    public CompositeExecution {
        StrictJson.text(handlerId); Objects.requireNonNull(startedAt); Objects.requireNonNull(guard); children = List.copyOf(children);
        StrictJson.require(children.size() <= 1024, "bounded composite child list");
        StrictJson.require(children.stream().map(Child::actionId).distinct().count() == children.size(), "unique child action identities required");
    }
    public record Child(String actionId, String bodySha256) {
        public Child { StrictJson.text(actionId); StrictJson.require(bodySha256 != null && bodySha256.matches("[0-9a-f]{64}"), "complete child body SHA required"); }
    }
}
