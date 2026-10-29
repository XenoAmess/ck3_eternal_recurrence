package org.xar.ck3.control.wave2.development.constructionincome;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.development.constructionincome.SameFrameConstructionIncome.Frame;
import org.xar.ck3.control.wave2.development.constructionincome.SameFrameConstructionIncome.HistoryRow;
import org.xar.ck3.control.wave2.development.constructionincome.SameFrameConstructionIncome.Observation;

/** Immutable samples for the original submit and receipt consumers, captured before the material query. */
public final class ConstructionIncomeConsumers {
    private ConstructionIncomeConsumers() { }

    public record StartingSample(Frame frame, Observation observation) {
        public StartingSample {
            Objects.requireNonNull(frame);
            Objects.requireNonNull(observation);
        }
    }
    public record PriorObservedDate(boolean present, BigInteger value) {
        public PriorObservedDate {
            if (!present && value != null) { throw new IllegalArgumentException("missing date has no value"); }
        }
        public BigInteger orPostDate(BigInteger postDate) { return present ? value : postDate; }
    }
    public record PriorReceipt(String completionStatus, BigInteger observedIncomeRaw,
                               PriorObservedDate incomeObservedDate, BigInteger postDateRaw) {
        public PriorReceipt { Objects.requireNonNull(incomeObservedDate); }
    }
    public record ReceiptIncome(BigInteger observedIncomeRaw, BigInteger incomeObservedDateRaw) { }

    /** The existing driver lock/view remains owned by the caller. This method never queries a driver. */
    public static StartingSample sampleStarting(Frame startingFrame, List<HistoryRow> currentHistory) {
        return new StartingSample(startingFrame, SameFrameConstructionIncome.observe(startingFrame, currentHistory));
    }

    public static BigInteger preSubmitIncome(StartingSample sample) {
        return Objects.requireNonNull(sample).observation().incomeRaw();
    }

    /** Exact scalar/date carry from query_construction_receipt; no delta, budget or material verification. */
    public static ReceiptIncome receiptIncome(StartingSample starting, PriorReceipt prior,
                                               boolean coldRecheck, boolean completed) {
        Objects.requireNonNull(starting);
        Objects.requireNonNull(prior);
        BigInteger observed = starting.observation().incomeRaw();
        BigInteger date = observed != null ? starting.frame().dateRaw() : null;
        if (coldRecheck && completed && observed == null && "completed".equals(prior.completionStatus())) {
            observed = prior.observedIncomeRaw();
            if (observed != null) { date = prior.incomeObservedDate().orPostDate(prior.postDateRaw()); }
        }
        return new ReceiptIncome(observed, date);
    }
}
