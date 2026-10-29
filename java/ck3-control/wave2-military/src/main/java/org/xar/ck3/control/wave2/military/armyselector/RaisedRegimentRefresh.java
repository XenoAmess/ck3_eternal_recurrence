package org.xar.ck3.control.wave2.military.armyselector;

import static org.xar.ck3.control.wave2.military.armyselector.ArmySelectorModel.*;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Shared exact signed32 current/max stores. Aliased DATA occurrences count repeatedly. */
public final class RaisedRegimentRefresh {
    private RaisedRegimentRefresh() {}
    public record PhysicalChunk(int persistentId, int chunkIndex, Integer current, Integer maximum) {}
    public record Contribution(int recordIndex, int persistentId, int chunkIndex, int physicalCurrent,
                               int effectiveCurrent, int maximum) {}
    public record Result(int regimentId, boolean ready, Integer current, Integer maximum,
                         Boolean characterOverride, boolean conditionalChunks,
                         List<String> missingInputs, List<Contribution> contributions) {
        public Result { missingInputs = List.copyOf(missingInputs); contributions = List.copyOf(contributions); }
        public boolean actualRefresh() { return false; }
    }
    private record Key(int persistent, int chunk) {}
    /** A null physical list means observed same-frame DATA; an empty list is an explicit empty replay. */
    public static Result project(DataSnapshot data, List<PhysicalChunk> physicalChunksAfter) {
        boolean conditional = physicalChunksAfter != null;
        if (data.lossWriterSkipped() == null) return missing(data, conditional, "native_2634880_character_predicate");
        if (data.lossWriterSkipped()) return new Result(data.regimentId(), true, 1, 1, true, conditional, List.of(), List.of());
        if (data.status() != Coverage.AVAILABLE || data.records() == null) return missing(data, conditional, "complete_available_DATA");
        Map<Key, PhysicalChunk> projected = new LinkedHashMap<>();
        if (conditional) for (PhysicalChunk chunk : physicalChunksAfter) projected.put(new Key(chunk.persistentId(), chunk.chunkIndex()), chunk);
        int current = 0, maximum = 0; List<Contribution> contributions = new ArrayList<>();
        for (DataRecord record : data.records()) {
            PhysicalChunk chunk = conditional ? projected.get(new Key(record.persistentId(), record.chunkIndex()))
                    : new PhysicalChunk(record.persistentId(), record.chunkIndex(), record.current(), record.maximum());
            if (chunk == null) return missing(data, conditional, "complete_projected_physical_chunks");
            if (chunk.current() == null || chunk.maximum() == null || record.state() == null) return missing(data, conditional, "complete_current_maximum_state");
            int contribution = record.state() == 3 && chunk.current() == 0 ? chunk.maximum() : chunk.current();
            current += contribution; maximum += chunk.maximum();
            contributions.add(new Contribution(record.recordIndex(), record.persistentId(), record.chunkIndex(), chunk.current(), contribution, chunk.maximum()));
        }
        return new Result(data.regimentId(), true, current, maximum, false, conditional, List.of(), contributions);
    }
    private static Result missing(DataSnapshot data, boolean conditional, String reason) {
        return new Result(data.regimentId(), false, null, null, null, conditional, List.of(reason), List.of());
    }
}
