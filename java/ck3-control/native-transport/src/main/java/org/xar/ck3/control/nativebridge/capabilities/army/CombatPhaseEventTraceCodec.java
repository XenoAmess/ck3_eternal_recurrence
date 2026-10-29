package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.require;

/** Complete paused evaluator and opt-in managed counter readout. Neither output is a battle transition or a forecast input. */
public final class CombatPhaseEventTraceCodec {
    public static final String CAPABILITY = "game.command.query-combat-phase-event-trace-v1-N";
    public static final String STEP_PREFIX = "query-combat-phase-event-trace-v1-";
    private static final String FINISH_STEP = "experimental-combat-phase-event-trace-finish-v1";
    private static final String COUNTER_SOURCE = "native_resolve_counter_classes_after_0x23caf20";
    public static final List<String> STOCK_KEYS = List.of("commander_none", "commander_wounded", "commander_maimed", "commander_killed", "knight_none",
            "knight_berserker_attack", "knight_become_berserker", "knight_shieldmaiden_attack", "knight_becomes_incapable", "knight_wounded", "knight_maimed", "knight_killed", "knight_qualify_for_accolade");
    private CombatPhaseEventTraceCodec() { }
    public record Cadence(long periodDays, boolean currentPhaseFiresEvents) { public Cadence { u32(periodDays); } }
    public record EventRow(int globalLoadIndex, int typeLoadIndex, String eventKey, String eventType, boolean emptyEffect,
            boolean selectorRoleApplicable, boolean triggerValid, boolean chanceEvaluatedForDifferential,
            boolean selectorWouldEvaluateChance, long chanceRaw, int intWeight, boolean positiveWeight, boolean selectorEligible) {
        public EventRow { Objects.requireNonNull(eventKey); Objects.requireNonNull(eventType); require(globalLoadIndex >= 0 && globalLoadIndex < STOCK_KEYS.size() && STOCK_KEYS.get(globalLoadIndex).equals(eventKey), "phase trace stock row identity/order differs"); }
        private ObjectNode json(boolean publicV2) {
            var n = empty().put("global_load_index", globalLoadIndex).put("type_load_index", typeLoadIndex).put("event_key", eventKey).put("event_type", eventType)
                    .put("empty_effect", emptyEffect).put("selector_role_applicable", selectorRoleApplicable).put("trigger_valid", triggerValid)
                    .put("chance_evaluated_for_differential", chanceEvaluatedForDifferential).put("selector_would_evaluate_chance", selectorWouldEvaluateChance);
            wide(n, "chance_raw", chanceRaw, publicV2); return n.put("int_weight", intWeight).put("positive_weight", positiveWeight).put("selector_eligible", selectorEligible);
        }
    }
    public record CharacterTrace(int characterId, int sideIndex, boolean orderedArmyCommander, boolean selectedSideCommander, boolean orderedKnight, List<EventRow> eventRows) {
        public CharacterTrace { eventRows = List.copyOf(eventRows); require(eventRows.size() == STOCK_KEYS.size(), "phase trace requires all thirteen stock rows"); for (int index = 0; index < eventRows.size(); index++) require(eventRows.get(index).globalLoadIndex() == index, "phase trace global loaded order differs"); }
        private ObjectNode json(boolean publicV2) {
            var n = empty().put("character_id", characterId).put("side_index", sideIndex).put("ordered_army_commander", orderedArmyCommander)
                    .put("selected_side_commander", selectedSideCommander).put("ordered_knight", orderedKnight); var rows = n.putArray("event_rows"); eventRows.forEach(row -> rows.add(row.json(publicV2))); return n;
        }
    }
    public record Observed(int combatId, int dateRaw, int targetProvinceId, int phaseRaw, String phase, int phaseDay,
            boolean evaluatorReady, boolean samePausedFrameStable, boolean realCombatSideScope, boolean allScopeTeardownsComplete,
            String unavailableReason, List<String> missingProductionReaders, Cadence cadence, boolean globalRngUnchangedByProbe, List<CharacterTrace> characters) {
        public Observed {
            positiveCombat(combatId); Objects.requireNonNull(phase); Objects.requireNonNull(unavailableReason); Objects.requireNonNull(cadence);
            missingProductionReaders = List.copyOf(missingProductionReaders); characters = List.copyOf(characters);
            if (evaluatorReady) require(samePausedFrameStable && realCombatSideScope && allScopeTeardownsComplete && globalRngUnchangedByProbe
                    && !characters.isEmpty() && !missingProductionReaders.isEmpty(), "phase trace evaluator proof is incomplete");
            else require(characters.isEmpty(), "unavailable phase trace cannot invent characters");
        }
        public ObjectNode toNativeJson() { return json(false); }
        public ObjectNode toPublicV2Json() { return json(true); }
        private ObjectNode json(boolean publicV2) {
            var n = empty().put("combat_id", combatId).put("date_raw", dateRaw).put("target_province_id", targetProvinceId).put("phase_raw", phaseRaw).put("phase", phase).put("phase_day", phaseDay)
                    .put("evaluator_probe_ready", evaluatorReady).put("production_trace_ready", false).put("same_paused_frame_stable", samePausedFrameStable).put("real_combat_side_scope", realCombatSideScope)
                    .put("all_scope_teardowns_complete", allScopeTeardownsComplete).put("unavailable_reason", unavailableReason).put("global_rng_unchanged_by_probe", globalRngUnchangedByProbe);
            var missing = n.putArray("missing_production_readers"); missingProductionReaders.forEach(missing::add);
            n.putObject("cadence").put("period_days", cadence.periodDays()).put("current_phase_fires_events", cadence.currentPhaseFiresEvents());
            var rows = n.putArray("characters"); characters.forEach(character -> rows.add(character.json(publicV2))); return n;
        }
    }
    public record CounterSide(int sideIndex, int counteredEntryCount, int counteringEntryCount, long contextRaw, int classCount, int capacity, List<Long> retentionRaw) {
        public CounterSide {
            require(sideIndex >= 0 && sideIndex <= 1 && counteredEntryCount >= 0 && counteredEntryCount <= 2048 && counteringEntryCount >= 0 && counteringEntryCount <= 2048, "counter side/entry count differs");
            require(classCount >= 1 && classCount <= 4096 && capacity >= classCount && capacity <= 4096, "counter class/capacity differs"); retentionRaw = List.copyOf(retentionRaw); require(retentionRaw.size() == classCount, "counter retention vector differs");
        }
        private ObjectNode json(boolean publicV2) {
            var n = empty().put("side_index", sideIndex).put("countered_entry_count", counteredEntryCount).put("countering_entry_count", counteringEntryCount).put("class_count", classCount).put("capacity", capacity);
            wide(n, "context_raw", contextRaw, publicV2); var values = n.putArray("retention_raw"); for (long value : retentionRaw) { if (publicV2) values.add(Long.toString(value)); else values.add(value); } return n;
        }
    }
    public record HookDiagnostic(long hookCalls, long targetCalls, int firstFailureGate) {
        public HookDiagnostic { u32(hookCalls); require(targetCalls >= 0 && targetCalls <= hookCalls && Set.of(0, 1, 2, 3, 4, 5, 31, 32, 33).contains(firstFailureGate)
                && (firstFailureGate == 0 || targetCalls > 0), "counter hook diagnostics differ"); }
    }
    public record CounterDiagnostic(boolean diagnosticObservationComplete, boolean pairComplete, List<CounterSide> sides, Optional<HookDiagnostic> hookDiagnostic) {
        public CounterDiagnostic {
            sides = List.copyOf(sides); Objects.requireNonNull(hookDiagnostic); require(sides.size() <= 2, "counter pair count differs");
            for (int index = 0; index < sides.size(); index++) require(sides.get(index).sideIndex() == index, "counter pair physical order differs");
            if (pairComplete) require(sides.size() == 2 && sides.get(0).classCount() == sides.get(1).classCount(), "counter pair incomplete");
            require(!diagnosticObservationComplete || pairComplete, "complete diagnostic requires the pair");
        }
        public boolean forecastUsable() { return false; }
        public ObjectNode toNativeJson() { return json(false); }
        public ObjectNode toPublicV2Json() { return json(true); }
        private ObjectNode json(boolean publicV2) {
            var n = empty().put("source", COUNTER_SOURCE).put("requested", true).put("diagnostic_observation_complete", diagnosticObservationComplete).put("forecast_usable", false)
                    .put("validation_status", "live_validation_pending").put("pair_complete", pairComplete).put("count", sides.size()); var rows = n.putArray("sides"); sides.forEach(side -> rows.add(side.json(publicV2)));
            if (hookDiagnostic.isPresent()) { HookDiagnostic hook = hookDiagnostic.orElseThrow(); n.putObject("hook_diagnostic").put("hook_calls", hook.hookCalls()).put("target_calls", hook.targetCalls()).put("first_failure_gate", hook.firstFailureGate()); } else n.putNull("hook_diagnostic"); return n;
        }
    }
    public record ExperimentalCounterDiagnostic(int combatId, BigInteger managedDailySequenceToken, CounterDiagnostic diagnostic) {
        public ExperimentalCounterDiagnostic { positiveCombat(combatId); require(managedDailySequenceToken != null && managedDailySequenceToken.signum() > 0 && managedDailySequenceToken.bitLength() <= 64, "managed daily sequence token must be positive uint64"); Objects.requireNonNull(diagnostic); }
        public ObjectNode toNativeJson() { var n = diagnostic.toNativeJson().put("combat_id", combatId); n.put("managed_daily_sequence_token", managedDailySequenceToken); return n; }
        public ObjectNode toPublicV2Json() { return diagnostic.toPublicV2Json().put("combat_id", combatId).put("managed_daily_sequence_token", managedDailySequenceToken.toString()); }
    }
    public static String step(int combatId) { positiveCombat(combatId); return STEP_PREFIX + combatId; }
    public static OptionalInt parseStep(String value) {
        if (value == null || !value.startsWith(STEP_PREFIX)) return OptionalInt.empty(); String raw = value.substring(STEP_PREFIX.length()); if (!raw.matches("[1-9][0-9]*")) return OptionalInt.empty();
        try { int combat = new BigInteger(raw).intValueExact(); positiveCombat(combat); return OptionalInt.of(combat); } catch (IllegalArgumentException | ArithmeticException invalid) { return OptionalInt.empty(); }
    }
    public static Observed normalize(JsonNode value, int combatId) {
        positiveCombat(combatId); var n = closed(value, "combat_id", "date_raw", "target_province_id", "phase_raw", "phase", "phase_day", "evaluator_probe_ready", "production_trace_ready", "same_paused_frame_stable", "real_combat_side_scope", "all_scope_teardowns_complete", "unavailable_reason", "missing_production_readers", "cadence", "global_rng_unchanged_by_probe", "characters");
        require(i32(get(n, "combat_id")) == combatId, "phase trace full CombatID differs"); no(get(n, "production_trace_ready"));
        ObjectNode cadence = closed(get(n, "cadence"), "period_days", "current_phase_fires_events");
        return new Observed(combatId, i32(get(n, "date_raw")), i32(get(n, "target_province_id")), i32(get(n, "phase_raw")), text(get(n, "phase")), i32(get(n, "phase_day")),
                bool(get(n, "evaluator_probe_ready")), bool(get(n, "same_paused_frame_stable")), bool(get(n, "real_combat_side_scope")), bool(get(n, "all_scope_teardowns_complete")),
                text(get(n, "unavailable_reason")), array(get(n, "missing_production_readers"), ArmyJson::text), new Cadence(uint32(get(cadence, "period_days")), bool(get(cadence, "current_phase_fires_events"))),
                bool(get(n, "global_rng_unchanged_by_probe")), array(get(n, "characters"), CombatPhaseEventTraceCodec::character));
    }
    private static CharacterTrace character(JsonNode raw) {
        var n = closed(raw, "character_id", "side_index", "ordered_army_commander", "selected_side_commander", "ordered_knight", "event_rows");
        return new CharacterTrace(i32(get(n, "character_id")), i32(get(n, "side_index")), bool(get(n, "ordered_army_commander")), bool(get(n, "selected_side_commander")), bool(get(n, "ordered_knight")), array(get(n, "event_rows"), CombatPhaseEventTraceCodec::event));
    }
    private static EventRow event(JsonNode raw) {
        var n = closed(raw, "global_load_index", "type_load_index", "event_key", "event_type", "empty_effect", "selector_role_applicable", "trigger_valid", "chance_evaluated_for_differential", "selector_would_evaluate_chance", "chance_raw", "int_weight", "positive_weight", "selector_eligible");
        return new EventRow(i32(get(n, "global_load_index")), i32(get(n, "type_load_index")), text(get(n, "event_key")), text(get(n, "event_type")), bool(get(n, "empty_effect")), bool(get(n, "selector_role_applicable")), bool(get(n, "trigger_valid")), bool(get(n, "chance_evaluated_for_differential")), bool(get(n, "selector_would_evaluate_chance")), i64(get(n, "chance_raw")), i32(get(n, "int_weight")), bool(get(n, "positive_weight")), bool(get(n, "selector_eligible")));
    }
    public static Optional<CounterDiagnostic> normalizeRuntimeCounterOutputDiagnostic(JsonNode managedResult) {
        ObjectNode managed = object(managedResult), trace = object(get(managed, "trace")); if (!trace.has("runtime_counter_output")) return Optional.empty();
        ObjectNode output = object(get(trace, "runtime_counter_output")); var base = Set.of("source", "requested", "pair_complete", "count", "sides"); var extended = new java.util.HashSet<>(base); extended.addAll(Set.of("hook_calls", "target_calls", "first_failure_gate"));
        require(names(output).equals(base) || names(output).equals(extended), "counter output fields differ");
        Optional<HookDiagnostic> hook = names(output).equals(extended) ? Optional.of(new HookDiagnostic(uint32(get(output, "hook_calls")), uint32(get(output, "target_calls")), i32(get(output, "first_failure_gate")))) : Optional.empty();
        equal(get(output, "source"), COUNTER_SOURCE); yes(get(output, "requested")); boolean pairComplete = bool(get(output, "pair_complete")); int count = bounded32(get(output, "count"), 0, 2);
        List<CounterSide> sides = array(get(output, "sides"), CombatPhaseEventTraceCodec::counterSide); require(sides.size() == count, "counter output count differs");
        equal(get(managed, "schema_version"), BigInteger.ONE); equal(get(trace, "schema_version"), BigInteger.ONE); String status = text(get(trace, "status")); require(status.equals("captured") || status.equals("failed"), "counter trace status differs");
        long flags = uint32(get(trace, "failure_flags")); ObjectNode readiness = object(get(trace, "readiness")), checkpoint = object(get(managed, "managed_checkpoint"));
        require(bool(get(readiness, "runtime_counter_output_pair_complete")) == pairComplete, "counter readiness differs from the pair"); boolean bounded = bool(get(readiness, "bounded_capture_complete"));
        boolean checkpointComplete = true; for (String field : List.of("recoverable_checkpoint_created", "exact_one_day_observed", "boundary_dates_match_checkpoint", "detours_uninstalled")) { boolean observed = bool(get(checkpoint, field)); checkpointComplete &= observed; }
        require(((flags & (1L << 20)) != 0) != pairComplete, "counter failure flag contradicts pair");
        boolean complete = pairComplete && status.equals("captured") && flags == 0 && bounded && checkpointComplete;
        return Optional.of(new CounterDiagnostic(complete, pairComplete, sides, hook));
    }
    private static CounterSide counterSide(JsonNode raw) {
        var n = closed(raw, "side_index", "countered_entry_count", "countering_entry_count", "context_raw", "class_count", "capacity", "retention_raw");
        return new CounterSide(i32(get(n, "side_index")), i32(get(n, "countered_entry_count")), i32(get(n, "countering_entry_count")), i64(get(n, "context_raw")), i32(get(n, "class_count")), i32(get(n, "capacity")), array(get(n, "retention_raw"), ArmyJson::i64));
    }
    public static Optional<ExperimentalCounterDiagnostic> normalizeExperimentalCounterOutputResponse(JsonNode frame, int combatId) {
        positiveCombat(combatId); ObjectNode packet = object(frame); equal(get(packet, "type"), "command_result"); equal(get(packet, "protocol_version"), BigInteger.ONE); yes(get(packet, "ok"));
        ObjectNode result = object(get(packet, "result")); equal(get(result, "step"), FINISH_STEP); yes(get(result, "accepted")); yes(get(result, "private_build")); no(get(result, "production_trace_ready"));
        require(i32(get(result, "combat_id")) == combatId, "experimental counter full CombatID differs"); BigInteger sequence = integer(get(result, "managed_daily_sequence_token")); require(sequence.signum() > 0 && sequence.bitLength() <= 64, "experimental counter sequence differs");
        String status = text(get(result, "status")); require(status.equals("bounded_trace_available") || status.equals("trace_unavailable"), "experimental counter boundary status differs");
        Optional<CounterDiagnostic> diagnostic = normalizeRuntimeCounterOutputDiagnostic(get(result, "managed_trace"));
        if (diagnostic.isEmpty()) return Optional.empty(); require(diagnostic.orElseThrow().diagnosticObservationComplete() == status.equals("bounded_trace_available"), "experimental counter status disagrees with diagnostic");
        return Optional.of(new ExperimentalCounterDiagnostic(combatId, sequence, diagnostic.orElseThrow()));
    }
    private static int bounded32(JsonNode raw, int minimum, int maximum) { int value = i32(raw); require(value >= minimum && value <= maximum, "bounded trace integer differs"); return value; }
    private static long uint32(JsonNode raw) { return range(raw, BigInteger.ZERO, BigInteger.valueOf(0xffff_ffffL)).longValueExact(); }
    private static void u32(long value) { require(value >= 0 && value <= 0xffff_ffffL, "trace uint32 differs"); }
    private static void positiveCombat(int value) { require(value > 0, "positive full-generation signed32 CombatID required"); }
    private static void wide(ObjectNode node, String key, long value, boolean publicV2) { if (publicV2) node.put(key, Long.toString(value)); else node.put(key, value); }
}
