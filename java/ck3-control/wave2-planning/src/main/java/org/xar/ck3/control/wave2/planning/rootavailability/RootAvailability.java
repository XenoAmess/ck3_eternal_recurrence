package org.xar.ck3.control.wave2.planning.rootavailability;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Read-only history recognition used by the existing M5 formal planner; never a new query or action. */
public final class RootAvailability {
    public static final String ROOT_QUERY_STEP = "query-campaign-root-context-v1";
    private RootAvailability() { }
    public enum Status { matching_completed_unavailable, not_observed }
    public enum IgnoredReason { unrelated_or_unsuccessful, unreadable_result, nonmatching_result, malformed_frame }
    public record Frame(BigInteger nativeRevision, BigInteger dateRaw) {
        public Frame {
            require(nativeRevision != null && nativeRevision.signum() > 0, "positive native revision required");
            require(dateRaw != null && dateRaw.signum() >= 0, "nonnegative native date required");
        }
    }
    public sealed interface HistoryRow permits Ignored, CompletedUnavailable { }
    public record Ignored(IgnoredReason reason) implements HistoryRow {
        public Ignored { Objects.requireNonNull(reason); }
    }
    public record CompletedUnavailable(BigInteger resultNativeRevision, BigInteger contextNativeRevision,
                                       BigInteger contextDateRaw) implements HistoryRow {
        public CompletedUnavailable {
            Objects.requireNonNull(resultNativeRevision); Objects.requireNonNull(contextNativeRevision); Objects.requireNonNull(contextDateRaw);
        }
        public boolean matches(Frame frame) {
            return resultNativeRevision.equals(frame.nativeRevision) && contextNativeRevision.equals(frame.nativeRevision)
                    && contextDateRaw.equals(frame.dateRaw);
        }
    }
    public record Request(Frame frame, List<HistoryRow> history) {
        public Request { Objects.requireNonNull(frame); history = List.copyOf(history); }
    }
    public record Result(Status status, int matchingHistoryIndex) {
        public Result {
            Objects.requireNonNull(status);
            require(status == Status.matching_completed_unavailable ? matchingHistoryIndex >= 0 : matchingHistoryIndex == -1, "matching history index/status");
        }
        public boolean sameFrameRootReturnedUnavailable() { return status == Status.matching_completed_unavailable; }
        public boolean formalActionReady() { return false; }
    }

    public static Result recognize(Request request) {
        Objects.requireNonNull(request);
        // Preserve the original reverse scan: a later nonmatching row does not erase an earlier matching unavailable read.
        for (int index = request.history.size() - 1; index >= 0; index--) {
            if (request.history.get(index) instanceof CompletedUnavailable receipt && receipt.matches(request.frame)) {
                return new Result(Status.matching_completed_unavailable, index);
            }
        }
        return new Result(Status.not_observed, -1);
    }

    public static Request decode(byte[] raw) {
        ObjectNode wrapper = StrictJson.object(StrictJson.parse(raw), Set.of("snapshot", "history"));
        ObjectNode snapshot = object(wrapper.get("snapshot"));
        Frame frame = new Frame(integer(snapshot.get("native_revision")), integer(snapshot.get("date_raw")));
        require(wrapper.get("history") instanceof ArrayNode, "history list required");
        List<HistoryRow> history = new ArrayList<>();
        for (JsonNode rawRow : wrapper.get("history")) { history.add(project(object(rawRow))); }
        return new Request(frame, history);
    }

    public static byte[] recognize(byte[] raw) {
        Result result = recognize(decode(raw)); ObjectNode output = StrictJson.object();
        output.put("policy", "g2-m5-same-frame-root-unavailable-history-v1"); output.put("status", result.status.name());
        output.put("same_frame_root_returned_unavailable", result.sameFrameRootReturnedUnavailable());
        if (result.matchingHistoryIndex < 0) { output.putNull("matching_history_index"); }
        else { output.put("matching_history_index", result.matchingHistoryIndex); }
        output.put("query_issued", false); output.putNull("selected_step"); output.put("formal_action_ready", false);
        return StrictJson.canonical(output);
    }

    private static HistoryRow project(ObjectNode row) {
        if (!textEquals(row.get("command"), ROOT_QUERY_STEP) || !isTrue(row.get("ok"))) {
            return new Ignored(IgnoredReason.unrelated_or_unsuccessful);
        }
        if (!(row.get("result") instanceof ObjectNode result)
                || !(result.get("campaign_root_context") instanceof ObjectNode context)) {
            return new Ignored(IgnoredReason.unreadable_result);
        }
        if (!textEquals(result.get("step"), ROOT_QUERY_STEP) || !isTrue(result.get("accepted"))
                || !textEquals(result.get("status"), "unavailable") || !textEquals(context.get("status"), "unavailable")) {
            return new Ignored(IgnoredReason.nonmatching_result);
        }
        JsonNode resultRevision = result.get("snapshot_revision"); JsonNode contextRevision = context.get("snapshot_revision");
        JsonNode date = context.get("date_raw");
        if (!isInteger(resultRevision) || !isInteger(contextRevision) || !isInteger(date)) {
            return new Ignored(IgnoredReason.malformed_frame);
        }
        return new CompletedUnavailable(resultRevision.bigIntegerValue(), contextRevision.bigIntegerValue(), date.bigIntegerValue());
    }
    private static boolean textEquals(JsonNode value, String expected) { return value != null && value.isTextual() && value.textValue().equals(expected); }
    private static boolean isTrue(JsonNode value) { return value != null && value.isBoolean() && value.booleanValue(); }
    private static boolean isInteger(JsonNode value) { return value != null && value.isIntegralNumber(); }
    private static BigInteger integer(JsonNode value) { require(isInteger(value), "integer token required; no boolean, float, string or null"); return value.bigIntegerValue(); }
    private static ObjectNode object(JsonNode value) { require(value instanceof ObjectNode, "JSON object required"); return (ObjectNode) value; }
    private static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}
