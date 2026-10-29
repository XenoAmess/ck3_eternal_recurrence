package org.xar.ck3.control.wave3.military.siegecontribution;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Measured inputs never grant source or action authority; this pure consumer only reports contribution. */
public final class SiegeContributionPolicy {
    public static final String INPUT_SCHEMA = "xar.siege-subject-contribution-input.v1";
    private SiegeContributionPolicy() { }

    public enum Status {
        UNAVAILABLE("unavailable"), ELIGIBLE("eligible"), EXCLUDED("excluded");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public enum Reason {
        SUBJECT_UNAVAILABLE("selected_controllable_subject_unavailable"),
        SUBJECT_NOT_ARRIVED("selected_subject_not_arrived_with_empty_route"),
        PROVINCE_UNAVAILABLE("current_province_qualification_unavailable"),
        SUBJECT_MEASUREMENT_UNAVAILABLE("selected_subject_native_qualification_unavailable"),
        MEASURED_NATIVE_QUALIFICATION("measured_native_province_qualification");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** Canonical three-field result of the existing selection normalizer. */
    public record Selection(Integer nativeCarmyId, Integer publicUnitId, Boolean controllable) {
        public Selection { id(nativeCarmyId, false); id(publicUnitId, false); }
    }
    /** Canonical occurrence row; order and repeated identities are significant. */
    public record Occurrence(int occurrenceIndex, Integer publicUnitId, Integer nativeCarmyId,
            Boolean eligible, List<Integer> qualifiedRegimentIds) {
        public Occurrence {
            if (occurrenceIndex < 0) { throw new IllegalArgumentException("nonnegative native occurrence index required"); }
            id(publicUnitId, false); id(nativeCarmyId, false);
            if (qualifiedRegimentIds != null) {
                qualifiedRegimentIds = List.copyOf(qualifiedRegimentIds);
                for (Integer regiment : qualifiedRegimentIds) {
                    if (regiment == null) { throw new IllegalArgumentException("regiment ID cannot be null"); }
                    id(regiment, false);
                }
            }
            if (Boolean.TRUE.equals(eligible) && (publicUnitId == null || nativeCarmyId == null)) {
                throw new IllegalArgumentException("eligible native occurrence requires both resolved identities");
            }
            if (Boolean.FALSE.equals(eligible) && (qualifiedRegimentIds == null || !qualifiedRegimentIds.isEmpty())) {
                throw new IllegalArgumentException("excluded occurrence cannot publish consumed regiments");
            }
            if (eligible == null && qualifiedRegimentIds != null) {
                throw new IllegalArgumentException("unknown qualification cannot publish consumed regiments");
            }
        }
    }
    public record Province(Integer provinceId, Selection currentBesiegingArmySelection, List<Occurrence> provinceUnitOccurrences) {
        public Province {
            id(provinceId, true);
            if (provinceUnitOccurrences != null) {
                provinceUnitOccurrences = List.copyOf(provinceUnitOccurrences);
                for (int index = 0; index < provinceUnitOccurrences.size(); index++) {
                    if (provinceUnitOccurrences.get(index).occurrenceIndex() != index) {
                        throw new IllegalArgumentException("native occurrence order/index must be preserved");
                    }
                }
            }
        }
    }
    public record Subject(Boolean controllable, Integer armyId, Integer currentProvinceId,
            Integer moveTargetProvinceId, List<Integer> routeProvinceIds) {
        public Subject {
            id(armyId, false); id(currentProvinceId, true); id(moveTargetProvinceId, true);
            if (routeProvinceIds != null) {
                routeProvinceIds = List.copyOf(routeProvinceIds);
                for (Integer province : routeProvinceIds) {
                    if (province == null) { throw new IllegalArgumentException("route province cannot be null"); }
                    id(province, true);
                }
            }
        }
    }
    public record Request(Province province, Subject subject) {
        public Request { Objects.requireNonNull(province); }
    }
    public record Decision(Status status, Selection currentBesiegingArmySelection, Integer publicUnitId,
            Integer nativeCarmyId, Boolean matchesCurrentSelection, Reason reason, List<Integer> occurrenceIndices) {
        public Decision {
            Objects.requireNonNull(status); Objects.requireNonNull(reason);
            occurrenceIndices = occurrenceIndices == null ? null : List.copyOf(occurrenceIndices);
        }
    }

    public static Decision observe(Request request) {
        Objects.requireNonNull(request);
        Province province = request.province(); Subject subject = request.subject();
        if (subject == null || !Boolean.TRUE.equals(subject.controllable())) {
            return unavailable(province, null, Reason.SUBJECT_UNAVAILABLE);
        }
        Integer unitId = subject.armyId();
        if (!Objects.equals(subject.currentProvinceId(), province.provinceId()) || subject.moveTargetProvinceId() != null
                || subject.routeProvinceIds() == null || !subject.routeProvinceIds().isEmpty()) {
            return unavailable(province, unitId, Reason.SUBJECT_NOT_ARRIVED);
        }
        if (province.provinceUnitOccurrences() == null) { return unavailable(province, unitId, Reason.PROVINCE_UNAVAILABLE); }
        List<Occurrence> rows = province.provinceUnitOccurrences().stream().filter(row -> Objects.equals(row.publicUnitId(), unitId)).toList();
        if (rows.isEmpty() || rows.stream().anyMatch(row -> row.eligible() == null)) {
            return unavailable(province, unitId, Reason.SUBJECT_MEASUREMENT_UNAVAILABLE);
        }
        Integer nativeId = rows.getFirst().nativeCarmyId();
        Selection selection = province.currentBesiegingArmySelection();
        Boolean matches = selection != null && selection.nativeCarmyId() != null ? selection.nativeCarmyId().equals(nativeId) : null;
        List<Integer> indices = new ArrayList<>(); for (Occurrence row : rows) { indices.add(row.occurrenceIndex()); }
        return new Decision(rows.stream().allMatch(row -> Boolean.TRUE.equals(row.eligible())) ? Status.ELIGIBLE : Status.EXCLUDED,
                selection, unitId, nativeId, matches, Reason.MEASURED_NATIVE_QUALIFICATION, indices);
    }
    private static Decision unavailable(Province province, Integer publicId, Reason reason) {
        return new Decision(Status.UNAVAILABLE, province.currentBesiegingArmySelection(), publicId, null, null, reason, null);
    }
    private static void id(Integer value, boolean positive) {
        if (value != null && (value < 0 || positive && value == 0)) { throw new IllegalArgumentException("native int32 ID outside its exact domain"); }
    }
}
