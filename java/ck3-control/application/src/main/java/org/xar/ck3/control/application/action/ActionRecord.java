package org.xar.ck3.control.application.action;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;

/** Immutable ledger-linked action fact; only the canonical writer head publishes it as authoritative. */
public record ActionRecord(ActionReceipt receipt, Optional<ExactRef> previous) {
    public ActionRecord { Objects.requireNonNull(receipt); previous = Objects.requireNonNull(previous); }
}
