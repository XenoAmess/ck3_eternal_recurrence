package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original public object shape. Declared 64-bit identities/raw scalars use decimal text; bounded numbers retain JSON number. */
public final class ArmyPublicWire {
    private static final BigInteger SAFE = BigInteger.valueOf(9_007_199_254_740_991L);
    private static final Set<String> META = Set.of("queried_snapshot_id", "queried_revision", "queried_native_revision");
    private static final Set<String> RETIRED = Set.of("public_wire_schema", "integer_paths");
    /** Explicit original uint64 fields, shared across the closed Army13 producer schemas. No suffix inference. */
    private static final Set<String> UNSIGNED64 = Set.of(
            "revision", "native_revision", "snapshot_revision", "expected_snapshot_revision", "expected_native_revision", "observation_revision", "observation_native_revision",
            "query_sequence", "capture_epoch", "epoch", "pump_epoch", "ticket_sequence", "executor_started_sequence", "completed_sequence", "connection_generation", "queried_connection_generation",
            "requested_after_sequence", "oldest_available_sequence", "latest_sequence", "event_sequence", "after_terminal_sequence",
            "capture_sequence", "preparation_capture_sequence", "latest_record_sequence", "record_sequence", "overwritten_records", "install_epoch",
            "physical_entry_identity", "clock_identity", "sequence", "combat_identity", "caller_return_rva", "caller_return_slot", "raw_return_bits",
            "data_address", "scratch_address", "model_address", "context_address", "owner_address", "date_object_raw_u64",
            "maximum_payload_bytes", "row_copy_budget", "creation_filetime", "process_creation_filetime", "bridge_process_creation_filetime", "file_id");
    /** Original native pointer tokens are restored as hexadecimal text only inside the original native decoder lane. */
    private static final Set<String> HEX_IDENTITIES = Set.of(
            "character_identity", "context_identity", "model_a_identity", "model_b_identity", "original_return_rva",
            "preparation_character_identity", "preparation_model_identity", "preparation_context_identity", "preparation_owner_character_identity",
            "observed_owner_identity", "observed_context_identity", "observed_model_identity", "owner_identity", "model_identity",
            "scratch_identity", "data_identity", "payload_identity", "array_identity", "receiver_identity", "entry_identity",
            "source_return_rva", "extension_identity", "row_array_identity", "pc_identity", "owner_character_identity",
            "model_a_owner_identity", "model_b_owner_identity", "carrier_identity", "installed_model_identity", "installed_model_owner_identity",
            "matching_installed_inline_context_identity", "storage_identity", "block_identity", "allocator_receiver_identity", "allocator_identity", "allocator_dispatch_vtable_identity");
    private static final Set<String> SIGNED64 = Set.of("hire_duration_months", "current_regiment_soldiers", "maximum_regiment_soldiers",
            "positive_siege_tier_current_soldiers", "request_power_basis_raw", "cross_coordinator_request_power_raw", "first_route_edge_remaining_duration_q100000",
            "base_advantage_raw", "base_toughness_multiplier_raw", "context_scale_raw", "counter_efficiency_raw", "counter_resistance_raw", "current_chunk_raw", "current_fighting_raw",
            "derived_current_fighting_raw", "derived_main_fighting_entry_hard_casualties_raw", "derived_soft_casualties_raw", "effective_damage_raw", "effective_pursuit_raw", "effective_screen_raw", "effective_siege_raw", "effective_toughness_raw", "effectiveness_raw",
            "enemy_modifier_raw", "hard_casualties_raw", "minimum_pursuit_multiplier_raw", "non_main_start_minus_current_minus_soft_raw", "opposing_hard_conversion_modifier_raw", "outgoing_advantage_factor_raw", "own_hard_conversion_modifier_raw", "own_modifier_raw", "participant_hard_total_raw",
            "province_winter_hard_conversion_modifier_raw", "pursuit_efficiency_raw", "pursuit_stat_multiplier_raw", "resolved_advantage_raw", "retreat_losses_raw", "runtime_damage_scaling_raw", "runtime_main_hard_conversion_raw", "runtime_pursuit_hard_conversion_raw", "soft_casualties_raw", "starting_raw",
            "stored_advantage_damage_factor_raw", "stored_current_fighting_raw", "stored_levy_current_fighting_raw", "stored_terminal_loss_baseline_raw", "weight_q100000", "weight_raw", "score_q64", "raw_value_q64", "scale_q64",
            "province_multiplier_raw", "holding_modifier_raw", "multiplier_raw", "signed_contribution_raw", "retained_contribution_raw", "current_holding_multiplier_raw", "side_dynamic_total_raw", "current_getter_resolution_raw", "current_minus_stored_raw", "stored_resolved_advantage_raw",
            "side_total_from_components_raw", "observed_direct_total_raw", "components_minus_direct_raw", "eligible_contribution_raw", "eligible_contribution_sum_raw", "own_modifier_19F_raw", "eligible_opposite_retained_sum_raw", "nested_contribution_raw", "amount_raw", "total_raw",
            "combat_width_multiplier_raw", "contribution_raw", "cross_coordinator_request_valid_raw", "elapsed_whole_days", "initial_loser_levy_soft_raw", "initial_loser_maa_soft_raw", "levy_damage_raw", "runtime_advantage_scaling_raw",
            "knight_effectiveness_raw", "province_evaluated_damage_raw", "province_evaluated_toughness_raw", "stored_combat_entry_damage_raw", "stored_combat_entry_toughness_raw", "weight_q64",
            "base430_q64", "base438_q64", "prepared430_q64", "prepared438_q64", "copied430_q64", "copied438_q64",
            "attacker_relative_delta_raw_q100000", "baseline_raw_q100000", "survivors_raw_q100000", "value_raw_q100000", "selected_cb_battle_scale_raw_q100000", "war_attacker_winner_cap_raw_q100000", "war_defender_winner_cap_raw_q100000",
            "province_component_raw", "commander_modifier_1a9_raw", "loaded_gain_raw", "loaded_excess_slope_raw", "loaded_min_loss_raw", "loaded_max_loss_raw", "loaded_divisor_floor_raw");
    private static final Set<String> SIGNED64_ARRAYS = Set.of("resource_costs_raw", "values_q64", "thresholds_used_q64");
    private static final Set<String> HEX64_ARRAYS = Set.of("values_q64_raw_bits", "ordered_payload_raw64");
    /* These fields belong to the additional actual war/forecast producers, not to an inferred suffix rule. */
    private static final Set<String> WAR_UNSIGNED64 = Set.of("queried_revision", "queried_native_revision", "public_revision",
            "declaration_query_sequence", "assessment_query_sequence", "ticket");
    /* Original _execute_native_war_step merge/halt formatter paths, plus its retained execute_step rejection frame.
       These do not assign uint64 meaning to similarly named fields elsewhere. */
    private static final Set<String> STRUCTURAL_UNSIGNED64_PATHS = Set.of(
            "/war_action/submitted_public_revision", "/war_action/submitted_native_revision",
            "/war_action/submitted_connection_generation", "/war_action/observed_public_revision",
            "/war_action/observed_native_revision", "/halt_rejection_evidence/native_request/expected_revision",
            "/native_error_evidence/native_request/expected_revision",
            "/readonly_unavailable_evidence/native_request/expected_revision",
            "/native_request_frame/expected_revision");
    private static final Set<String> WAR_SIGNED64 = Set.of("faith_fervor_raw", "raised_current_soldiers", "raised_maximum_soldiers",
            "actor_ready_unraised_lower_soldiers", "enemy_upper_soldiers", "distance_raw", "actor_power_base_raw",
            "actor_network_contribution_raw", "actor_power_total_raw", "target_power_base_raw", "target_network_contribution_raw",
            "target_pre_adjustment_total_raw", "target_adjustment_delta_raw", "target_power_total_raw", "actual_power_ratio_raw", "chance_raw");
    /* Closed combat normalizer schemas and PUBLIC-WIRE-FIELDS05; names are explicit, never suffix-derived.
       These rules apply only under the five admitted original combat result subtrees. */
    private static final Set<String> COMBAT_UNSIGNED64 = Set.of("overwritten_events", "wrapper_caller_return_rva",
            "writer_sequence", "original_return_value", "consumed_return_rva", "preparation_source_return_rva",
            "getter_caller_return_rva", "native_session_generation", "linked_character_identity", "selected_character_identity",
            "output_cache_identity", "native_return_identity", "province_identity", "getter_context_identity",
            "returned_character_identity", "returned_context_identity", "consumed_pc_identity", "preparation_source_pc_identity",
            "preparation_pc_identity", "b_before_pc_identity", "a_after_pc_identity", "consumed_context_identity");
    private static final Set<String> COMBAT_SIGNED64 = Set.of("projected_effectiveness_raw", "operand_raw", "modifier_raw",
            "operand_q64", "modifier_q64", "term_q64", "accumulated_q64", "common_wrap64_product", "value_q64",
            "siege_value_raw", "damage_raw", "toughness_raw", "pursuit_raw", "screen_raw",
            "wounded_rank_raw", "fragile_bones_rank_raw", "fragile_bones_xp_raw", "lifestyle_blademaster_xp_raw",
            "tourney_bow_xp_raw", "tourney_foot_xp_raw", "tourney_horse_xp_raw", "liege_accolade_progress_raw");
    private static final Set<String> COMBAT_SUMS = Set.of(
            "/current_special_knight_initial_value/ready_member_contributions_by_role/attacker/ready_member_damage_raw_sum",
            "/current_special_knight_initial_value/ready_member_contributions_by_role/attacker/ready_member_toughness_raw_sum",
            "/current_special_knight_initial_value/ready_member_contributions_by_role/defender/ready_member_damage_raw_sum",
            "/current_special_knight_initial_value/ready_member_contributions_by_role/defender/ready_member_toughness_raw_sum");
    private ArmyPublicWire() { }

    /**
     * Preserve the caller's already validated original public object shape. Unlike encode, this does
     * not invent queried_* fields. An existing source triplet must be complete, native integer typed
     * and exactly equal to the supplied actual context. This conversion grants no read authority.
     */
    public static RawJson encodeExactSourceBound(Obj strictSourceResult, Context source) {
        java.util.Objects.requireNonNull(source);
        ObjectNode n = object(OpportunityJson.toNode(strictSourceResult)).deepCopy();
        require(java.util.Collections.disjoint(names(n), RETIRED), "retired Army wrapper is not an original public object");
        requireBoundMetadata(n, source);
        project(n, "", false, true);
        return new RawJson(bytes(n));
    }

    /** Restore only the declared integer representation; callers still run the original domain decoder. */
    public static Obj decodeExactSourceBound(RawJson encoded, Context source) {
        java.util.Objects.requireNonNull(source);
        ObjectNode n = parse(encoded.bytes()).deepCopy();
        require(java.util.Collections.disjoint(names(n), RETIRED), "retired Army wrapper is not an original public object");
        project(n, "", true, true);
        requireBoundMetadata(n, source);
        Obj restored = DriverJson.object(bytes(n), DriverJson.MAX_NATIVE_BYTES);
        require(encodeExactSourceBound(restored, source).equals(encoded), "noncanonical exact Army public object");
        return restored;
    }

    private static void requireBoundMetadata(ObjectNode n, Context source) {
        long count = META.stream().filter(n::has).count();
        require(count == 0 || count == META.size(), "partial queried source triplet is invalid");
        if (count != 0) {
            equal(get(n, "queried_snapshot_id"), source.before().frame().snapshotId());
            require(integer(get(n, "queried_revision")).equals(source.before().frame().revision())
                    && integer(get(n, "queried_native_revision")).equals(source.nativeRevision()), "existing public source triplet differs from actual context");
        }
    }

    /** Caller first runs its complete original domain validator; projection grants no native or gameplay authority. */
    public static RawJson encode(Obj strictNativeValue, Context source) {
        ObjectNode n = object(OpportunityJson.toNode(strictNativeValue)).deepCopy();
        require(java.util.Collections.disjoint(names(n), META) && java.util.Collections.disjoint(names(n), RETIRED), "native payload collides with public source metadata or retired ABI");
        project(n, "", false);
        n.put("queried_snapshot_id", source.before().frame().snapshotId()).put("queried_revision", source.before().frame().revision().toString())
                .put("queried_native_revision", source.nativeRevision().toString());
        return new RawJson(bytes(n));
    }

    /** Restore declared native types; the route's strict domain validator remains mandatory after this conversion. */
    public static Obj decode(RawJson encoded, Context source) {
        ObjectNode n = parse(encoded.bytes()).deepCopy();
        require(java.util.Collections.disjoint(names(n), RETIRED), "retired all-string Army ABI is not an original public object");
        equal(get(n, "queried_snapshot_id"), source.before().frame().snapshotId());
        require(decimal(get(n, "queried_revision")).equals(source.before().frame().revision())
                && decimal(get(n, "queried_native_revision")).equals(source.nativeRevision()), "public Army source changed");
        n.remove(META); project(n, "", true);
        Obj restored = DriverJson.object(bytes(n), DriverJson.MAX_NATIVE_BYTES);
        require(encode(restored, source).equals(encoded), "public Army representation is not canonical");
        return restored;
    }

    /** The sole Driver BattleControl cache uses the same closed operand/identity roles as its original public query.
     * This is pure DATA conversion; the archived strict decoder and cache writer own all source qualification. */
    public static Obj encodeBattleControlCache(Obj originalNumeric) { return battleControlCache(originalNumeric, false); }
    public static Obj decodeBattleControlCache(Obj canonicalPublic) { return battleControlCache(canonicalPublic, true); }
    private static Obj battleControlCache(Obj fields, boolean restoring) {
        require(fields.members().keySet().equals(Set.of("battle_control_snapshot_v1", "active_combat_resume_inputs_v1")),
                "exact two BattleControl cache payload slots required");
        ObjectNode nativeShape = empty();
        nativeShape.set("battle_control_snapshot", OpportunityJson.toNode(fields.get("battle_control_snapshot_v1")));
        nativeShape.set("active_combat_resume_inputs_v1", OpportunityJson.toNode(fields.get("active_combat_resume_inputs_v1")));
        project(nativeShape, "", restoring); // Exactly the existing ArmyBattlePublicPresenter native schema.
        ObjectNode cacheShape = empty();
        cacheShape.set("battle_control_snapshot_v1", nativeShape.get("battle_control_snapshot"));
        cacheShape.set("active_combat_resume_inputs_v1", nativeShape.get("active_combat_resume_inputs_v1"));
        return DriverJson.object(bytes(cacheShape), DriverJson.MAX_NATIVE_BYTES);
    }

    private static void project(JsonNode node, String path, boolean restoring) { project(node, path, restoring, false); }
    private static void project(JsonNode node, String path, boolean restoring, boolean exactWar) {
        if (node instanceof ObjectNode object) {
            for (String key : List.copyOf(names(object))) {
                JsonNode value = object.get(key); String child = path + "/" + key;
                if (value.isNull()) continue;
                boolean combat = exactWar && combatPath(child);
                boolean captureHex = combat && (path.contains("/preparation_capture_at_consumption/")
                        || path.endsWith("/preparation_capture_at_consumption") || path.contains("/preparation_at_entry/")
                        || path.endsWith("/preparation_at_entry") || path.contains("/owned_capture_compositions/"));
                if (combat && COMBAT_SUMS.contains(child)) {
                    BigInteger exact = restoring ? unboundedDecimal(value) : integer(value);
                    if (restoring) object.put(key, exact); else object.put(key, exact.toString());
                    continue;
                }
                boolean hex = HEX_IDENTITIES.contains(key) || (key.equals("clock_identity") && path.startsWith("/person_installed_transfers/"))
                        || (key.equals("identity") && (path.startsWith("/person_six_stage_captures/") || path.startsWith("/person_installed_transfers/")));
                if (combat) hex = captureHex && (HEX_IDENTITIES.contains(key) || key.equals("identity"));
                boolean wide = hex || UNSIGNED64.contains(key) || (combat && (HEX_IDENTITIES.contains(key)
                        || COMBAT_UNSIGNED64.contains(key) || (key.equals("identity") && path.endsWith("/consumed_pc"))))
                        || (exactWar && (WAR_UNSIGNED64.contains(key)||STRUCTURAL_UNSIGNED64_PATHS.contains(child))), signed = SIGNED64.contains(key)
                        || (combat && COMBAT_SIGNED64.contains(key)) || (exactWar && WAR_SIGNED64.contains(key))
                        || (key.equals("raw") && (path.endsWith("/commander") || path.endsWith("/side_aggregate")));
                if (combat && HEX64_ARRAYS.contains(key)) {
                    require(value instanceof ArrayNode, "normalized combat raw bits array required: " + child);
                    ArrayNode values = (ArrayNode)value;
                    for (int index = 0; index < values.size(); index++) {
                        BigInteger exact = restoring ? decimal(values.get(index)) : new UInt64(integer(values.get(index))).value();
                        if (restoring) values.set(index, empty().numberNode(exact)); else values.set(index, empty().textNode(exact.toString()));
                    }
                    continue;
                }
                if (HEX64_ARRAYS.contains(key) && path.startsWith("/person_installed_transfers/")) {
                    require(value instanceof ArrayNode, "declared native raw64 array required: " + child); ArrayNode values = (ArrayNode)value;
                    for (int index = 0; index < values.size(); index++) {
                        BigInteger exact;
                        if (restoring) { exact = decimal(values.get(index)); String bits = exact.toString(16); values.set(index, empty().textNode("0x" + "0".repeat(16 - bits.length()) + bits)); }
                        else { String bits = text(values.get(index)); require(bits.matches("0x[0-9a-fA-F]{16}"), "native raw64 retains sixteen hex digits: " + child); exact = new UInt64(new BigInteger(bits.substring(2), 16)).value(); values.set(index, empty().textNode(exact.toString())); }
                    }
                    continue;
                }
                if (SIGNED64_ARRAYS.contains(key) || (combat && (key.equals("modifier_raw") || key.equals("operand_raw")) && value.isArray()) || (key.equals("items") && path.endsWith("/value_array"))) {
                    require(value instanceof ArrayNode, "declared raw64 array required: " + child);
                    ArrayNode values = (ArrayNode) value;
                    for (int index = 0; index < values.size(); index++) {
                        if (values.get(index).isNull()) continue;
                        BigInteger exact = restoring ? signedDecimal(values.get(index)) : signedNative(values.get(index));
                        if (restoring) values.set(index, empty().numberNode(exact)); else values.set(index, empty().textNode(exact.toString()));
                    }
                    continue;
                }
                if (signed) {
                    BigInteger exact = restoring ? signedDecimal(value) : signedNative(value);
                    if (restoring) object.put(key, exact); else object.put(key, exact.toString());
                    continue;
                }
                if (wide) {
                    if (restoring) {
                        BigInteger exact = decimal(value);
                        if (hex) object.put(key, "0x" + exact.toString(16)); else object.put(key, exact);
                    } else {
                        BigInteger exact;
                        if (value.isTextual()) {
                            String token = text(value);
                            require(token.matches("0x[0-9a-fA-F]+"), "native 64-bit identity must retain its native integer or hex domain: " + child);
                            exact = new UInt64(new BigInteger(token.substring(2), 16)).value();
                        } else exact = new UInt64(integer(value)).value();
                        object.put(key, exact.toString());
                    }
                } else if (value.isIntegralNumber()) requireSafe(value, child);
                else project(value, child, restoring, exactWar);
            }
        } else if (node instanceof ArrayNode array) {
            for (int index = 0; index < array.size(); index++) {
                JsonNode value = array.get(index); String child = path + "/" + index;
                if (value.isIntegralNumber()) requireSafe(value, child); else project(value, child, restoring, exactWar);
            }
        }
    }
    private static boolean combatPath(String path) {
        return path.startsWith("/combat_simulation_inputs/") || path.startsWith("/knight_stat_consumption_projection_v1/")
                || path.startsWith("/current_special_knight_initial_value/")
                || path.startsWith("/current_physical_entry_writeback_association_v1/") || path.startsWith("/loaded_playset_proof/");
    }
    private static BigInteger unboundedDecimal(JsonNode value) {
        String token = text(value); require(token.matches("0|-?[1-9][0-9]*"), "canonical mathematical integer text required");
        return new BigInteger(token);
    }
    private static BigInteger integer(JsonNode value) { require(value != null && value.isIntegralNumber(), "native integer identity required; bool and floating point are invalid"); return value.bigIntegerValue(); }
    private static BigInteger decimal(JsonNode value) { String token = text(value); require(token.matches("0|[1-9][0-9]*"), "canonical unsigned decimal public identity required"); return new UInt64(new BigInteger(token)).value(); }
    private static BigInteger signedNative(JsonNode value) { return signedRange(integer(value)); }
    private static BigInteger signedDecimal(JsonNode value) { String token = text(value); require(token.matches("0|-?[1-9][0-9]*"), "canonical signed decimal raw64 required"); return signedRange(new BigInteger(token)); }
    private static BigInteger signedRange(BigInteger value) { require(value.compareTo(BigInteger.valueOf(Long.MIN_VALUE)) >= 0 && value.compareTo(BigInteger.valueOf(Long.MAX_VALUE)) <= 0, "signed raw64 out of range"); return value; }
    private static void requireSafe(JsonNode value, String path) { require(integer(value).abs().compareTo(SAFE) <= 0, "undeclared numeric integer exceeds exact public range: " + path); }
}

