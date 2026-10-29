package org.xar.ck3.control.wave2.finance.holyloan;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Copied decision predicates and costs. This model has no submission or wallet authority. */
public final class HolyLoanModel {
    public static final BigInteger UINT64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    private HolyLoanModel() { }

    public record ExpectedFrame(int playedCharacterId, int dateRaw, BigInteger captureEpoch) {
        public ExpectedFrame {
            Objects.requireNonNull(captureEpoch, "captureEpoch");
            if (playedCharacterId < 1 || dateRaw < 0 || captureEpoch.signum() < 1
                    || captureEpoch.compareTo(UINT64_MAX) > 0) {
                throw new IllegalArgumentException("bounded owner actor/date/capture epoch required");
            }
        }
    }

    public enum Definition {
        BORROW("borrow_from_holy_order_decision"), REPAY("repay_loan_decision");
        private final String wire;
        Definition(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public sealed interface Decision permits ObservedDecision, UnknownDecision {
        Definition definition();
    }
    public record ObservedDecision(Definition definition, boolean shown, boolean canTake,
            boolean affordable, List<Long> declaredCostsRaw) implements Decision {
        public ObservedDecision {
            Objects.requireNonNull(definition, "definition");
            declaredCostsRaw = List.copyOf(declaredCostsRaw);
            if (declaredCostsRaw.size() != 10) { throw new IllegalArgumentException("ten signed native slots required"); }
        }
        public boolean nativeGatesAllowDecision() { return shown && canTake && affordable; }
    }
    public record UnknownDecision(Definition definition) implements Decision {
        public UnknownDecision { Objects.requireNonNull(definition, "definition"); }
    }
    public sealed interface Availability permits Available, Unavailable { }
    public record Available() implements Availability { }
    public record Unavailable(String reason) implements Availability {
        public Unavailable {
            if (reason == null || reason.isEmpty()) { throw new IllegalArgumentException("unavailable reason required"); }
        }
    }
    public record Observation(ExpectedFrame source, Availability availability, Decision borrowDecision,
            Decision repayDecision) {
        public Observation {
            Objects.requireNonNull(source, "source"); Objects.requireNonNull(availability, "availability");
            Objects.requireNonNull(borrowDecision, "borrowDecision"); Objects.requireNonNull(repayDecision, "repayDecision");
            if (borrowDecision.definition() != Definition.BORROW || repayDecision.definition() != Definition.REPAY
                    || (availability instanceof Available) != (borrowDecision instanceof ObservedDecision)
                    || (availability instanceof Available) != (repayDecision instanceof ObservedDecision)) {
                throw new IllegalArgumentException("decision availability/identity mismatch");
            }
        }
    }
}
