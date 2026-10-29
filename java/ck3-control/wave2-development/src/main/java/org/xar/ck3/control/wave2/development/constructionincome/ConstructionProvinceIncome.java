package org.xar.ck3.control.wave2.development.constructionincome;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.Evidence;

/** Aggregate province observation and the original completed-cold-receipt retention predicate. */
public final class ConstructionProvinceIncome {
    private ConstructionProvinceIncome() { }
    public record Target(BigInteger baronyTitleId, BigInteger provinceId) { }
    public record Frame(String snapshotId, BigInteger nativeRevision, BigInteger dateRaw) { }
    public record ProvinceRow(Target target, Evidence monthlyIncomeObserved, BigInteger monthlyIncomeRaw) {
        public ProvinceRow {
            Objects.requireNonNull(target);
            Objects.requireNonNull(monthlyIncomeObserved);
        }
    }
    public enum Status {
        OBSERVED("observed"), UNAVAILABLE("unavailable");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Observation(Status status, Target target, Frame frame, BigInteger monthlyIncomeRaw) {
        public Observation {
            Objects.requireNonNull(status);
            Objects.requireNonNull(target);
            Objects.requireNonNull(frame);
            if ((status == Status.OBSERVED) != (monthlyIncomeRaw != null)) {
                throw new IllegalArgumentException("current observed province income needs an exact scalar");
            }
        }
    }
    public record PriorObservation(String status, BigInteger dateRaw) { }
    public record PriorReceipt(String completionStatus, BigInteger completionObservedDateRaw,
                               PriorObservation provinceObservation) { }

    public static Observation observe(List<ProvinceRow> activeConstructions, Target target, Frame sourceFrame) {
        Objects.requireNonNull(activeConstructions);
        Objects.requireNonNull(target);
        Objects.requireNonNull(sourceFrame);
        ProvinceRow unique = null;
        int count = 0;
        for (ProvinceRow row : activeConstructions) {
            Objects.requireNonNull(row);
            if (row.target().equals(target)) { unique = row; count++; }
        }
        boolean observed = count == 1 && unique != null && unique.monthlyIncomeObserved() == Evidence.TRUE
                && unique.monthlyIncomeRaw() != null;
        return new Observation(observed ? Status.OBSERVED : Status.UNAVAILABLE, target, sourceFrame,
                observed ? unique.monthlyIncomeRaw() : null);
    }

    /** Only chooses which existing observation to expose; it grants no fresh native/material proof. */
    public static boolean retainPrior(Status current, PriorReceipt prior, boolean coldRecheck, boolean completed) {
        Objects.requireNonNull(current);
        Objects.requireNonNull(prior);
        PriorObservation previous = prior.provinceObservation();
        return coldRecheck && completed && current != Status.OBSERVED
                && "completed".equals(prior.completionStatus()) && previous != null
                && "observed".equals(previous.status()) && previous.dateRaw() != null
                && prior.completionObservedDateRaw() != null
                && previous.dateRaw().compareTo(prior.completionObservedDateRaw()) >= 0;
    }
}
