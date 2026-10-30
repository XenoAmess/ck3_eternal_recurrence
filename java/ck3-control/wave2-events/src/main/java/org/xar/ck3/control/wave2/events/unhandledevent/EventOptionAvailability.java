package org.xar.ck3.control.wave2.events.unhandledevent;

import java.math.BigInteger;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation.LegacyNotReported;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation.Observed;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation.Unobserved;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

/** Versioned stock GUI observation, independent of the retained raw enabled byte. */
public final class EventOptionAvailability {
    private EventOptionAvailability() { }

    public static boolean selectionAllowed(ObjectValue context, ObjectValue row) {
        Objects.requireNonNull(row, "option row");
        return observation(context, row).permitsSelectionWithRawFallback(Boolean.TRUE.equals(RetainedJson.bool(row.get("enabled"))));
    }

    public static GuiAvailabilityObservation observation(ObjectValue context, ObjectValue row) {
        Objects.requireNonNull(row, "option row");
        boolean v2 = context != null && ("current-event-window-context-v2".equals(RetainedJson.string(context.get("schema")))
                || BigInteger.TWO.equals(RetainedJson.integer(context.get("schema_version"))));
        if (v2) {
            StrictJson.require("current-event-window-context-v2".equals(RetainedJson.string(context.get("schema")))
                    && BigInteger.TWO.equals(RetainedJson.integer(context.get("schema_version"))), "exact v2 event context required");
            StrictJson.require(row.get("gui_availability") instanceof ObjectValue, "v2 GUI observation required");
            return observation((ObjectValue) row.get("gui_availability"));
        }
        // Earlier retained captures may predate the version wrapper; no v2 signal can enter this branch.
        StrictJson.require(!row.contains("gui_availability"), "v1 option must not contain a GUI observation");
        return new LegacyNotReported();
    }

    /** Strict decoder for a persisted observation copied from an actual v2 option. */
    public static GuiAvailabilityObservation observation(ObjectValue wire) {
        Objects.requireNonNull(wire, "GUI observation");
        String status = RetainedJson.string(wire.get("status"));
        if ("observed".equals(status)) {
            StrictJson.require(wire.fields().keySet().equals(Set.of("status", "is_valid")), "exact observed GUI fields required");
            Boolean valid = RetainedJson.bool(wire.get("is_valid"));
            StrictJson.require(valid != null, "GUI is_valid boolean required");
            return new Observed(valid);
        }
        StrictJson.require("unobserved".equals(status) && wire.fields().keySet().equals(Set.of("status", "reason")), "exact unobserved GUI fields required");
        String reason = RetainedJson.string(wire.get("reason"));
        StrictJson.require(reason != null, "GUI unavailable reason required");
        return new Unobserved(GuiAvailabilityObservation.Reason.fromWire(reason));
    }

    /** Legacy absence remains absence; callers omit this null value on v1 wires. */
    public static Value wire(GuiAvailabilityObservation observation) {
        Objects.requireNonNull(observation, "GUI observation");
        if (observation instanceof Observed observed) return new ObjectValue(Map.of(
                "status", new StringValue("observed"), "is_valid", new BooleanValue(observed.isValid())));
        if (observation instanceof Unobserved unobserved) return new ObjectValue(Map.of(
                "status", new StringValue("unobserved"), "reason", new StringValue(unobserved.reason().wire())));
        return RetainedJson.NULL;
    }

    public static boolean supportedContext(ObjectValue context) {
        if (context == null) return false;
        String schema = RetainedJson.string(context.get("schema"));
        BigInteger version = RetainedJson.integer(context.get("schema_version"));
        return "current-event-window-context-v1".equals(schema) && BigInteger.ONE.equals(version)
                || "current-event-window-context-v2".equals(schema) && BigInteger.TWO.equals(version);
    }

    /** The persisted selection must retain the actual bound row's raw value and observation. */
    public static boolean matchesBoundRow(ObjectValue context, ObjectValue selected) {
        if (context == null || !(context.get("options") instanceof ArrayValue rows))
            return observation(context, selected) instanceof LegacyNotReported;
        for (Value value : rows.values()) if (value instanceof ObjectValue row
                && Objects.equals(row.get("native_option_index"), selected.get("native_option_index"))
                && Objects.equals(row.get("rendered_index"), selected.get("rendered_index")))
            return Objects.equals(row.get("enabled"), selected.get("enabled"))
                    && observation(context, row).equals(observation(context, selected));
        return observation(context, selected) instanceof LegacyNotReported;
    }
}
