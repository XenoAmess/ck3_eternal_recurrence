package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Fixed composition-root registry. Neither HTTP callers nor planners can supply execution implementations. */
public final class CompositeRegistry {
    private final List<CompositeActionPort> handlers;
    public CompositeRegistry(List<CompositeActionPort> handlers) {
        this.handlers = List.copyOf(handlers);
        StrictJson.require(handlers.stream().map(CompositeActionPort::handlerId).distinct().count() == handlers.size(), "unique composite handler identities required");
    }
    public Optional<CompositeActionPort> find(OperationKey operation) {
        List<CompositeActionPort> matching = handlers.stream().filter(handler -> handler.supports(operation)).toList();
        StrictJson.require(matching.size() <= 1, "ambiguous composite operation registration"); return matching.stream().findFirst();
    }
    public CompositeActionPort require(String handlerId) {
        return handlers.stream().filter(handler -> handler.handlerId().equals(handlerId)).findFirst().orElseThrow(() -> new IllegalStateException("retained composite handler is unavailable; no replay"));
    }
}
