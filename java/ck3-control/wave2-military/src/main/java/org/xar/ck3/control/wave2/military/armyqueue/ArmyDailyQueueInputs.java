package org.xar.ck3.control.wave2.military.armyqueue;

import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Initial current-frame occurrences, before any transfer or removal call. */
public record ArmyDailyQueueInputs(
        Readiness readiness,
        Optional<List<ArmyId>> orderedIds,
        Optional<List<InitialResolution>> initialRows) {
    public ArmyDailyQueueInputs {
        Objects.requireNonNull(readiness, "readiness");
        orderedIds = Objects.requireNonNull(orderedIds, "orderedIds").map(List::copyOf);
        initialRows = Objects.requireNonNull(initialRows, "initialRows").map(List::copyOf);
        if (initialRows.isPresent()) {
            List<InitialResolution> rows = initialRows.orElseThrow();
            if (orderedIds.isPresent() && rows.size() != orderedIds.orElseThrow().size()) {
                throw new IllegalArgumentException("resolution rows disagree with ordered IDs");
            }
            for (int index = 0; index < rows.size(); index++) {
                InitialResolution row = rows.get(index);
                if (row.storedIndex() != index || (orderedIds.isPresent()
                        && !row.rawArmyReference().equals(orderedIds.orElseThrow().get(index)))) {
                    throw new IllegalArgumentException("queue occurrence order disagrees with IDs");
                }
            }
        }
        if (readiness instanceof Available && (orderedIds.isEmpty() || initialRows.isEmpty()
                || initialRows.orElseThrow().stream().anyMatch(row -> !(row.readiness() instanceof Available)))) {
            throw new IllegalArgumentException("available daily queue inputs are incomplete");
        }
    }

    public boolean ready() { return readiness instanceof Available; }

    /** The stored DWORD is signed in this wire ABI; repetitions are separate occurrences. */
    public record ArmyId(int value) { }

    public record ArmyMagic(long value) {
        public ArmyMagic {
            if (value < 0 || value > 0xffff_ffffL) {
                throw new IllegalArgumentException("army magic must be uint32");
            }
        }
    }

    public sealed interface Readiness permits Available, Unavailable { }
    public record Available() implements Readiness { }
    public record Unavailable(String reason) implements Readiness {
        public Unavailable {
            if (reason == null || reason.isEmpty()) {
                throw new IllegalArgumentException("unavailable queue reason must be nonempty");
            }
        }
    }

    public record InitialResolution(
            Readiness readiness, int storedIndex, ArmyId rawArmyReference,
            Optional<ArmyId> resolvedArmy, Optional<Boolean> usedFallback,
            Optional<ArmyMagic> armyMagic, Optional<Boolean> nativeIdentityValid) {
        public InitialResolution {
            Objects.requireNonNull(readiness, "readiness");
            Objects.requireNonNull(rawArmyReference, "rawArmyReference");
            Objects.requireNonNull(resolvedArmy, "resolvedArmy");
            Objects.requireNonNull(usedFallback, "usedFallback");
            Objects.requireNonNull(armyMagic, "armyMagic");
            Objects.requireNonNull(nativeIdentityValid, "nativeIdentityValid");
            if (readiness instanceof Available && (resolvedArmy.isEmpty() || usedFallback.isEmpty()
                    || armyMagic.isEmpty() || nativeIdentityValid.isEmpty())) {
                throw new IllegalArgumentException("available daily queue resolution row is incomplete");
            }
        }

        /** Consumer predicate only; false or incomplete observations cannot select a request. */
        public boolean identityPredicateConsistent() {
            return readiness instanceof Available && resolvedArmy.isPresent() && usedFallback.isPresent()
                    && armyMagic.isPresent() && nativeIdentityValid.isPresent()
                    && nativeIdentityValid.orElseThrow() == (armyMagic.orElseThrow().value() == 0x4172_6d79L
                    && resolvedArmy.orElseThrow().value() != -1);
        }
    }

    /** The additive family in an extensible strength container retains missing versus explicit null. */
    public sealed interface Family permits Missing, ExplicitNull, Observed { }
    public record Missing() implements Family { }
    public record ExplicitNull() implements Family { }
    public record Observed(ArmyDailyQueueInputs value) implements Family {
        public Observed { Objects.requireNonNull(value, "value"); }
    }
}
