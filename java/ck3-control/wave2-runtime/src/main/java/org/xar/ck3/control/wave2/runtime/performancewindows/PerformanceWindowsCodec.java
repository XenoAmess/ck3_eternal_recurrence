package org.xar.ck3.control.wave2.runtime.performancewindows;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Strict declared projection of four extensible sealed evidence containers, never runtime bodies. */
public final class PerformanceWindowsCodec {
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private PerformanceWindowsCodec() { }

    public static HistoricalPerformanceWindows.Inputs decode(HistoricalPerformanceWindows.Context context,
                                                             List<HistoricalPerformanceWindows.SourceInput> sources) {
        StrictJson.require(sources != null && sources.size() == 4, "exactly four source roles required");
        EnumMap<HistoricalPerformanceWindows.SourceRole, JsonNode> data = new EnumMap<>(HistoricalPerformanceWindows.SourceRole.class);
        EnumMap<HistoricalPerformanceWindows.SourceRole, HistoricalPerformanceWindows.SourceReference> refs =
                new EnumMap<>(HistoricalPerformanceWindows.SourceRole.class);
        for (HistoricalPerformanceWindows.SourceInput input : sources) {
            StrictJson.require(input != null && !data.containsKey(input.role()), "unique source roles required");
            byte[] bytes = input.bytes();
            data.put(input.role(), parse(bytes));
            refs.put(input.role(), new HistoricalPerformanceWindows.SourceReference(input.role().relativePath(),
                    bytes.length, sha256(bytes)));
        }
        List<HistoricalPerformanceWindows.SourceReference> ordered = new ArrayList<>();
        for (HistoricalPerformanceWindows.SourceRole role : HistoricalPerformanceWindows.SourceRole.values()) {
            StrictJson.require(data.containsKey(role), "all four source roles required"); ordered.add(refs.get(role));
        }
        ObjectNode p49 = object(data.get(HistoricalPerformanceWindows.SourceRole.P49_SETTLED));
        ObjectNode settled = object(required(p49, "5104-5165"));
        ObjectNode groupSource = object(required(settled, "auto_by_group"));
        LinkedHashMap<String, HistoricalPerformanceWindows.AutoGroup> groups = new LinkedHashMap<>();
        groupSource.properties().forEach(entry -> {
            StrictJson.text(entry.getKey()); ObjectNode group = object(entry.getValue());
            groups.put(entry.getKey(), new HistoricalPerformanceWindows.AutoGroup(integer(required(group, "count")),
                    seconds(required(group, "auto_seconds")), integer(required(group, "game_days")), group));
        });
        HistoricalPerformanceWindows.SettledWindow window = new HistoricalPerformanceWindows.SettledWindow(machine(p49),
                integer(required(settled, "game_days")), seconds(required(settled, "wall_seconds")),
                integer(required(settled, "turns")), integer(required(settled, "zero_date_turns")),
                seconds(required(object(required(settled, "rpc_elapsed_by_tool_seconds")), "ck3_auto_turn")),
                seconds(required(settled, "rpc_busy_union_seconds")), number(required(settled, "unattributed_gap_seconds")), groups);
        ObjectNode stages = object(data.get(HistoricalPerformanceWindows.SourceRole.P49_STAGES));
        JsonNode stageList = required(stages, "stages");
        StrictJson.require(stageList.isArray(), "stages array required");
        Map<String, HistoricalPerformanceWindows.StageStats> statistics = new HashMap<>();
        for (JsonNode value : stageList) {
            ObjectNode item = object(value); String name = StrictJson.text(required(item, "stage"));
            StrictJson.require(!statistics.containsKey(name), "duplicate stage identity rejected");
            statistics.put(name, new HistoricalPerformanceWindows.StageStats(integer(required(item, "count")),
                    seconds(required(item, "nested_elapsed_sum_seconds")), seconds(required(item, "max_seconds"))));
        }
        ObjectNode waits = object(required(stages, "public_change_wait_by_calendar_delta"));
        ObjectNode nested = object(required(stages, "nested_within_plan"));
        HistoricalPerformanceWindows.StageSlice stageSlice = new HistoricalPerformanceWindows.StageSlice(machine(stages),
                StrictJson.text(required(stages, "time_lower")), StrictJson.text(required(stages, "time_upper")),
                seconds(required(object(required(waits, "date_changed")), "elapsed_seconds")),
                seconds(required(object(required(waits, "same_date")), "elapsed_seconds")),
                seconds(required(object(required(stages, "plan_intervals")), "unique_wall_seconds")),
                seconds(required(object(required(nested, "native_wait_or_pipe")), "unique_intersection_seconds")),
                seconds(required(object(required(nested, "semantic_snapshot")), "unique_intersection_seconds")),
                stage(statistics, "driver.full_state_persistence"), stage(statistics, "driver.full_state_temp_stream_write"),
                stage(statistics, "driver.full_state_json_serialization"));
        ObjectNode p63 = object(data.get(HistoricalPerformanceWindows.SourceRole.P63));
        ObjectNode performance = object(required(p63, "performance"));
        return new HistoricalPerformanceWindows.Inputs(context, ordered, window, stageSlice,
                StrictJson.text(required(p63, "machine_id")), rateWindow(required(performance, "R6_window")),
                rateWindow(required(performance, "R5_distinct_window")));
    }

    public static ObjectNode toJson(HistoricalPerformanceWindows.Projection projection) {
        HistoricalPerformanceWindows.Inputs input = projection.inputs();
        HistoricalPerformanceWindows.SettledWindow settled = input.settled();
        HistoricalPerformanceWindows.StageSlice stages = input.stages();
        ObjectNode result = JSON.createObjectNode();
        result.put("schema", HistoricalPerformanceWindows.SCHEMA);
        result.put("machine_id", input.context().machineId()); result.put("observed_utc", input.context().observedUtc());
        result.put("scope", HistoricalPerformanceWindows.SCOPE);
        var sourceArray = result.putArray("sources");
        for (HistoricalPerformanceWindows.SourceReference ref : input.sources()) {
            ObjectNode source = sourceArray.addObject(); source.put("path", ref.path());
            source.put("bytes", ref.bytes()); source.put("sha256", ref.sha256());
        }
        ObjectNode history = result.putObject("historical_window");
        ObjectNode machines = history.putObject("source_machine_ids");
        putMachine(machines, "P49_settled", settled.machine()); putMachine(machines, "P49_stages", stages.machine());
        machines.put("P63", input.p63MachineId());
        history.put("P63_same_as_executing_machine", input.p63MachineId().equals(input.context().machineId()));
        history.put("stage_lower_source_clock", stages.lowerSourceClock()); history.put("stage_upper_source_clock", stages.upperSourceClock());
        history.put("P49_machine_identity_note", "small P49 source projections omit machine_id; ownership not inferred from paths or associated P63");
        ObjectNode p49 = result.putObject("P49_settled");
        p49.put("game_days", settled.gameDays()); p49.put("wall_seconds", settled.wallSeconds());
        p49.put("turns", settled.turns()); p49.put("zero_date_turns", settled.zeroDateTurns());
        p49.put("zero_date_turn_fraction", projection.zeroDateTurnFraction());
        p49.put("zero_date_auto_seconds", projection.zeroDateAutoSeconds());
        p49.put("progress_auto_seconds", projection.progressAutoSeconds());
        ObjectNode zero = p49.putObject("zero_date_groups");
        projection.zeroDateGroups().forEach((name, value) -> zero.set(name, value.sourceValue()));
        p49.put("rpc_busy_union_seconds", settled.rpcBusyUnionSeconds()); p49.put("unattributed_gap_seconds", settled.unattributedGapSeconds());
        p49.put("date_changed_wait_seconds", stages.dateChangedWaitSeconds()); p49.put("same_date_wait_seconds", stages.sameDateWaitSeconds());
        p49.put("plan_unique_wall_seconds", stages.planUniqueWallSeconds());
        p49.put("native_wait_within_plan_seconds", stages.nativeWaitWithinPlanSeconds());
        p49.put("semantic_snapshot_within_plan_seconds", stages.semanticSnapshotWithinPlanSeconds());
        ObjectNode persistence = p49.putObject("persistence");
        persistence.put("count", stages.persistence().count()); persistence.put("sum_seconds", stages.persistence().sumSeconds());
        persistence.put("max_seconds", stages.persistence().maxSeconds());
        persistence.put("stream_write_sum_seconds", stages.stream().sumSeconds());
        persistence.put("stream_fraction_of_persistence", projection.streamFractionOfPersistence());
        persistence.put("serialization_sum_seconds", stages.serialization().sumSeconds());
        ObjectNode p63 = result.putObject("P63"); p63.set("R6_window", input.r6().sourceValue());
        p63.set("R5_window", input.r5().sourceValue()); p63.put("same_state_AB", false);
        result.put("seconds_level_hotspot", "21 full-state writes total 10.448259s, 9.954374s in stream.write; JSON serialization is not this window's persistence bottleneck");
        ObjectNode candidate = result.putObject("source_candidate");
        candidate.put("path", "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py");
        candidate.putArray("functions").add("_combat_simulation_inputs_cache_for_snapshot").add("_combat_simulation_inputs_v3_cache_for_snapshot");
        candidate.put("issue", "existing frame equality rejection occurs after expensive full payload normalization");
        candidate.put("proposal", "reject the same stale frame before payload normalization; keep all current-frame normalization and result guards");
        candidate.putNull("predicted_seconds_saved"); candidate.put("new_cache", false); candidate.put("live_accepted", false);
        result.putArray("limits")
                .add("Nested stages are overlapping categories and must not be summed into wall time.")
                .add("Zero-date queries can be necessary business observations; the fraction is not a removal target.")
                .add("P63 R5/R6 are distinct states; their rates are not a controlled speedup ratio.")
                .add("P67 87.814s query lacks native/normalization/clone/archive/MCP component timings; no seconds are assigned to a component.")
                .add("Actual game's date wait cannot be eliminated by skipping legal observation or changing war policy.");
        result.put("new_game_or_native_calls", 0); result.put("runtime_bodies_read", 0);
        ObjectNode storage = result.putObject("storage"); storage.put("policy_version", "1.0.0");
        storage.put("source_max_bytes", HistoricalPerformanceWindows.SOURCE_MAX_BYTES);
        storage.put("output_limit_bytes", HistoricalPerformanceWindows.SOURCE_MAX_BYTES); storage.put("deletions", 0);
        storage.put("record_review_at_utc", input.context().reviewUtc());
        return result;
    }

    public static byte[] encode(HistoricalPerformanceWindows.Projection projection) {
        try {
            byte[] bytes = JSON.writeValueAsBytes(toJson(projection));
            StrictJson.require(bytes.length <= HistoricalPerformanceWindows.SOURCE_MAX_BYTES, "bounded sealed projection output required");
            return bytes;
        } catch (JsonProcessingException error) { throw new ContractViolationException("cannot encode sealed projection", error); }
    }

    public static JsonNode parse(byte[] bytes) {
        StrictJson.require(bytes != null && bytes.length > 0 && bytes.length <= HistoricalPerformanceWindows.SOURCE_MAX_BYTES,
                "bounded sealed JSON source required");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode node = JSON.readTree(text); StrictJson.require(node != null, "JSON source required"); return node;
        } catch (IOException error) { throw new ContractViolationException("invalid UTF-8 or duplicate source JSON", error); }
    }

    private static HistoricalPerformanceWindows.CopiedRateWindow rateWindow(JsonNode value) {
        ObjectNode node = object(value);
        seconds(required(node, "actual_days")); seconds(required(node, "wall_seconds"));
        endpoint(required(node, "first")); endpoint(required(node, "last"));
        return HistoricalPerformanceWindows.copiedRateWindow(node);
    }
    private static void endpoint(JsonNode value) {
        ObjectNode node = object(value);
        for (String field : List.of("sequence", "date_raw", "native_revision", "revision", "actor_character_id", "driver_state_bytes")) {
            integer(required(node, field));
        }
        for (String optional : List.of("connection_generation", "army_strengths_query_sequence")) {
            if (node.has(optional)) { integer(node.get(optional)); }
        }
        StrictJson.utc(StrictJson.text(required(node, "utc"))); StrictJson.text(required(node, "episode_run_id"));
        seconds(required(node, "elapsed_seconds"));
    }
    private static HistoricalPerformanceWindows.StageStats stage(Map<String, HistoricalPerformanceWindows.StageStats> map, String key) {
        StrictJson.require(map.containsKey(key), "required stage missing: " + key); return map.get(key);
    }
    private static HistoricalPerformanceWindows.MachineMarker machine(ObjectNode value) {
        if (!value.has("machine_id")) { return new HistoricalPerformanceWindows.MissingMachine(); }
        if (value.get("machine_id").isNull()) { return new HistoricalPerformanceWindows.NullMachine(); }
        return new HistoricalPerformanceWindows.NamedMachine(StrictJson.text(value.get("machine_id")));
    }
    private static void putMachine(ObjectNode target, String key, HistoricalPerformanceWindows.MachineMarker marker) {
        switch (marker) {
            case HistoricalPerformanceWindows.NullMachine ignored -> target.putNull(key);
            case HistoricalPerformanceWindows.NamedMachine named -> target.put(key, named.value());
            case HistoricalPerformanceWindows.MissingMachine ignored -> target.put(key, "unknown");
        }
    }
    private static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "sealed JSON object required"); return (ObjectNode) value;
    }
    private static JsonNode required(ObjectNode value, String key) {
        StrictJson.require(value.has(key), "required sealed source field missing: " + key); return value.get(key);
    }
    private static BigInteger integer(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber(), "exact integer token required; no bool, float or string");
        BigInteger number = value.bigIntegerValue(); HistoricalPerformanceWindows.nonnegative(number); return number;
    }
    private static double number(JsonNode value) {
        StrictJson.require(value != null && value.isNumber() && Double.isFinite(value.doubleValue()), "finite numeric token required");
        return value.doubleValue();
    }
    private static double seconds(JsonNode value) { double result = number(value); HistoricalPerformanceWindows.seconds(result); return result; }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
