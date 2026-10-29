package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.BattleContextJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.BattlePersonLateWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import java.util.Set;

/** Exact original following2921350 numeric source contract; no native writes. */
public final class BattlePersonProvinceCodec {
    private BattlePersonProvinceCodec() { }
    public static final String FIELD = "following_2921350";
    public static final String COLD_REASON = "tier_default_2560620_result";
    private static final BigInteger PROV_MAGIC = BigInteger.valueOf(0x50726F76L);
    private record Visit(int root, Integer parent, BigInteger requested) { }
    private record Walk(ArrayNode rows, List<Integer> collected, boolean complete) { }
    public record TierInput(OptionalInt count, Optional<List<Long>> thresholds, OptionalLong operand) {
        public TierInput {
            Objects.requireNonNull(count); Objects.requireNonNull(thresholds); Objects.requireNonNull(operand);
            thresholds = thresholds.map(List::copyOf);
        }
    }

    /** Entry used by the single Late facade. Null is a real optional leaf. */
    public static JsonNode normalize(JsonNode raw, String field) {
        if (nil(raw)) return com.fasterxml.jackson.databind.node.NullNode.instance;
        ObjectNode out = start(raw, field, "character_id", "character_identity", "source_scope",
                "title_source", "title_walk", "provinces", "manager");
        out.set("character_id", number(raw.get("character_id"), field + ".character_id", 32, false, false));
        texts(raw, out, field, "character_identity", "source_scope");
        require(is(out.get("source_scope"), "held_current_native_inputs"), field, "held-current inputs cannot be renamed as fresh stage observation");
        ObjectNode titles = titleSource(raw.get("title_source"), field + ".title_source");
        out.set("title_source", titles);
        Walk walk = titleWalk(raw.get("title_walk"), field + ".title_walk", titles);
        out.set("title_walk", walk.rows());
        JsonNode rawProvinces = array(raw.get("provinces"), field + ".provinces", false, (value, name) -> value);
        require(rawProvinces.size() <= walk.collected().size(), field, "Province rows exceed collected full Title pointers");
        ArrayNode provinces = list();
        for (int i = 0; i < rawProvinces.size(); i++)
            provinces.add(province(rawProvinces.get(i), field + ".provinces[" + i + "]", i, walk.collected().get(i), walk.rows()));
        out.set("provinces", provinces);
        JsonNode managerRaw = raw.get("manager");
        ObjectNode manager = start(managerRaw, field + ".manager", "loaded", "identity", "group_count_raw_i32");
        texts(managerRaw, manager, field + ".manager", "identity");
        bools(managerRaw, manager, field + ".manager", "loaded");
        nums(managerRaw, manager, field + ".manager", 32, false, "group_count_raw_i32");
        BigInteger groups = integer(manager.get("group_count_raw_i32"));
        boolean managerComplete = yes(manager.get("loaded")) && !nil(manager.get("identity")) && groups != null && groups.signum() >= 0;
        if (Boolean.FALSE.equals(booleanValue(manager.get("loaded"))))
            require(allNull(manager, "identity", "group_count_raw_i32"), field, "null manager cannot supply numeric group dimension");
        ready(manager, managerComplete, field + ".manager"); out.set("manager", manager);
        boolean complete = walk.complete() && provinces.size() == walk.collected().size()
                && yes(manager.get("ready")) && !nil(out.get("character_identity"));
        for (JsonNode p : provinces) {
            JsonNode steps = p.get("steps");
            complete &= nil(p.get("reason")) && noReasons(steps) && !steps.isEmpty()
                    && !nil(steps.get(steps.size() - 1).get("tier_raw_i32"))
                    && !eq(steps.get(steps.size() - 1).get("tier_raw_i32"), 2)
                    && !nil(p.get("province_identity")) && !nil(p.get("admitted"));
            if (yes(p.get("admitted"))) {
                BigInteger n = integer(p.get("source_count_raw"));
                complete &= !nil(p.get("full_id_u32")) && n != null && n.signum() >= 0 && !nil(p.get("source_ids_u32"))
                        && n.equals(BigInteger.valueOf(p.get("sources").size()));
                for (JsonNode source : p.get("sources")) {
                    BigInteger group = integer(source.get("group_index_raw_i32"));
                    complete &= nil(source.get("reason")) && !nil(source.get("selection")) && !nil(source.get("object_identity"))
                            && !nil(source.get("definition_identity")) && group != null && groups != null
                            && group.signum() >= 0 && group.compareTo(groups) < 0
                            && yes(source.get("map").get("ready")) && yes(source.get("tiers").get("ready"));
                }
            }
        }
        ready(out, complete, field); return out;
    }

    private static ObjectNode row(JsonNode value, String field, String... fields) {
        String[] keys = Arrays.copyOf(fields, fields.length + 1); keys[fields.length] = "reason";
        shape(value, field, keys); ObjectNode out = object();
        out.set("reason", text(value.get("reason"), field + ".reason", true, true)); return out;
    }
    private static boolean idsComplete(JsonNode count, JsonNode present, JsonNode ids, String field) {
        BigInteger n = integer(count);
        if (n == null || n.signum() < 0) {
            require(nil(ids), field, "missing/negative count cannot become an empty stream"); return false;
        }
        if (n.signum() == 0) {
            require(nil(present) && ids.isArray() && ids.isEmpty(), field, "zero count must avoid undemanded array reads"); return true;
        }
        if (!nil(ids)) require(n.equals(BigInteger.valueOf(ids.size())), field, "IDs disagree with full signed count");
        return yes(present) && !nil(ids);
    }
    private static boolean resolution(ObjectNode out, String field) {
        String selected = string(out.get("selection"));
        require(selected == null || Set.of("registry_full_id", "native_fallback").contains(selected), field, "invalid actual full-ID resolution");
        if ("registry_full_id".equals(selected))
            require(!nil(out.get("requested_full_id_u32")) && Objects.equals(integer(out.get("selected_full_id_u32")), integer(out.get("requested_full_id_u32"))),
                    field, "full-generation comparator disagrees");
        else require(nil(out.get("selected_full_id_u32")), field, "fallback contains indexed selected ID");
        return selected != null;
    }
    private static ObjectNode titleSource(JsonNode raw, String field) {
        ObjectNode out = start(raw, field, "carrier_present", "selection", "header_identity", "count_raw", "array_present", "full_ids_u32");
        texts(raw, out, field, "selection", "header_identity"); bools(raw, out, field, "carrier_present", "array_present");
        nums(raw, out, field, 32, false, "count_raw");
        out.set("full_ids_u32", numbers(raw.get("full_ids_u32"), field + ".full_ids_u32", 32, true, true, false));
        String expected = yes(out.get("carrier_present")) ? "current_1c0_1e0"
                : Boolean.FALSE.equals(booleanValue(out.get("carrier_present"))) ? "actual_default_5459c88" : null;
        require(Objects.equals(string(out.get("selection")), expected), field, "current/default Title header selection differs");
        boolean complete = idsComplete(out.get("count_raw"), out.get("array_present"), out.get("full_ids_u32"), field);
        ready(out, complete && !nil(out.get("header_identity")) && expected != null, field); return out;
    }
    private static Walk titleWalk(JsonNode values, String field, ObjectNode source) {
        JsonNode input = array(values, field, false, (value, name) -> value); ArrayDeque<Visit> pending = new ArrayDeque<>();
        JsonNode roots = source.get("full_ids_u32");
        if (!nil(roots)) for (int i = roots.size() - 1; i >= 0; i--) pending.addLast(new Visit(i, null, integer(roots.get(i))));
        Set<String> seen = new HashSet<>(); ArrayNode rows = list(); List<Integer> collected = new ArrayList<>();
        boolean complete = yes(source.get("ready"));
        for (int i = 0; i < input.size(); i++) {
            JsonNode raw = input.get(i); String name = field + "[" + i + "]";
            ObjectNode out = row(raw, name, "native_index", "root_index", "parent_index", "requested_full_id_u32", "selection",
                    "selected_full_id_u32", "title_identity", "definition_identity", "tier_raw_i32", "children_count_raw",
                    "children_array_present", "child_ids_u32", "collected");
            out.set("native_index", number(raw.get("native_index"), name + ".native_index", 32, false, false));
            out.set("root_index", number(raw.get("root_index"), name + ".root_index", 32, false, false));
            nums(raw, out, name, 32, false, "parent_index", "tier_raw_i32", "children_count_raw");
            nums(raw, out, name, 32, true, "requested_full_id_u32", "selected_full_id_u32");
            texts(raw, out, name, "selection", "title_identity", "definition_identity");
            bools(raw, out, name, "children_array_present", "collected");
            out.set("child_ids_u32", numbers(raw.get("child_ids_u32"), name + ".child_ids_u32", 32, true, true, false));
            require(eq(out.get("native_index"), i) && !pending.isEmpty() && complete, name, "rows must retain actual demanded DFS prefix");
            Visit next = pending.removeLast();
            require(eq(out.get("root_index"), next.root())
                    && Objects.equals(integer(out.get("parent_index")), next.parent() == null ? null : BigInteger.valueOf(next.parent()))
                    && Objects.equals(integer(out.get("requested_full_id_u32")), next.requested()), name, "DFS occurrence/order differs");
            boolean resolved = resolution(out, name); BigInteger tier = integer(out.get("tier_raw_i32"));
            String identity = string(out.get("title_identity")); Boolean expected = null;
            boolean rowComplete = resolved && identity != null && !nil(out.get("definition_identity")) && tier != null;
            if (rowComplete) {
                if (tier.compareTo(BigInteger.ONE) > 0) {
                    rowComplete = idsComplete(out.get("children_count_raw"), out.get("children_array_present"), out.get("child_ids_u32"), name);
                    if (rowComplete) for (int child = out.get("child_ids_u32").size() - 1; child >= 0; child--)
                        pending.addLast(new Visit(next.root(), i, integer(out.get("child_ids_u32").get(child))));
                    expected = false;
                } else {
                    require(allNull(out, "children_count_raw", "children_array_present", "child_ids_u32"), name, "non-parent has undemanded children");
                    expected = BigInteger.ONE.equals(tier) && !seen.contains(identity);
                    if (BigInteger.ONE.equals(tier)) seen.add(identity);
                    if (expected) collected.add(i);
                }
            }
            require(Objects.equals(booleanValue(out.get("collected")), expected), name, "first full-pointer Title dedup differs");
            complete = complete && rowComplete && nil(out.get("reason")); rows.add(out);
        }
        return new Walk(rows, List.copyOf(collected), complete && pending.isEmpty());
    }

    /** Native FNV-1a consumes the four little-endian full-ID bytes, including generation. */
    public static long fnv1a(long fullId) {
        require(fullId >= 0 && fullId <= 0xffff_ffffL, FIELD, "unsigned32 full ID required");
        long value = 0x811c9dc5L;
        for (int shift = 0; shift < 32; shift += 8) value = ((value ^ ((fullId >>> shift) & 255L)) * 0x1000193L) & 0xffff_ffffL;
        return value;
    }
    public static OptionalInt tierIndex(TierInput input) {
        Objects.requireNonNull(input);
        if (input.count().isEmpty() || input.operand().isEmpty()) return OptionalInt.empty();
        int count = input.count().getAsInt();
        if (count <= 0) return OptionalInt.of(count - 1);
        if (input.thresholds().isEmpty()) return OptionalInt.empty();
        List<Long> thresholds = input.thresholds().orElseThrow(); long operand = input.operand().getAsLong();
        for (int i = 0; i < thresholds.size(); i++) if (operand < thresholds.get(i)) return OptionalInt.of(i - 1);
        return thresholds.size() == count ? OptionalInt.of(count - 1) : OptionalInt.empty();
    }
    private static ObjectNode map(JsonNode raw, String field, BigInteger provinceId) {
        ObjectNode out = start(raw, field, "data_identity", "mask_raw_i32", "overflow_raw_u8", "probes", "found", "operand_q64");
        texts(raw, out, field, "data_identity"); nums(raw, out, field, 32, false, "mask_raw_i32");
        nums(raw, out, field, 8, true, "overflow_raw_u8"); nums(raw, out, field, 64, false, "operand_q64");
        bools(raw, out, field, "found");
        BigInteger mask = integer(out.get("mask_raw_i32")), overflow = integer(out.get("overflow_raw_u8"));
        BigInteger bucket = mask == null ? null : wrap(BigInteger.valueOf(fnv1a(provinceId.longValueExact())), 32).and(mask);
        BigInteger end = mask == null || overflow == null ? null : mask.add(BigInteger.ONE).add(overflow);
        JsonNode probes = array(raw.get("probes"), field + ".probes", false, (value, name) -> value);
        ArrayNode rows = list(); Boolean found = null; BigInteger operand = null;
        for (int i = 0; i < probes.size(); i++) {
            JsonNode item = probes.get(i); String name = field + ".probes[" + i + "]";
            ObjectNode probe = row(item, name, "native_index", "bucket_index_i64", "distance_raw_u8", "key_raw_u32", "operand_q64");
            probe.set("native_index", number(item.get("native_index"), name + ".native_index", 32, false, false));
            nums(item, probe, name, 64, false, "bucket_index_i64", "operand_q64");
            nums(item, probe, name, 8, true, "distance_raw_u8"); nums(item, probe, name, 32, true, "key_raw_u32");
            require(bucket != null && found == null && eq(probe.get("native_index"), i)
                    && bucket.add(BigInteger.valueOf(i)).equals(integer(probe.get("bucket_index_i64"))), name, "physical signed FNV probe order differs");
            BigInteger distance = integer(probe.get("distance_raw_u8")); int expectedDistance = (i + 1) & 255;
            if (distance != null && distance.intValueExact() < expectedDistance) {
                require(allNull(probe, "key_raw_u32", "operand_q64"), name, "terminating distance has undemanded key/payload");
                found = false; operand = BigInteger.ZERO;
            } else if (distance != null && provinceId.equals(integer(probe.get("key_raw_u32")))) {
                found = end == null ? null : !integer(probe.get("bucket_index_i64")).equals(end);
                operand = Boolean.TRUE.equals(found) ? integer(probe.get("operand_q64")) : Boolean.FALSE.equals(found) ? BigInteger.ZERO : null;
                if (Boolean.FALSE.equals(found)) require(nil(probe.get("operand_q64")), name, "end bucket has undemanded payload");
            } else require(nil(probe.get("operand_q64")), name, "unmatched bucket has undemanded operand");
            if (!nil(probe.get("reason")) || distance == null
                    || distance.intValueExact() >= expectedDistance && nil(probe.get("key_raw_u32")))
                require(i == probes.size() - 1, name, "probe continues after unread input");
            rows.add(probe);
        }
        out.set("probes", rows);
        require(Objects.equals(booleanValue(out.get("found")), found) && Objects.equals(integer(out.get("operand_q64")), operand),
                field, "found/actual absent-zero operand differs");
        ready(out, !nil(out.get("data_identity")) && mask != null && overflow != null && found != null && operand != null && noReasons(rows), field);
        return out;
    }
    private static ObjectNode tiers(JsonNode raw, String field, JsonNode operand) {
        ObjectNode out = start(raw, field, "count_raw_i32", "data_identity", "thresholds_q64", "selected_index_raw_i32", "selection", "default_guard_raw_i32", "pc");
        nums(raw, out, field, 32, false, "count_raw_i32", "selected_index_raw_i32", "default_guard_raw_i32");
        texts(raw, out, field, "data_identity", "selection");
        out.set("thresholds_q64", numbers(raw.get("thresholds_q64"), field + ".thresholds_q64", 64, false, true, false));
        out.set("pc", pc(raw.get("pc"), field + ".pc"));
        BigInteger count = integer(out.get("count_raw_i32")); JsonNode thresholds = out.get("thresholds_q64");
        if (count != null && count.signum() <= 0)
            require(thresholds.isArray() && thresholds.isEmpty() && nil(out.get("data_identity")), field, "nonpositive count has undemanded tier data");
        List<Long> values = nil(thresholds) ? null : new ArrayList<>();
        if (values != null) for (JsonNode value : thresholds) values.add(integer(value).longValueExact());
        if (count != null && count.signum() > 0 && values != null) {
            require(values.size() <= count.intValueExact(), field, "thresholds exceed stored count");
            for (int i = 0; i < values.size(); i++) if (!nil(operand) && integer(operand).compareTo(BigInteger.valueOf(values.get(i))) < 0) {
                require(i == values.size() - 1, field, "threshold scan continued after strict greater"); break;
            }
        }
        OptionalInt index = tierIndex(new TierInput(count == null ? OptionalInt.empty() : OptionalInt.of(count.intValueExact()),
                Optional.ofNullable(values), nil(operand) ? OptionalLong.empty() : OptionalLong.of(integer(operand).longValueExact())));
        require(Objects.equals(integer(out.get("selected_index_raw_i32")), index.isPresent() ? BigInteger.valueOf(index.getAsInt()) : null),
                field, "ordinal-minus-one/equality tier selection differs");
        String selection = null;
        if (index.isPresent()) {
            if (index.getAsInt() >= 0 && index.getAsInt() < count.intValueExact()) {
                selection = "indexed_tier"; require(nil(out.get("default_guard_raw_i32")), field, "valid tier has undemanded fallback guard");
            } else if (!nil(out.get("default_guard_raw_i32")))
                selection = eq(out.get("default_guard_raw_i32"), 0) || eq(out.get("default_guard_raw_i32"), -1)
                        ? "cold_default_5d65b00" : "initialized_default_5d65b00";
        }
        require(Objects.equals(string(out.get("selection")), selection), field, "selected tier/default route differs");
        if ("cold_default_5d65b00".equals(selection))
            require(is(out.get("reason"), COLD_REASON) && absentPc(out.get("pc")), field, "cold fallback cannot fabricate empty observed PC");
        boolean selectorComplete = index.isPresent() && (count.signum() <= 0 || !nil(out.get("data_identity")));
        ready(out, selectorComplete && ("indexed_tier".equals(selection) || "initialized_default_5d65b00".equals(selection))
                && pcReady(out.get("pc")), field); return out;
    }
    private static ObjectNode source(JsonNode raw, String field, int index, JsonNode requested, BigInteger provinceId) {
        ObjectNode out = row(raw, field, "native_index", "requested_full_id_u32", "selection", "selected_full_id_u32",
                "object_identity", "definition_identity", "group_index_raw_i32", "map", "tiers");
        out.set("native_index", number(raw.get("native_index"), field + ".native_index", 32, false, false));
        nums(raw, out, field, 32, true, "requested_full_id_u32", "selected_full_id_u32");
        nums(raw, out, field, 32, false, "group_index_raw_i32"); texts(raw, out, field, "selection", "object_identity", "definition_identity");
        require(eq(out.get("native_index"), index) && Objects.equals(integer(out.get("requested_full_id_u32")), integer(requested)),
                field, "ordered full-DWORD occurrence differs");
        resolution(out, field);
        ObjectNode map = map(raw.get("map"), field + ".map", provinceId); out.set("map", map);
        out.set("tiers", tiers(raw.get("tiers"), field + ".tiers", yes(map.get("ready")) ? map.get("operand_q64") : com.fasterxml.jackson.databind.node.NullNode.instance));
        return out;
    }
    private static ObjectNode province(JsonNode raw, String field, int index, int titleIndex, ArrayNode walk) {
        ObjectNode out = row(raw, field, "native_index", "title_walk_index", "steps", "province_identity", "magic_u32",
                "admitted", "full_id_u32", "source_count_raw", "source_array_present", "source_ids_u32", "sources");
        for (String key : List.of("native_index", "title_walk_index")) out.set(key, number(raw.get(key), field + "." + key, 32, false, false));
        require(eq(out.get("native_index"), index) && eq(out.get("title_walk_index"), titleIndex), field, "collected Title/Province occurrence order differs");
        texts(raw, out, field, "province_identity"); nums(raw, out, field, 32, true, "magic_u32", "full_id_u32");
        nums(raw, out, field, 32, false, "source_count_raw"); bools(raw, out, field, "admitted", "source_array_present");
        out.set("source_ids_u32", numbers(raw.get("source_ids_u32"), field + ".source_ids_u32", 32, true, true, false));
        JsonNode rawSteps = array(raw.get("steps"), field + ".steps", false, (value, name) -> value);
        ArrayNode steps = list(); boolean done = false; BigInteger previous = null;
        for (int i = 0; i < rawSteps.size(); i++) {
            JsonNode item = rawSteps.get(i); String name = field + ".steps[" + i + "]";
            ObjectNode step = row(item, name, "native_index", "title_identity", "definition_identity", "tier_raw_i32",
                    "requested_full_id_u32", "selection", "selected_full_id_u32", "first_child_count_raw", "first_child_array_present", "first_child_full_id_u32");
            step.set("native_index", number(item.get("native_index"), name + ".native_index", 32, false, false));
            texts(item, step, name, "title_identity", "definition_identity", "selection");
            nums(item, step, name, 32, false, "tier_raw_i32", "first_child_count_raw");
            nums(item, step, name, 32, true, "requested_full_id_u32", "selected_full_id_u32", "first_child_full_id_u32");
            bools(item, step, name, "first_child_array_present");
            require(eq(step.get("native_index"), i) && !done && Objects.equals(integer(step.get("requested_full_id_u32")), previous),
                    name, "230F900 first-child trace differs");
            if (i == 0) require(Objects.equals(string(step.get("title_identity")), string(walk.get(titleIndex).get("title_identity")))
                    && allNull(step, "selection", "selected_full_id_u32"), name, "230F900 starts on different collected pointer");
            else resolution(step, name);
            if (eq(step.get("tier_raw_i32"), 2)) {
                if (eq(step.get("first_child_count_raw"), 0))
                    require(eq(step.get("first_child_full_id_u32"), 0xffff_ffffL) && nil(step.get("first_child_array_present")),
                            name, "empty first-child header must resolve full FFFFFFFF");
                previous = integer(step.get("first_child_full_id_u32"));
            } else if (!nil(step.get("tier_raw_i32"))) {
                done = true; require(allNull(step, "first_child_count_raw", "first_child_array_present", "first_child_full_id_u32"),
                        name, "non-tier2 has undemanded first child");
            }
            if (!nil(step.get("reason"))) require(i == rawSteps.size() - 1, name, "Province selection continues after unread input");
            steps.add(step);
        }
        out.set("steps", steps);
        Boolean admitted = nil(out.get("magic_u32")) ? null : PROV_MAGIC.equals(integer(out.get("magic_u32")));
        require(Objects.equals(booleanValue(out.get("admitted")), admitted), field, "actual Prov magic admission differs");
        JsonNode ids = out.get("source_ids_u32");
        JsonNode rawSources = array(raw.get("sources"), field + ".sources", false, (value, name) -> value);
        if (Boolean.FALSE.equals(admitted)) require(allNull(out, "full_id_u32", "source_count_raw", "source_array_present", "source_ids_u32")
                && rawSources.isEmpty(), field, "rejected Province has undemanded numeric sources");
        else if (Boolean.TRUE.equals(admitted)) idsComplete(out.get("source_count_raw"), out.get("source_array_present"), ids, field);
        require(rawSources.isEmpty() || !nil(ids) && !nil(out.get("full_id_u32")), field, "sources lack ordered IDs/Province full ID");
        require(nil(ids) || rawSources.size() <= ids.size(), field, "sources exceed ordered full IDs");
        ArrayNode sources = list();
        for (int i = 0; i < rawSources.size(); i++) sources.add(source(rawSources.get(i), field + ".sources[" + i + "]", i, ids.get(i), integer(out.get("full_id_u32"))));
        out.set("sources", sources); return out;
    }
    private static boolean yes(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static boolean noReasons(JsonNode rows) { for (JsonNode row : rows) if (!nil(row.get("reason"))) return false; return true; }
}
