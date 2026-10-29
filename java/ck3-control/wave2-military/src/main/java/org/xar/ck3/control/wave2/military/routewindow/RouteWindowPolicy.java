package org.xar.ck3.control.wave2.military.routewindow;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Closed-interval projection while current native route timelines remain frozen. */
public final class RouteWindowPolicy {
    public static final int RAW_UNITS_PER_DAY = 24;
    private RouteWindowPolicy() { }

    public record Route(int armyId, int currentProvinceId, List<Integer> provinceIds, List<Integer> arrivalDateRaws) {
        public Route {
            StrictJson.require(armyId >= 0 && currentProvinceId > 0, "native route identities required");
            provinceIds = List.copyOf(provinceIds); arrivalDateRaws = List.copyOf(arrivalDateRaws);
            StrictJson.require(provinceIds.size() == arrivalDateRaws.size(), "route and arrival arrays differ");
            for (Integer province : provinceIds) { StrictJson.require(province > 0, "positive Province required"); }
            for (int index = 1; index < arrivalDateRaws.size(); index++) {
                StrictJson.require(arrivalDateRaws.get(index - 1) <= arrivalDateRaws.get(index), "arrival dates decrease");
            }
        }
    }

    public record Horizon(int startDateRaw, int horizonDays, Route subject, List<Route> hostiles) {
        public Horizon {
            days(horizonDays); Objects.requireNonNull(subject, "subject route"); hostiles = List.copyOf(hostiles);
            StrictJson.require(!hostiles.isEmpty(), "complete hostile route set required");
            StrictJson.require((long) startDateRaw + (long) horizonDays * RAW_UNITS_PER_DAY <= Integer.MAX_VALUE,
                    "route window clock overflow");
            for (Route route : concat(subject, hostiles)) {
                for (Integer arrival : route.arrivalDateRaws()) {
                    StrictJson.require(arrival >= startDateRaw, "arrival precedes current date");
                }
            }
        }
        public int endDateRaw() { return Math.toIntExact((long) startDateRaw + (long) horizonDays * RAW_UNITS_PER_DAY); }
    }

    public sealed interface Conflict permits SameProvince, OpposingEdge {
        int hostileArmyId(); int overlapStartDateRaw(); int overlapEndDateRaw();
    }
    public record SameProvince(int hostileArmyId, int provinceId, int overlapStartDateRaw,
                               int overlapEndDateRaw) implements Conflict {
        public SameProvince {
            StrictJson.require(hostileArmyId >= 0 && provinceId > 0 && overlapStartDateRaw <= overlapEndDateRaw,
                    "valid closed Province conflict required");
        }
    }
    public record OpposingEdge(int hostileArmyId, int subjectFromProvinceId, int subjectToProvinceId,
                               int hostileFromProvinceId, int hostileToProvinceId, int overlapStartDateRaw,
                               int overlapEndDateRaw) implements Conflict {
        public OpposingEdge {
            StrictJson.require(hostileArmyId >= 0 && subjectFromProvinceId > 0 && subjectToProvinceId > 0
                    && hostileFromProvinceId == subjectToProvinceId && hostileToProvinceId == subjectFromProvinceId
                    && overlapStartDateRaw <= overlapEndDateRaw, "valid closed opposing-edge conflict required");
        }
    }
    public sealed interface Projection permits Unavailable, Available {
        int horizonDays(); Integer windowStartDateRaw(); Integer windowEndDateRaw();
    }
    public record Unavailable(int horizonDays, Integer windowStartDateRaw, Integer windowEndDateRaw,
                              List<String> missing) implements Projection {
        public Unavailable {
            days(horizonDays); missing = List.copyOf(missing);
            StrictJson.require((windowStartDateRaw == null) == (windowEndDateRaw == null) && !missing.isEmpty(),
                    "unavailable window must retain missing inputs and nullable date pair");
        }
    }
    public record Available(int horizonDays, Integer windowStartDateRaw, Integer windowEndDateRaw,
                            List<Conflict> conflicts, Integer firstContactDateRaw,
                            int contactFreeWholeDays) implements Projection {
        public Available {
            days(horizonDays); Objects.requireNonNull(windowStartDateRaw, "window start");
            Objects.requireNonNull(windowEndDateRaw, "window end"); conflicts = List.copyOf(conflicts);
            StrictJson.require(windowEndDateRaw.longValue() - windowStartDateRaw.longValue()
                    == (long) horizonDays * RAW_UNITS_PER_DAY, "window duration differs");
            Integer first = conflicts.stream().map(Conflict::overlapStartDateRaw).min(Integer::compareTo).orElse(null);
            StrictJson.require(Objects.equals(first, firstContactDateRaw), "first contact differs from closed intervals");
            int expected = first == null ? horizonDays : Math.max(0, Math.min(horizonDays,
                    Math.toIntExact(Math.floorDiv((long) first - windowStartDateRaw - 1, RAW_UNITS_PER_DAY))));
            StrictJson.require(contactFreeWholeDays == expected, "whole-day boundary differs");
            for (Conflict conflict : conflicts) {
                StrictJson.require(conflict.overlapStartDateRaw() >= windowStartDateRaw
                        && conflict.overlapEndDateRaw() <= windowEndDateRaw, "conflict outside projected window");
            }
        }
        public boolean contactFree() { return conflicts.isEmpty(); }
    }
    private record Occupancy(int province, int enter, int leave) { }
    private record Edge(int from, int to, int depart, int arrive) { }
    private record Intervals(List<Occupancy> occupancy, List<Edge> edges) {
        private Intervals { occupancy = List.copyOf(occupancy); edges = List.copyOf(edges); }
    }
    private record Overlap(int enter, int leave) { }

    public static Available project(Horizon horizon) {
        Objects.requireNonNull(horizon, "horizon"); int start = horizon.startDateRaw(); int end = horizon.endDateRaw();
        Intervals subject = intervals(horizon.subject(), start, end);
        LinkedHashSet<Conflict> conflicts = new LinkedHashSet<>();
        for (Route hostile : horizon.hostiles()) {
            Intervals other = intervals(hostile, start, end);
            for (Occupancy left : subject.occupancy()) {
                for (Occupancy right : other.occupancy()) {
                    Overlap overlap = overlap(left.enter(), left.leave(), right.enter(), right.leave(), start, end);
                    if (left.province() == right.province() && overlap != null) {
                        conflicts.add(new SameProvince(hostile.armyId(), left.province(), overlap.enter(), overlap.leave()));
                    }
                }
            }
            for (Edge left : subject.edges()) {
                for (Edge right : other.edges()) {
                    Overlap overlap = overlap(left.depart(), left.arrive(), right.depart(), right.arrive(), start, end);
                    if (left.from() == right.to() && left.to() == right.from() && overlap != null) {
                        conflicts.add(new OpposingEdge(hostile.armyId(), left.from(), left.to(), right.from(), right.to(),
                                overlap.enter(), overlap.leave()));
                    }
                }
            }
        }
        List<Conflict> ordered = List.copyOf(conflicts);
        Integer first = ordered.stream().map(Conflict::overlapStartDateRaw).min(Integer::compareTo).orElse(null);
        int wholeDays = first == null ? horizon.horizonDays() : Math.max(0, Math.min(horizon.horizonDays(),
                Math.toIntExact(Math.floorDiv((long) first - start - 1, RAW_UNITS_PER_DAY))));
        return new Available(horizon.horizonDays(), start, end, ordered, first, wholeDays);
    }

    public static void days(int days) { StrictJson.require(days >= 1 && days <= 3, "route contact window requires one to three days"); }

    private static Intervals intervals(Route route, int start, int end) {
        List<Occupancy> occupancy = new ArrayList<>(); List<Edge> edges = new ArrayList<>();
        List<Integer> arrivals = route.arrivalDateRaws();
        occupancy.add(new Occupancy(route.currentProvinceId(), start, arrivals.isEmpty() ? end : arrivals.getFirst()));
        int origin = route.currentProvinceId(); int depart = start;
        for (int index = 0; index < route.provinceIds().size(); index++) {
            int target = route.provinceIds().get(index); int arrive = arrivals.get(index);
            edges.add(new Edge(origin, target, depart, arrive));
            int leave = index + 1 < arrivals.size() ? arrivals.get(index + 1) : end;
            occupancy.add(new Occupancy(target, arrive, leave)); origin = target; depart = arrive;
        }
        return new Intervals(occupancy, edges);
    }
    private static Overlap overlap(int leftStart, int leftEnd, int rightStart, int rightEnd, int start, int end) {
        int enter = Math.max(start, Math.max(leftStart, rightStart)); int leave = Math.min(end, Math.min(leftEnd, rightEnd));
        return enter <= leave ? new Overlap(enter, leave) : null;
    }
    private static List<Route> concat(Route subject, List<Route> hostiles) {
        List<Route> result = new ArrayList<>(); result.add(subject); result.addAll(hostiles); return result;
    }
}
