package org.xar.ck3.control.application.routecontact;

import static org.xar.ck3.control.application.routecontact.RouteContactModel.*;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.routewindow.RouteWindowPolicy;

/** NativeDriver 33974/34044: latest query per exact scope, then the complete controlled-army conjunction. */
public final class RouteContactProofs {
    private RouteContactProofs() { }
    public record Scope(int subjectId, int targetId, List<Integer> hostiles) {
        public Scope { unit(subjectId); province(targetId); hostiles = canonicalUnits(hostiles, 1, 64); }
    }
    public record QueryEntry(Scope scope, Optional<RouteQuery> valid) {
        public QueryEntry { java.util.Objects.requireNonNull(scope); valid = java.util.Objects.requireNonNull(valid);
            valid.ifPresent(query -> StrictJson.require(scope.equals(new Scope(query.subjectArmyId(), query.targetProvinceId(), query.hostileArmyIds())), "history scope differs")); }
    }
    /** Queries are the surviving writer branch after its latest restore, oldest first. Failed latest rows shadow older rows. */
    public static Map<Scope, Proof> oneDay(Frame frame, List<RouteQuery> survivingQueries, List<? extends TimelineEntry> survivingAdvances) {
        return oneDayEntries(frame, survivingQueries.stream().map(query -> new QueryEntry(new Scope(query.subjectArmyId(), query.targetProvinceId(), query.hostileArmyIds()), Optional.of(query))).toList(), survivingAdvances);
    }
    public static Map<Scope, Proof> oneDayEntries(Frame frame, List<QueryEntry> survivingQueries, List<? extends TimelineEntry> survivingAdvances) {
        if (!frame.paused() || frame.hostileIds().isEmpty() || frame.hostileIds().size() > 64) return Map.of();
        Map<Scope, QueryEntry> latest = new LinkedHashMap<>();
        for (QueryEntry query : survivingQueries) latest.put(query.scope(), query);
        Map<Scope, Proof> candidates = new LinkedHashMap<>(); Map<Integer, Proof> bySubject = new LinkedHashMap<>();
        for (Map.Entry<Scope, QueryEntry> item : latest.entrySet()) {
            if (item.getValue().valid().isEmpty()) continue;
            RouteQuery query = item.getValue().valid().orElseThrow(); Optional<Army> selected = frame.own(query.subjectArmyId());
            if (!sameFrame(frame, query) || selected.isEmpty()) continue;
            Army army = selected.orElseThrow(); List<Integer> timed = remaining(query.subjectRoute());
            boolean active = army.targetProvinceId().equals(Optional.of(query.targetProvinceId())) && !army.remainingRoute().isEmpty()
                    && army.remainingRoute().getLast() == query.targetProvinceId();
            boolean stationary = army.currentProvinceId() == query.targetProvinceId() && army.targetProvinceId().isEmpty()
                    && army.remainingRoute().isEmpty() && army.knownStationary();
            ProofKind kind = query.oneDayContactFree() ? ProofKind.CONTACT_FREE : unavoidable(query)
                    ? ProofKind.UNAVOIDABLE_CURRENT_PROVINCE_CONTACT : null;
            if (!army.controllable() || !(active || stationary) || !timed.equals(army.remainingRoute())
                    || query.subjectRoute().currentProvinceId() != army.currentProvinceId() || kind == null) continue;
            Proof proof = new Proof(kind, query, false, Optional.empty(), 1, List.of(), Map.of());
            candidates.put(item.getKey(), proof); bySubject.put(query.subjectArmyId(), proof);
        }
        Map<Scope, Proof> results = new LinkedHashMap<>();
        for (Map.Entry<Scope, Proof> item : candidates.entrySet()) {
            Proof proof = item.getValue(); if (!isolated(frame, proof, bySubject)) continue;
            if (proof.kind() == ProofKind.UNAVOIDABLE_CURRENT_PROVINCE_CONTACT) {
                Proof original = proof;
                Optional<AdvanceHistory> last = !survivingAdvances.isEmpty() && survivingAdvances.getLast() instanceof AdvanceHistory route
                        ? Optional.of(route) : Optional.empty();
                if (last.filter(row -> !row.ok() && row.strictFollowupUnresolved()
                        && row.subjectArmyId() == original.subjectId() && row.episodeRunId().equals(frame.owner().episodeRunId())
                        && row.endingDateRaw() == frame.dateRaw()).isPresent()) continue;
                Optional<Transition> prior = last.filter(row -> row.ok() && row.subjectArmyId() == original.subjectId()
                        && row.endingDateRaw() == frame.dateRaw()).flatMap(AdvanceHistory::transition)
                        .filter(value -> value.kind() == TransitionKind.PREDICTED_CONTACT_BOUNDARY_REACHED && !value.contactObserved()
                                && value.subjectArmyId() == original.subjectId() && value.episodeRunId().equals(frame.owner().episodeRunId())
                                && value.contactProvinceId() == original.query().subjectRoute().currentProvinceId()
                                && value.endingDateRaw() == frame.dateRaw());
                if (prior.isPresent()) proof = new Proof(proof.kind(), proof.query(), true, prior, 1, List.of(), Map.of());
            }
            results.put(item.getKey(), proof);
        }
        return Map.copyOf(results);
    }
    public static Optional<Proof> window(Frame frame, Map<Scope, Proof> days, Scope scope, int requestedDays,
            boolean explicitCampaignDeadline) {
        StrictJson.require(requestedDays == 2 || requestedDays == 3, "two/three day typed window required");
        Proof selected = days.get(scope); List<Integer> own = frame.controlledIds();
        if (selected == null || selected.kind() != ProofKind.CONTACT_FREE || own.isEmpty() || own.size() > 64
                || frame.own(scope.subjectId()).orElseThrow().remainingRoute().isEmpty()) return Optional.empty();
        Map<Integer, Proof> bySubject = new LinkedHashMap<>();
        days.values().stream().filter(proof -> proof.kind() == ProofKind.CONTACT_FREE).forEach(proof -> bySubject.put(proof.subjectId(), proof));
        Map<Integer, RouteWindowPolicy.Available> windows = new LinkedHashMap<>(); RouteQuery reference = selected.query();
        for (int id : own) {
            Army army = frame.own(id).orElseThrow(); Proof sibling = bySubject.get(id); RouteWindowPolicy.Route route;
            if (sibling != null) {
                if (!sameHostiles(reference, sibling.query())) return Optional.empty(); route = sibling.query().subjectRoute();
            } else if (army.knownStationary() && army.remainingRoute().isEmpty()) {
                route = new RouteWindowPolicy.Route(id, army.currentProvinceId(), List.of(), List.of());
            } else return Optional.empty();
            windows.put(id, RouteWindowPolicy.project(new RouteWindowPolicy.Horizon(frame.dateRaw(), 3, route, reference.hostileRoutes())));
        }
        int supported = windows.values().stream().mapToInt(RouteWindowPolicy.Available::contactFreeWholeDays).min().orElse(0);
        // NativeDriver only permits a shorter prefix when campaign cadence explicitly caps that frozen window.
        if (supported < 2 || requestedDays != supported && !(explicitCampaignDeadline && requestedDays < supported)) return Optional.empty();
        Set<Integer> watch = new java.util.TreeSet<>(own); watch.addAll(scope.hostiles()); if (watch.size() > 64) return Optional.empty();
        return Optional.of(new Proof(ProofKind.BOUNDED_FROZEN_ROUTE_WINDOW, reference, false, Optional.empty(), requestedDays,
                List.copyOf(watch), windows));
    }
    public static boolean sameFrame(Frame frame, RouteQuery query) {
        return query.ok() && query.owner().equals(frame.owner()) && query.snapshotId().equals(frame.snapshotId())
                && query.revision().equals(frame.revision()) && query.nativeRevision().equals(frame.nativeRevision())
                && query.dateRaw() == frame.dateRaw() && query.hostileArmyIds().equals(frame.hostileIds());
    }
    private static boolean unavoidable(RouteQuery query) {
        int current = query.subjectRoute().currentProvinceId();
        boolean cannotClear = query.subjectRoute().provinceIds().isEmpty() && query.targetProvinceId() == current && query.subjectEffectiveOriginProvinceId() == current
                || !query.subjectRoute().arrivalDateRaws().isEmpty() && query.subjectRoute().arrivalDateRaws().getFirst() > Math.addExact(query.dateRaw(), 24);
        return cannotClear && !query.nativeConflicts().isEmpty() && query.nativeConflicts().stream()
                .allMatch(value -> value instanceof RouteWindowPolicy.SameProvince same && same.provinceId() == current);
    }
    private static boolean isolated(Frame frame, Proof selected, Map<Integer, Proof> bySubject) {
        for (Army army : frame.ownArmies()) {
            if (!army.controllable() || army.armyId() == selected.subjectId()) continue;
            if (army.inCombat() || army.retreating()) return false;
            if (!army.remainingRoute().isEmpty() && army.targetProvinceId().isPresent()) {
                if (army.remainingRoute().getLast().equals(army.targetProvinceId().orElseThrow()) && geometricallySafe(army, selected.query())) continue;
                Proof sibling = bySubject.get(army.armyId());
                if (sibling != null && sibling.kind() == ProofKind.CONTACT_FREE
                        && sibling.targetProvinceId() == army.targetProvinceId().orElseThrow() && sameHostiles(selected.query(), sibling.query())) continue;
                return false;
            }
            if (army.targetProvinceId().isPresent() || !army.remainingRoute().isEmpty() || !army.knownStationary()
                    || !stationarySafe(army.currentProvinceId(), selected.query())) return false;
        }
        return true;
    }
    private static boolean sameHostiles(RouteQuery left, RouteQuery right) {
        return left.dateRaw() == right.dateRaw() && left.nativeRevision().equals(right.nativeRevision())
                && left.hostileArmyIds().equals(right.hostileArmyIds()) && left.hostileRoutes().equals(right.hostileRoutes())
                && left.hostileEffectiveOriginProvinceIds().equals(right.hostileEffectiveOriginProvinceIds());
    }
    private static boolean stationarySafe(int province, RouteQuery query) {
        return RouteWindowPolicy.project(new RouteWindowPolicy.Horizon(query.dateRaw(), 1,
                new RouteWindowPolicy.Route(query.subjectArmyId(), province, List.of(), List.of()), query.hostileRoutes())).contactFree();
    }
    private static boolean geometricallySafe(Army army, RouteQuery query) {
        if (!army.knownActive() || !stationarySafe(army.currentProvinceId(), query)) return false;
        Set<Integer> route = new LinkedHashSet<>(army.remainingRoute());
        for (RouteWindowPolicy.Route hostile : query.hostileRoutes()) {
            if (route.contains(hostile.currentProvinceId()) || remaining(hostile).stream().anyMatch(route::contains)) return false;
        }
        // This is the original conservative disjoint-route test, never an observed contact result.
        return true;
    }
    public static List<Integer> remaining(RouteWindowPolicy.Route route) {
        List<Integer> result = new ArrayList<>(route.provinceIds());
        if (!result.isEmpty() && result.getFirst() == route.currentProvinceId()) result.removeFirst(); return List.copyOf(result);
    }
}
