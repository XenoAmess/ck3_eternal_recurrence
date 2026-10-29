package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/** Single source-ordered2303120 fold; Q arithmetic is the shared native cached kernel. */
public final class NativePropertyFold2303120 {
    private NativePropertyFold2303120() { }
    public record Block(List<Integer> keysU16, List<Long> valuesQ64) {
        public Block {
            keysU16 = List.copyOf(keysU16); valuesQ64 = List.copyOf(valuesQ64);
            if (keysU16.size() != valuesQ64.size() || keysU16.stream().anyMatch(key -> key < 0 || key > 65535))
                throw new IllegalArgumentException("parallel native ushort keys/signed64 values required");
        }
        public static Block empty() { return new Block(List.of(), List.of()); }
        public ObjectNode toJson() {
            ObjectNode result = BattleContextJson.object(); result.put("keys_count", keysU16.size()); result.put("values_count", valuesQ64.size());
            var keys = result.putArray("keys_u16"); keysU16.forEach(key -> keys.add(key.intValue()));
            var values = result.putArray("values_q64"); valuesQ64.forEach(value -> values.add(value.longValue()));
            result.putNull("reason"); return result;
        }
    }
    public sealed interface Update permits BulkCopy, SentinelSkip, Accumulation { ObjectNode toJson(); }
    public record BulkCopy(long weightQ64, boolean valuesScaled, int keyCount, int valueCount) implements Update {
        @Override public ObjectNode toJson() {
            ObjectNode row = BattleContextJson.object(); row.put("branch", "bulk_copy_including_FFFF");
            row.put("weight_q64", weightQ64); row.put("values_scaled", valuesScaled); row.put("key_count_i32", keyCount); row.put("value_count_i32", valueCount); return row;
        }
    }
    public record SentinelSkip(int sourcePropertyIndex, int keyU16, long sourceValueQ64, long weightQ64, long termQ64) implements Update {
        @Override public ObjectNode toJson() {
            ObjectNode row = term(sourcePropertyIndex, keyU16, sourceValueQ64, weightQ64, termQ64);
            row.put("branch", "FFFF_skip_after_term_computation"); return row;
        }
    }
    public enum AccumulationBranch { KEY_INSERT_PARALLEL_ZERO, EXISTING_KEY_ADD }
    public record Accumulation(int sourcePropertyIndex, int keyU16, long sourceValueQ64, long weightQ64,
            long termQ64, AccumulationBranch branch, int position, long beforeQ64, long afterQ64, int keyCount, int valueCount) implements Update {
        public Accumulation { Objects.requireNonNull(branch); }
        @Override public ObjectNode toJson() {
            ObjectNode row = term(sourcePropertyIndex, keyU16, sourceValueQ64, weightQ64, termQ64);
            row.put("branch", branch == AccumulationBranch.KEY_INSERT_PARALLEL_ZERO ? "key_insert_parallel_zero" : "existing_key_add");
            row.put("position", position); row.put("aggregate_before_q64", beforeQ64); row.put("aggregate_after_q64", afterQ64);
            row.put("key_count_i32", keyCount); row.put("value_count_i32", valueCount); return row;
        }
    }
    public record Result(Block block, List<Update> updates) {
        public Result { Objects.requireNonNull(block); updates = List.copyOf(updates); }
    }
    public static Result fold(Block destination, Block source, long weightQ64) {
        Objects.requireNonNull(destination); Objects.requireNonNull(source);
        List<Integer> keys = new ArrayList<>(destination.keysU16()); List<Long> values = new ArrayList<>(destination.valuesQ64());
        List<Update> updates = new ArrayList<>();
        if (keys.isEmpty()) {
            keys.addAll(source.keysU16());
            for (long value : source.valuesQ64()) values.add(weightQ64 == 100000L ? value : BattleRecipientArithmetic.cachedFixedMultiplyQ64(value, weightQ64));
            updates.add(new BulkCopy(weightQ64, weightQ64 != 100000L, keys.size(), values.size()));
        } else for (int index = 0; index < source.keysU16().size(); index++) {
            int key = source.keysU16().get(index); long value = source.valuesQ64().get(index);
            long term = BattleRecipientArithmetic.cachedFixedMultiplyQ64(value, weightQ64);
            if (key == 65535) { updates.add(new SentinelSkip(index, key, value, weightQ64, term)); continue; }
            int position = lowerBound(keys, key); AccumulationBranch branch;
            if (position == keys.size() || keys.get(position) != key) {
                keys.add(position, key); values.add(position, 0L); branch = AccumulationBranch.KEY_INSERT_PARALLEL_ZERO;
            } else branch = AccumulationBranch.EXISTING_KEY_ADD;
            long before = values.get(position), after = before + term; values.set(position, after);
            updates.add(new Accumulation(index, key, value, weightQ64, term, branch, position, before, after, keys.size(), values.size()));
        }
        return new Result(new Block(keys, values), updates);
    }
    private static int lowerBound(List<Integer> keys, int key) {
        int low = 0, high = keys.size();
        while (low < high) { int middle = low + (high - low) / 2; if (keys.get(middle) < key) low = middle + 1; else high = middle; }
        return low;
    }
    private static ObjectNode term(int index, int key, long source, long weight, long term) {
        ObjectNode row = BattleContextJson.object(); row.put("source_property_index", index); row.put("key_u16", key);
        row.put("source_value_q64", source); row.put("weight_q64", weight); row.put("term_q64", term); return row;
    }
}
