package org.xar.ck3.control.wave3.military.routereroute;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovement;
import org.xar.ck3.control.wave2.military.disembark.EvidenceJson;

/** Source-bound pure route planning. Native preview/validation and the action writer stay authoritative. */
public final class RouteReroutePolicy {
    private RouteReroutePolicy() { }
    public record Lease(String snapshotId, long revision, long nativeRevision,
                        long connectionGeneration, String episodeRunId) {
        public Lease {
            StrictJson.text(snapshotId); StrictJson.text(episodeRunId);
            StrictJson.safe(revision, 0); StrictJson.safe(nativeRevision, 0);
            StrictJson.safe(connectionGeneration, 0);
        }
    }
    public enum PreviewStatus { AVAILABLE, DEFERRED }
    public enum RejectionStage { NONE, MOVE_MODE_UNAVAILABLE, OTHER }
    public record Query(int armyId, int originProvinceId, int targetProvinceId,
                        Optional<Integer> dateRaw, Optional<Lease> expectedLease) {
        public Query {
            publicArmy(armyId); province(originProvinceId); province(targetProvinceId);
            dateRaw = Objects.requireNonNull(dateRaw); expectedLease = Objects.requireNonNull(expectedLease);
        }
    }
    public record Preview(PreviewStatus status, int armyId, int originProvinceId, int targetProvinceId,
                          int previewedDateRaw, List<Integer> routeProvinceIds,
                          RejectionStage rejectionStage, EvidenceJson.ObjectValue originalDocument) {
        public Preview {
            Objects.requireNonNull(status); Objects.requireNonNull(rejectionStage); Objects.requireNonNull(originalDocument);
            publicArmy(armyId); province(originProvinceId); province(targetProvinceId);
            routeProvinceIds = List.copyOf(routeProvinceIds); routeProvinceIds.forEach(RouteReroutePolicy::province);
            if (status == PreviewStatus.DEFERRED) { routeProvinceIds = List.of(); }
        }
    }
    public sealed interface HistoryEntry permits Restore, Merge, ReturnedPreview, Ignored { }
    public record Restore(boolean successful) implements HistoryEntry { }
    public record Merge(boolean successful, int destinationArmyId, int sourceArmyId) implements HistoryEntry {
        public Merge { publicArmy(destinationArmyId); publicArmy(sourceArmyId); }
    }
    public record ReturnedPreview(boolean successful, int requestedArmyId, int requestedTargetProvinceId,
                                  Optional<Lease> lease, Optional<Preview> preview) implements HistoryEntry {
        public ReturnedPreview {
            publicArmy(requestedArmyId); province(requestedTargetProvinceId);
            lease = Objects.requireNonNull(lease); preview = Objects.requireNonNull(preview);
        }
    }
    public record Ignored() implements HistoryEntry { }
    public record Lookup(List<HistoryEntry> history, Query query) {
        public Lookup { history = List.copyOf(history); Objects.requireNonNull(query); }
    }
    /** The exact production lookup's restore, merge, lease and first-valid-result semantics. */
    public static Optional<Preview> freshPreview(Lookup lookup) {
        Query query = lookup.query();
        if (query.dateRaw().isEmpty()) { return Optional.empty(); }
        for (int i = lookup.history().size() - 1; i >= 0; i--) {
            HistoryEntry entry = lookup.history().get(i);
            if (entry instanceof Restore restore && restore.successful()) { return Optional.empty(); }
            if (entry instanceof Merge merge && merge.successful()
                    && (merge.destinationArmyId() == query.armyId() || merge.sourceArmyId() == query.armyId())) {
                return Optional.empty();
            }
            if (!(entry instanceof ReturnedPreview returned) || !returned.successful()
                    || returned.requestedArmyId() != query.armyId()
                    || returned.requestedTargetProvinceId() != query.targetProvinceId()
                    || query.expectedLease().isPresent() && !query.expectedLease().equals(returned.lease())
                    || returned.preview().isEmpty()) { continue; }
            Preview preview = returned.preview().orElseThrow();
            if (preview.armyId() == query.armyId() && preview.originProvinceId() == query.originProvinceId()
                    && preview.targetProvinceId() == query.targetProvinceId()
                    && preview.previewedDateRaw() == query.dateRaw().orElseThrow()) { return Optional.of(preview); }
        }
        return Optional.empty();
    }

    /** A cache is usable only for the complete observed planning input; no wall-clock TTL grants freshness. */
    public record CacheScope(String machineId, String executableSha256, Lease lease, int dateRaw,
                             int armyId, int currentProvinceId, List<Integer> committedRoute,
                             Optional<CurrentMovement> movement, String hostileScopeSha256,
                             String nativeLegalitySha256, String goalOrderingSha256, String historySha256) {
        public CacheScope {
            StrictJson.text(machineId); digest(executableSha256); Objects.requireNonNull(lease);
            publicArmy(armyId); province(currentProvinceId);
            committedRoute = List.copyOf(committedRoute); committedRoute.forEach(RouteReroutePolicy::province);
            movement = Objects.requireNonNull(movement); digest(hostileScopeSha256);
            digest(nativeLegalitySha256); digest(goalOrderingSha256); digest(historySha256);
        }
    }
    public record CachedPreview(CacheScope scope, int targetProvinceId, Optional<Preview> preview) {
        public CachedPreview {
            Objects.requireNonNull(scope); province(targetProvinceId); preview = Objects.requireNonNull(preview);
            if (preview.isPresent()) {
                Preview value = preview.orElseThrow();
                if (value.armyId() != scope.armyId() || value.originProvinceId() != scope.currentProvinceId()
                        || value.targetProvinceId() != targetProvinceId || value.previewedDateRaw() != scope.dateRaw()) {
                    throw new IllegalArgumentException("cached preview differs from its observed subject/date/target");
                }
            }
        }
    }
    public record Cache(List<CachedPreview> entries) {
        public Cache {
            entries = List.copyOf(entries); Set<CacheKey> seen = new HashSet<>();
            for (CachedPreview row : entries) {
                if (!seen.add(new CacheKey(row.scope(), row.targetProvinceId()))) { throw new IllegalArgumentException("duplicate cached preview identity"); }
            }
        }
        public Optional<CachedPreview> find(CacheScope scope, int target) {
            return entries.stream().filter(row -> row.scope().equals(scope) && row.targetProvinceId() == target).findFirst();
        }
    }
    private record CacheKey(CacheScope scope, int targetProvinceId) { }
    public record Goal(int targetProvinceId, boolean blocked, boolean qualifiedContact) {
        public Goal { province(targetProvinceId); }
    }
    public sealed interface Plan permits PreviewRequired, CandidateReady, NoCandidate, ReadinessRequired { }
    public record PreviewRequired(int armyId, int targetProvinceId, String existingNativeStep, Cache cache) implements Plan {
        public PreviewRequired { publicArmy(armyId); province(targetProvinceId); StrictJson.text(existingNativeStep); Objects.requireNonNull(cache); }
    }
    public record CandidateReady(int targetProvinceId, Preview preview, int objectiveRank, Cache cache) implements Plan {
        public CandidateReady { province(targetProvinceId); Objects.requireNonNull(preview); Objects.requireNonNull(cache);
            if (objectiveRank < 0 || preview.targetProvinceId() != targetProvinceId) { throw new IllegalArgumentException("ranked target binding required"); } }
    }
    public record NoCandidate(Cache cache) implements Plan { public NoCandidate { Objects.requireNonNull(cache); } }
    public record ReadinessRequired(int targetProvinceId, Cache cache) implements Plan {
        public ReadinessRequired { province(targetProvinceId); Objects.requireNonNull(cache); }
    }
    /** Actual consumer for freshPreview. Goal order is caller-owned; rejected destinations fall through without a top-N cap. */
    public static Plan selectRanked(List<HistoryEntry> history, CacheScope scope, List<Goal> orderedGoals, Cache cache) {
        List<CachedPreview> updated = new ArrayList<>();
        // Invalidate every old scope, including known negative results, on an observed-input change.
        for (CachedPreview row : cache.entries()) { if (row.scope().equals(scope)) { updated.add(row); } }
        for (int rank = 0; rank < orderedGoals.size(); rank++) {
            Goal goal = orderedGoals.get(rank);
            if (goal.blocked()) { continue; }
            Optional<CachedPreview> cached = new Cache(updated).find(scope, goal.targetProvinceId());
            Optional<Preview> preview;
            if (cached.isPresent()) { preview = cached.orElseThrow().preview(); }
            else {
                preview = freshPreview(new Lookup(history, new Query(scope.armyId(), scope.currentProvinceId(),
                        goal.targetProvinceId(), Optional.of(scope.dateRaw()), Optional.of(scope.lease()))));
                updated.add(new CachedPreview(scope, goal.targetProvinceId(), preview));
            }
            Cache next = new Cache(updated);
            if (preview.isEmpty()) {
                return new PreviewRequired(scope.armyId(), goal.targetProvinceId(),
                        "preview-move-army-" + scope.armyId() + "-to-" + goal.targetProvinceId(), next);
            }
            Preview value = preview.orElseThrow();
            if (value.status() == PreviewStatus.DEFERRED) {
                if (value.rejectionStage() == RejectionStage.MOVE_MODE_UNAVAILABLE) { continue; }
                return new ReadinessRequired(goal.targetProvinceId(), next);
            }
            if (!value.routeProvinceIds().isEmpty()
                    && value.routeProvinceIds().getLast() == goal.targetProvinceId() && goal.qualifiedContact()) {
                return new CandidateReady(goal.targetProvinceId(), value, rank, next);
            }
        }
        return new NoCandidate(new Cache(updated));
    }

    public enum LockStatus { CURRENT_PROVINCE, FIRST_EDGE_RETAINED, UNAVAILABLE }
    public record HaltExpectation(LockStatus status, Optional<Integer> destination,
                                  List<Integer> expectedRoute, boolean requiresNativeValidator,
                                  boolean actualStopVerified) {
        public HaltExpectation {
            Objects.requireNonNull(status); destination = Objects.requireNonNull(destination);
            expectedRoute = List.copyOf(expectedRoute); expectedRoute.forEach(RouteReroutePolicy::province);
            destination.ifPresent(RouteReroutePolicy::province);
            if (actualStopVerified || !requiresNativeValidator) { throw new IllegalArgumentException("prediction cannot grant native admission or postcondition credit"); }
        }
    }
    /** Preview of the documented native strict comparison, never native Halt eligibility or an observed stop. */
    public static HaltExpectation haltExpectation(int currentProvinceId, List<Integer> completeRoute,
                                                 Optional<CurrentMovement> movement) {
        province(currentProvinceId); completeRoute.forEach(RouteReroutePolicy::province);
        if (movement.isEmpty() || movement.orElseThrow().normalizedProgress() == null
                || movement.orElseThrow().loadedLockCutoff().value() == null) {
            return new HaltExpectation(LockStatus.UNAVAILABLE, Optional.empty(), List.of(), true, false);
        }
        CurrentMovement value = movement.orElseThrow();
        if (value.normalizedProgress().raw() > value.loadedLockCutoff().value().raw()) {
            if (completeRoute.isEmpty()) { return new HaltExpectation(LockStatus.UNAVAILABLE, Optional.empty(), List.of(), true, false); }
            return new HaltExpectation(LockStatus.FIRST_EDGE_RETAINED, Optional.of(completeRoute.getFirst()),
                    List.of(completeRoute.getFirst()), true, false);
        }
        return new HaltExpectation(LockStatus.CURRENT_PROVINCE, Optional.of(currentProvinceId), List.of(), true, false);
    }
    public enum SubmissionState { NEVER_SUBMITTED, REJECTED, UNKNOWN, ACKNOWLEDGED, POSTCONDITION_OBSERVED }
    public static boolean maySubmitHalt(SubmissionState state, boolean advertised, boolean nativeValidatorAccepted) {
        return state == SubmissionState.NEVER_SUBMITTED && advertised && nativeValidatorAccepted;
    }

    public record StockRules(int waterMinimumDays, int waterSavingsDays, int holyWaterMinimumDays,
                             int holyWaterSavingsDays, int pathFactor, CurrentMovement.FixedPoint waterFactor,
                             int goalsForFinalPathfinding, CurrentMovement.FixedPoint badAdjacencyExtraCost,
                             int supportIgnoreSupplyRerouteSteps, String sourceSha256) {
        public StockRules {
            if (waterMinimumDays < 0 || waterSavingsDays < 0 || holyWaterMinimumDays < 0 || holyWaterSavingsDays < 0
                    || pathFactor < 1 || goalsForFinalPathfinding < 1 || supportIgnoreSupplyRerouteSteps < 0
                    || waterFactor.raw() <= 0 || badAdjacencyExtraCost.raw() < 0) { throw new IllegalArgumentException("positive source rules required"); }
            digest(sourceSha256);
        }
    }
    public record Costs(CurrentMovement.FixedPoint landDays, CurrentMovement.FixedPoint waterDays,
                         CurrentMovement.FixedPoint fastestLandPathCost, CurrentMovement.FixedPoint waterPathCost,
                         CurrentMovement.FixedPoint straightPathCost, boolean sameLandBody,
                         boolean greatHolyWar) {
        public Costs {
            if (landDays.raw() < 0 || waterDays.raw() < 0 || fastestLandPathCost.raw() < 0
                    || waterPathCost.raw() < 0 || straightPathCost.raw() < 0) { throw new IllegalArgumentException("nonnegative observed costs required"); }
        }
    }
    public record CostCandidates(boolean considerWaterPreview, boolean withinWaterFactor,
                                  boolean withinMaximumPathFactor, boolean combatProbabilityKnown) { }
    /** Source-defined candidate hints. Cost units must be explicitly supplied; this grants no Move/Halt permission. */
    public static CostCandidates costCandidates(StockRules rules, Costs costs) {
        BigInteger scale = BigInteger.valueOf(CurrentMovement.FixedPoint.SCALE);
        BigInteger land = BigInteger.valueOf(costs.landDays().raw());
        BigInteger water = BigInteger.valueOf(costs.waterDays().raw());
        int min = costs.greatHolyWar() ? rules.holyWaterMinimumDays() : rules.waterMinimumDays();
        int saving = costs.greatHolyWar() ? rules.holyWaterSavingsDays() : rules.waterSavingsDays();
        boolean consider = land.compareTo(BigInteger.valueOf(min).multiply(scale)) >= 0
                && land.subtract(water).compareTo(BigInteger.valueOf(saving).multiply(scale)) >= 0;
        boolean factor = !costs.sameLandBody() || BigInteger.valueOf(costs.waterPathCost().raw()).multiply(scale).compareTo(
                BigInteger.valueOf(costs.fastestLandPathCost().raw()).multiply(BigInteger.valueOf(rules.waterFactor().raw()))) <= 0;
        boolean maxPath = BigInteger.valueOf(costs.fastestLandPathCost().raw()).compareTo(BigInteger.valueOf(costs.straightPathCost().raw())
                .multiply(BigInteger.valueOf(rules.pathFactor()))) <= 0;
        return new CostCandidates(consider, factor, maxPath, false);
    }
    public static boolean allowSupplyRerouteCandidate(StockRules rules, int remainingSteps, boolean supportingPlayer) {
        if (remainingSteps < 0) { throw new IllegalArgumentException("nonnegative remaining steps required"); }
        return !supportingPlayer || remainingSteps > rules.supportIgnoreSupplyRerouteSteps();
    }
    private static void publicArmy(int value) { if (value < 0) { throw new IllegalArgumentException("public CUnit ID required"); } }
    private static void province(int value) { if (value <= 0) { throw new IllegalArgumentException("positive province ID required"); } }
    private static void digest(String value) { if (value == null || !value.matches("[0-9a-f]{64}")) { throw new IllegalArgumentException("source-bound SHA-256 required"); } }
}
