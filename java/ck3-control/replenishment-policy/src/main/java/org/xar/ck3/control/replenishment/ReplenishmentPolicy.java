package org.xar.ck3.control.replenishment;

import static org.xar.ck3.control.replenishment.ReplenishmentModel.*;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Exact integer projection of observed operands at native RVA 0x262C9D0. */
public final class ReplenishmentPolicy {
    public static final int FRACTION_SCALE = 100_000;
    public static final int CHUNK_COUNT = 7;

    private ReplenishmentPolicy() {}

    /** Java overflow and division implement native low64, signed trunc-zero, and low32 store. */
    public static ChunkCalculation sameInputChunkQ(int maximumSoldiers, int effectiveCurrentSoldiers,
                                                   long preparedFractionRaw,
                                                   boolean nativeChunkCanReplenish) {
        long deficit = (long) maximumSoldiers - effectiveCurrentSoldiers;
        boolean qualifies = preparedFractionRaw > 0 && nativeChunkCanReplenish && deficit > 0;
        if (!qualifies) {
            return new ChunkCalculation(0, Math.max(deficit, 0), false, null, null);
        }
        long product = maximumSoldiers * preparedFractionRaw;
        long numerator = Math.min(product, deficit * FRACTION_SCALE);
        return new ChunkCalculation((int) (numerator / FRACTION_SCALE), deficit,
                true, product, numerator);
    }

    public static List<PersistentOutput> observedPersistentOutputs(List<ArmyRow> armyRows) {
        Map<Integer, List<List<ChunkObservation>>> groups = new LinkedHashMap<>();
        for (ArmyRow army : armyRows) {
            if (!(army.snapshots() instanceof PublishedSnapshots published)) {
                continue;
            }
            for (FullDataSnapshot snapshot : published.values()) {
                for (FullDataRecord record : snapshot.records()) {
                    int ordinal = record.chunkIndex();
                    if (record.persistentRegimentId() == -1 || ordinal < 0 || ordinal >= CHUNK_COUNT) {
                        continue;
                    }
                    List<List<ChunkObservation>> observations = groups.computeIfAbsent(
                            record.persistentRegimentId(), ignored -> emptyObservationSlots());
                    RecordStatus status = record.status();
                    String reason = record.unavailableReason();
                    ChunkCalculation calculation = null;
                    if (status == RecordStatus.AVAILABLE) {
                        try {
                            calculation = recordCalculation(record);
                        } catch (IllegalArgumentException failure) {
                            status = RecordStatus.UNAVAILABLE;
                            reason = failure.getMessage();
                        }
                    }
                    observations.get(ordinal).add(new ChunkObservation(army.armyId(),
                            snapshot.armyRegimentId(), record.recordIndex(), status, reason, calculation));
                }
            }
        }
        List<PersistentOutput> outputs = new ArrayList<>();
        for (Map.Entry<Integer, List<List<ChunkObservation>>> entry : groups.entrySet()) {
            List<Integer> quantities = new ArrayList<>(Collections.nCopies(CHUNK_COUNT, null));
            List<Long> deficits = new ArrayList<>(Collections.nCopies(CHUNK_COUNT, null));
            List<ChunkStatus> statuses = new ArrayList<>(Collections.nCopies(CHUNK_COUNT, ChunkStatus.UNOBSERVED));
            for (int ordinal = 0; ordinal < CHUNK_COUNT; ordinal++) {
                List<ChunkObservation> observations = entry.getValue().get(ordinal);
                if (observations.isEmpty()) continue;
                if (observations.stream().anyMatch(observation -> observation.calculation() == null)) {
                    statuses.set(ordinal, ChunkStatus.UNAVAILABLE);
                    continue;
                }
                ChunkCalculation first = observations.getFirst().calculation();
                if (observations.stream().anyMatch(observation -> !first.equals(observation.calculation()))) {
                    statuses.set(ordinal, ChunkStatus.CONFLICTING_OBSERVATIONS);
                    continue;
                }
                statuses.set(ordinal, ChunkStatus.AVAILABLE);
                quantities.set(ordinal, first.sameInputQ());
                deficits.set(ordinal, first.effectiveDeficit());
            }
            outputs.add(new PersistentOutput(entry.getKey(), quantities, deficits, statuses, entry.getValue(),
                    statuses.stream().allMatch(status -> status == ChunkStatus.AVAILABLE)));
        }
        return List.copyOf(outputs);
    }

    public static Projection projectObservedReplenishmentV1(List<ArmyRow> armyRows) {
        List<SourceSnapshot> snapshots = new ArrayList<>();
        for (ArmyRow army : armyRows) {
            if (army.snapshots() instanceof PublishedSnapshots published) {
                for (FullDataSnapshot snapshot : published.values()) {
                    snapshots.add(new SourceSnapshot(army.armyId(), snapshot.armyRegimentId(), snapshot.status(),
                            snapshot.nativeDataRecordCount(), snapshot.unavailableReason()));
                }
            } else {
                snapshots.add(new SourceSnapshot(army.armyId(), null, CoverageStatus.UNAVAILABLE, null,
                        "regiment_replenishment_records_v1_not_published"));
            }
        }
        List<PersistentOutput> outputs = observedPersistentOutputs(armyRows);
        boolean incomplete = snapshots.stream().anyMatch(snapshot -> snapshot.status() != CoverageStatus.AVAILABLE)
                || outputs.stream().anyMatch(output -> output.statusByChunk().stream().anyMatch(
                        status -> status == ChunkStatus.UNAVAILABLE || status == ChunkStatus.CONFLICTING_OBSERVATIONS));
        CoverageStatus status = CoverageStatus.AVAILABLE;
        if (incomplete) {
            status = snapshots.stream().anyMatch(snapshot -> snapshot.status() == CoverageStatus.AVAILABLE
                    || snapshot.status() == CoverageStatus.PARTIAL) ? CoverageStatus.PARTIAL : CoverageStatus.UNAVAILABLE;
        }
        return new Projection(status, snapshots, outputs);
    }

    private static List<List<ChunkObservation>> emptyObservationSlots() {
        List<List<ChunkObservation>> values = new ArrayList<>();
        for (int ordinal = 0; ordinal < CHUNK_COUNT; ordinal++) values.add(new ArrayList<>());
        return values;
    }

    private static ChunkCalculation recordCalculation(FullDataRecord record) {
        if (record.preparedFractionScale() != FRACTION_SCALE) {
            throw new IllegalArgumentException("prepared replenishment fraction scale must be 100000");
        }
        if (record.nativeChunkCanReplenish() == null) {
            throw new IllegalArgumentException("native_chunk_can_replenish must be bool");
        }
        if (record.maximumSoldiers() == null) {
            throw new IllegalArgumentException("maximum_soldiers must be signed int32");
        }
        if (record.effectiveCurrentSoldiers() == null) {
            throw new IllegalArgumentException("effective_current_soldiers must be signed int32");
        }
        if (record.preparedFractionRaw() == null) {
            throw new IllegalArgumentException("prepared_fraction_raw must be signed int64");
        }
        return sameInputChunkQ(record.maximumSoldiers(), record.effectiveCurrentSoldiers(),
                record.preparedFractionRaw(), record.nativeChunkCanReplenish());
    }
}
