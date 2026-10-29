package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class BattleControlExtensionCodecTest {
    private static ObjectNode fixture;
    @BeforeAll static void originalFixture() throws Exception { fixture = BattleOriginalOracle.fixture(); }
    private static ObjectNode parent() { return object(fixture.get("parent")).deepCopy(); }
    private static ArrayNode arrayNode() { return empty().arrayNode(); }
    private static ObjectNode actual(ObjectNode raw) {
        var value = OpportunityJson.object(OpportunityJson.parse(bytes(raw)), "BattleControl test producer");
        return parse(OpportunityJson.encode(BattleResponseCodec.normalizeControl(value, i32(raw.get("subject_public_cunit_id")),
                integer(raw.get("snapshot_revision")), i64(raw.get("observed_date_raw")))));
    }
    private static void assertDomain(JsonNode expected, JsonNode actual) { assertDoesNotThrow(() -> BattleControlExtensionCodec.same(expected, actual)); }
    private static ObjectNode available(String key, long raw) { ObjectNode n = empty(); n.put("status", "available"); n.put(key, raw); n.putNull("unavailable_reason"); return n; }
    private static ObjectNode selection() { ObjectNode n = available("resolved_character_id_raw", -1); n.put("used_native_fallback", false); return n; }
    private static ObjectNode geography() {
        ObjectNode g = empty(); ObjectNode terrain = available("combat_width_multiplier_raw", 0); terrain.put("scale", 100_000); terrain.put("key", "plains"); g.set("terrain", terrain); g.put("constructor_adjacency_kind_raw", 0); g.put("holding_defender", false);
        ObjectNode effects = empty(); effects.put("status", "available"); effects.put("points_scale", 1); effects.putNull("unavailable_reason"); ArrayNode effectRows = arrayNode();
        for (int i = 0; i < 3; i++) { ObjectNode r = empty(); r.put("stage", List.of("attacker_adjacency", "defender_adjacency", "holding_defender").get(i)); r.put("side_index", i == 0 ? 0 : 1); r.put("rules_pointer_offset", i == 0 ? 0xF70 : i == 1 ? 0xFA0 : 0xF10); r.put("status", "available"); r.put("key", i == 2 ? "holding_defender_advantage" : "river_crossing"); r.put("advantage_points", 0); r.putNull("unavailable_reason"); effectRows.add(r); }
        effects.set("rows", effectRows); g.set("constructor_rule_effects_v1", effects);
        ObjectNode context = empty(), holding = empty(), commander = empty(); holding.put("status", "not_applicable"); holding.put("scale", 100_000);
        for (String key : List.of("province_multiplier_raw", "province_has_holding", "holding_modifier_raw", "unavailable_reason")) holding.putNull(key);
        commander.put("status", "available"); commander.put("selected_character_id_raw", -1); commander.put("used_native_fallback", false); commander.put("defender_adjacency_excluded", false); commander.putNull("unavailable_reason"); context.set("holding_multiplier", holding); context.set("commander_exclusion", commander); g.set("current_rule_context_v1", context);
        ObjectNode stored = empty(); stored.put("scale", 100_000); stored.put("base_advantage_raw", -5_000_000_000L); stored.put("resolved_advantage_raw", 6_000_000_000L); ArrayNode ledgers = arrayNode();
        ObjectNode dynamic = empty(); dynamic.put("scale", 100_000); dynamic.put("base_advantage_raw", -5_000_000_000L); dynamic.put("stored_resolved_advantage_raw", 6_000_000_000L); ArrayNode dynamics = arrayNode();
        ObjectNode components = empty(); components.put("scale", 100_000); ArrayNode componentRows = arrayNode(); ObjectNode own = empty(); own.put("scale", 100_000); own.put("modifier_id", 415); ArrayNode ownRows = arrayNode();
        for (int i = 0; i < 2; i++) {
            ObjectNode ledger = empty(); ledger.put("side_index", i); ledger.put("status", "available"); ledger.putNull("unavailable_reason"); ObjectNode row = empty(); row.put("effect_key", "retained_source"); row.putNull("key_unavailable_reason"); row.put("contribution_raw", Long.MIN_VALUE);
            ObjectNode flags = empty(); flags.put("status", "available"); flags.put("flag88_raw", 0); flags.put("flag89_raw", 255); flags.putNull("unavailable_reason"); row.set("effect_flags_v1", flags); ledger.set("rows", arrayNode().add(row)); ledgers.add(ledger);
            ObjectNode d = available("side_dynamic_total_raw", Long.MIN_VALUE); d.put("side_index", i); d.put("current_roll_points", 0); d.put("selected_character_id_raw", -1); dynamics.add(d);
            ObjectNode c = empty(); c.put("side_index", i); c.put("current_roll_points", 0); c.put("selected_character_id_raw", -1); c.set("selection", selection()); c.set("relation", available("kind_raw", -1)); c.set("commander", available("total_raw", 0)); c.set("side_aggregate", available("total_raw", Long.MAX_VALUE)); componentRows.add(c);
            ObjectNode o = empty(); o.put("side_index", i); o.put("selected_character_id_raw", -1); o.set("selection", selection()); o.set("combat_side_aggregate", available("amount_raw", 0)); o.set("selected_character_aggregate", available("amount_raw", Long.MIN_VALUE)); ownRows.add(o);
        }
        stored.set("sides", ledgers); dynamic.set("sides", dynamics); components.set("sides", componentRows); own.set("sides", ownRows);
        g.set("stored_advantage_sources_v1", stored); g.set("current_dynamic_advantage_v1", dynamic); g.set("current_dynamic_components_v1", components); g.set("current_own_nested_modifier_v1", own); return g;
    }
    private static ObjectNode full() {
        ObjectNode p = parent(); int combat = i32(p.get("combat_id")), province = i32(p.get("province_id")); p.put("roll_cadence_interval", 0);
        ObjectNode phase = empty(); phase.put("forced_winner_raw", -1); phase.put("result_start_date_raw", 0); phase.put("minimum_elapsed_days", 0); ArrayNode phaseSides = arrayNode(), backingSides = arrayNode(), lossSides = arrayNode(), hardSides = arrayNode(), pursuitSides = arrayNode();
        for (int i = 0; i < 2; i++) {
            ObjectNode source = object(p.get(i == 0 ? "attacker" : "defender")); ObjectNode s = empty(); s.put("side_index", i); s.put("stored_current_fighting_raw", 0L); s.put("disallowed", false); s.put("allow_early", true); s.put("skip_pursuit", false); s.set("first_native_carmy_id", source.path("ordered_armies").get(0).get("native_carmy_id")); s.putNull("native_can_retreat"); s.putNull("owner_land_rule_allows"); phaseSides.add(s);
            ObjectNode backing = empty(); backing.put("side_index", i); ArrayNode armies = arrayNode();
            for (JsonNode sourceArmy : source.path("ordered_armies")) { ObjectNode army = empty(); for (String key : List.of("native_carmy_id", "public_cunit_id", "owner_character_id")) army.set(key, sourceArmy.get(key)); ObjectNode regiment = empty(); regiment.put("regiment_id", 0); regiment.put("current_soldiers", -1); army.set("ordered_regiments", arrayNode().add(regiment)); armies.add(army); } backing.set("ordered_armies", armies); backingSides.add(backing);
            ObjectNode loss = empty(); loss.put("side_index", i); loss.put("outgoing_advantage_factor_raw", 100_000); loss.put("own_hard_conversion_modifier_raw", Long.MIN_VALUE); loss.put("opposing_hard_conversion_modifier_raw", 0); loss.set("primary_participant_character_id", source.get("primary_participant_character_id")); loss.putNull("levy_damage_raw"); lossSides.add(loss);
            ObjectNode hard = empty(); hard.put("side_index", i); hard.put("encounter_role", i == 0 ? "attacker" : "defender"); ArrayNode ids = arrayNode(); for (JsonNode army : source.path("ordered_armies")) ids.add(army.get("public_cunit_id")); hard.set("ordered_army_ids", ids); hard.put("commander_character_id", source.get("selected_commander_character_id").isNull() ? -1 : i32(source.get("selected_commander_character_id"))); hard.put("own_modifier_raw", Long.MIN_VALUE); hard.put("enemy_modifier_raw", Long.MAX_VALUE); hardSides.add(hard);
            ObjectNode pursuit = empty(); pursuit.put("side_index", i); pursuit.put("encounter_role", i == 0 ? "attacker" : "defender"); pursuit.put("pursuit_efficiency_raw", 0); pursuit.put("retreat_losses_raw", -1); pursuitSides.add(pursuit);
        }
        phase.set("sides", phaseSides); p.set("current_phase_transition_inputs_v1", phase);
        ObjectNode backing = empty(); backing.put("scale", 1); backing.put("source_combat_id", combat); backing.put("source_target_province_id", province); backing.put("enumeration_complete", true); backing.set("sides", backingSides); p.set("full_backing_inputs_v1", backing);
        ObjectNode loss = empty(); loss.put("scale", 100_000); loss.put("source_combat_id", combat); loss.put("source_target_province_id", province); loss.put("province_has_holding", false); for (String key : List.of("stored_advantage_damage_factor_raw", "runtime_damage_scaling_raw", "runtime_main_hard_conversion_raw", "runtime_pursuit_hard_conversion_raw", "province_winter_hard_conversion_modifier_raw")) loss.put(key, 0); loss.putNull("runtime_advantage_scaling_raw"); loss.set("sides", lossSides); p.set("current_loss_inputs_v1", loss);
        for (String key : List.of("actual_hard_casualty_sides", "pursuit_modifier_sides")) { ObjectNode leaf = empty(); leaf.put("status", "available"); leaf.put("source_combat_id", combat); leaf.put("source_target_province_id", province); leaf.put("scale", 100_000); leaf.putNull("unavailable_reason"); leaf.set("sides", key.equals("actual_hard_casualty_sides") ? hardSides : pursuitSides); p.set(key, leaf); }
        ObjectNode manager = empty(); manager.put("source_combat_id", combat); manager.put("combat_manager_row_admitted", false); manager.put("pending_suppression_sweep_raw", 0); manager.put("pending_suppression_sweep", false); p.set("current_finalizer_manager_inputs_v1", manager);
        ObjectNode caps = empty(); caps.put("source_combat_id", combat); caps.put("war_attacker_winner_cap_raw_q100000", Long.MIN_VALUE); caps.put("war_defender_winner_cap_raw_q100000", Long.MAX_VALUE); p.set("current_warscore_caps_v1", caps);
        ObjectNode pursuit = empty(); pursuit.put("scale", 100_000); pursuit.put("source_combat_id", combat); pursuit.put("pursuit_phase_days", -1); pursuit.put("base_toughness_multiplier_raw", 0); pursuit.put("minimum_pursuit_multiplier_raw", Long.MIN_VALUE); pursuit.put("pursuit_stat_multiplier_raw", Long.MAX_VALUE); for (String key : List.of("losing_side_index", "initial_loser_levy_soft_raw", "initial_loser_maa_soft_raw", "losing_side_skip_pursuit")) pursuit.putNull(key); p.set("current_pursuit_inputs_v1", pursuit);
        p.set("active_counter_inputs_v1", fixture.get("counter").deepCopy()); p.set("actual_geography_v1", geography());
        ObjectNode preceding = empty(); preceding.put("schema", "xar.ck3.entry-preceding-capture-12004-v1"); preceding.put("configured", false); preceding.put("installed", false); preceding.put("request_filtered", true); preceding.put("install_failure_flags", 0); preceding.put("latest_record_sequence", new BigInteger("18446744073709551615")); preceding.put("overwritten_records", 0); preceding.put("full_entry", false); preceding.set("records", arrayNode()); p.set("entry_preceding_capture_12004", preceding); return p;
    }
    @Test void fullActualProducerCoreExtensionsAndPersistenceMatchOriginal() throws Exception {
        ObjectNode source = full(), expected = BattleOriginalOracle.normalizeControl(source, i32(source.get("subject_public_cunit_id")), integer(source.get("snapshot_revision")), i64(source.get("observed_date_raw")));
        ObjectNode normalized = actual(source); assertDomain(expected, normalized); assertDomain(normalized, actual(parse(bytes(normalized))));
        assertEquals(12, BattleControlExtensionCodec.OPTIONAL_FIELDS.stream().filter(normalized::has).count()); assertFalse(normalized.path("current_finalizer_manager_inputs_v1").path("pending_suppression_sweep").booleanValue());
    }
    @Test void oldAbsentAndExplicitNullRemainDistinct() {
        ObjectNode old = parent(); assertDomain(old, actual(old));
        for (String key : List.of("roll_cadence_interval", "current_phase_transition_inputs_v1", "current_finalizer_manager_inputs_v1", "current_warscore_caps_v1", "current_pursuit_inputs_v1", "current_loss_inputs_v1", "full_backing_inputs_v1", "actual_geography_v1", "entry_preceding_capture_12004")) { ObjectNode n = parent(); n.putNull(key); assertTrue(actual(n).get(key).isNull(), key); assertFalse(actual(old).has(key)); }
        for (String key : List.of("actual_hard_casualty_sides", "pursuit_modifier_sides", "active_counter_inputs_v1")) { ObjectNode n = parent(); n.putNull(key); assertThrows(IllegalArgumentException.class, () -> actual(n), key); }
    }
    @Test void everyOptionalObjectRejectsWrongAndUnknownFieldsExceptDocumentedRawSidecar() {
        for (String key : BattleControlExtensionCodec.OPTIONAL_FIELDS) {
            if (key.equals("roll_cadence_interval")) continue; ObjectNode n = full(); object(n.get(key)).put("invented", true);
            if (key.equals("entry_preceding_capture_12004")) assertTrue(actual(n).get(key).isNull());
            else assertThrows(IllegalArgumentException.class, () -> actual(n), key);
        }
        for (String key : List.of("full_backing_inputs_v1", "current_loss_inputs_v1", "current_pursuit_inputs_v1", "active_counter_inputs_v1", "actual_hard_casualty_sides", "pursuit_modifier_sides")) {
            ObjectNode n = full(); object(n.get(key)).put("source_combat_id", 42); assertThrows(IllegalArgumentException.class, () -> actual(n), key);
            ObjectNode bool = full(); object(bool.get(key)).put("scale", true); assertThrows(IllegalArgumentException.class, () -> actual(bool), key);
            ObjectNode floating = full(); object(floating.get(key)).put("scale", 100000.0); assertThrows(IllegalArgumentException.class, () -> actual(floating), key);
        }
    }
    @Test void counterCensusChunkDirectionalBindingsAndInt64TypesAreStrict() {
        ObjectNode n = full(); object(n.path("active_counter_inputs_v1").path("sides").get(1).path("men_at_arms_entries").get(0)).put("current_chunk_raw", 1); assertThrows(IllegalArgumentException.class, () -> actual(n));
        ObjectNode direction = full(); object(direction.path("active_counter_inputs_v1").path("contexts").get(0)).put("countering_side_index", 0); assertThrows(IllegalArgumentException.class, () -> actual(direction));
        ObjectNode overflow = full(); object(overflow.path("current_loss_inputs_v1")).put("runtime_damage_scaling_raw", BigInteger.ONE.shiftLeft(63)); assertThrows(IllegalArgumentException.class, () -> actual(overflow));
        ObjectNode floating = full(); object(floating.path("actual_hard_casualty_sides").path("sides").get(0)).put("own_modifier_raw", 0.0); assertThrows(IllegalArgumentException.class, () -> actual(floating));
        ObjectNode mirror = full(); object(mirror.get("current_finalizer_manager_inputs_v1")).put("pending_suppression_sweep_raw", 1); assertThrows(IllegalArgumentException.class, () -> actual(mirror));
    }
    @Test void geographyValidatesEveryRetainedAndCurrentNestedBranch() {
        for (String key : List.of("constructor_rule_effects_v1", "current_rule_context_v1", "stored_advantage_sources_v1", "current_dynamic_advantage_v1", "current_dynamic_components_v1", "current_own_nested_modifier_v1")) {
            ObjectNode n = full(); object(n.path("actual_geography_v1").get(key)).put("invented", 0); assertThrows(IllegalArgumentException.class, () -> actual(n), key);
        }
        ObjectNode flags = full(); object(flags.path("actual_geography_v1").path("stored_advantage_sources_v1").path("sides").get(0).path("rows").get(0).path("effect_flags_v1")).put("flag89_raw", 256); assertThrows(IllegalArgumentException.class, () -> actual(flags));
        ObjectNode source = full(); object(source.path("actual_geography_v1").path("constructor_rule_effects_v1").path("rows").get(1)).put("rules_pointer_offset", 0); assertThrows(IllegalArgumentException.class, () -> actual(source));
        ObjectNode context = full(); object(context.path("actual_geography_v1").path("current_rule_context_v1").path("holding_multiplier")).put("status", "available"); assertThrows(IllegalArgumentException.class, () -> actual(context));
    }
    @Test void malformedPrecedingFactsInvalidateOnlyThatIndependentOptionalLeaf() throws Exception {
        ObjectNode n = full(); object(n.get("entry_preceding_capture_12004")).put("full_entry", true);
        ObjectNode expected = BattleOriginalOracle.normalizeControl(n, i32(n.get("subject_public_cunit_id")), integer(n.get("snapshot_revision")), i64(n.get("observed_date_raw")));
        ObjectNode normalized = actual(n); assertDomain(expected, normalized); assertTrue(normalized.get("entry_preceding_capture_12004").isNull()); assertTrue(normalized.path("battle_control_ready").booleanValue());
    }
    @Test void resumeSameFrameUnknownsNeverBecomeReadyAndCopiesCannotMutateEvidence() throws Exception {
        ObjectNode p = actual(parent()), resume = object(fixture.get("resume")).deepCopy();
        ObjectNode input = empty(); input.set("value", resume); input.set("parent", p);
        ObjectNode expected = BattleOriginalOracle.call("""
                import json,sys
                from xar_autoplayer.bridge.battle_control_contract import normalize_active_combat_resume_inputs_v1
                v=json.load(sys.stdin)
                print(json.dumps(normalize_active_combat_resume_inputs_v1(v['value'],parent=v['parent']),allow_nan=False))
                """, input);
        ObjectNode normalized = BattleControlExtensionCodec.normalizeResume(resume, p); assertDomain(expected, normalized); assertFalse(normalized.path("input_observation_ready").booleanValue());
        object(normalized.get("source")).put("combat_id", 1); assertNotEquals(1, resume.path("source").path("combat_id").intValue());
        ObjectNode ready = resume.deepCopy(); ready.put("input_observation_ready", true); assertThrows(IllegalArgumentException.class, () -> BattleControlExtensionCodec.normalizeResume(ready, p));
        ObjectNode stale = resume.deepCopy(); object(stale.get("source")).put("snapshot_revision", 6); assertThrows(IllegalArgumentException.class, () -> BattleControlExtensionCodec.normalizeResume(stale, p));
    }

    @Test void precedingFullGenerationAndUnsigned64FactsRoundTripWithoutPrecisionLoss() throws Exception {
        ObjectNode p = parent(); p.put("combat_id", Integer.MIN_VALUE);
        for (String role : List.of("attacker", "defender")) for (JsonNode army : p.path(role).path("ordered_armies")) object(army).put("combat_backlink_id", Integer.MIN_VALUE);
        ObjectNode capture = empty(); capture.put("schema", "xar.ck3.entry-preceding-capture-12004-v1"); capture.put("configured", true); capture.put("installed", true); capture.put("request_filtered", true); capture.put("install_failure_flags", 0); capture.put("latest_record_sequence", new BigInteger("9007199254740993")); capture.put("overwritten_records", 0); capture.put("full_entry", false);
        ObjectNode r = empty(); r.put("record_sequence", new BigInteger("9007199254740993")); r.put("install_epoch", new BigInteger("18446744073709551615")); r.put("offline_fixture", false); r.put("original_returned", true); r.put("identity_stable", true); r.put("combat_identity", new BigInteger("18446744073709551615")); r.put("combat_full_id_before", 2147483648L); r.put("combat_full_id_after", 2147483648L); r.put("caller_return_rva", 0); r.put("caller_return_slot", new BigInteger("18446744073709551615")); r.put("raw_return_bits", new BigInteger("18446744073709551615")); r.putNull("outer_invocation");
        ObjectNode begin = empty(); begin.put("clock_identity", new BigInteger("18446744073709551615")); begin.put("sequence", new BigInteger("9007199254740993")); begin.put("thread_id", 4294967295L); r.set("original_begin", begin); r.set("original_completion", begin.deepCopy());
        capture.set("records", arrayNode().add(r)); p.set("entry_preceding_capture_12004", capture);
        ObjectNode expected = BattleOriginalOracle.normalizeControl(p, i32(p.get("subject_public_cunit_id")), integer(p.get("snapshot_revision")), i64(p.get("observed_date_raw")));
        ObjectNode result = actual(parse(bytes(p))); assertDomain(expected, result); assertEquals(new BigInteger("18446744073709551615"), result.path("entry_preceding_capture_12004").path("records").get(0).path("raw_return_bits").bigIntegerValue());
        object(result.path("entry_preceding_capture_12004").path("records").get(0)).put("combat_full_id_after", 4294967295L); assertTrue(actual(result).get("entry_preceding_capture_12004").isNull());
    }
    @Test void resumeObservedMappingRollBoundsAndCounterRemainUnavailableWithExactCustody() {
        ObjectNode p = actual(full()), resume = object(fixture.get("resume")).deepCopy(), observed = object(resume.get("observed"));
        for (int index = 0; index < 2; index++) { ObjectNode bounds = available("effective_min_roll", -7); bounds.put("effective_max_roll", 8); observed.set("side_" + index + "_selected_commander_next_roll_bounds", bounds); }
        ArrayNode missing = arrayNode(); for (JsonNode name : resume.path("missing_required_domains")) if (!SetHolder.CLOSED_CURRENT.contains(name.textValue())) missing.add(name);
        resume.set("missing_required_domains", missing); ObjectNode mapping = empty(); mapping.put("status", "available"); mapping.put("subject_side_index", 0); mapping.put("opposing_side_index", 1); mapping.set("subject_owner_character_id", p.get("selected_owner_character_id")); mapping.set("side_scope", p.get("side_scope"));
        for (String role : List.of("attacker", "defender")) { ArrayNode ids = arrayNode(); for (JsonNode army : p.path(role).path("ordered_armies")) ids.add(army.get("public_cunit_id")); mapping.set(role.equals("attacker") ? "same_side_public_cunit_ids_in_stored_order" : "opposing_side_public_cunit_ids_in_stored_order", ids); }
        for (String key : List.of("affected_public_cunit_ids_in_stored_order", "unaffected_same_side_public_cunit_ids_in_stored_order")) mapping.set(key, p.get(key));
        observed.set("battle_side_mapping", mapping); observed.set("active_counter_inputs_v1", p.get("active_counter_inputs_v1").deepCopy());
        for (String key : List.of("roll_cadence_interval", "current_phase_transition_inputs_v1", "current_finalizer_manager_inputs_v1", "current_warscore_caps_v1", "current_pursuit_inputs_v1")) observed.set(key, p.get(key).deepCopy());
        ObjectNode normalized = BattleControlExtensionCodec.normalizeResume(resume, p); assertFalse(normalized.path("input_observation_ready").booleanValue()); assertDomain(normalized, BattleControlExtensionCodec.normalizeResume(parse(bytes(normalized)), p));
        ObjectNode wrongMapping = resume.deepCopy(); object(wrongMapping.path("observed").get("battle_side_mapping")).put("subject_owner_character_id", 1); assertThrows(IllegalArgumentException.class, () -> BattleControlExtensionCodec.normalizeResume(wrongMapping, p));
        ObjectNode wrongMirror = resume.deepCopy(); object(wrongMirror.path("observed").get("current_finalizer_manager_inputs_v1")).put("pending_suppression_sweep_raw", 1); assertThrows(IllegalArgumentException.class, () -> BattleControlExtensionCodec.normalizeResume(wrongMirror, p));
    }
    private static final class SetHolder {
        private static final java.util.Set<String> CLOSED_CURRENT = java.util.Set.of("active_coalition_side_mapping", "selected_commander_next_roll_bounds");
    }

    @Test void unavailableCurrentCensusesRemainExplicitAndNeverLeakPartialOperands() throws Exception {
        ObjectNode p = full();
        for (String key : List.of("actual_hard_casualty_sides", "pursuit_modifier_sides")) { ObjectNode leaf = object(p.get(key)); leaf.put("status", "unavailable"); leaf.putNull("sides"); leaf.put("unavailable_reason", "native_operand_not_observed"); }
        ObjectNode counter = object(p.get("active_counter_inputs_v1")); counter.put("status", "unavailable"); counter.put("operand_census_complete", false); counter.putNull("class_count"); counter.putNull("sides"); counter.putNull("contexts"); counter.put("unavailable_reason", "native_counter_not_observed");
        ObjectNode expected = BattleOriginalOracle.normalizeControl(p, i32(p.get("subject_public_cunit_id")), integer(p.get("snapshot_revision")), i64(p.get("observed_date_raw")));
        assertDomain(expected, actual(p)); ObjectNode partial = p.deepCopy(); object(partial.get("active_counter_inputs_v1")).put("class_count", 2); assertThrows(IllegalArgumentException.class, () -> actual(partial));
    }
}
