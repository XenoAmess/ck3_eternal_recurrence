package org.xar.ck3.control.wave2.military.armytransfer;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ArmyId;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.ArmyMagic;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Family;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.InitialResolution;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputs.Observed;

/** Finite same-input logical projection. It neither drains a queue nor submits a native request. */
public final class DailyQueueTransferProjection {
    private DailyQueueTransferProjection() { }

    public enum StrengthAvailability { AVAILABLE, UNAVAILABLE }
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum TransferBranch { TRANSFER, NOT_CALLED }
    public enum RemainingBasis { UNKNOWN_INITIAL_RESOLUTION, REQUIRES_POST_REMOVAL_STAGE_FRAMES }

    public record Occurrence(int storedIndex, ArmyId rawArmyReference) {
        public Occurrence {
            if (storedIndex < 0) { throw new IllegalArgumentException("negative occurrence index"); }
            Objects.requireNonNull(rawArmyReference, "rawArmyReference");
        }
    }

    public record ResolvedOccurrence(Occurrence occurrence, ArmyId resolvedArmy,
            boolean usedFallback, ArmyMagic armyMagic, boolean nativeIdentityValid) {
        public ResolvedOccurrence {
            Objects.requireNonNull(occurrence, "occurrence");
            Objects.requireNonNull(resolvedArmy, "resolvedArmy");
            Objects.requireNonNull(armyMagic, "armyMagic");
            if (nativeIdentityValid != (armyMagic.value() == 0x4172_6d79L && resolvedArmy.value() != -1)) {
                throw new IllegalArgumentException("inconsistent captured initial identity predicate");
            }
        }
    }

    public record Transfer(List<ArmyId> sourceIds) {
        public Transfer { sourceIds = List.copyOf(sourceIds); }
        public TransferBranch branch() { return sourceIds.isEmpty() ? TransferBranch.NOT_CALLED : TransferBranch.TRANSFER; }
    }

    public record Result(Status status, Optional<Transfer> transfer, boolean selectionReady,
            List<ResolvedOccurrence> invalidPrefix, Optional<ResolvedOccurrence> firstRemovalRequest,
            List<Occurrence> remainingOccurrences, Optional<RemainingBasis> remainingBasis,
            List<String> missingInputs) {
        public Result {
            Objects.requireNonNull(status, "status");
            Objects.requireNonNull(transfer, "transfer");
            invalidPrefix = List.copyOf(invalidPrefix);
            Objects.requireNonNull(firstRemovalRequest, "firstRemovalRequest");
            remainingOccurrences = List.copyOf(remainingOccurrences);
            Objects.requireNonNull(remainingBasis, "remainingBasis");
            missingInputs = List.copyOf(missingInputs);
            if (invalidPrefix.stream().anyMatch(ResolvedOccurrence::nativeIdentityValid)) {
                throw new IllegalArgumentException("invalid prefix contains a valid identity");
            }
            if (firstRemovalRequest.isPresent() && (!selectionReady || transfer.isEmpty()
                    || !firstRemovalRequest.orElseThrow().nativeIdentityValid())) {
                throw new IllegalArgumentException("first request requires an initial valid occurrence");
            }
        }
        public boolean conditionalTransferReady() { return transfer.isPresent(); }
        public boolean firstRemovalRequestReady() { return firstRemovalRequest.isPresent(); }
        public boolean postRemovalStageRequired() { return firstRemovalRequest.isPresent() && !remainingOccurrences.isEmpty(); }
    }

    public static Result project(StrengthAvailability strengthAvailability, Family queueFamily) {
        Objects.requireNonNull(strengthAvailability, "strengthAvailability");
        Objects.requireNonNull(queueFamily, "queueFamily");
        if (strengthAvailability != StrengthAvailability.AVAILABLE) {
            return unavailable("available_same_query_army_strength");
        }
        if (!(queueFamily instanceof Observed observed) || observed.value().orderedIds().isEmpty()) {
            return unavailable("manager_army_id_list_2a5a8");
        }
        ArmyDailyQueueInputs queue = observed.value();
        List<ArmyId> ids = queue.orderedIds().orElseThrow();
        Optional<Transfer> transfer = Optional.of(new Transfer(ids));
        if (ids.isEmpty()) {
            return new Result(Status.AVAILABLE, transfer, true, List.of(), Optional.empty(), List.of(),
                    Optional.empty(), List.of());
        }
        List<ResolvedOccurrence> prefix = new ArrayList<>();
        for (int index = 0; index < ids.size(); index++) {
            InitialResolution row = queue.initialRows().isPresent() ? queue.initialRows().orElseThrow().get(index) : null;
            if (row == null || !row.identityPredicateConsistent()) {
                return new Result(Status.PARTIAL, transfer, false, prefix, Optional.empty(), occurrences(ids, index),
                        Optional.of(RemainingBasis.UNKNOWN_INITIAL_RESOLUTION),
                        List.of("initial_army_resolution_rows[" + index + "].available_identity"));
            }
            ResolvedOccurrence occurrence = new ResolvedOccurrence(new Occurrence(index, ids.get(index)),
                    row.resolvedArmy().orElseThrow(), row.usedFallback().orElseThrow(),
                    row.armyMagic().orElseThrow(), row.nativeIdentityValid().orElseThrow());
            if (!occurrence.nativeIdentityValid()) { prefix.add(occurrence); continue; }
            List<Occurrence> suffix = occurrences(ids, index + 1);
            return new Result(suffix.isEmpty() ? Status.AVAILABLE : Status.PARTIAL, transfer, true, prefix,
                    Optional.of(occurrence), suffix,
                    suffix.isEmpty() ? Optional.empty() : Optional.of(RemainingBasis.REQUIRES_POST_REMOVAL_STAGE_FRAMES),
                    suffix.isEmpty() ? List.of() : List.of("post_removal_stage_full_id_slot_and_virtual_effects"));
        }
        return new Result(Status.AVAILABLE, transfer, true, prefix, Optional.empty(), List.of(), Optional.empty(), List.of());
    }

    private static Result unavailable(String missingInput) {
        return new Result(Status.UNAVAILABLE, Optional.empty(), false, List.of(), Optional.empty(), List.of(),
                Optional.empty(), List.of(missingInput));
    }

    private static List<Occurrence> occurrences(List<ArmyId> ids, int start) {
        List<Occurrence> result = new ArrayList<>();
        for (int index = start; index < ids.size(); index++) { result.add(new Occurrence(index, ids.get(index))); }
        return List.copyOf(result);
    }
}
