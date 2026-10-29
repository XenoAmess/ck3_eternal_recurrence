package org.xar.ck3.control.wave2.military.prestore;

import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRisk;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.MovementOperands;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.MovementPrefix;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.PrestoreCall;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.Risk;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.RouteContext;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.Strength;
import org.xar.ck3.control.wave2.military.disembark.DisembarkPenalty.Observation;

/** One source-conditional local Army1D0 fixed-write projection. No native callback is executed. */
public final class PrestoreDisembark {
    public static final String KEY = "current_unit_arrival_prestore_disembark_write_v1";
    private PrestoreDisembark() { }

    public record Arrival(boolean ready, Boolean firstProvinceAssignmentSelected, String unavailableReason,
                          Long subjectArmyId, Long subjectCarmyId, List<Integer> storedIdPositions) {
        public Arrival {
            if (storedIdPositions != null) { storedIdPositions = List.copyOf(storedIdPositions); }
            checkU32(subjectArmyId); checkU32(subjectCarmyId);
        }
        private static void checkU32(Long value) {
            if (value != null && (value < 0 || value > 0xffff_ffffL)) { throw new IllegalArgumentException("subject uint32 or null required"); }
        }
    }
    public record Input(Strength strength, Arrival arrival, Optional<CurrentMovement> movement,
                        RouteContext context, MovementPrefix prefix, Optional<Observation> observedCurrentDays) {
        public Input { Objects.requireNonNull(strength); Objects.requireNonNull(arrival); Objects.requireNonNull(movement); Objects.requireNonNull(observedCurrentDays); }
    }
    public enum Operand { CURRENT_PROVINCE_TYPE, UNIT_KIND, TARGET_DEFINITION_BYTE, CURRENT_DEFINITION_BYTE, LOADED_DAYS_RULE }
    public record Selection(Boolean callSelected, Boolean writeSelected, Integer writeValue, String unavailableReason, Set<Operand> demanded) {
        public Selection { demanded = Set.copyOf(demanded); }
        public boolean ready() { return unavailableReason == null; }
    }
    public record Result(Input input, Selection selection, Risk countyRisk) {
        public Result { Objects.requireNonNull(input); Objects.requireNonNull(selection); Objects.requireNonNull(countyRisk); }
    }

    public static Result project(Input input) {
        Selection selection = select(input.arrival(), input.movement());
        CurrentMovement movement = input.movement().orElse(null);
        MovementOperands operands = movement == null ? new MovementOperands(null, null, null, null, null)
                : new MovementOperands(movement.currentProvinceType().value(), movement.unitKind().value(), movement.targetProvinceType().value(),
                        movement.targetDefinitionByte().value(), movement.currentDefinitionByte().value());
        Risk risk = CountyEntryRisk.project(input.strength(), input.context(), input.prefix(), operands,
                new PrestoreCall(selection.callSelected(), selection.unavailableReason()));
        return new Result(input, selection, risk);
    }

    public static Selection select(Arrival arrival, Optional<CurrentMovement> currentMovement) {
        Set<Operand> demanded = EnumSet.noneOf(Operand.class);
        if (!arrival.ready()) { return result(null, null, null,
                nonemptyOr(arrival.unavailableReason(), "source31_arrival_transition_unavailable"), demanded); }
        if (Boolean.FALSE.equals(arrival.firstProvinceAssignmentSelected())) { return result(false, false, null, null, demanded); }
        if (!Boolean.TRUE.equals(arrival.firstProvinceAssignmentSelected())) {
            return result(null, null, null, "source31_typed_distinct_target_unavailable", demanded);
        }
        CurrentMovement movement = currentMovement.orElse(null);
        demanded.add(Operand.CURRENT_PROVINCE_TYPE);
        Long provinceType = movement == null ? null : movement.currentProvinceType().value();
        if (provinceType == null) { return result(null, null, null, "current_province_type_tag_unavailable", demanded); }
        if (provinceType != 0x50726f76L) { return result(false, false, null, null, demanded); }
        demanded.add(Operand.UNIT_KIND);
        Integer kind = movement.unitKind().value();
        if (kind == null) { return result(null, null, null, "unit_kind_18_raw_unavailable", demanded); }
        if (kind != 0) { return result(false, false, null, null, demanded); }
        demanded.add(Operand.TARGET_DEFINITION_BYTE);
        Integer targetByte = movement.targetDefinitionByte().value();
        if (targetByte == null) { return result(true, null, null, "first_route_target_province_definition_byte_1b_unavailable", demanded); }
        if (targetByte == 0) { return result(true, false, null, null, demanded); }
        demanded.add(Operand.CURRENT_DEFINITION_BYTE);
        Integer currentByte = movement.currentDefinitionByte().value();
        if (currentByte == null) { return result(true, null, null, "current_province_definition_byte_1b_unavailable", demanded); }
        if (currentByte != 0) { return result(true, false, null, null, demanded); }
        demanded.add(Operand.LOADED_DAYS_RULE);
        Integer loadedDays = movement.loadedDisembarkDays().value();
        if (loadedDays == null) { return result(true, true, null, "loaded_disembark_penalty_days_rule_unavailable", demanded); }
        return result(true, true, loadedDays, null, demanded);
    }
    private static Selection result(Boolean call, Boolean write, Integer value, String reason, Set<Operand> demands) {
        return new Selection(call, write, value, reason, demands);
    }
    private static String nonemptyOr(String value, String fallback) { return value == null || value.isEmpty() ? fallback : value; }
}
