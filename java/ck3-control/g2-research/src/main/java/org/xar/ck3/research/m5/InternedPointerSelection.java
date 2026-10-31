package org.xar.ck3.research.m5;

import java.util.Map;
import java.util.Objects;
import java.util.OptionalInt;
import java.util.OptionalLong;

/** Pureselection-stage consumer of actual3F4F8E0 read-lock-protectedobservations. No lock/memory/Native execution. */
public final class InternedPointerSelection {
    public enum Route { SLOT_POINTER, FALLBACK_ON_NORMAL_COMPLETION, NEEDS_UPPER_BOUND, NEEDS_SLOT }
    public enum Reason { NONZERO_SLOT, NEGATIVE_INDEX, ABOVE_INCLUSIVE_MAX, NULL_SLOT, UPPER_BOUND_UNOBSERVED, SLOT_UNOBSERVED }
    public record Rva(long bits) { }
    public record Snapshot(OptionalInt upperInclusive, Map<Integer, Long> observedSlotPointerBits) {
        public Snapshot {
            Objects.requireNonNull(upperInclusive, "upperInclusive");
            observedSlotPointerBits = Map.copyOf(observedSlotPointerBits);
        }
    }
    public record Selection(Route route, Reason reason, OptionalLong observedPointerBits, java.util.Optional<Rva> fallbackObjectRva) {
        public Selection {
            Objects.requireNonNull(route, "route"); Objects.requireNonNull(reason, "reason");
            Objects.requireNonNull(observedPointerBits, "observedPointerBits"); Objects.requireNonNull(fallbackObjectRva, "fallbackObjectRva");
        }
    }
    private InternedPointerSelection() { }

    /**
     * The actualinput is ECXnativeStringID at3F4F8E0, signextended3F4F8E4, not tierrawcode.
     * Assume actualnative table-read lock acquisition stagecompleted; do not mint suchreceipt here.
     * NegativeindexJS3F4F92C takesfallback beforeupperboundread, evenwhen boundunobserved.
     * Fornonnegativeindex, missingmax =>NEEDS_UPPER_BOUND/UPPER_BOUND_UNOBSERVED.
     * Ifindex>signedmax (JG3F4F932), fallback ABOVE_INCLUSIVE_MAX; index==max isvalid.
     * In-range missingmapkey =>NEEDS_SLOT/SLOT_UNOBSERVED (not Native null or fallback).
     * Observedslot0 =>fallbackNULL_SLOT; observednonzero64bitpattern=>SLOT_POINTER/NONZERO_SLOT.
     * Allfallbacks carryonly typedRva(0x5DC1128), observedPointerempty. Matchcarriesonlyobservedpointer,
     * needs states carryneither. Missingmemory isnotzero; negativepointerbits arenotnull.
     * FALLBACK_ON_NORMAL_COMPLETION is a branchintent: actualfallbackinitialization/opaque helpers,
     * globalimagebase/loadedpointer/textcontents and functionnormalcompletion remain outside thismethod.
     */
    public static Selection select(int nativeStringId, Snapshot snapshot) {
        // 1. Negative index check (JS 3F4F92C) happens before upper bound check.
        if (nativeStringId < 0) {
            return new Selection(
                Route.FALLBACK_ON_NORMAL_COMPLETION,
                Reason.NEGATIVE_INDEX,
                OptionalLong.empty(),
                java.util.Optional.of(new Rva(0x5DC1128L))
            );
        }

        // 2. Check if upper bound is observed.
        if (snapshot.upperInclusive().isEmpty()) {
            return new Selection(
                Route.NEEDS_UPPER_BOUND,
                Reason.UPPER_BOUND_UNOBSERVED,
                OptionalLong.empty(),
                java.util.Optional.empty()
            );
        }

        int upperBound = snapshot.upperInclusive().getAsInt();

        // 3. Check if index is above inclusive max (JG 3F4F932).
        if (nativeStringId > upperBound) {
            return new Selection(
                Route.FALLBACK_ON_NORMAL_COMPLETION,
                Reason.ABOVE_INCLUSIVE_MAX,
                OptionalLong.empty(),
                java.util.Optional.of(new Rva(0x5DC1128L))
            );
        }

        // 4. Index is in range. Check if slot pointer bits are observed.
        if (!snapshot.observedSlotPointerBits().containsKey(nativeStringId)) {
            return new Selection(
                Route.NEEDS_SLOT,
                Reason.SLOT_UNOBSERVED,
                OptionalLong.empty(),
                java.util.Optional.empty()
            );
        }

        long bits = snapshot.observedSlotPointerBits().get(nativeStringId);

        // 5. Check if observed slot is null (0).
        if (bits == 0L) {
            return new Selection(
                Route.FALLBACK_ON_NORMAL_COMPLETION,
                Reason.NULL_SLOT,
                OptionalLong.empty(),
                java.util.Optional.of(new Rva(0x5DC1128L))
            );
        }

        // 6. Observed nonzero 64-bit pattern.
        return new Selection(
            Route.SLOT_POINTER,
            Reason.NONZERO_SLOT,
            OptionalLong.of(bits),
            java.util.Optional.empty()
        );
    }
}
