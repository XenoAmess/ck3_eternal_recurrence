package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.FullSnapshotEventOptionControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;

/** Correlated ACK data only: a submitted option still needs independent business post-state. */
public final class EventOptionControlResult {
    public static final String SCHEMA = "ck3_1210_event_option_control_result_v1";
    private static final Set<String> KEYS = Set.of("schema", "game_version", "executable_sha256", "adapter_id", "backend", "step", "accepted",
            "status", "native_revision", "event_instance_id", "native_option_index", "application_main_observed", "full_snapshot_before_verified", "effect_attempted", "options", "unavailable_reason");
    private static final Set<String> STATUSES = Set.of("available", "submitted", "unavailable", "expired", "stale_full_snapshot", "no_active_event", "event_mismatch", "option_missing", "option_disabled", "rejected", "indeterminate");
    private EventOptionControlResult() { }
    public enum Disposition { OBSERVED, SUBMITTED, REJECTED_BEFORE_EFFECT, UNKNOWN }
    public record Option(int nativeOptionIndex, boolean enabled) { }
    public record Assessment(Disposition disposition, String step, String status, BigInteger nativeRevision, int eventInstanceId,
                             Optional<Integer> nativeOptionIndex, boolean applicationMainObserved, boolean fullBeforeVerified,
                             boolean effectAttempted, List<Option> options, Optional<String> unavailableReason) {
        public Assessment { options = List.copyOf(options); }
    }

    public static Assessment decode(NativeActionPort.AckReceived original, String expectedStep, BigInteger expectedRevision, int eventInstanceId) throws IOException {
        var result = FullSnapshotClockControlResult.correlatedAck(original, expectedStep);
        boolean query = FullSnapshotEventOptionControl.QUERY_STEP.equals(expectedStep);
        int requestedIndex = query ? -1 : FullSnapshotEventOptionControl.selectedIndex(expectedStep);
        try {
            var request = NativeWire.decodeExecuteRequest(original.outbound().orElseThrow().originalPacket());
            require(request.expectedRevision().filter(expectedRevision::equals).isPresent() && request.expectedSnapshotRevision().isEmpty(), "event request lacks its exact positive Full revision");
            var additional = NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));
            var claim = NativeWire.object(additional.get("event_option_control"));
            long deadline = NativeWire.integer(claim.get("deadline_unix_ms"), BigInteger.ONE, BigInteger.valueOf(Long.MAX_VALUE)).longValueExact();
            var expected = query ? FullSnapshotEventOptionControl.query("native:" + expectedRevision, expectedRevision, Instant.ofEpochMilli(deadline), eventInstanceId)
                    : FullSnapshotEventOptionControl.select("native:" + expectedRevision, expectedRevision, Instant.ofEpochMilli(deadline), eventInstanceId, requestedIndex);
            require(Arrays.equals(StrictJson.canonical(additional), expected.additionalFields().bytes()), "event request claim/arguments changed from exact preparation");
            var row = NativeWire.object(NativeWire.parse(result.result().token().orElseThrow().value()));
            keys(row, KEYS);
            require(SCHEMA.equals(text(row, "schema")) && ExactCk3Build.CK3_1210.matches(text(row, "game_version"), text(row, "executable_sha256"))
                    && "ck3-1.21.0-msvc-x64".equals(text(row, "adapter_id")) && "ck3-1.21.0-native-headless-main-thread".equals(text(row, "backend")), "event option exact producer differs");
            String step = text(row, "step"), status = text(row, "status");
            require(expectedStep.equals(step) && STATUSES.contains(status), "event option step/status differs");
            BigInteger revision = NativeWire.integer(row.get("native_revision"), BigInteger.ONE, NativeWire.UINT64_MAX);
            int instance = NativeWire.integer(row.get("event_instance_id"), BigInteger.ONE, BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();
            require(revision.equals(expectedRevision) && instance == eventInstanceId, "event option result escaped original Full/event occurrence");
            Optional<Integer> selected = Optional.empty();
            if (query) require(row.get("native_option_index").isNull(), "query cannot identify a submitted option");
            else {
                int index = NativeWire.integer(row.get("native_option_index"), BigInteger.ZERO, BigInteger.valueOf(511)).intValueExact();
                require(index == requestedIndex, "event option result changed authored native index"); selected = Optional.of(index);
            }
            boolean accepted = bool(row, "accepted"), applicationMain = bool(row, "application_main_observed"), before = bool(row, "full_snapshot_before_verified"), attempted = bool(row, "effect_attempted");
            require(accepted == (status.equals(query ? "available" : "submitted")), "event option status and accepted disagree");
            require(!query || !status.equals("submitted"), "query cannot submit an option");
            require(query || !status.equals("available"), "select cannot claim an observation result");
            var values = row.get("options"); require(values != null && values.isArray() && values.size() <= FullSnapshotEventOptionControl.MAXIMUM_OPTIONS, "bounded event option list required");
            List<Option> options = new ArrayList<>(); Set<Integer> seen = new HashSet<>();
            for (var value : values) {
                var option = NativeWire.object(value); keys(option, Set.of("native_option_index", "enabled"));
                int index = NativeWire.integer(option.get("native_option_index"), BigInteger.ZERO, BigInteger.valueOf(511)).intValueExact();
                require(seen.add(index), "authored native event index repeated"); options.add(new Option(index, bool(option, "enabled")));
            }
            Optional<String> reason = row.get("unavailable_reason").isNull() ? Optional.empty() : Optional.of(text(row, "unavailable_reason"));
            if (accepted) {
                require(original.nativeOk() && applicationMain && before && attempted != query && reason.isEmpty(), "accepted event option lacks actual owner/full-before/effect semantics");
                if (!query) require(options.stream().anyMatch(option -> option.nativeOptionIndex() == requestedIndex && option.enabled()), "submitted event option was not in the observed enabled list");
                return new Assessment(query ? Disposition.OBSERVED : Disposition.SUBMITTED, step, status, revision, instance, selected, true, true, attempted, options, reason);
            }
            require(options.isEmpty(), "failed event query/select cannot supply option observation credit");
            Disposition disposition = attempted || status.equals("indeterminate") ? Disposition.UNKNOWN : Disposition.REJECTED_BEFORE_EFFECT;
            return new Assessment(disposition, step, status, revision, instance, selected, applicationMain, before, attempted, options, reason);
        } catch (IllegalArgumentException invalid) { throw new IOException("invalid event option producer result", invalid); }
    }
    private static String text(ObjectNode row, String field) throws IOException { return NativeWire.text(row.get(field)); }
    private static boolean bool(ObjectNode row, String field) throws IOException { JsonNode value = row.get(field); require(value != null && value.isBoolean(), "exact event boolean required: " + field); return value.booleanValue(); }
    private static void keys(ObjectNode row, Set<String> expected) throws IOException { Set<String> actual = new HashSet<>(); row.fieldNames().forEachRemaining(actual::add); require(actual.equals(expected), "closed event option result fields differ"); }
    private static void require(boolean condition, String reason) throws IOException { if (!condition) throw new IOException(reason); }
}
