package org.xar.ck3.control.wave2.military.armyselector;

import static org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.*;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Existing selector summary consumes the single shared ordered physical producer and DATA refresh closure. */
public final class OrderedRefill {
    private OrderedRefill() {}
    private record Key(int persistent, int chunk) {}
    private record Pair(boolean ready, Integer current, Integer maximum) {}

    public static Projection project(StrengthRow row) {
        OrderedInputs inputs = row.ordered();
        if (inputs == null) return unavailable("scoped_ordered_refill_inputs_v1");
        if (inputs.subjectArmyId() != row.armyId() || row.nativeArmyId() == null
                || inputs.subjectNativeArmyId() != row.nativeArmyId()) return unavailable("same_capture_subject_identity");
        if (inputs.occurrenceCount() == null) return unavailable("native_persistent_occurrence_roster");
        OrderedRefillPhysicalCore.Result physicalResult = OrderedRefillPhysicalCore.project(inputs);
        Map<Integer, List<Chunk>> physical = physicalResult.physical();
        Set<Integer> failed = new LinkedHashSet<>(physicalResult.failedPersistentIds());
        Set<String> missing = new LinkedHashSet<>(physicalResult.missingInputs());
        Map<Key, Chunk> projected = new LinkedHashMap<>();
        for (var entry : physical.entrySet()) if (!failed.contains(entry.getKey()) && entry.getValue().size() == 7) {
            for (Chunk chunk : entry.getValue()) projected.put(new Key(entry.getKey(), chunk.physicalIndex()), chunk);
        }
        List<DataSnapshot> data = row.data();
        if (data == null || row.regimentCount() == null || data.size() != row.regimentCount()) missing.add("complete_requested_army_DATA_roster");
        else {
            boolean missingPhysical = false, incompleteData = false;
            for (DataSnapshot snapshot : data) {
                if (snapshot.records() != null) for (DataRecord record : snapshot.records()) {
                    if (!physical.containsKey(record.persistentId())) missingPhysical = true;
                }
                if (snapshot.status() != Coverage.AVAILABLE) incompleteData = true;
            }
            if (missingPhysical) missing.add("all_requested_DATA_persistent_inputs");
            if (incompleteData) missing.add("complete_requested_army_DATA");
        }
        boolean orderedReady = missing.isEmpty();
        boolean refreshReady = false;
        Integer current = null, maximum = null;
        if (inputs.refreshCount() == null) missing.add("native_army_refresh_occurrence_roster");
        else if (data != null) {
            List<Pair> strengths = new ArrayList<>();
            if (!inputs.refreshIndices().isEmpty()) {
                for (int ignored : inputs.refreshIndices()) {
                    strengths.clear();
                    List<RaisedRegimentRefresh.PhysicalChunk> values = projected.entrySet().stream().map(entry ->
                            new RaisedRegimentRefresh.PhysicalChunk(entry.getKey().persistent(), entry.getKey().chunk(),
                                    entry.getValue().current(), entry.getValue().maximum())).toList();
                    for (DataSnapshot snapshot : data) {
                        RaisedRegimentRefresh.Result refreshed = RaisedRegimentRefresh.project(snapshot, values);
                        strengths.add(new Pair(refreshed.ready(), refreshed.current(), refreshed.maximum()));
                    }
                }
            } else if (row.observedStrengths() != null) {
                for (Strength strength : row.observedStrengths()) strengths.add(new Pair(true, strength.current(), strength.maximum()));
            }
            refreshReady = row.regimentCount() != null && strengths.size() == row.regimentCount() && strengths.stream().allMatch(Pair::ready);
            if (refreshReady) {
                int c = 0, m = 0;
                for (Pair pair : strengths) { c += pair.current(); m += pair.maximum(); }
                current = c; maximum = m;
            } else missing.add("requested_raised_current_maximum_refresh_inputs");
        }
        return new Projection(orderedReady, refreshReady, current, maximum, List.copyOf(missing));
    }
    private static Projection unavailable(String reason) { return new Projection(false, false, null, null, List.of(reason)); }
}
