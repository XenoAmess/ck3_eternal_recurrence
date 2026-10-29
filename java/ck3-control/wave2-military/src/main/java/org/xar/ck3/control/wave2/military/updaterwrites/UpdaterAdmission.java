package org.xar.ck3.control.wave2.military.updaterwrites;

import java.util.List;
import java.util.Objects;

public record UpdaterAdmission(boolean ready, Boolean admitted, String rejection,
                               List<Witness> witnesses, List<String> missingInputs) {
    public UpdaterAdmission {
        witnesses = List.copyOf(witnesses); missingInputs = List.copyOf(missingInputs);
        if (ready != (admitted != null) || ready && (Boolean.FALSE.equals(admitted) != (rejection != null))) {
            throw new IllegalArgumentException("updater admission state fields differ");
        }
    }
    public enum GateField {
        UNIT_NATIVE_170_RAW("unit_native_170_raw"), NATIVE_UNIT_IN_COMBAT("native_unit_in_combat"),
        NATIVE_UNIT_GATHERING("native_unit_gathering"), ARMY_GATHERING_COUNT_RAW("army_gathering_count_raw");
        private final String wire;
        GateField(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public sealed interface Witness permits IntegerGateWitness, BooleanGateWitness, GraceWitness {}
    public record IntegerGateWitness(GateField field, Integer value, Boolean passed) implements Witness {
        public IntegerGateWitness { Objects.requireNonNull(field); }
    }
    public record BooleanGateWitness(GateField field, Boolean value, Boolean passed) implements Witness {
        public BooleanGateWitness { Objects.requireNonNull(field); }
    }
    public record GraceWitness(int passedDateRawI32, int graceAnchorDateRawI32, int elapsedDateRawI32,
                               int elapsedDays, int loadedGraceDays, boolean passed) implements Witness {}
}
