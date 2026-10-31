package org.xar.ck3.control.reconciliation;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Decodes the actual 20-field native STATUS slot, not a historical armed_reply projection. */
public final class SentinelCodec {
    private SentinelCodec() { }
    static final Set<String> FIELDS = Set.of("state", "generation", "starting_date_raw", "target_date_raw",
            "last_observed_date_raw", "trigger_date_raw", "speed", "mode", "army_count", "combat_count",
            "completed_daily_ticks", "intermediate_pause_count", "trigger_flags", "trigger_reasons",
            "signed_date_delta_from_target_raw", "overshoot_days", "pause_wrapper_called", "pause_observed",
            "terminal_observed", "abnormal");
    private static final List<String> REASONS = List.of("date_deadline", "army_unavailable", "route_target_changed",
            "combat_transition", "retreat_transition", "combat_unavailable", "combat_phase_changed",
            "combat_roster_changed", "combat_terminal", "date_sequence_failure", "world_identity_changed",
            "pause_not_observed", "original_unavailable", "native_pause", "combat_winner_changed",
            "evaluation_failure", "army_position_changed");

    public static Status decode(byte[] rawSlot) { return decodeNode(StrictJson.parse(rawSlot)); }
    static Status decodeNode(JsonNode value) {
        JsonNode row = StrictJson.object(value, FIELDS);
        String state = StrictJson.text(row.get("state")), mode = StrictJson.text(row.get("mode"));
        State typedState = switch (state) {
            case "idle" -> State.IDLE; case "armed" -> State.ARMED; case "triggered" -> State.TRIGGERED;
            case "failed" -> State.FAILED; case "unavailable" -> State.UNAVAILABLE;
            default -> throw new org.xar.ck3.control.contracts.ContractViolationException("unknown sentinel state");
        };
        Mode typedMode = switch (mode) {
            case "decision_epoch" -> Mode.DECISION_EPOCH; case "terminal_or_sentinel" -> Mode.TERMINAL_OR_SENTINEL;
            default -> throw new org.xar.ck3.control.contracts.ContractViolationException("unknown sentinel mode");
        };
        JsonNode reasons = row.get("trigger_reasons");
        StrictJson.require(reasons != null && reasons.isArray() && reasons.size() <= 17, "bounded trigger reasons array");
        List<String> names = new ArrayList<>();
        reasons.forEach(item -> names.add(StrictJson.text(item)));
        return new Status(typedState, nativeUInt64(row.get("generation")), i32(row.get("starting_date_raw")),
                i32(row.get("target_date_raw")), i32(row.get("last_observed_date_raw")), i32(row.get("trigger_date_raw")),
                (int) StrictJson.integer(row.get("speed"), typedState == State.IDLE || typedState == State.UNAVAILABLE ? 0 : 1, 5), typedMode, u32(row.get("army_count")),
                u32(row.get("combat_count")), u32(row.get("completed_daily_ticks")), u32(row.get("intermediate_pause_count")),
                u32(row.get("trigger_flags")), names, i32(row.get("signed_date_delta_from_target_raw")),
                i32(row.get("overshoot_days")), bool(row.get("pause_wrapper_called")), bool(row.get("pause_observed")),
                bool(row.get("terminal_observed")), bool(row.get("abnormal")));
    }
    /** Explicit raw-native uint64 number to new cross-JS decimal-string memory domain; no numeric alias. */
    static CrossJsDecimalUInt64 nativeUInt64(JsonNode node) {
        return new CrossJsDecimalUInt64(StrictJson.integer(node, BigInteger.ZERO, StrictJson.UINT64_MAX).toString());
    }
    static int i32(JsonNode node) { return (int) StrictJson.integer(node, Integer.MIN_VALUE, Integer.MAX_VALUE); }
    static long u32(JsonNode node) { return StrictJson.integer(node, 0, 0xffff_ffffL); }
    static boolean bool(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "exact JSON boolean required"); return node.booleanValue();
    }
    static List<String> reasons(long flags) {
        List<String> result = new ArrayList<>();
        for (int bit = 0; bit < REASONS.size(); bit++) { if ((flags & (1L << bit)) != 0) { result.add(REASONS.get(bit)); } }
        return List.copyOf(result);
    }
}
