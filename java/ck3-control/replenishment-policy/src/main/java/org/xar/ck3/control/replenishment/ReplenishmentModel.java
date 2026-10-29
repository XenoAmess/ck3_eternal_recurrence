package org.xar.ck3.control.replenishment;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

/** No game, source-reading, clock, writer, or transport authority. */
public final class ReplenishmentModel {
    private ReplenishmentModel() {}

    public enum RecordStatus { AVAILABLE, UNAVAILABLE }
    public enum CoverageStatus { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum ChunkStatus { UNOBSERVED, AVAILABLE, UNAVAILABLE, CONFLICTING_OBSERVATIONS }

    /** Missing and explicit null are retained separately even though the legacy output merges them. */
    public sealed interface Snapshots permits MissingSnapshots, NullSnapshots, PublishedSnapshots {}
    public record MissingSnapshots() implements Snapshots {}
    public record NullSnapshots() implements Snapshots {}
    public record PublishedSnapshots(List<FullDataSnapshot> values) implements Snapshots {
        public PublishedSnapshots { values = List.copyOf(values); }
    }
    public record ArmyRow(int armyId, Snapshots snapshots) {
        public ArmyRow { Objects.requireNonNull(snapshots); }
    }
    public record FullDataSnapshot(int armyRegimentId, CoverageStatus status,
                                   Integer nativeDataRecordCount, String unavailableReason,
                                   List<FullDataRecord> records) {
        public FullDataSnapshot {
            Objects.requireNonNull(status);
            if (nativeDataRecordCount != null && nativeDataRecordCount < 0) {
                throw new IllegalArgumentException("native_data_record_count cannot be negative");
            }
            records = List.copyOf(records);
        }
    }
    public record FullDataRecord(RecordStatus status, String unavailableReason, int recordIndex,
                                 int persistentRegimentId, int chunkIndex, Integer maximumSoldiers,
                                 Integer effectiveCurrentSoldiers, Long preparedFractionRaw,
                                 int preparedFractionScale, Boolean nativeChunkCanReplenish) {
        public FullDataRecord { Objects.requireNonNull(status); }
    }
    public record ChunkCalculation(int sameInputQ, long effectiveDeficit,
                                   boolean nativeCoreChunkQualifies, Long wrappedProduct,
                                   Long selectedScaledNumerator) {
        public ChunkCalculation {
            if (effectiveDeficit < 0 || effectiveDeficit > 4_294_967_295L) {
                throw new IllegalArgumentException("effective deficit exceeds signed32 endpoint difference domain");
            }
            if (nativeCoreChunkQualifies != (wrappedProduct != null && selectedScaledNumerator != null)
                    || (wrappedProduct == null) != (selectedScaledNumerator == null)
                    || (!nativeCoreChunkQualifies && sameInputQ != 0)) {
                throw new IllegalArgumentException("chunk qualification and calculation fields differ");
            }
        }
    }
    public record ChunkInput(int maximumSoldiers, int effectiveCurrentSoldiers,
                             long preparedFractionRaw, boolean nativeChunkCanReplenish) {}
    public record ChunkObservation(int armyId, int armyRegimentId, int recordIndex,
                                   RecordStatus status, String unavailableReason,
                                   ChunkCalculation calculation) {
        public ChunkObservation {
            Objects.requireNonNull(status);
            if ((status == RecordStatus.AVAILABLE) != (calculation != null)) {
                throw new IllegalArgumentException("chunk observation status and calculation differ");
            }
        }
    }
    public record PersistentOutput(int persistentRegimentId, List<Integer> sameInputQByChunk,
                                   List<Long> effectiveDeficitByChunk, List<ChunkStatus> statusByChunk,
                                   List<List<ChunkObservation>> observationsByChunk,
                                   boolean allSevenObserved) {
        public PersistentOutput {
            if (sameInputQByChunk.size() != 7 || effectiveDeficitByChunk.size() != 7
                    || statusByChunk.size() != 7 || observationsByChunk.size() != 7) {
                throw new IllegalArgumentException("persistent output requires seven slots");
            }
            sameInputQByChunk = nullableCopy(sameInputQByChunk);
            effectiveDeficitByChunk = nullableCopy(effectiveDeficitByChunk);
            statusByChunk = List.copyOf(statusByChunk);
            observationsByChunk = observationsByChunk.stream().map(List::copyOf).toList();
            if (allSevenObserved != statusByChunk.stream().allMatch(status -> status == ChunkStatus.AVAILABLE)) {
                throw new IllegalArgumentException("all seven flag and slot coverage differ");
            }
            for (int ordinal = 0; ordinal < 7; ordinal++) {
                boolean available = statusByChunk.get(ordinal) == ChunkStatus.AVAILABLE;
                if (available != (sameInputQByChunk.get(ordinal) != null && effectiveDeficitByChunk.get(ordinal) != null)
                        || (!available && (sameInputQByChunk.get(ordinal) != null || effectiveDeficitByChunk.get(ordinal) != null))) {
                    throw new IllegalArgumentException("chunk coverage and nullable numeric slots differ");
                }
            }
        }
    }
    public record SourceSnapshot(int armyId, Integer armyRegimentId, CoverageStatus status,
                                 Integer nativeDataRecordCount, String unavailableReason) {
        public SourceSnapshot { Objects.requireNonNull(status); }
    }
    public record Projection(CoverageStatus status, List<SourceSnapshot> sourceSnapshots,
                             List<PersistentOutput> persistentOutputs) {
        public Projection {
            Objects.requireNonNull(status);
            sourceSnapshots = List.copyOf(sourceSnapshots);
            persistentOutputs = List.copyOf(persistentOutputs);
        }
    }
    private static <T> List<T> nullableCopy(List<T> values) {
        return Collections.unmodifiableList(new ArrayList<>(values));
    }
}
