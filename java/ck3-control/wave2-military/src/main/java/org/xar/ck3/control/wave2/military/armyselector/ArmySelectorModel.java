package org.xar.ck3.control.wave2.military.armyselector;

import java.util.List;
import java.util.Objects;

/** Same-capture inputs and conditional results. No native, clock, action, or writer authority. */
public final class ArmySelectorModel {
    private ArmySelectorModel() {}
    public enum Presence { MISSING, NULL, VALUE }
    public record Slot<T>(Presence presence, T value) {
        public Slot {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) throw new IllegalArgumentException("slot presence differs");
        }
        public static <T> Slot<T> missing() { return new Slot<>(Presence.MISSING, null); }
        public static <T> Slot<T> nil() { return new Slot<>(Presence.NULL, null); }
        public static <T> Slot<T> of(T value) { return new Slot<>(Presence.VALUE, Objects.requireNonNull(value)); }
    }
    public enum Coverage { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum SelectionStatus { NOT_APPLICABLE, CURRENT_INPUTS_UNAVAILABLE, AVAILABLE }
    public record Army(int armyId, Integer soldiers, String armyState, Integer moveTargetProvinceId,
                       List<Integer> routeProvinceIds, Integer currentProvinceId) {
        public Army {
            if (armyId < 0) throw new IllegalArgumentException("public CUnit must be nonnegative int32");
            routeProvinceIds = routeProvinceIds == null ? null : List.copyOf(routeProvinceIds);
        }
    }
    public record Snapshot(Boolean paused, String snapshotId, Long revision, Slot<String> strengthsStatus,
                           String queriedSnapshotId, Long queriedRevision, Slot<List<StrengthRow>> strengths) {
        public Snapshot {
            Objects.requireNonNull(strengthsStatus); Objects.requireNonNull(strengths);
            if (strengths.presence() == Presence.VALUE) strengths = Slot.of(List.copyOf(strengths.value()));
        }
    }
    public record Input(List<Army> armies, Snapshot snapshot, List<Long> activeWarIds) {
        public Input { armies = List.copyOf(armies); Objects.requireNonNull(snapshot); activeWarIds = List.copyOf(activeWarIds); }
    }
    public record Strength(int regimentId, int current, int maximum) {}
    public record DataRecord(int recordIndex, int persistentId, int chunkIndex, Integer state,
                             Integer current, Integer maximum) {}
    public record DataSnapshot(int regimentId, Coverage status, Boolean lossWriterSkipped, List<DataRecord> records) {
        public DataSnapshot { Objects.requireNonNull(status); records = records == null ? null : List.copyOf(records); }
    }
    public record StrengthRow(int armyId, Integer nativeArmyId, Coverage status, String scopeRole,
                              Integer currentSoldiers, List<Long> warIds, Integer regimentCount,
                              List<DataSnapshot> data, List<Strength> observedStrengths, OrderedInputs ordered) {
        public StrengthRow {
            Objects.requireNonNull(status);
            warIds = warIds == null ? null : List.copyOf(warIds);
            data = data == null ? null : List.copyOf(data);
            observedStrengths = observedStrengths == null ? null : List.copyOf(observedStrengths);
        }
    }
    public record Occurrence(int storedIndex, int persistentId) {}
    public record Persistent(int persistentId, Long fraction, List<Chunk> chunks) {
        public Persistent { chunks = List.copyOf(chunks); }
    }
    public record OrderedInputs(int subjectArmyId, int subjectNativeArmyId, Integer occurrenceCount,
                                Integer refreshCount, List<Occurrence> occurrences,
                                List<Integer> refreshIndices, List<Persistent> persistents) {
        public OrderedInputs {
            occurrences = List.copyOf(occurrences); refreshIndices = List.copyOf(refreshIndices); persistents = List.copyOf(persistents);
        }
    }
    /** Declared operands of the original ordered physical loop; unrelated SDK fields stay outside this model. */
    public record Chunk(int physicalIndex, int current, int maximum, int ordinal, int armyRegimentId,
                        int exclusionByte, int state, Integer origin788, Integer origin73c,
                        Long associatedMagic, Integer associatedRegimentId, Integer armyByte1d4,
                        Integer armyByte1ec, Boolean inCombat, Integer unit170, Long provinceMagic,
                        Integer positionOwner, Integer positionHolder, Boolean positionEligible,
                        Integer ownerGuard, Long ownerMagic) {
        public Chunk withPair(int newCurrent, int newMaximum) {
            return new Chunk(physicalIndex, newCurrent, newMaximum, ordinal, armyRegimentId, exclusionByte,
                    state, origin788, origin73c, associatedMagic, associatedRegimentId, armyByte1d4,
                    armyByte1ec, inCombat, unit170, provinceMagic, positionOwner, positionHolder,
                    positionEligible, ownerGuard, ownerMagic);
        }
    }
    public record Projection(boolean orderedCoreReady, boolean currentMaximumReady, Integer conditionalCurrent,
                             Integer conditionalMaximum, List<String> missingInputs) {
        public Projection { missingInputs = List.copyOf(missingInputs); }
    }
    public record Candidate(int armyId, int currentSoldiers, Integer conditionalCurrent, Long signedDelta,
                            Long positiveOpportunity, Slot<List<String>> missingInputs) {
        public Candidate {
            Objects.requireNonNull(missingInputs);
            if (missingInputs.presence() == Presence.VALUE) missingInputs = Slot.of(List.copyOf(missingInputs.value()));
            if (missingInputs.presence() == Presence.NULL) throw new IllegalArgumentException("missing inputs cannot be explicit null");
            if (conditionalCurrent == null) {
                if (signedDelta != null || positiveOpportunity != null) throw new IllegalArgumentException("unavailable candidate cannot carry partial arithmetic");
            } else if (signedDelta == null || positiveOpportunity == null || signedDelta != (long) conditionalCurrent - currentSoldiers
                    || positiveOpportunity != Math.max(0, signedDelta) || missingInputs.presence() != Presence.MISSING) {
                throw new IllegalArgumentException("available candidate arithmetic or missing-input state differs");
            }
        }
        public boolean available() { return conditionalCurrent != null; }
    }
    public record Selection(Army selected, SelectionStatus status, List<Long> activeWarIds,
                            boolean queryNeeded, List<Candidate> candidates) {
        public Selection {
            Objects.requireNonNull(status); activeWarIds = List.copyOf(activeWarIds); candidates = List.copyOf(candidates);
            if (queryNeeded && status != SelectionStatus.CURRENT_INPUTS_UNAVAILABLE) throw new IllegalArgumentException("query request requires unavailable current inputs");
            if (status == SelectionStatus.NOT_APPLICABLE && !candidates.isEmpty()) throw new IllegalArgumentException("inapplicable selection cannot carry candidates");
            if (status == SelectionStatus.AVAILABLE) {
                if (selected == null || candidates.size() < 2 || candidates.stream().anyMatch(candidate -> !candidate.available())) throw new IllegalArgumentException("available selection lacks complete candidates");
                Candidate expected = candidates.stream().min(java.util.Comparator.comparing(Candidate::positiveOpportunity).thenComparingInt(Candidate::armyId)).orElseThrow();
                if (selected.armyId() != expected.armyId()) throw new IllegalArgumentException("selected identity differs from current refill ordering");
            }
        }
        public boolean actualAfter() { return false; }
        public boolean fullMonthlyReady() { return false; }
    }
}
