package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import static org.xar.ck3.control.wave2.military.combatwire.CombatPhaseSchema.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;

/** Complete production-v3 wire normalization and deterministic projection, separate from battle forecasting. */
public final class CombatPhaseInputsCodec {
    public static final String CAPABILITY = "game.command.query-combat-simulation-inputs-v3-N";
    public static final String PREFIX = "query-combat-simulation-inputs-v3-";
    private static final JsonNodeFactory J = JsonNodeFactory.instance;
    private final PhaseEventRuntime runtime;
    private final PhaseRefPartition partition;
    private final CombatSimulationInputsCodec baseCodec;
    public CombatPhaseInputsCodec(PhaseEventRuntime runtime) {
        this(new CombatSimulationInputsCodec(), runtime);
    }
    /** Root must supply the same complete v2 optional-leaf codec used by its ordinary query route. */
    public CombatPhaseInputsCodec(CombatSimulationInputsCodec baseCodec, PhaseEventRuntime runtime) {
        this.baseCodec = Objects.requireNonNull(baseCodec);
        this.runtime = Objects.requireNonNull(runtime); partition = new PhaseRefPartition(runtime);
    }
    public static String toStep(CombatRequest request) { return PREFIX + request.toStep().substring(CombatRequest.PREFIX.length()); }
    public static Optional<CombatRequest> parseStep(String step) {
        return step == null || !step.startsWith(PREFIX) ? Optional.empty() : CombatRequest.parseStep(CombatRequest.PREFIX + step.substring(PREFIX.length()));
    }
    public ObjectNode stateRefPartition() { return partition.toJson(); }
    public CombatPhaseInputs normalize(JsonNode value, CombatRequest request, CombatEncounterScope expectedScope) {
        Objects.requireNonNull(request); Objects.requireNonNull(expectedScope);
        if (value instanceof ObjectNode enriched && enriched.has("completeness")) {
            object(enriched, keys(ROOT + " completeness"), Set.of(), "normalized phase root");
            ObjectNode candidate = J.objectNode(); candidate.setAll(enriched); candidate.remove("completeness");
            ObjectNode phase = object(candidate.get("phase_event_inputs"), keys(PHASE + " " + ENRICHED), keys(PRIVATE), "normalized phase input");
            ObjectNode stripped = J.objectNode(); stripped.setAll(phase); for (String key : keys(ENRICHED)) stripped.remove(key); candidate.set("phase_event_inputs", stripped);
            CombatPhaseInputs recomputed = normalize(candidate, request, expectedScope);
            require(sameJson(recomputed.toJson(), value), "normalized production combat v3 derivation drifted"); return recomputed;
        }
        ObjectNode root = object(value, ROOT, "combat_simulation_inputs_v3");
        require(i32(root.get("schema_version"), "schema_version") == 3, "production v3 schema version malformed");
        eq(root.get("contract_stage"), "production_exact_132_refs", "production v3 contract stage malformed");
        eq(root.get("rules_manifest_sha256"), MANIFEST, "production v3 manifest hash malformed");
        CombatSimulationInputs base = baseCodec.normalize(root.get("base_inputs"), request, expectedScope);
        require(base.completeness().inputObservationReady(), "production v3 requires complete v2 base slice");
        ObjectNode phase = normalizePhase(root.get("phase_event_inputs"), base);
        boolean ready = phase.path("offline_admission").path("ready").booleanValue(), astReady = evaluatorReady(phase.get("row_evaluations"), ready);
        List<String> missingFidelity = new ArrayList<>(); missingFidelity.add("loaded_playset_verified"); if (!astReady) missingFidelity.add("ast_evaluator_ready"); missingFidelity.add("original_trace_ready");
        ObjectNode normalized = J.objectNode().put("schema_version", 3).put("contract_stage", "production_exact_132_refs").put("rules_manifest_sha256", MANIFEST);
        normalized.set("base_inputs", base.toJson()); normalized.set("phase_event_inputs", phase);
        ObjectNode completeness = normalized.putObject("completeness").put("observation_slice", "precontact-phase-event-inputs-v3").put("base_input_observation_ready", true)
                .put("phase_raw_observation_ready", ready).put("offline_exact_state_refs_ready", ready).put("phase_event_inputs_ready", ready).put("input_observation_ready", ready)
                .put("monte_carlo_ready", false).put("transition_fidelity_gate", false).put("planner_usable", false).put("active_attack_allowed", false);
        completeness.putObject("phase_event_manifest_fidelity").put("loaded_playset_verified", false).put("ast_evaluator_ready", astReady).put("original_trace_ready", false).put("fidelity_gate", false);
        ArrayNode missingObservations = completeness.putArray("missing_observation_domains"); if (!ready) missingObservations.add("phase_event_inputs");
        ArrayNode missing = completeness.putArray("missing_fidelity_gates"); missingFidelity.forEach(missing::add);
        completeness.set("missing_required_domains", base.toJson().path("completeness").get("missing_required_domains").deepCopy());
        return new CombatPhaseInputs(base, new CombatPhaseInputs.Completeness(ready, ready, ready, astReady, missingFidelity), normalized);
    }
    private ObjectNode normalizePhase(JsonNode value, CombatSimulationInputs base) {
        ObjectNode row = object(value, keys(PHASE), keys(PRIVATE), "phase_event_inputs");
        eq(row.get("rules_source"), "stock-installation-static-manifest", "phase rules_source malformed"); eq(row.get("rules_manifest_sha256"), MANIFEST, "phase manifest hash malformed");
        eq(row.get("scope_mode"), "hypothetical_precontact_offline_ast", "phase scope_mode malformed");
        ObjectNode required = object(row.get("required_state_refs"), "count sha256", "required_state_refs");
        require(i32(required.get("count"), "required count") == 132, "phase required-state count malformed"); eq(required.get("sha256"), REQUIRED_SHA, "phase required-state SHA malformed");
        require(sameJson(row.get("state_ref_coverage"), PhaseRefPartition.coverage()), "phase state-ref coverage malformed");
        String status = token(row.get("status"), "phase status", "available", "unavailable");
        ObjectNode normalized = J.objectNode().put("status", status).put("rules_source", "stock-installation-static-manifest").put("rules_manifest_sha256", MANIFEST);
        normalized.set("required_state_refs", required.deepCopy()); normalized.set("state_ref_coverage", PhaseRefPartition.coverage()); normalized.put("scope_mode", "hypothetical_precontact_offline_ast");
        if (status.equals("unavailable")) {
            require(!row.has("hard_casualty_winter") && !row.has("hard_casualty_sides"), "unavailable phase published private combat data");
            require(nil(row.get("raw")) && nil(row.get("advantage_model")), "unavailable phase published partial data");
            normalized.putNull("raw").putNull("advantage_model"); normalized.set("state_ref_partition", partition.toJson()); normalized.putNull("evaluation_contexts").putNull("row_evaluations");
            normalized.set("offline_admission", admission(false)); normalized.put("unavailable_reason", text(row.get("unavailable_reason"), "unavailable_reason")); return normalized;
        }
        require(nil(row.get("unavailable_reason")), "available phase has unavailable_reason");
        ObjectNode raw = PhaseRawCodec.normalize(row.get("raw"), base.toJson());
        ObjectNode advantage = PhaseAdvantageModelCodec.normalize(row.get("advantage_model"));
        ArrayNode contexts = PhaseContextDerivation.derive(raw, partition);
        ObjectNode evaluations = Objects.requireNonNull(runtime.evaluateContexts(contexts.deepCopy()), "phase AST evaluator returned null");
        normalized.set("raw", raw); normalized.set("advantage_model", advantage);
        if (row.has("hard_casualty_winter")) normalized.set("hard_casualty_winter", winter(row.get("hard_casualty_winter"), base.targetProvinceId()));
        if (row.has("hard_casualty_sides")) normalized.set("hard_casualty_sides", casualtySides(row.get("hard_casualty_sides"), base.targetProvinceId(), array(raw.get("sides"), "raw sides")));
        normalized.set("state_ref_partition", partition.toJson()); normalized.set("evaluation_contexts", contexts); normalized.set("row_evaluations", evaluations.deepCopy());
        normalized.set("offline_admission", admission(true)); normalized.putNull("unavailable_reason"); return normalized;
    }
    private static ObjectNode admission(boolean ready) {
        ObjectNode out = J.objectNode().put("native_leaf_exact_count", ready ? 81 : 0).put("offline_exact_count", ready ? 51 : 0).put("determinable_count", ready ? 132 : 0).put("partition_complete", true).put("ready", ready);
        ArrayNode missing = out.putArray("missing_required_domains"); if (!ready) missing.add("phase_event_inputs"); return out;
    }
    private static boolean evaluatorReady(JsonNode evaluations, boolean ready) {
        if (!ready || !(evaluations instanceof ObjectNode row)) return false;
        JsonNode coverage = row.get("event_row_coverage"), order = row.get("candidate_materialization_and_order"), feedback = row.get("battle_horizon_feedback");
        if (!(coverage instanceof ObjectNode) || !(order instanceof ObjectNode) || !(feedback instanceof ObjectNode)) return false;
        return row.path("status").asText().equals("ready") && intEquals(coverage.get("event_row_count"), 13) && intEquals(coverage.get("trigger_ast_rows_covered"), 13)
                && intEquals(coverage.get("chance_ast_rows_covered"), 13) && intEquals(coverage.get("effect_ast_rows_covered"), 13)
                && emptyArray(coverage.get("unsupported_nodes")) && emptyArray(coverage.get("unsupported_effects")) && trueBool(coverage.get("ready")) && trueBool(row.get("ast_evaluator_ready"))
                && trueBool(order.get("ready")) && trueBool(feedback.get("ready"));
    }
    private static boolean intEquals(JsonNode node, int expected) { return node != null && node.isIntegralNumber() && node.bigIntegerValue().equals(java.math.BigInteger.valueOf(expected)); }
    private static boolean emptyArray(JsonNode node) { return node instanceof ArrayNode array && array.isEmpty(); }
    private static boolean trueBool(JsonNode node) { return node != null && node.isBoolean() && node.booleanValue(); }
    private static ObjectNode winter(JsonNode value, int target) {
        ObjectNode row = object(value, "status source_target_province_id scale first_original_guard second_original_guard raw unavailable_reason", "hard_casualty_winter");
        require(positive(row.get("source_target_province_id"), "winter source target") == target, "winter target mismatch"); scale(row.get("scale"), "winter scale");
        String status = token(row.get("status"), "winter status", "available", "unavailable");
        if (status.equals("unavailable")) {
            require(nil(row.get("first_original_guard")) && nil(row.get("second_original_guard")) && nil(row.get("raw")), "unavailable winter has partial values"); text(row.get("unavailable_reason"), "winter unavailable_reason");
        } else {
            require(nil(row.get("unavailable_reason")), "available winter has reason"); boolean first = bool(row.get("first_original_guard"), "first_original_guard");
            if (!first) require(nil(row.get("second_original_guard")) && nil(row.get("raw")), "false first guard has numeric data");
            else if (!bool(row.get("second_original_guard"), "second_original_guard")) require(nil(row.get("raw")), "false second guard has numeric data");
            else require(row.get("raw") != null && row.get("raw").isIntegralNumber(), "guarded winter raw must be integer");
        }
        return row.deepCopy();
    }
    private static ObjectNode casualtySides(JsonNode value, int target, ArrayNode phaseSides) {
        ObjectNode row = object(value, "status source_target_province_id scale sides unavailable_reason", "hard_casualty_sides");
        require(positive(row.get("source_target_province_id"), "side source target") == target, "casualty sides target mismatch"); scale(row.get("scale"), "casualty side scale");
        String status = token(row.get("status"), "casualty side status", "available", "unavailable");
        if (status.equals("unavailable")) { require(nil(row.get("sides")), "unavailable casualty readout has sides"); text(row.get("unavailable_reason"), "casualty sides unavailable_reason"); return row.deepCopy(); }
        require(nil(row.get("unavailable_reason")), "available casualty sides have reason"); ArrayNode sides = array(row.get("sides"), "casualty sides");
        require(sides.size() == 2 && phaseSides.size() == 2, "casualty readout needs two ordered sides");
        for (int index = 0; index < 2; index++) {
            ObjectNode side = object(sides.get(index), "side_index encounter_role ordered_army_ids commander_character_id own_modifier_raw enemy_modifier_raw", "casualty side"); JsonNode expected = phaseSides.get(index);
            int commander = nil(expected.get("commander_character_id")) ? -1 : positive(expected.get("commander_character_id"), "expected commander");
            require(i32(side.get("side_index"), "side_index") == index && text(side.get("encounter_role"), "encounter_role").equals(expected.path("encounter_role").asText())
                    && ids(side.get("ordered_army_ids"), false, true, "ordered_army_ids").equals(ids(expected.get("ordered_army_ids"), false, true, "expected armies"))
                    && i32(side.get("commander_character_id"), "commander_character_id") == commander, "casualty side identity differs from same-frame phase");
            i64(side.get("own_modifier_raw"), "own_modifier_raw"); i64(side.get("enemy_modifier_raw"), "enemy_modifier_raw");
        }
        return row.deepCopy();
    }
    /** Compare the JSON type domain: integer widths are serialization details; bool/float/null/missing stay distinct. */
    public static boolean sameJson(JsonNode left, JsonNode right) {
        if (left == null || right == null) return left == right;
        if (left.isIntegralNumber() || right.isIntegralNumber()) return left.isIntegralNumber() && right.isIntegralNumber() && left.bigIntegerValue().equals(right.bigIntegerValue());
        if (left.isObject() && right.isObject()) {
            Set<String> a = new HashSet<>(), b = new HashSet<>(); left.fieldNames().forEachRemaining(a::add); right.fieldNames().forEachRemaining(b::add); if (!a.equals(b)) return false;
            for (String key : a) if (!sameJson(left.get(key), right.get(key))) return false; return true;
        }
        if (left.isArray() && right.isArray()) { if (left.size() != right.size()) return false; for (int index = 0; index < left.size(); index++) if (!sameJson(left.get(index), right.get(index))) return false; return true; }
        return left.equals(right);
    }
}
