package org.xar.ck3.markets.core;

import java.util.List;

public record SubmissionResult(OrderView order, List<Trade> trades) {
    public SubmissionResult {
        trades = List.copyOf(trades);
    }
}
