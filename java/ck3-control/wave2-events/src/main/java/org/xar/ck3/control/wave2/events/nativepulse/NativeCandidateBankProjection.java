package org.xar.ck3.control.wave2.events.nativepulse;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/**
 * The reviewed .4 character bank layout and two membership projections only.
 * This pure projection is not a native collection reader, an event predicate,
 * or proof that its input list is the complete original native universe.
 */
public final class NativeCandidateBankProjection {
    public static final int MANAGER_OFFSET = 0x2ee40;
    public static final int FIRST_BANK_OFFSET = 0x38;
    public static final int BANK_STRIDE = 0x2640;
    public static final int SELECTOR_OFFSET = 0x4cb8;
    private NativeCandidateBankProjection() { }

    public enum Bank {
        ZERO(0), ONE(1);
        private final int index;
        Bank(int index) { this.index = index; }
        public int index() { return index; }
        /** 22A112C..22A1137 and 28F514F..28F516F: (selector - 1) & 1. */
        public Bank opposite() { return this == ZERO ? ONE : ZERO; }
        public int dataOffsetFromManager() { return FIRST_BANK_OFFSET + BANK_STRIDE * index; }
        public int dataOffsetFromGameStateData() { return MANAGER_OFFSET + dataOffsetFromManager(); }
        public static Bank exact(int value) {
            StrictJson.require(value == 0 || value == 1, "native bank selector must be exactly 0 or 1");
            return value == 0 ? ZERO : ONE;
        }
    }

    /** Names describe pointer presence at actual offsets, not inferred character categories. */
    public record NativeFields(long fullIdU32, boolean at1c8, boolean at1c0,
                               boolean at1b8, boolean at1b0, boolean at1d0) {
        public NativeFields {
            StrictJson.require(fullIdU32 >= 0 && fullIdU32 <= 0xffffffffL, "full native uint32 identity required");
        }
    }
    public enum NativeBranch {
        AT_1C8(5), AT_1C0(4), AT_1B8(3), AT_1B0(2), AT_1D0(0), NONE(1);
        private final int tag;
        NativeBranch(int tag) { this.tag = tag; }
        public int nativeTag() { return tag; }
    }
    /** Exact precedence from 28F4903..28F4955; overlapping pointers are not normalized. */
    public static NativeBranch classify(NativeFields fields) {
        Objects.requireNonNull(fields);
        if (fields.at1c8()) return NativeBranch.AT_1C8;
        if (fields.at1c0()) return NativeBranch.AT_1C0;
        if (fields.at1b8()) return NativeBranch.AT_1B8;
        if (fields.at1b0()) return NativeBranch.AT_1B0;
        if (fields.at1d0()) return NativeBranch.AT_1D0;
        return NativeBranch.NONE;
    }
    public record Projection(NativePlayableAnnualGate.Executable executable, Bank active,
                             Bank rebuildTarget, List<Long> vector00, List<Long> vector18) {
        public Projection {
            Objects.requireNonNull(executable); Objects.requireNonNull(active); Objects.requireNonNull(rebuildTarget);
            StrictJson.require(rebuildTarget == active.opposite(), "rebuild must target the opposite bank");
            vector00 = List.copyOf(vector00); vector18 = List.copyOf(vector18);
        }
        public boolean completeNativeInputUniverseProven() { return false; }
        public boolean completeBankProjection() { return false; }
        public boolean scriptEligibilityProven() { return false; }
        public boolean eventSelected() { return false; }
    }
    /**
     * 28F5140 clears the opposite bank then 28F48C0 consumes the supplied native
     * pointer array in original order. Branch5 appends vector00 at 28F4A3B;
     * branches4/5 append vector18 through 28F4B32 -> 28F42F2.
     * Other bank sub-vectors require additional native facts and are not modeled.
     */
    public static Projection rebuild(NativePlayableAnnualGate.Executable executable, Bank active,
                                     List<NativeFields> originalNativeOrder) {
        Objects.requireNonNull(executable); Objects.requireNonNull(active);
        List<NativeFields> inputs = List.copyOf(originalNativeOrder);
        List<Long> first = new ArrayList<>(); List<Long> second = new ArrayList<>();
        for (NativeFields fields : inputs) {
            NativeBranch branch = classify(fields);
            if (branch == NativeBranch.AT_1C8) first.add(fields.fullIdU32());
            if (branch == NativeBranch.AT_1C8 || branch == NativeBranch.AT_1C0) second.add(fields.fullIdU32());
        }
        return new Projection(executable, active, active.opposite(), first, second);
    }
}
