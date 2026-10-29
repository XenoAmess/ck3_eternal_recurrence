package org.xar.ck3.control.wave2.planning.mercenarypurchaseneed;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Current-headcount query pruning only; it makes no overall war-safety claim. */
public final class MercenaryPurchaseNeed {
    private MercenaryPurchaseNeed() { }

    public enum Truth { TRUE, FALSE, UNKNOWN }
    public record War(List<String> protectCashReasons, Optional<BigInteger> playerRelativeWarScore,
                      Optional<BigInteger> observedPlayerRaisedSoldiers,
                      Optional<BigInteger> observedEnemyRaisedSoldiers, Truth raisedForceDeficit) {
        public War {
            protectCashReasons = List.copyOf(protectCashReasons);
            Objects.requireNonNull(playerRelativeWarScore, "playerRelativeWarScore");
            Objects.requireNonNull(observedPlayerRaisedSoldiers, "observedPlayerRaisedSoldiers");
            Objects.requireNonNull(observedEnemyRaisedSoldiers, "observedEnemyRaisedSoldiers");
            observedPlayerRaisedSoldiers.ifPresent(MercenaryPurchaseNeed::nonnegative);
            observedEnemyRaisedSoldiers.ifPresent(MercenaryPurchaseNeed::nonnegative);
            Objects.requireNonNull(raisedForceDeficit, "raisedForceDeficit");
        }
        boolean recoverableProtectedWar() {
            return !protectCashReasons.isEmpty() && playerRelativeWarScore
                    .filter(score -> score.compareTo(BigInteger.valueOf(-100)) > 0).isPresent();
        }
    }
    public record HostileUnion(List<BigInteger> warIds, Truth sharedForceDeficit) {
        public HostileUnion {
            warIds = List.copyOf(warIds);
            Objects.requireNonNull(sharedForceDeficit, "sharedForceDeficit");
        }
    }
    public record Input(List<War> wars, HostileUnion hostileUnion) {
        public Input {
            wars = List.copyOf(wars);
            Objects.requireNonNull(hostileUnion, "hostileUnion");
        }
    }
    public enum Reason {
        CURRENT_DEFICIT_OR_UNKNOWN("current_deficit_or_unknown_scope"),
        NO_RECOVERABLE_CURRENT_DEFICIT("no_recoverable_current_headcount_deficit");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Need(boolean queryCanChangeCurrentHeadcountFlipModel, Reason reason) {
        public Need {
            Objects.requireNonNull(reason, "reason");
            if (queryCanChangeCurrentHeadcountFlipModel != (reason == Reason.CURRENT_DEFICIT_OR_UNKNOWN)) {
                throw new IllegalArgumentException("query model reason differs from decision");
            }
        }
    }
    public enum PendingHire { ABSENT, PENDING, UNKNOWN }
    public sealed interface Route permits ExistingReceiptRoute, ModelRoute { }
    public record ExistingReceiptRoute(PendingHire pending) implements Route {
        public ExistingReceiptRoute {
            if (pending == null || pending == PendingHire.ABSENT) { throw new IllegalArgumentException("pending receipt identity required"); }
        }
    }
    public record ModelRoute(Need need) implements Route {
        public ModelRoute { Objects.requireNonNull(need, "need"); }
    }

    public static Need observe(Input input) {
        List<War> wars = input.wars().stream().filter(War::recoverableProtectedWar).toList();
        boolean unknown = wars.stream().anyMatch(war -> war.observedPlayerRaisedSoldiers().isEmpty()
                || war.observedEnemyRaisedSoldiers().isEmpty());
        boolean deficit = wars.stream().anyMatch(war -> war.raisedForceDeficit() == Truth.TRUE);
        boolean shared = input.hostileUnion().warIds().size() > 1
                && input.hostileUnion().sharedForceDeficit() != Truth.FALSE;
        boolean useful = !wars.isEmpty() && (unknown || deficit || shared);
        return new Need(useful, useful ? Reason.CURRENT_DEFICIT_OR_UNKNOWN : Reason.NO_RECOVERABLE_CURRENT_DEFICIT);
    }

    /** Corresponds to the real consumer's pending-before-model branch; never replays a hire. */
    public static Route route(Input input, PendingHire pending) {
        Objects.requireNonNull(pending, "pending");
        return pending == PendingHire.ABSENT ? new ModelRoute(observe(input)) : new ExistingReceiptRoute(pending);
    }
    private static void nonnegative(BigInteger value) {
        if (value.signum() < 0) { throw new IllegalArgumentException("observed soldiers must be nonnegative"); }
    }
}
