package org.xar.ck3.control.application.routecontact;

import java.math.BigInteger;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy;

/** Detached semantic inputs. Construction follows strict JSON validation; none grants submission authority. */
public final class RouteContactModel {
    private RouteContactModel() { }
    public static int unit(int id) { StrictJson.require(id >= 0, "public CUnit ID required"); return id; }
    public static int province(int id) { StrictJson.require(id > 0, "positive Province ID required"); return id; }
    /** Observed public snapshot ownership; this record grants no character-specific native action eligibility. */
    public record Owner(String machineId, GameGeneration game, String sessionId, BigInteger connectionGeneration,
            long bridgePid, String episodeRunId, int episodeCharacterId, int localPlayerId) {
        public Owner {
            StrictJson.text(machineId); Objects.requireNonNull(game); StrictJson.text(sessionId); StrictJson.text(episodeRunId);
            Objects.requireNonNull(connectionGeneration); StrictJson.require(connectionGeneration.signum() > 0 && connectionGeneration.compareTo(StrictJson.UINT64_MAX) <= 0, "positive uint64 connection generation required");
            NativeCharacterId.of(episodeCharacterId);
            StrictJson.require(bridgePid > 0 && bridgePid <= 4_294_967_295L && bridgePid == game.pid() && localPlayerId >= 0, "native owner identity required");
        }
    }
    public record Army(int armyId, boolean controllable, int currentProvinceId, Optional<Integer> targetProvinceId,
            List<Integer> remainingRoute, Optional<String> state, Optional<Integer> stateCode,
            boolean inCombat, boolean retreating) {
        public Army {
            unit(armyId); province(currentProvinceId); targetProvinceId = Objects.requireNonNull(targetProvinceId);
            targetProvinceId.ifPresent(RouteContactModel::province); remainingRoute = List.copyOf(remainingRoute);
            remainingRoute.forEach(RouteContactModel::province); state = Objects.requireNonNull(state); stateCode = Objects.requireNonNull(stateCode);
        }
        public boolean knownStationary() {
            return !inCombat && !retreating && (state.map(value -> Set.of("regular", "sieging").contains(value.toLowerCase(java.util.Locale.ROOT)))
                    .orElseGet(() -> stateCode.map(value -> value == 1 || value == 3).orElse(false)));
        }
        public boolean knownActive() {
            return state.map(value -> Set.of("regular", "sieging", "moving", "embarked").contains(value.toLowerCase(java.util.Locale.ROOT)))
                    .orElseGet(() -> stateCode.map(value -> Set.of(1, 3, 4, 7).contains(value)).orElse(false));
        }
    }
    public record Frame(Owner owner, String snapshotId, BigInteger revision, BigInteger nativeRevision, int dateRaw,
            boolean mapReady, boolean paused, int speed, boolean oneLifeTerminal, boolean playedCharacterAlive,
            OpportunityJson.Value activeEvent, OpportunityJson.Value pendingInteraction, OpportunityJson.Value modal,
            List<Integer> activeWarIds, List<Army> ownArmies, List<Army> hostileArmies) {
        public Frame {
            Objects.requireNonNull(owner); StrictJson.text(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(nativeRevision);
            StrictJson.require(revision.signum() >= 0 && nativeRevision.signum() > 0 && speed >= 1 && speed <= 5, "valid native frame required");
            Objects.requireNonNull(activeEvent); Objects.requireNonNull(pendingInteraction); Objects.requireNonNull(modal);
            activeWarIds = sortedPositive(activeWarIds); ownArmies = List.copyOf(ownArmies); hostileArmies = List.copyOf(hostileArmies);
            uniqueArmies(ownArmies); uniqueArmies(hostileArmies);
        }
        public Optional<Army> own(int id) { return ownArmies.stream().filter(army -> army.armyId() == id).findFirst(); }
        public Optional<Army> hostile(int id) { return hostileArmies.stream().filter(army -> army.armyId() == id).findFirst(); }
        public List<Integer> hostileIds() { return hostileArmies.stream().filter(army -> !army.retreating()).map(Army::armyId).distinct().sorted().toList(); }
        public List<Integer> controlledIds() { return ownArmies.stream().filter(Army::controllable).map(Army::armyId).sorted().toList(); }
        public boolean playerDecision() { return activeEvent != OpportunityJson.Nil.INSTANCE || pendingInteraction != OpportunityJson.Nil.INSTANCE || modal != OpportunityJson.Nil.INSTANCE; }
    }
    public record RouteQuery(String step, boolean ok, Owner owner, String snapshotId, BigInteger revision,
            BigInteger nativeRevision, int dateRaw, int subjectArmyId, int targetProvinceId, List<Integer> hostileArmyIds,
            RouteWindowPolicy.Route subjectRoute, List<RouteWindowPolicy.Route> hostileRoutes,
            int subjectEffectiveOriginProvinceId, List<Integer> hostileEffectiveOriginProvinceIds, List<RouteWindowPolicy.Conflict> nativeConflicts) {
        public RouteQuery {
            StrictJson.text(step); Objects.requireNonNull(owner); StrictJson.text(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(nativeRevision);
            unit(subjectArmyId); province(targetProvinceId); hostileArmyIds = canonicalUnits(hostileArmyIds, 1, 64);
            StrictJson.require(!hostileArmyIds.contains(subjectArmyId), "subject cannot be hostile"); Objects.requireNonNull(subjectRoute);
            hostileRoutes = List.copyOf(hostileRoutes);
            province(subjectEffectiveOriginProvinceId); nativeConflicts = List.copyOf(nativeConflicts);
            hostileEffectiveOriginProvinceIds = List.copyOf(hostileEffectiveOriginProvinceIds); hostileEffectiveOriginProvinceIds.forEach(RouteContactModel::province);
            StrictJson.require(hostileEffectiveOriginProvinceIds.size() == hostileRoutes.size(), "complete hostile native effective origins required");
            StrictJson.require(subjectRoute.armyId() == subjectArmyId && hostileRoutes.stream().map(RouteWindowPolicy.Route::armyId).toList().equals(hostileArmyIds), "complete ordered native timelines required");
            new RouteWindowPolicy.Horizon(dateRaw, 1, subjectRoute, hostileRoutes);
            for (RouteWindowPolicy.Conflict conflict : nativeConflicts) StrictJson.require(hostileArmyIds.contains(conflict.hostileArmyId())
                    && conflict.overlapStartDateRaw() >= dateRaw && conflict.overlapEndDateRaw() <= Math.addExact(dateRaw, 24), "native conflict scope/date differs");
        }
        public RouteWindowPolicy.Available project(int days) { return RouteWindowPolicy.project(new RouteWindowPolicy.Horizon(dateRaw, days, subjectRoute, hostileRoutes)); }
        public boolean oneDayContactFree() { return nativeConflicts.isEmpty(); }
    }
    public enum ProofKind { CONTACT_FREE, UNAVOIDABLE_CURRENT_PROVINCE_CONTACT, BOUNDED_FROZEN_ROUTE_WINDOW }
    public enum TransitionKind { EPISODE_TERMINAL, ACTIVE_WAR_SET_CHANGED, SUBJECT_ARMY_REMOVED, ACTIVE_COMBAT_OBSERVED,
        RETREAT_OBSERVED, HOSTILE_ENTERED_CONTACT_PROVINCE, HOSTILE_INTENT_CHANGED, PREDICTED_CONTACT_BOUNDARY_REACHED;
        public String wire() { return name().toLowerCase(java.util.Locale.ROOT); }
    }
    public record Transition(TransitionKind kind, boolean contactObserved, String episodeRunId, int subjectArmyId,
            int contactProvinceId, int startingDateRaw, int endingDateRaw, List<Integer> changedHostileIds) {
        public Transition {
            Objects.requireNonNull(kind); StrictJson.text(episodeRunId); unit(subjectArmyId); province(contactProvinceId);
            changedHostileIds = canonicalUnits(changedHostileIds, 0, 64);
            StrictJson.require(!contactObserved || kind == TransitionKind.ACTIVE_COMBAT_OBSERVED, "only actual combat can claim observed contact");
        }
    }
    public sealed interface TimelineEntry permits AdvanceHistory, TimelineBarrier { }
    /** Actual latest life advance exists but is not a usable route-contact marker. No invented subject/episode/date. */
    public record TimelineBarrier(String originalStep, String reason) implements TimelineEntry {
        public TimelineBarrier { StrictJson.text(originalStep); StrictJson.text(reason); }
    }
    public record AdvanceHistory(boolean ok, int subjectArmyId, String episodeRunId, int endingDateRaw,
            Optional<Transition> transition, boolean strictFollowupUnresolved) implements TimelineEntry {
        public AdvanceHistory { unit(subjectArmyId); StrictJson.text(episodeRunId); transition = Objects.requireNonNull(transition);
            for (Transition value : transition.stream().toList()) StrictJson.require(value.subjectArmyId() == subjectArmyId
                    && value.episodeRunId().equals(episodeRunId) && value.endingDateRaw() == endingDateRaw, "timeline marker source/result identity differs"); }
    }
    public record Proof(ProofKind kind, RouteQuery query, boolean strictFollowup, Optional<Transition> priorBoundary,
            int horizonDays, List<Integer> watchArmyIds, Map<Integer, RouteWindowPolicy.Available> controlledWindows) {
        public Proof {
            Objects.requireNonNull(kind); Objects.requireNonNull(query); priorBoundary = Objects.requireNonNull(priorBoundary);
            RouteWindowPolicy.days(horizonDays); watchArmyIds = canonicalUnits(watchArmyIds, 0, 64); controlledWindows = Map.copyOf(controlledWindows);
            StrictJson.require(!strictFollowup || priorBoundary.isPresent(), "strict followup needs retained adjacent boundary");
            StrictJson.require(kind == ProofKind.BOUNDED_FROZEN_ROUTE_WINDOW ? horizonDays >= 2 : horizonDays == 1, "proof horizon differs");
        }
        public int targetDateRaw() { return Math.addExact(query.dateRaw(), Math.multiplyExact(horizonDays, 24)); }
        public int subjectId() { return query.subjectArmyId(); }
        public int targetProvinceId() { return query.targetProvinceId(); }
        public List<Integer> hostileIds() { return query.hostileArmyIds(); }
    }
    public static List<Integer> canonicalUnits(List<Integer> values, int minimum, int maximum) {
        List<Integer> result = List.copyOf(values); result.forEach(RouteContactModel::unit);
        StrictJson.require(result.size() >= minimum && result.size() <= maximum && result.equals(result.stream().distinct().sorted().toList()), "canonical sorted unique public IDs required"); return result;
    }
    private static List<Integer> sortedPositive(List<Integer> values) {
        List<Integer> result = List.copyOf(values); result.forEach(RouteContactModel::province);
        StrictJson.require(result.size() == result.stream().distinct().count(), "duplicate War ID"); return result.stream().sorted().toList();
    }
    private static void uniqueArmies(List<Army> armies) { StrictJson.require(armies.size() == armies.stream().map(Army::armyId).distinct().count(), "duplicate Army ID"); }
}
