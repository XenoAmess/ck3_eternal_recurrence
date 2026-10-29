package org.xar.ck3.control.wave2.planning.reinforcementcount;

import org.xar.ck3.control.contracts.StrictJson;

import java.math.BigInteger;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

/** Existing current-soldier counting and stationary staging predicates, without strength forecasts. */
public final class ReinforcementCounts {
    private ReinforcementCounts() { }
    public enum CacheStatus { AVAILABLE, PARTIAL, OTHER }
    public enum Truth { TRUE, FALSE, UNKNOWN }
    public record Army(Optional<BigInteger> armyId, Optional<BigInteger> soldiers) {
        public Army { Objects.requireNonNull(armyId, "armyId"); Objects.requireNonNull(soldiers, "soldiers"); }
    }
    public record Strength(Optional<BigInteger> armyId, String scopeRole, List<BigInteger> warIds,
                           boolean available, Optional<BigInteger> currentSoldiers) {
        public Strength {
            Objects.requireNonNull(armyId, "armyId");
            Objects.requireNonNull(scopeRole, "scopeRole");
            warIds = List.copyOf(warIds);
            Objects.requireNonNull(currentSoldiers, "currentSoldiers");
        }
    }
    public record CountInput(List<Army> rows, String snapshotId, BigInteger revision,
                             CacheStatus cacheStatus, Optional<String> queriedSnapshotId,
                             Optional<BigInteger> queriedRevision, List<Strength> strengths,
                             String role, Optional<BigInteger> warId) {
        public CountInput {
            rows = List.copyOf(rows);
            StrictJson.text(snapshotId);
            Objects.requireNonNull(revision, "revision");
            Objects.requireNonNull(cacheStatus, "cacheStatus");
            Objects.requireNonNull(queriedSnapshotId, "queriedSnapshotId");
            Objects.requireNonNull(queriedRevision, "queriedRevision");
            strengths = List.copyOf(strengths);
            StrictJson.text(role);
            Objects.requireNonNull(warId, "warId");
        }
        boolean currentCache() {
            return cacheStatus != CacheStatus.OTHER && queriedSnapshotId.filter(snapshotId::equals).isPresent()
                    && queriedRevision.filter(revision::equals).isPresent();
        }
    }
    public record StagingInput(Truth controllable, Optional<BigInteger> currentProvinceId,
                               Truth moveTargetObservable, Optional<BigInteger> moveTargetProvinceId,
                               boolean completeEmptyRoute, Optional<BigInteger> routeSourceCount,
                               boolean regularState, Optional<List<BigInteger>> routeProvinceIds,
                               Truth inCombat, Truth retreating, BigInteger targetProvinceId) {
        public StagingInput {
            Objects.requireNonNull(controllable, "controllable");
            Objects.requireNonNull(currentProvinceId, "currentProvinceId");
            Objects.requireNonNull(moveTargetObservable, "moveTargetObservable");
            Objects.requireNonNull(moveTargetProvinceId, "moveTargetProvinceId");
            Objects.requireNonNull(routeSourceCount, "routeSourceCount");
            Objects.requireNonNull(routeProvinceIds, "routeProvinceIds");
            routeProvinceIds = routeProvinceIds.map(List::copyOf);
            Objects.requireNonNull(inCombat, "inCombat");
            Objects.requireNonNull(retreating, "retreating");
            Objects.requireNonNull(targetProvinceId, "targetProvinceId");
        }
    }

    public static Optional<BigInteger> count(CountInput input) {
        Map<BigInteger, BigInteger> counts = new HashMap<>();
        for (Army army : input.rows()) {
            if (army.armyId().isEmpty()) { return Optional.empty(); }
            BigInteger identity = army.armyId().orElseThrow();
            Optional<BigInteger> number = army.soldiers();
            if (input.currentCache()) {
                List<Strength> matched = input.strengths().stream()
                        .filter(strength -> strength.armyId().filter(identity::equals).isPresent()
                                && strength.scopeRole().equals(input.role())
                                && (input.warId().isEmpty() || strength.warIds().contains(input.warId().orElseThrow()))).toList();
                if (matched.size() == 1 && matched.getFirst().available()) { number = matched.getFirst().currentSoldiers(); }
            }
            if (number.isEmpty() || number.orElseThrow().signum() < 0) { return Optional.empty(); }
            BigInteger value = number.orElseThrow();
            BigInteger previous = counts.putIfAbsent(identity, value);
            if (previous != null && !previous.equals(value)) { return Optional.empty(); }
        }
        return Optional.of(counts.values().stream().reduce(BigInteger.ZERO, BigInteger::add));
    }

    public static boolean stationaryStaging(StagingInput input) {
        boolean emptyRoute = input.routeProvinceIds().filter(List::isEmpty).isPresent();
        boolean stationaryRoute = input.moveTargetObservable() == Truth.TRUE && input.moveTargetProvinceId().isEmpty()
                || input.completeEmptyRoute() && input.routeSourceCount().filter(BigInteger.ZERO::equals).isPresent() && input.regularState()
                || input.regularState() && input.moveTargetProvinceId().isEmpty() && emptyRoute;
        return input.controllable() == Truth.TRUE && input.currentProvinceId().filter(input.targetProvinceId()::equals).isPresent()
                && stationaryRoute && input.inCombat() == Truth.FALSE && input.retreating() == Truth.FALSE && emptyRoute;
    }
}
