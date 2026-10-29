package org.xar.ck3.control.admission.batchtiming;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Pure existing-row accounting. It obtains no timestamps and grants no game credit. */
public final class FullBatchTiming {
    public static final String SCHEMA = "xar.ck3.full-existing-rpc-rows/v1";
    public static final String SOURCE = "existing per-row wall: normal Queue includes model_dump; resident row ends before model_dump; excludes later response write/relay/classifier";
    public static final String INTERVAL_SOURCE = "existing Queue monotonic start plus existing elapsed_seconds; no new row clock";
    public static final int INTERVAL_LIMIT = 2_048;

    private FullBatchTiming() { }

    public enum Tool {
        AUTO("ck3_auto_turn"), MET("root_current_runtime_metrics"),
        SEM("ck3_take_semantic_snapshot_private_v1"), SAVE("ck3_save_checkpoint");

        private final String requestName;
        Tool(String requestName) { this.requestName = requestName; }
        public String requestName() { return requestName; }
        public static Optional<Tool> fromRequestName(String value) {
            for (Tool tool : values()) {
                if (tool.requestName.equals(value)) { return Optional.of(tool); }
            }
            return Optional.empty();
        }
    }

    /** Arguments are an opaque, defensively copied JSON object, compared before accounting. */
    public record Request(BigInteger sequence, String tool, JsonNode arguments) {
        public Request {
            positive(sequence, "positive request sequence required");
            StrictJson.text(tool);
            StrictJson.require(arguments != null && arguments.isObject(), "request arguments object required");
            validateJson(arguments, 0, new int[] {0});
            arguments = arguments.deepCopy();
        }
        @Override public JsonNode arguments() { return arguments.deepCopy(); }
    }

    /** Nullable elapsed/start represent an observed invalid scalar, never an invented zero. */
    public record Observation(Request request, Request responseRequest, Double elapsedSeconds,
                              Double monotonicStartSeconds, boolean resultIsError,
                              boolean clientErrorPresent) {
        public Observation {
            Objects.requireNonNull(request, "request");
            Objects.requireNonNull(responseRequest, "responseRequest");
        }
    }

    public record ToolTotals(int count, double elapsedSecondsSum, int errorCount, int clientErrorCount) {
        public ToolTotals {
            StrictJson.require(count >= 0 && errorCount >= 0 && clientErrorCount >= 0,
                    "nonnegative tool counts required");
            StrictJson.require(errorCount <= count && clientErrorCount <= errorCount,
                    "tool errors must be contained in observed rows");
            finiteNonnegative(elapsedSecondsSum, "finite nonnegative elapsed sum required");
        }
    }

    public record Summary(BigInteger controlSequence, Map<Tool, ToolTotals> tools,
                          int rowCount, int duplicateRowsIgnored, int invalidElapsedRows,
                          double elapsedSecondsSum, Double intervalUnionSeconds, Double overlapSeconds) {
        public Summary {
            positive(controlSequence, "positive FULL sequence required");
            Objects.requireNonNull(tools, "tools");
            StrictJson.require(tools.keySet().equals(EnumSet.allOf(Tool.class)), "all four tool totals required");
            tools = Map.copyOf(tools);
            StrictJson.require(rowCount >= 0 && duplicateRowsIgnored >= 0
                    && invalidElapsedRows >= 0 && invalidElapsedRows <= rowCount, "nonnegative row counts required");
            StrictJson.require(tools.values().stream().mapToLong(ToolTotals::count).sum() == rowCount,
                    "tool count sum must equal row count");
            finiteNonnegative(elapsedSecondsSum, "finite elapsed total required");
            double total = 0.0;
            for (Tool tool : Tool.values()) { total += tools.get(tool).elapsedSecondsSum(); }
            StrictJson.require(Double.compare(total, elapsedSecondsSum) == 0, "tool elapsed sum differs");
            StrictJson.require((intervalUnionSeconds == null) == (overlapSeconds == null),
                    "unavailable union requires null overlap");
            if (intervalUnionSeconds != null) {
                finiteNonnegative(intervalUnionSeconds, "finite union required");
                finiteNonnegative(overlapSeconds, "finite overlap required");
                StrictJson.require(invalidElapsedRows == 0, "invalid elapsed prevents a union");
                StrictJson.require(Double.compare(Math.max(0.0, elapsedSecondsSum - intervalUnionSeconds),
                        overlapSeconds) == 0, "overlap must derive from sum minus union");
            }
        }
    }

    public enum Origin {
        NEW_SUBMISSION_SAME_PRODUCER("new_submission_same_producer"),
        SUBMISSION_NOT_OBSERVED("submission_not_observed");
        private final String wire;
        Origin(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** Nanoseconds are monotonic process-local values, never UTC or transferable origins. */
    public record Wall(BigInteger controlSequence, Origin origin, BigInteger submitMonotonicNs,
                       BigInteger receiptValidatedMonotonicNs, BigInteger wallNs) {
        public Wall {
            positive(controlSequence, "positive FULL sequence required");
            Objects.requireNonNull(origin, "origin");
            if (origin == Origin.SUBMISSION_NOT_OBSERVED) {
                StrictJson.require(submitMonotonicNs == null && receiptValidatedMonotonicNs == null
                        && wallNs == null, "unobserved submission must retain null clock fields");
            } else {
                nonnegative(submitMonotonicNs, "observed monotonic start required");
                nonnegative(receiptValidatedMonotonicNs, "observed validated receipt endpoint required");
                nonnegative(wallNs, "observed wall duration required");
                StrictJson.require(receiptValidatedMonotonicNs.subtract(submitMonotonicNs).equals(wallNs),
                        "wall must equal monotonic endpoint difference");
            }
        }
        public static Wall unobserved(BigInteger sequence) {
            return new Wall(sequence, Origin.SUBMISSION_NOT_OBSERVED, null, null, null);
        }
    }

    public record Combined(Wall wall, Optional<Summary> summary, Double wallMinusRpcUnionSeconds) {
        public Combined {
            Objects.requireNonNull(wall, "wall");
            Objects.requireNonNull(summary, "summary");
            StrictJson.require(summary.isEmpty() || wall.controlSequence().equals(summary.orElseThrow().controlSequence()),
                    "RPC summary must bind the same FULL sequence");
            Double expectedResidual = null;
            if (summary.isPresent() && wall.wallNs() != null
                    && summary.orElseThrow().intervalUnionSeconds() != null) {
                double seconds = wall.wallNs().doubleValue() / 1e9;
                double union = summary.orElseThrow().intervalUnionSeconds();
                if (Double.isFinite(seconds) && seconds >= union) { expectedResidual = seconds - union; }
            }
            StrictJson.require(Objects.equals(expectedResidual, wallMinusRpcUnionSeconds),
                    "residual must derive from this FULL and union, or remain null");
            if (wallMinusRpcUnionSeconds != null) {
                finiteNonnegative(wallMinusRpcUnionSeconds, "finite nonnegative residual required");
            }
        }
    }

    public static Combined combine(Summary summary, Wall wall) {
        Objects.requireNonNull(summary, "summary");
        Objects.requireNonNull(wall, "wall");
        if (!summary.controlSequence().equals(wall.controlSequence())) {
            return new Combined(wall, Optional.empty(), null);
        }
        if (wall.wallNs() != null && !Double.isFinite(wall.wallNs().doubleValue())) {
            // Python's original ns / 1e9 conversion raises at this boundary and keeps wall fields only.
            return new Combined(wall, Optional.empty(), null);
        }
        Double residual = null;
        if (wall.wallNs() != null && summary.intervalUnionSeconds() != null) {
            double seconds = wall.wallNs().doubleValue() / 1e9;
            if (Double.isFinite(seconds) && seconds >= summary.intervalUnionSeconds()) {
                residual = seconds - summary.intervalUnionSeconds();
            }
        }
        return new Combined(wall, Optional.of(summary), residual);
    }

    /** One accumulator per FULL. Sequence consumption is local accounting, not request execution. */
    public static final class Accumulator {
        private final BigInteger controlSequence;
        private final Set<BigInteger> seen = new HashSet<>();
        private final EnumMap<Tool, MutableTotals> tools = new EnumMap<>(Tool.class);
        private List<Interval> intervals = new ArrayList<>();
        private boolean unionAvailable = true;
        private int duplicates;
        private int invalidElapsed;

        public Accumulator(BigInteger controlSequence) {
            positive(controlSequence, "positive FULL sequence required");
            this.controlSequence = controlSequence;
            for (Tool tool : Tool.values()) { tools.put(tool, new MutableTotals()); }
        }

        public void record(Observation observation) {
            Objects.requireNonNull(observation, "observation");
            Optional<Tool> category = Tool.fromRequestName(observation.request().tool());
            if (category.isEmpty() || !observation.request().equals(observation.responseRequest())) { return; }
            if (!seen.add(observation.request().sequence())) { duplicates++; return; }
            MutableTotals item = tools.get(category.orElseThrow());
            item.count++;
            if (observation.clientErrorPresent()) { item.clientErrors++; }
            if (observation.clientErrorPresent() || observation.resultIsError()) { item.errors++; }
            Double elapsed = observation.elapsedSeconds();
            if (!valid(elapsed) || elapsed < 0) {
                invalidElapsed++;
                unionAvailable = false;
                return;
            }
            item.elapsed += elapsed;
            // Match Python binary64 arithmetic and explicitly reject aggregate overflow.
            finiteNonnegative(item.elapsed, "elapsed aggregate overflow");
            Double startValue = observation.monotonicStartSeconds();
            if (!valid(startValue) || startValue < 0 || !Double.isFinite(startValue + elapsed)) {
                unionAvailable = false;
                return;
            }
            double start = startValue;
            double end = start + elapsed;
            List<Interval> merged = new ArrayList<>();
            for (Interval interval : intervals) {
                if (interval.right() < start) {
                    merged.add(interval);
                } else if (end < interval.left()) {
                    merged.add(new Interval(start, end));
                    start = interval.left();
                    end = interval.right();
                } else {
                    start = Math.min(start, interval.left());
                    end = Math.max(end, interval.right());
                }
            }
            merged.add(new Interval(start, end));
            if (merged.size() <= INTERVAL_LIMIT) {
                intervals = merged;
            } else {
                unionAvailable = false;
                intervals = new ArrayList<>();
            }
        }

        public Summary summary() {
            EnumMap<Tool, ToolTotals> result = new EnumMap<>(Tool.class);
            double elapsed = 0.0;
            for (Tool tool : Tool.values()) {
                MutableTotals item = tools.get(tool);
                result.put(tool, new ToolTotals(item.count, item.elapsed, item.errors, item.clientErrors));
                elapsed += item.elapsed;
            }
            Double union = null;
            if (unionAvailable) {
                union = 0.0;
                for (Interval interval : intervals) { union += interval.right() - interval.left(); }
            }
            return new Summary(controlSequence, result, seen.size(), duplicates, invalidElapsed, elapsed,
                    union, union == null ? null : Math.max(0.0, elapsed - union));
        }
    }

    private record Interval(double left, double right) { }
    private static final class MutableTotals {
        private int count;
        private double elapsed;
        private int errors;
        private int clientErrors;
    }

    static void positive(BigInteger value, String message) {
        StrictJson.require(value != null && value.signum() > 0, message);
    }
    static void nonnegative(BigInteger value, String message) {
        StrictJson.require(value != null && value.signum() >= 0, message);
    }
    private static boolean valid(Double value) { return value != null && Double.isFinite(value); }
    private static void validateJson(JsonNode value, int depth, int[] visited) {
        StrictJson.require(value != null && depth <= 32 && ++visited[0] <= 10_000,
                "bounded request arguments JSON required");
        if (value.isObject()) {
            value.properties().forEach(field -> {
                if (!field.getKey().isEmpty()) { StrictJson.text(field.getKey()); }
                validateJson(field.getValue(), depth + 1, visited);
            });
        } else if (value.isArray()) {
            for (JsonNode item : value) { validateJson(item, depth + 1, visited); }
        } else if (value.isTextual()) {
            if (!value.textValue().isEmpty()) { StrictJson.text(value.textValue()); }
        } else if (value.isNumber()) {
            StrictJson.require(value.isIntegralNumber() || Double.isFinite(value.doubleValue()),
                    "finite request argument number required");
        } else {
            StrictJson.require(value.isBoolean() || value.isNull(), "JSON argument scalar required");
        }
    }
    private static void finiteNonnegative(double value, String message) {
        StrictJson.require(Double.isFinite(value) && value >= 0, message);
    }
}
