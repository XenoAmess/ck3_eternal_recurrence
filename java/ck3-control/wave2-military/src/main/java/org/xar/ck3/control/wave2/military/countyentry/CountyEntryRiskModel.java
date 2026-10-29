package org.xar.ck3.control.wave2.military.countyentry;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Declared projections of existing SDK extension containers, not replacement SDK DTOs. */
public final class CountyEntryRiskModel {
    private CountyEntryRiskModel() { }
    public record Strength(boolean available, int armyId, Integer nativeCarmyId, Integer currentSoldiers,
                           CountyEntryInputs countyInputs, LossPartition lossPartition) {
        public Strength {
            StrictJson.require(armyId >= 0, "public CUnit ID must be nonnegative signed32");
            StrictJson.require(!available || currentSoldiers != null && currentSoldiers >= 0, "available whole strength required");
            StrictJson.require(available || countyInputs == null, "unavailable strength cannot publish county inputs");
            if (countyInputs != null && countyInputs.budget() instanceof CountyEntryInputs.AvailableBudget budget) {
                StrictJson.require(currentSoldiers != null && budget.wholeSoldiers() == currentSoldiers,
                        "county budget must match same-frame whole strength");
            }
        }
    }
    public record LossPartition(boolean available, Integer wholeSoldiers, Integer preferredSoldiers) { }
    public record RouteContext(int armyId, Integer currentProvinceId, String routeReadStatus,
                               Integer routeSourceCount, List<Integer> routeProvinceIds) {
        public RouteContext { if (routeProvinceIds != null) routeProvinceIds = List.copyOf(routeProvinceIds); }
    }
    public record MovementPrefix(boolean ready, Long armyId, Long nativeCarmyId, Long conditionalUnit170) {
        public MovementPrefix {
            StrictJson.require(armyId == null || armyId >= 0 && armyId <= 0xffff_ffffL, "prefix public subject unsigned32 required");
            StrictJson.require(nativeCarmyId == null || nativeCarmyId >= 0 && nativeCarmyId <= 0xffff_ffffL, "prefix CArmy subject unsigned32 required");
        }
    }
    public record MovementOperands(Long currentProvinceType, Integer unitKind, Long targetProvinceType,
                                   Integer targetDefinitionByte, Integer currentDefinitionByte) { }
    public record PrestoreCall(Boolean selected, String unavailableReason) { }
    public record Provenance(String snapshotId, Long revision, Long nativeRevision) {
        public boolean complete() { return snapshotId != null && revision != null && nativeRevision != null; }
    }
    public record QueryFrame(Provenance provenance, List<RouteContext> playerArmies) {
        public QueryFrame { Objects.requireNonNull(provenance); playerArmies = List.copyOf(playerArmies); }
    }
    public record Input(Strength strength, RouteContext context, MovementPrefix prefix,
                        MovementOperands movement, PrestoreCall prestore) {
        public Input { Objects.requireNonNull(strength); Objects.requireNonNull(movement); Objects.requireNonNull(prestore); }
    }
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public sealed interface Value permits BooleanValue, IntegerValue { }
    public record BooleanValue(boolean value) implements Value { }
    public record IntegerValue(long value) implements Value { }
    public record Predicate(String name, Value value, Boolean passes, String source) { }
    public record Requirement(String field, String reason, String neededFor) { }
    public record ZeroPredicate(Boolean passes, String basis) { }
    public record MultiplierExplanation(Boolean baseFloorDemanded, Boolean secondFloorDemanded, Long ordinaryProperty) { }
    public record Allocation(boolean ready, Integer preferred, Integer primary, Integer residual,
                             Boolean primarySelected, Boolean residualSelected) { }
    public enum Review {
        NO_CURRENT_FIRST_EDGE_TO_ASSESS, REVIEW_CURRENT_EDGE_BEFORE_ADVANCING,
        NO_POSITIVE_COUNTY_BUDGET_ON_THIS_LOCAL_BRANCH, OBTAIN_MISSING_CURRENT_OBSERVATIONS
    }
    public record Decision(Review review, String reason, boolean showEdgeChoices, boolean emptyRoute) { }
    public record Risk(Status status, Strength strength, boolean budgetReady, boolean floorReady,
                       boolean freshContext, boolean contextReady, Boolean firstEdgePresent,
                       boolean observedEmptyRoute, String emptyRouteEvidence, Integer currentProvinceId,
                       Integer targetProvinceId, Boolean admission, Boolean positiveSelected,
                       Boolean edgeAdmission, Boolean edgePositive, boolean noArrivalDoesNotProveZero,
                       Long priorUnit170, List<Predicate> predicates, ZeroPredicate zeroPredicate,
                       MultiplierExplanation multiplier, Allocation allocation, Decision decision,
                       List<Requirement> requirements) {
        public Risk { predicates = List.copyOf(predicates); requirements = List.copyOf(requirements); }
    }
}
