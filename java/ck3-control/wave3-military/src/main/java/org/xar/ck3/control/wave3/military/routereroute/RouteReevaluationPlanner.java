package org.xar.ck3.control.wave3.military.routereroute;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.Lookup;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.Preview;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.PreviewStatus;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.Query;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.RejectionStage;

/** Ordinary planner's ranked preview stage, strategy.py:12451-12762.
 * A usable preview returns to the real geometric/native-contact audit stage. It is never a Move proposal.
 */
public final class RouteReevaluationPlanner {
    private RouteReevaluationPlanner() { }

    public enum CandidateSource {
        WAR_OBJECTIVE_PROVINCE, ENEMY_SIEGE_RELIEF, PLAYER_HELD_COUNTY_CAPITAL,
        SAME_REALM_VASSAL_CAPITAL, STATIONARY_PLAYER_HELD_CAPITAL, STATIONARY_SAME_REALM_VASSAL_CAPITAL
    }
    public record Objective(int targetProvinceId, CandidateSource source, boolean blocked) {
        public Objective { province(targetProvinceId); Objects.requireNonNull(source, "candidate source"); }
        public boolean refuge() {
            return source == CandidateSource.PLAYER_HELD_COUNTY_CAPITAL || source == CandidateSource.SAME_REALM_VASSAL_CAPITAL;
        }
    }
    public record Context(boolean stationaryThreatened, boolean refugeLifecycleActive,
                          boolean activeRouteUnsafe, boolean exactSiegeRejected) {
        public boolean needsStationaryContact() { return stationaryThreatened || refugeLifecycleActive; }
    }
    public enum RejectionReason {
        CURRENT_EXACT_SIEGE_REJECTED, CANNOT_REPLACE_UNSAFE_ACTIVE_ROUTE, BLOCKED,
        MOVE_MODE_UNAVAILABLE, DEFERRED_WHILE_STATIONARY_PROVINCE_THREATENED,
        DEFERRED_WHILE_ACTIVE_ROUTE_UNSAFE, DEFERRED_WHILE_EXACT_SIEGE_REJECTED
    }
    public record Rejection(int targetProvinceId, RejectionReason reason) {
        public Rejection { province(targetProvinceId); Objects.requireNonNull(reason, "rejection reason"); }
    }
    public sealed interface Result permits PreviewQuery, ReadinessRequired, ExistingDateBoundary,
            AuditContinuation, StationaryContinuation, Arrived, Exhausted, Unavailable {
        List<Rejection> rejections();
        default boolean actionAuthorized() { return false; }
    }
    public record PreviewQuery(int armyId, int originProvinceId, int targetProvinceId, String requiredStep,
                               boolean stepAvailable, List<Rejection> rejections) implements Result {
        public PreviewQuery {
            army(armyId); province(originProvinceId); province(targetProvinceId);
            StrictJson.require(previewStep(armyId, targetProvinceId).equals(requiredStep), "canonical preview step required");
            rejections = List.copyOf(rejections);
        }
    }
    public record ReadinessRequired(int targetProvinceId, Preview preview,
                                    List<Rejection> rejections) implements Result {
        public ReadinessRequired { binding(targetProvinceId, preview); deferred(preview); rejections = List.copyOf(rejections); }
    }
    /** The existing ordinary planner owns the date transition, including its submission and unknown-result rules. */
    public record ExistingDateBoundary(int targetProvinceId, Optional<String> existingCandidateStep,
                                       Preview preview, List<Rejection> rejections) implements Result {
        public ExistingDateBoundary {
            binding(targetProvinceId, preview); deferred(preview); existingCandidateStep = Objects.requireNonNull(existingCandidateStep);
            existingCandidateStep.ifPresent(step -> StrictJson.require(step.equals("life-advance-one-day") || step.equals("life-advance"), "existing date step required"));
            rejections = List.copyOf(rejections);
        }
    }
    public record AuditContinuation(int targetProvinceId, int objectiveRank, CandidateSource source,
                                     Preview preview, List<Rejection> rejections) implements Result {
        public AuditContinuation {
            binding(targetProvinceId, preview); Objects.requireNonNull(source);
            StrictJson.require(objectiveRank >= 0 && preview.status() == PreviewStatus.AVAILABLE, "available ranked preview required");
            rejections = List.copyOf(rejections);
        }
    }
    /** This boundary precedes blocked-destination filtering in the original caller. */
    public record StationaryContinuation(int targetProvinceId, int objectiveRank,
                                          List<Rejection> rejections) implements Result {
        public StationaryContinuation { province(targetProvinceId); rank(objectiveRank); rejections = List.copyOf(rejections); }
    }
    public record Arrived(int targetProvinceId, int objectiveRank, List<Rejection> rejections) implements Result {
        public Arrived { province(targetProvinceId); rank(objectiveRank); rejections = List.copyOf(rejections); }
    }
    /** Exhaustion resumes the original all-alternatives-rejected/rally logic, rather than concluding no legal action. */
    public record Exhausted(List<Rejection> rejections) implements Result {
        public Exhausted { rejections = List.copyOf(rejections); }
    }
    public enum MissingInput { CURRENT_DATE, SAME_FRAME_LEASE }
    public record Unavailable(MissingInput missing, List<Rejection> rejections) implements Result {
        public Unavailable { Objects.requireNonNull(missing); rejections = List.copyOf(rejections); }
    }

    /** Actual candidate producer at strategy.py:12249-12261. Ranking itself is upstream and unchanged. */
    public static List<Objective> exactSiegeObjectives(List<Integer> rankedExactProvinceIds,
            Set<Integer> siegeObjectiveProvinceIds, Optional<Integer> readyReliefTargetProvinceId,
            Set<Integer> blockedProvinceIds) {
        List<Integer> ranked = List.copyOf(rankedExactProvinceIds); ranked.forEach(RouteReevaluationPlanner::province);
        Set<Integer> siege = Set.copyOf(siegeObjectiveProvinceIds); siege.forEach(RouteReevaluationPlanner::province);
        Set<Integer> blocked = Set.copyOf(blockedProvinceIds); blocked.forEach(RouteReevaluationPlanner::province);
        Objects.requireNonNull(readyReliefTargetProvinceId); readyReliefTargetProvinceId.ifPresent(RouteReevaluationPlanner::province);
        if (readyReliefTargetProvinceId.isPresent()) {
            int target = readyReliefTargetProvinceId.orElseThrow();
            return List.of(new Objective(target, CandidateSource.ENEMY_SIEGE_RELIEF, blocked.contains(target)));
        }
        return ranked.stream().filter(siege::contains)
                .map(target -> new Objective(target, CandidateSource.WAR_OBJECTIVE_PROVINCE, blocked.contains(target))).toList();
    }

    public static Result plan(Lookup lookup, Context context, List<Objective> orderedObjectives, List<String> availableSteps) {
        Objects.requireNonNull(lookup); Objects.requireNonNull(context);
        List<Objective> objectives = List.copyOf(orderedObjectives); List<String> steps = List.copyOf(availableSteps);
        steps.forEach(StrictJson::text); Query query = lookup.query();
        if (query.dateRaw().isEmpty()) { return new Unavailable(MissingInput.CURRENT_DATE, List.of()); }
        if (query.expectedLease().isEmpty()) { return new Unavailable(MissingInput.SAME_FRAME_LEASE, List.of()); }
        List<Rejection> rejected = new ArrayList<>();
        for (int rank = 0; rank < objectives.size(); rank++) {
            Objective goal = objectives.get(rank); int target = goal.targetProvinceId();
            if (target == query.originProvinceId()) {
                if (context.exactSiegeRejected()) { rejected.add(new Rejection(target, RejectionReason.CURRENT_EXACT_SIEGE_REJECTED)); continue; }
                if (context.activeRouteUnsafe()) { rejected.add(new Rejection(target, RejectionReason.CANNOT_REPLACE_UNSAFE_ACTIVE_ROUTE)); continue; }
                if (context.needsStationaryContact()) { return new StationaryContinuation(target, rank, rejected); }
                return new Arrived(target, rank, rejected);
            }
            if (goal.blocked()) { rejected.add(new Rejection(target, RejectionReason.BLOCKED)); continue; }
            Optional<Preview> found = RouteReroutePolicy.freshPreview(new Lookup(lookup.history(),
                    new Query(query.armyId(), query.originProvinceId(), target, query.dateRaw(), query.expectedLease())));
            if (found.isEmpty()) {
                String step = previewStep(query.armyId(), target);
                return new PreviewQuery(query.armyId(), query.originProvinceId(), target, step, steps.contains(step), rejected);
            }
            Preview preview = found.orElseThrow();
            if (preview.status() == PreviewStatus.DEFERRED) {
                if (preview.rejectionStage() == RejectionStage.MOVE_MODE_UNAVAILABLE) {
                    rejected.add(new Rejection(target, RejectionReason.MOVE_MODE_UNAVAILABLE)); continue;
                }
                if (context.needsStationaryContact()) {
                    rejected.add(new Rejection(target, RejectionReason.DEFERRED_WHILE_STATIONARY_PROVINCE_THREATENED));
                    if (goal.refuge()) { continue; }
                    return new ReadinessRequired(target, preview, rejected);
                }
                if (context.activeRouteUnsafe() || context.exactSiegeRejected()) {
                    rejected.add(new Rejection(target, context.activeRouteUnsafe()
                            ? RejectionReason.DEFERRED_WHILE_ACTIVE_ROUTE_UNSAFE : RejectionReason.DEFERRED_WHILE_EXACT_SIEGE_REJECTED));
                    continue;
                }
                Optional<String> step = steps.contains("life-advance-one-day") ? Optional.of("life-advance-one-day")
                        : steps.contains("life-advance") ? Optional.of("life-advance") : Optional.empty();
                return new ExistingDateBoundary(target, step, preview, rejected);
            }
            // Do not silently skip an unaudited route or mark a boolean as native contact permission.
            return new AuditContinuation(target, rank, goal.source(), preview, rejected);
        }
        return new Exhausted(rejected);
    }
    public static String previewStep(int armyId, int targetProvinceId) {
        army(armyId); province(targetProvinceId); return "preview-move-army-" + armyId + "-to-" + targetProvinceId;
    }
    private static void binding(int target, Preview preview) { province(target); Objects.requireNonNull(preview); StrictJson.require(preview.targetProvinceId() == target, "preview target differs"); }
    private static void deferred(Preview preview) { StrictJson.require(preview.status() == PreviewStatus.DEFERRED, "deferred preview required"); }
    private static void rank(int value) { StrictJson.require(value >= 0, "nonnegative objective rank required"); }
    private static void province(int value) { StrictJson.require(value > 0, "positive Province required"); }
    private static void army(int value) { StrictJson.require(value >= 0, "public CUnit required"); }
}
