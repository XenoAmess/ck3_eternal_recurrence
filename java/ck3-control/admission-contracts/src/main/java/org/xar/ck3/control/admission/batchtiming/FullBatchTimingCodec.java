package org.xar.ck3.control.admission.batchtiming;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Centralized JSON projection for the legacy Python-only receipt; no integer coercion. */
public final class FullBatchTimingCodec {
    private static final ObjectMapper WRITER = new ObjectMapper();
    private static final Set<String> SUMMARY_FIELDS = Set.of("schema", "control_sequence", "source", "interval_source",
            "tools", "row_count", "duplicate_rows_ignored", "invalid_elapsed_rows", "elapsed_seconds_sum",
            "interval_union_seconds", "overlap_seconds", "zero_day_rows_included", "error_rows_included",
            "native_only", "CPU_attribution");
    private static final Set<String> WALL_FIELDS = Set.of("full_timing_control_sequence", "full_timing_clock",
            "full_timing_origin", "full_submit_monotonic_ns", "full_receipt_validated_monotonic_ns", "full_wall_ns");

    private FullBatchTimingCodec() { }

    public record Input(BigInteger controlSequence, List<FullBatchTiming.Observation> observations) {
        public Input {
            FullBatchTiming.positive(controlSequence, "positive FULL sequence required");
            observations = List.copyOf(observations);
            StrictJson.require(observations.size() <= 10_000, "bounded FULL observation list required");
        }
    }

    public static Input decodeInput(byte[] bytes) {
        ObjectNode root = StrictJson.object(StrictJson.parse(bytes), Set.of("control_sequence", "observations"));
        JsonNode rows = root.get("observations");
        StrictJson.require(rows.isArray() && rows.size() <= 10_000, "bounded observations array required");
        List<FullBatchTiming.Observation> values = new ArrayList<>();
        for (JsonNode value : rows) { values.add(decodeObservation(value)); }
        return new Input(positiveInteger(root.get("control_sequence")), values);
    }

    public static FullBatchTiming.Summary evaluate(Input input) {
        FullBatchTiming.Accumulator accumulator = new FullBatchTiming.Accumulator(input.controlSequence());
        for (FullBatchTiming.Observation observation : input.observations()) { accumulator.record(observation); }
        return accumulator.summary();
    }

    /** Optional metrics remain non-blocking: malformed timing cannot reject a validated business receipt. */
    public static FullBatchTiming.Combined composeOptionalSummary(byte[] summaryBytes, FullBatchTiming.Wall wall) {
        java.util.Objects.requireNonNull(wall, "wall");
        try {
            return FullBatchTiming.combine(decodeSummary(summaryBytes), wall);
        } catch (ContractViolationException invalidMetrics) {
            return new FullBatchTiming.Combined(wall, java.util.Optional.empty(), null);
        }
    }

    public static FullBatchTiming.Observation decodeObservation(JsonNode value) {
        ObjectNode node = StrictJson.object(value, Set.of("request", "response_request", "elapsed_seconds",
                "monotonic_start_seconds", "result_is_error", "client_error_present"));
        return new FullBatchTiming.Observation(decodeRequest(node.get("request")),
                decodeRequest(node.get("response_request")), nullableNumber(node.get("elapsed_seconds")),
                nullableNumber(node.get("monotonic_start_seconds")), bool(node.get("result_is_error")),
                bool(node.get("client_error_present")));
    }

    public static FullBatchTiming.Request decodeRequest(JsonNode value) {
        ObjectNode node = StrictJson.object(value, Set.of("sequence", "tool", "arguments"));
        return new FullBatchTiming.Request(positiveInteger(node.get("sequence")),
                StrictJson.text(node.get("tool")), node.get("arguments"));
    }

    public static FullBatchTiming.Summary decodeSummary(byte[] bytes) {
        return decodeSummary(StrictJson.parse(bytes));
    }

    public static FullBatchTiming.Summary decodeSummary(JsonNode value) {
        ObjectNode node = StrictJson.object(value, SUMMARY_FIELDS);
        literal(node.get("schema"), FullBatchTiming.SCHEMA);
        literal(node.get("source"), FullBatchTiming.SOURCE);
        literal(node.get("interval_source"), FullBatchTiming.INTERVAL_SOURCE);
        StrictJson.trueValue(node.get("zero_day_rows_included"));
        StrictJson.trueValue(node.get("error_rows_included"));
        StrictJson.require(!bool(node.get("native_only")), "row wall is not native-only timing");
        StrictJson.require(node.get("CPU_attribution").isNull(), "CPU attribution must remain unknown");
        ObjectNode tools = StrictJson.object(node.get("tools"), Set.of("AUTO", "MET", "SEM", "SAVE"));
        EnumMap<FullBatchTiming.Tool, FullBatchTiming.ToolTotals> values = new EnumMap<>(FullBatchTiming.Tool.class);
        for (FullBatchTiming.Tool tool : FullBatchTiming.Tool.values()) {
            ObjectNode item = StrictJson.object(tools.get(tool.name()),
                    Set.of("count", "elapsed_seconds_sum", "error_count", "client_error_count"));
            values.put(tool, new FullBatchTiming.ToolTotals(count(item.get("count")),
                    number(item.get("elapsed_seconds_sum")), count(item.get("error_count")),
                    count(item.get("client_error_count"))));
        }
        return new FullBatchTiming.Summary(positiveInteger(node.get("control_sequence")), values,
                count(node.get("row_count")), count(node.get("duplicate_rows_ignored")),
                count(node.get("invalid_elapsed_rows")), number(node.get("elapsed_seconds_sum")),
                nullableNumber(node.get("interval_union_seconds")), nullableNumber(node.get("overlap_seconds")));
    }

    public static FullBatchTiming.Wall decodeWall(byte[] bytes) { return decodeWall(StrictJson.parse(bytes)); }
    public static FullBatchTiming.Wall decodeWall(JsonNode value) {
        ObjectNode node = StrictJson.object(value, WALL_FIELDS);
        literal(node.get("full_timing_clock"), "monotonic_ns");
        String origin = StrictJson.text(node.get("full_timing_origin"));
        FullBatchTiming.Origin state;
        if (origin.equals(FullBatchTiming.Origin.NEW_SUBMISSION_SAME_PRODUCER.wire())) {
            state = FullBatchTiming.Origin.NEW_SUBMISSION_SAME_PRODUCER;
        } else {
            StrictJson.require(origin.equals(FullBatchTiming.Origin.SUBMISSION_NOT_OBSERVED.wire()),
                    "known timing origin required");
            state = FullBatchTiming.Origin.SUBMISSION_NOT_OBSERVED;
        }
        return new FullBatchTiming.Wall(positiveInteger(node.get("full_timing_control_sequence")), state,
                nullableInteger(node.get("full_submit_monotonic_ns")),
                nullableInteger(node.get("full_receipt_validated_monotonic_ns")),
                nullableInteger(node.get("full_wall_ns")));
    }

    public static ObjectNode summaryNode(FullBatchTiming.Summary value) {
        ObjectNode node = StrictJson.object();
        node.put("schema", FullBatchTiming.SCHEMA);
        node.put("control_sequence", value.controlSequence());
        node.put("source", FullBatchTiming.SOURCE);
        node.put("interval_source", FullBatchTiming.INTERVAL_SOURCE);
        ObjectNode tools = node.putObject("tools");
        for (FullBatchTiming.Tool tool : FullBatchTiming.Tool.values()) {
            FullBatchTiming.ToolTotals total = value.tools().get(tool);
            ObjectNode item = tools.putObject(tool.name());
            item.put("count", total.count());
            item.put("elapsed_seconds_sum", total.elapsedSecondsSum());
            item.put("error_count", total.errorCount());
            item.put("client_error_count", total.clientErrorCount());
        }
        node.put("row_count", value.rowCount());
        node.put("duplicate_rows_ignored", value.duplicateRowsIgnored());
        node.put("invalid_elapsed_rows", value.invalidElapsedRows());
        node.put("elapsed_seconds_sum", value.elapsedSecondsSum());
        nullable(node, "interval_union_seconds", value.intervalUnionSeconds());
        nullable(node, "overlap_seconds", value.overlapSeconds());
        node.put("zero_day_rows_included", true);
        node.put("error_rows_included", true);
        node.put("native_only", false);
        node.putNull("CPU_attribution");
        return node;
    }

    public static ObjectNode wallNode(FullBatchTiming.Wall value) {
        ObjectNode node = StrictJson.object();
        node.put("full_timing_control_sequence", value.controlSequence());
        node.put("full_timing_clock", "monotonic_ns");
        node.put("full_timing_origin", value.origin().wire());
        node.put("full_submit_monotonic_ns", value.submitMonotonicNs());
        node.put("full_receipt_validated_monotonic_ns", value.receiptValidatedMonotonicNs());
        node.put("full_wall_ns", value.wallNs());
        return node;
    }

    public static ObjectNode combinedNode(FullBatchTiming.Combined value) {
        ObjectNode node = wallNode(value.wall());
        if (value.summary().isPresent()) {
            node.set("full_rpc_rows_v1", summaryNode(value.summary().orElseThrow()));
            nullable(node, "full_wall_minus_rpc_union_seconds", value.wallMinusRpcUnionSeconds());
            node.putNull("full_wall_residual_attribution");
        }
        return node;
    }

    public static byte[] encodeSummary(FullBatchTiming.Summary value) { return encode(summaryNode(value)); }
    public static byte[] encodeWall(FullBatchTiming.Wall value) { return encode(wallNode(value)); }
    public static byte[] encodeCombined(FullBatchTiming.Combined value) { return encode(combinedNode(value)); }

    private static byte[] encode(JsonNode node) {
        try {
            byte[] bytes = WRITER.writeValueAsBytes(node);
            StrictJson.require(bytes.length <= StrictJson.INPUT_MAX_BYTES, "bounded timing receipt required");
            return bytes;
        } catch (JsonProcessingException error) {
            throw new ContractViolationException("cannot encode timing receipt", error);
        }
    }
    private static BigInteger positiveInteger(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber() && node.bigIntegerValue().signum() > 0,
                "positive exact integer required; no bool, float or string");
        return node.bigIntegerValue();
    }
    private static BigInteger nullableInteger(JsonNode node) {
        StrictJson.require(node != null, "required nullable integer missing");
        if (node.isNull()) { return null; }
        StrictJson.require(node.isIntegralNumber() && node.bigIntegerValue().signum() >= 0,
                "nonnegative exact monotonic integer required");
        return node.bigIntegerValue();
    }
    private static int count(JsonNode node) { return (int) StrictJson.integer(node, 0, 10_000); }
    private static boolean bool(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "exact boolean required");
        return node.booleanValue();
    }
    private static double number(JsonNode node) {
        StrictJson.require(node != null && node.isNumber() && Double.isFinite(node.doubleValue()),
                "finite numeric token required");
        return node.doubleValue();
    }
    private static Double nullableNumber(JsonNode node) {
        StrictJson.require(node != null, "required nullable numeric field missing");
        return node.isNull() ? null : number(node);
    }
    private static void literal(JsonNode node, String expected) {
        StrictJson.require(StrictJson.text(node).equals(expected), "exact timing literal required");
    }
    private static void nullable(ObjectNode node, String name, Double value) {
        if (value == null) { node.putNull(name); } else { node.put(name, value); }
    }
}
