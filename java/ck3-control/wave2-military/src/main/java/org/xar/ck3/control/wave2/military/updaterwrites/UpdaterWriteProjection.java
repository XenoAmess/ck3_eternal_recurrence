package org.xar.ck3.control.wave2.military.updaterwrites;

import static org.xar.ck3.control.wave2.military.updaterwrites.UpdaterAdmission.*;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;

/** Exact conditional +22/+188 source ordering; performs no actual writes. */
public final class UpdaterWriteProjection {
    private UpdaterWriteProjection() {}

    public static UpdaterProjection project(UpdaterInput input) {
        SourceNextFrame future = input.sourceNextDate();
        Integer nextLow = future == null ? null : future.nextDateRawI32();
        Long nextFull = future == null ? null : future.nextDateStorageRaw64();
        boolean fullReady = future != null && future.fullCdate64Ready() && nextFull != null;
        boolean typedRow = input.rowAvailable() && input.nativeCarmyId() != null;
        UpdaterAdmission admission = typedRow ? admit(input.gateInputs(), input.clock(), nextLow)
                : new UpdaterAdmission(false, null, null, List.of(), List.of("available_typed_army_row"));
        Boolean admitted = admission.admitted();
        Long old188 = input.clock().lastSupplyUpdateDateStorageRaw64();
        Long currentFull = input.caller().currentDateStorageRaw64();
        Long sourceCurrentFull = future == null ? null : future.currentDateStorageRaw64();
        boolean comparisonReady = old188 != null && currentFull != null;
        Integer currentLow = input.clock().currentDateRaw();
        Integer anchorLow = input.clock().graceAnchorDateRaw();
        Integer currentElapsed = currentLow != null && anchorLow != null ? (currentLow - anchorLow) / 24 : null;
        boolean afterReady = Boolean.TRUE.equals(admitted) && fullReady || Boolean.FALSE.equals(admitted) && old188 != null;
        Long after188 = Boolean.TRUE.equals(admitted) && fullReady ? nextFull : Boolean.FALSE.equals(admitted) && old188 != null ? old188 : null;
        List<String> missing = new ArrayList<>(admission.missingInputs());
        if (Boolean.TRUE.equals(admitted) && !fullReady) {
            missing.add("source_derived_next_daily_supply_frame_inputs_v1.source_derived_next_date_storage_raw64");
        } else if (Boolean.FALSE.equals(admitted) && old188 == null) {
            missing.add("army_update_clock_v1.last_supply_update_date_storage_raw64");
        }
        boolean ready = typedRow && admission.ready() && afterReady;
        Long old22 = input.caller().armyByte22Raw();
        ConditionalWrite.ValueOrigin origin = Boolean.TRUE.equals(admitted)
                ? ConditionalWrite.ValueOrigin.SOURCE_DERIVED_NEXT_FULL_CDATE64
                : Boolean.FALSE.equals(admitted) ? ConditionalWrite.ValueOrigin.OBSERVED_CURRENT_188_RETAINED : null;
        return new UpdaterProjection(ready ? UpdaterProjection.Status.AVAILABLE
                : typedRow ? UpdaterProjection.Status.PARTIAL : UpdaterProjection.Status.UNAVAILABLE, ready,
                new ArrayList<>(new LinkedHashSet<>(missing)), input.armyId(), input.nativeCarmyId(), future,
                old22, old22 != null && old22 >= 0 && old22 < 256,
                old188, input.clock().lastSupplyUpdateDateRaw(), currentFull, comparisonReady,
                comparisonReady ? old188.longValue() == currentFull.longValue() : null,
                currentFull != null && sourceCurrentFull != null ? currentFull.longValue() == sourceCurrentFull.longValue() : null,
                currentElapsed, admission,
                List.of(new ConditionalWrite.Byte22Write(typedRow, typedRow ? true : null, old22, typedRow ? 1 : null),
                        new ConditionalWrite.Date188Write(afterReady, admission.ready(), admitted, afterReady, old188, after188, origin)),
                new UpdaterProjection.GraceAnchor(input.clock().graceAnchorDateStorageRaw64() != null,
                        input.clock().graceAnchorDateStorageRaw64(), anchorLow), fullReady);
    }

    private static UpdaterAdmission admit(UpdaterInput.GateInputs gate, UpdaterInput.ClockInputs clock, Integer nextLow) {
        List<Witness> witnesses = new ArrayList<>();
        Integer first = gate.unitNative170Raw();
        Boolean passed = first == null ? null : first != 3;
        witnesses.add(new IntegerGateWitness(GateField.UNIT_NATIVE_170_RAW, first, passed));
        if (passed == null || !passed) return stop(GateField.UNIT_NATIVE_170_RAW, passed, witnesses);
        Boolean combat = gate.nativeUnitInCombat();
        passed = combat == null ? null : !combat;
        witnesses.add(new BooleanGateWitness(GateField.NATIVE_UNIT_IN_COMBAT, combat, passed));
        if (passed == null || !passed) return stop(GateField.NATIVE_UNIT_IN_COMBAT, passed, witnesses);
        Boolean gathering = gate.nativeUnitGathering();
        passed = gathering == null ? null : !gathering;
        witnesses.add(new BooleanGateWitness(GateField.NATIVE_UNIT_GATHERING, gathering, passed));
        if (passed == null || !passed) return stop(GateField.NATIVE_UNIT_GATHERING, passed, witnesses);
        Integer count = gate.armyGatheringCountRaw();
        passed = count == null ? null : count == 0;
        witnesses.add(new IntegerGateWitness(GateField.ARMY_GATHERING_COUNT_RAW, count, passed));
        if (passed == null || !passed) return stop(GateField.ARMY_GATHERING_COUNT_RAW, passed, witnesses);
        List<String> missing = new ArrayList<>();
        if (nextLow == null) missing.add("source_derived_next_date_raw_i32");
        if (clock.graceAnchorDateRaw() == null) missing.add("grace_anchor_date_raw");
        if (clock.loadedGraceDays() == null) missing.add("loaded_grace_days");
        if (!missing.isEmpty()) return new UpdaterAdmission(false, null, null, witnesses, missing);
        int elapsed = nextLow - clock.graceAnchorDateRaw();
        int days = elapsed / 24;
        boolean admitted = days > clock.loadedGraceDays();
        witnesses.add(new GraceWitness(nextLow, clock.graceAnchorDateRaw(), elapsed, days, clock.loadedGraceDays(), admitted));
        return new UpdaterAdmission(true, admitted, admitted ? null : "native_grace_strict_greater", witnesses, List.of());
    }
    private static UpdaterAdmission stop(GateField field, Boolean passed, List<Witness> witnesses) {
        return passed == null ? new UpdaterAdmission(false, null, null, witnesses,
                List.of("monthly_loss_budget_inputs_v1." + field.wire()))
                : new UpdaterAdmission(true, false, field.wire(), witnesses, List.of());
    }
}
