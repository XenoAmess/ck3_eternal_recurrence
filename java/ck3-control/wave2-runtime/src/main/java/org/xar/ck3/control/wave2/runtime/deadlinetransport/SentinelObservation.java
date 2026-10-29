package org.xar.ck3.control.wave2.runtime.deadlinetransport;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.reconciliation.SentinelCodec;

/** Narrow legacy numeric-wire adapter to the single shared, decimal-memory status contract. */
public final class SentinelObservation {
    public static final String NUMERIC_WIRE_PROFILE = "tactical-daily-sentinel-native-numeric/v1";
    public static final String MEMORY_PROFILE = "late-outcome-status-decimal-memory/v1";

    private SentinelObservation() { }

    public static Status decode(byte[] raw) { return SentinelCodec.decode(raw); }

    public static Status decode(JsonNode value) {
        // Canonicalization rejects floating nodes before serialization can erase their numeric type.
        return decode(StrictJson.canonical(value));
    }

    public static BigInteger nativeGeneration(Status value) { return new BigInteger(value.generation().decimal()); }

    /** Explicit v1 native numeric uint64 representation; shared memory retains a decimal string. */
    public static ObjectNode toJson(Status value) {
        ObjectNode node = StrictJson.object();
        node.put("state", value.state().name().toLowerCase(Locale.ROOT));
        node.put("generation", nativeGeneration(value));
        node.put("starting_date_raw", value.startingDateRaw()); node.put("target_date_raw", value.targetDateRaw());
        node.put("last_observed_date_raw", value.lastObservedDateRaw()); node.put("trigger_date_raw", value.triggerDateRaw());
        node.put("speed", value.speed()); node.put("mode", value.mode().name().toLowerCase(Locale.ROOT));
        node.put("army_count", value.armyCount()); node.put("combat_count", value.combatCount());
        node.put("completed_daily_ticks", value.completedDailyTicks());
        node.put("intermediate_pause_count", value.intermediatePauseCount()); node.put("trigger_flags", value.triggerFlags());
        ArrayNode reasons = node.putArray("trigger_reasons"); value.triggerReasons().forEach(reasons::add);
        node.put("signed_date_delta_from_target_raw", value.signedDateDeltaFromTargetRaw()); node.put("overshoot_days", value.overshootDays());
        node.put("pause_wrapper_called", value.pauseWrapperCalled()); node.put("pause_observed", value.pauseObserved());
        node.put("terminal_observed", value.terminalObserved()); node.put("abnormal", value.abnormal());
        return node;
    }

    static boolean bool(JsonNode value) {
        require(value != null && value.isBoolean(), "actual JSON boolean required");
        return value.booleanValue();
    }
}
