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
import org.xar.ck3.control.application.action.FullSnapshotGuiControl;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;

/** Correlated GUI observation/submission data. Activation never grants business or SAVE success. */
public final class GuiControlResult {
    public static final String SCHEMA = "ck3_1210_gui_control_result_v1";
    private static final Set<String> KEYS = Set.of("schema", "step", "game_version", "executable_sha256", "adapter_id", "backend",
            "status", "accepted", "native_revision", "root_name", "query_generation", "widget_id", "application_main_observed",
            "full_snapshot_before_verified", "source_abi_pins_verified", "effect_attempted", "native_handled", "verification_pending",
            "complete", "widgets", "unavailable_reason");
    private static final Set<String> STATUSES = Set.of("available", "submitted", "expired", "stale_full_snapshot", "stale_gui", "disabled", "unavailable", "indeterminate");
    private GuiControlResult() { }

    public enum Disposition { OBSERVED, SUBMITTED, REJECTED_BEFORE_EFFECT, UNKNOWN }
    public record Control(BigInteger widgetId, String runtimeName, String childPath, long vtableRva,
                          boolean effectiveVisible, boolean enabled, boolean clickable) {
        public boolean activatable() { return effectiveVisible && enabled && clickable; }
    }
    public record Assessment(Disposition disposition, String step, String status, BigInteger nativeRevision,
                             String rootName, BigInteger queryGeneration, BigInteger widgetId, boolean applicationMainObserved,
                             boolean fullBeforeVerified, boolean abiPinsVerified, boolean effectAttempted,
                             boolean nativeHandled, boolean verificationPending, boolean complete, List<Control> widgets,
                             Optional<String> unavailableReason) {
        public Assessment { widgets = List.copyOf(widgets); }
    }

    public static Assessment decode(NativeActionPort.AckReceived original, String expectedStep,
            BigInteger expectedRevision, String expectedRoot, BigInteger expectedGeneration, BigInteger expectedWidget) throws IOException {
        try {
            boolean query = FullSnapshotGuiControl.QUERY_STEP.equals(expectedStep);
            require(query || FullSnapshotGuiControl.ACTIVATE_STEP.equals(expectedStep), "unknown GUI control operation");
            var result = FullSnapshotClockControlResult.correlatedAck(original, expectedStep);
            var request = NativeWire.decodeExecuteRequest(original.outbound().orElseThrow().originalPacket());
            require(request.expectedRevision().filter(expectedRevision::equals).isPresent()
                    && request.expectedSnapshotRevision().isEmpty(), "GUI request lacks its actual Full revision");
            var additional = NativeWire.object(NativeWire.parse(request.normalizedAdditionalFields().value()));
            var claim = NativeWire.object(additional.get("gui_control_v1"));
            long until = NativeWire.integer(claim.get("deadline_unix_ms"), BigInteger.ONE, BigInteger.valueOf(Long.MAX_VALUE)).longValueExact();
            var prepared = query ? FullSnapshotGuiControl.query("native:" + expectedRevision, expectedRevision, Instant.ofEpochMilli(until), expectedRoot)
                    : FullSnapshotGuiControl.activate("native:" + expectedRevision, expectedRevision, Instant.ofEpochMilli(until), expectedRoot, expectedGeneration, expectedWidget);
            require(Arrays.equals(StrictJson.canonical(additional), prepared.additionalFields().bytes()), "GUI request differs from exact preparation");
            if (query) require(BigInteger.ZERO.equals(expectedGeneration) && BigInteger.ZERO.equals(expectedWidget), "query cannot request an observed control");
            var row = NativeWire.object(NativeWire.parse(result.result().token().orElseThrow().value()));
            keys(row, KEYS);
            require(SCHEMA.equals(text(row, "schema"))
                    && ExactCk3Build.CK3_1210.matches(text(row, "game_version"), text(row, "executable_sha256"))
                    && "ck3-1.21.0-msvc-x64".equals(text(row, "adapter_id"))
                    && "ck3-1.21.0-native-headless-main-thread".equals(text(row, "backend")), "GUI result producer differs from exact Florin ABI");
            String step = text(row, "step"), status = text(row, "status"), root = text(row, "root_name");
            require(expectedStep.equals(step) && expectedRoot.equals(root) && STATUSES.contains(status), "GUI result operation/root/status differs");
            BigInteger revision = NativeWire.integer(row.get("native_revision"), BigInteger.ONE, NativeWire.UINT64_MAX);
            BigInteger generation = decimal(row.get("query_generation")), widget = decimal(row.get("widget_id"));
            require(revision.equals(expectedRevision) && widget.equals(expectedWidget), "GUI result escaped its Full/control identity");
            boolean accepted = bool(row, "accepted"), applicationMain = bool(row, "application_main_observed"), before = bool(row, "full_snapshot_before_verified");
            boolean abi = bool(row, "source_abi_pins_verified"), attempted = bool(row, "effect_attempted"), handled = bool(row, "native_handled");
            boolean pending = bool(row, "verification_pending"), complete = bool(row, "complete");
            require(accepted == status.equals(query ? "available" : "submitted"), "GUI result status and acceptance contradict");
            require(query ? !status.equals("submitted") : !status.equals("available"), "GUI result crossed observation/submission roles");
            JsonNode list = row.get("widgets");
            require(list != null && list.isArray() && list.size() <= FullSnapshotGuiControl.MAXIMUM_CONTROLS, "bounded GUI control list required");
            var controls = new ArrayList<Control>();
            var seen = new HashSet<BigInteger>();
            for (JsonNode value : list) {
                var control = NativeWire.object(value);
                keys(control, Set.of("widget_id", "runtime_name", "child_path", "vtable_rva", "effective_visible", "enabled", "clickable"));
                BigInteger id = decimal(control.get("widget_id"));
                require(id.signum() > 0 && seen.add(id), "observed GUI control id is zero or repeated");
                String name = boundedString(control.get("runtime_name"), 1024), path = boundedString(control.get("child_path"), 4096);
                require(path.isEmpty() || path.matches("(0|[1-9][0-9]*)(/(0|[1-9][0-9]*))*"), "GUI child path is not canonical");
                long rva = NativeWire.integer(control.get("vtable_rva"), BigInteger.ONE, BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE)).longValueExact();
                controls.add(new Control(id, name, path, rva, bool(control, "effective_visible"), bool(control, "enabled"), bool(control, "clickable")));
            }
            Optional<String> reason = row.get("unavailable_reason").isNull() ? Optional.empty() : Optional.of(text(row, "unavailable_reason"));
            if (accepted) {
                require(original.nativeOk() && applicationMain && before && abi && reason.isEmpty(), "accepted GUI result lacks native owner/Full/ABI evidence");
                if (query) {
                    require(generation.signum() > 0 && complete && !attempted && !handled && !pending, "GUI observation cannot claim activation");
                    return assessment(Disposition.OBSERVED, step, status, revision, root, generation, widget, true, true, true, false, false, false, true, controls, reason);
                }
                require(generation.equals(expectedGeneration) && attempted && pending && !complete && controls.isEmpty(), "GUI activation cannot claim post-state or replace its observed generation");
                return assessment(handled ? Disposition.SUBMITTED : Disposition.UNKNOWN, step, status, revision, root, generation, widget,
                        true, true, true, true, handled, true, false, controls, reason);
            }
            require(!complete && controls.isEmpty(), "rejected GUI operation cannot supply observation credit");
            require(generation.signum() == 0 || (!query && generation.equals(expectedGeneration)), "rejected GUI operation invented an observation generation");
            require(!query || (!attempted && !handled && !pending), "read-only GUI query attempted activation");
            require(!handled || attempted, "native GUI handling requires an attempted effect");
            return assessment(attempted || status.equals("indeterminate") ? Disposition.UNKNOWN : Disposition.REJECTED_BEFORE_EFFECT,
                    step, status, revision, root, generation, widget, applicationMain, before, abi, attempted, handled, pending, false, controls, reason);
        } catch (IllegalArgumentException invalid) {
            throw new IOException("invalid exact GUI producer result", invalid);
        }
    }

    private static Assessment assessment(Disposition disposition, String step, String status, BigInteger revision,
            String root, BigInteger generation, BigInteger widget, boolean main, boolean before, boolean abi, boolean attempted,
            boolean handled, boolean pending, boolean complete, List<Control> controls, Optional<String> reason) {
        return new Assessment(disposition, step, status, revision, root, generation, widget, main, before, abi, attempted, handled, pending, complete, controls, reason);
    }
    private static BigInteger decimal(JsonNode value) throws IOException {
        String text = boundedString(value, 20);
        require(text.matches("0|[1-9][0-9]*"), "canonical decimal GUI identifier required");
        var number = new BigInteger(text);
        require(number.compareTo(NativeWire.UINT64_MAX) <= 0, "GUI identifier exceeds uint64");
        return number;
    }
    private static String boundedString(JsonNode value, int maximum) throws IOException {
        require(value != null && value.isTextual() && value.textValue().length() <= maximum, "bounded GUI string required");
        return value.textValue();
    }
    private static String text(ObjectNode row, String field) throws IOException { return NativeWire.text(row.get(field)); }
    private static boolean bool(ObjectNode row, String field) throws IOException {
        JsonNode value = row.get(field);
        require(value != null && value.isBoolean(), "exact GUI boolean required: " + field);
        return value.booleanValue();
    }
    private static void keys(ObjectNode row, Set<String> expected) throws IOException {
        var actual = new HashSet<String>();
        row.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(expected), "closed GUI result fields differ");
    }
    private static void require(boolean condition, String reason) throws IOException { if (!condition) throw new IOException(reason); }
}
