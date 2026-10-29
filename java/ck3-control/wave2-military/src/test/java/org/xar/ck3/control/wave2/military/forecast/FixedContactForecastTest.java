package org.xar.ck3.control.wave2.military.forecast;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.military.forecast.CombatJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import org.junit.jupiter.api.Test;

final class FixedContactForecastTest {
    private static final String FORECAST = """
            import json,sys
            from xar_autoplayer.simulation.general_battle_forecast import forecast_fixed_contact
            value=json.load(sys.stdin)
            request=value['request']
            request['attacker_army_ids']=tuple(request['attacker_army_ids'])
            request['defender_army_ids']=tuple(request['defender_army_ids'])
            print(json.dumps(forecast_fixed_contact(value['payload'],**request),allow_nan=False))
            """;
    record Case(ObjectNode payload, FixedContactForecast.Request request) { }
    static Case liveCase() throws Exception {
        JsonNode source = ForecastOriginalOracle.fixture("ck3_autonomous_player/tests/fixtures/combat/live_rev4_player_attacks_357.json");
        var base = object(source.get("combat_simulation_inputs"), "base").deepCopy(); var payload = object();
        var ready = object(); ready.put("input_observation_ready", true); payload.set("completeness", ready); payload.set("base_inputs", base);
        JsonNode scenario = base.get("scenario");
        var request = new FixedContactForecast.Request(integer(base.get("target_province_id"), "target"), absentOrNull(scenario.get("attacker_entry_province_id")) ? null : integer(scenario.get("attacker_entry_province_id"), "entry"), ids(scenario.get("attacker_army_ids"), "attackers"), ids(scenario.get("defender_army_ids"), "defenders"), new CombatInputs.Capture(object(source.get("capture"), "capture")), 16, 4);
        return new Case(payload, request);
    }
    private static ObjectNode oracleInput(Case value) { var input = object(); input.set("payload", value.payload()); input.set("request", value.request().toJson()); return input; }
    private static void assertJsonDomain(JsonNode expected, JsonNode actual) { assertArrayEquals(CombatJson.canonical(expected), CombatJson.canonical(actual)); }
    private static ObjectNode assertOriginal(Case value) throws Exception {
        ObjectNode actual = FixedContactForecast.forecast(value.payload(), value.request()).toJson();
        assertJsonDomain(ForecastOriginalOracle.call(FORECAST, oracleInput(value)), actual);
        assertJsonDomain(actual, CombatJson.parse(CombatJson.canonical(actual)));
        assertEquals(value.request(), FixedContactForecast.Request.fromJson(value.request().toJson())); return actual;
    }
    static ObjectNode nativeV3(Case value, long totalRaw) {
        value.payload().put("schema_version", 3); value.payload().put("contract_stage", "production_exact_132_refs");
        var model = object(); model.put("status", "available"); model.put("scale", 100_000); model.put("scenario_policy", value.payload().path("base_inputs").path("participant_policy").textValue()); model.put("observation_origin", "native_exact_build_production"); model.put("base_static_accumulator_raw", totalRaw);
        var sides = array(); var inputs = array();
        for (String role : List.of("attacker", "defender")) {
            var own = elements(value.payload().path("base_inputs").path("armies"), "armies").stream().filter(army -> is(army.get("encounter_role"), role)).toList();
            var side = object(); side.put("side", role); JsonNode commander = own.getFirst().path("commander").get("character_id");
            side.set("battle_commander_character_id", commander); side.put("battle_commander_selected", !absentOrNull(commander)); side.put("battle_commander_selection", "native_0x23C8A60"); side.put("roll_points", 0);
            for (String name : List.of("roll_raw", "target_conditionals_residual_raw", "commander_dynamic_raw", "side_dynamic_raw", "side_total_raw")) side.put(name, 0); sides.add(side);
            var input = object(); input.put("side", role); input.set("primary_army_id", own.getFirst().get("army_id")); var ordered = array(); own.forEach(army -> ordered.add(army.get("army_id"))); input.set("ordered_army_ids", ordered); inputs.add(input);
        }
        model.set("side_inputs", inputs); var dynamic = object(); dynamic.put("status", "available"); dynamic.put("helper_status", "original_helpers_matched"); dynamic.put("roll_policy", "zero_in_query_sampled_offline"); dynamic.put("original_total_helper_match", true); dynamic.put("resolved_advantage_at_zero_roll_raw", totalRaw); dynamic.put("original_total_helper_raw", totalRaw); dynamic.put("side_0_dynamic_raw", 0); dynamic.put("side_1_dynamic_raw", 0); dynamic.set("sides", sides); model.set("resolved_dynamic", dynamic);
        var phase = object(); phase.put("status", "available"); phase.set("advantage_model", model); value.payload().set("phase_event_inputs", phase); return model;
    }
    static ObjectNode nativeV2(Case value) {
        value.payload().put("schema_version", 2); var base = object(value.payload().get("base_inputs"), "base");
        var context = object(); context.put("schema_version", 2); context.put("status", "available"); context.put("scope", "hypothetical_constructor_context"); context.put("scale", 100_000); context.put("target_province_id", value.request().targetProvinceId()); context.put("synthetic_helper_total_match", true); context.put("base_constructor_accumulator_raw", -600_000); context.put("synthetic_zero_roll_total_raw", -600_000);
        var sides = array();
        for (int index = 0; index < 2; index++) {
            final String role = index == 0 ? "attacker" : "defender"; var own = elements(base.get("armies"), "armies").stream().filter(army -> is(army.get("encounter_role"), role)).toList();
            var side = object(); side.put("side_index", index); var ordered = array(); own.forEach(army -> ordered.add(army.get("army_id"))); side.set("ordered_public_cunit_ids", ordered); side.set("selected_commander_character_id", own.getFirst().path("commander").get("character_id"));
            for (String name : List.of("commander_dynamic_raw", "side_dynamic_raw", "target_conditionals_residual_raw", "side_total_raw")) side.put(name, 0); sides.add(side);
        }
        context.set("sides", sides); base.set("contextual_advantage", context); return context;
    }
    @Test void originalProducerMatchesCompleteGenericForecastAndRoundTrip() throws Exception {
        Case value = liveCase(); ObjectNode result = assertOriginal(value); assertEquals("estimated", result.path("status").textValue()); assertEquals(16, result.path("sample_count").intValue());
        assertEquals(16, result.path("player_wins").intValue() + result.path("player_losses").intValue() + result.path("no_resolution").intValue()); assertFalse(result.path("native_parity").booleanValue()); assertTrue(result.path("commander_or_knight_death_probability").isNull()); assertEquals(result, FixedContactForecast.forecast(value.payload(), value.request()).toJson());
    }
    @Test void nativeV3ActuallyChangesKernelCasualtiesAndRetainsSource() throws Exception {
        Case value = liveCase(); ObjectNode generic = assertOriginal(value); nativeV3(value, -20_000_000); ObjectNode result = assertOriginal(value);
        assertEquals(ConstructorAdvantage.Source.V3_NATIVE.wire(), result.path("advantage_input").path("source").textValue()); assertEquals(-20_000_000, result.path("advantage_input").path("zero_roll_raw").intValue()); assertNotEquals(generic.get("player_p90_hard_loss_raw"), result.get("player_p90_hard_loss_raw")); assertEquals(generic.get("input_sha256"), result.get("input_sha256"));
    }
    @Test void v2ConstructorHasCompleteArithmeticAndEncounterBinding() throws Exception {
        Case value = liveCase(); ObjectNode context = nativeV2(value); ObjectNode result = assertOriginal(value);
        assertEquals(ConstructorAdvantage.V2_CONSTRUCTOR_ADVANTAGE_SOURCE, result.path("advantage_input").path("source").textValue()); assertFalse(result.path("advantage_input").path("complete_encounter_advantage_ready").booleanValue());
        context.put("synthetic_zero_roll_total_raw", -599_999); assertEquals("model_unavailable", assertOriginal(value).path("status").textValue());
        context.put("synthetic_zero_roll_total_raw", -600_000); object(context.path("sides").get(0), "side").put("selected_commander_character_id", 42); assertEquals("model_unavailable", assertOriginal(value).path("status").textValue());
    }
    @Test void unavailablePhasePermitsDeclaredFallbackButMalformedAvailableCannot() throws Exception {
        Case value = liveCase(); ObjectNode baseline = assertOriginal(value); value.payload().put("schema_version", 3); value.payload().put("contract_stage", "production_exact_132_refs"); object(value.payload().get("completeness"), "completeness").put("input_observation_ready", false);
        var unavailable = object(); unavailable.put("status", "unavailable"); value.payload().set("phase_event_inputs", unavailable); ObjectNode fallback = assertOriginal(value); assertEquals(baseline.get("player_p90_hard_loss_raw"), fallback.get("player_p90_hard_loss_raw")); assertEquals("phase_event_inputs_unavailable", fallback.path("advantage_input").path("fallback_reason").textValue());
        var model = nativeV3(value, -600_000); object(model.get("resolved_dynamic"), "resolved").put("original_total_helper_raw", -599_999); ObjectNode rejected = assertOriginal(value); assertEquals("model_unavailable", rejected.path("status").textValue()); assertEquals("CombatInputError", rejected.path("error_type").textValue());
    }
    @Test void actualV3RetainsObservedSelectedCommanderAndOngoingCombatBarrier() throws Exception {
        var source = ForecastOriginalOracle.fixture("ck3_autonomous_player/native_bridge/research/fixtures/combat_simulation_inputs_v3_production_available.json"); JsonNode payload = source.path("result").path("combat_simulation_inputs"); var frozen = CombatInputs.freeze(payload.get("base_inputs"), CombatInputs.Capture.empty()); var selection = ConstructorAdvantage.readV3(payload, frozen).orElseThrow();
        assertEquals(BigInteger.valueOf(16_777_217), selection.attackerArmyId()); assertEquals(BigInteger.valueOf(16_777_218), selection.defenderArmyId()); assertEquals(BigInteger.valueOf(-600_000), selection.zeroRollRaw()); assertEquals(BigInteger.valueOf(16_777_218), selection.selectedCommanders().attackerCharacterId()); assertNull(selection.selectedCommanders().defenderCharacterId());
        var request = new FixedContactForecast.Request(frozen.encounter().targetProvinceId(), frozen.encounter().attackerEntryProvinceId(), frozen.encounter().attackerArmyIds(), frozen.encounter().defenderArmyIds(), CombatInputs.Capture.empty(), 4, 4);
        assertEquals("active_combat_requires_resume_input", FixedContactForecast.forecast(payload, request).toJson().path("status").textValue());
    }
    @Test void originalActiveAndMissingObservationNeverProduceUnrelatedEstimate() throws Exception {
        Case value = liveCase(); var ongoing = array(); var row = object(); row.put("combat_id", 16_777_218); ongoing.add(row); object(value.payload().get("base_inputs"), "base").set("ongoing_combats", ongoing); assertEquals("active_combat_requires_resume_input", assertOriginal(value).path("status").textValue());
        object(value.payload().get("base_inputs"), "base").remove("ongoing_combats"); assertEquals("input_or_encounter_mismatch", assertOriginal(value).path("status").textValue());
    }
    @Test void inputBoundariesRejectBooleanFloatingIdsAndBudgets() throws Exception {
        Case value = liveCase(); var request = value.request().toJson(); request.put("target_province_id", true); assertThrows(CombatInputException.class, () -> FixedContactForecast.Request.fromJson(request)); request.put("target_province_id", 357.0); assertThrows(CombatInputException.class, () -> FixedContactForecast.Request.fromJson(request));
        var budget = value.request().toJson(); budget.put("sample_count", 0); assertThrows(IllegalArgumentException.class, () -> FixedContactForecast.Request.fromJson(budget));
        var missing = value.request().toJson(); missing.remove("attacker_entry_province_id"); assertThrows(CombatInputException.class, () -> FixedContactForecast.Request.fromJson(missing));
        var unknown = value.request().toJson(); unknown.put("target_provinc_id", 357); assertThrows(CombatInputException.class, () -> FixedContactForecast.Request.fromJson(unknown));
        value.payload().put("schema_version", 2.0); assertEquals("input_or_encounter_mismatch", FixedContactForecast.forecast(value.payload(), value.request()).toJson().path("status").textValue());
        nativeV2(value).put("synthetic_zero_roll_total_raw", BigInteger.ONE.shiftLeft(63)); assertEquals("model_unavailable", FixedContactForecast.forecast(value.payload(), value.request()).toJson().path("status").textValue());
    }
    @Test void originalAdmissionIncludesUnmodeledCharacterRiskAndRejectsMalformedFields() throws Exception {
        var forecast = object(); forecast.put("status", "estimated"); forecast.put("native_parity", false); var interval = object(); interval.put("lower", .8); forecast.set("resolved_win_wilson95", interval); forecast.put("player_p90_hard_loss_fraction", .1); forecast.put("player_stack_wipe_probability", .01); forecast.put("commander_or_knight_death_probability", .01); forecast.put("no_resolution", 0); forecast.put("sample_count", 100);
        for (boolean relief : List.of(false, true)) {
            var input = object(); input.set("forecast", forecast); input.put("relief", relief);
            JsonNode original = ForecastOriginalOracle.call("import json,sys\nfrom xar_autoplayer.simulation.general_battle_forecast import contact_admission\nv=json.load(sys.stdin)\nprint(json.dumps(contact_admission(v['forecast'],defensive_relief=v['relief']),allow_nan=False))\n", input);
            assertJsonDomain(original, FixedContactForecast.contactAdmission(forecast, relief).toJson()); assertTrue(FixedContactForecast.contactAdmission(forecast, relief).admitted());
        }
        forecast.putNull("commander_or_knight_death_probability"); var admitted = FixedContactForecast.contactAdmission(forecast); assertTrue(admitted.admitted()); assertTrue(admitted.toJson().path("risk_limits").path("death").isNull()); assertEquals("commander_or_knight_death", admitted.toJson().path("unquantified_risks").get(0).textValue());
        forecast.put("player_p90_hard_loss_fraction", .4); assertFalse(FixedContactForecast.contactAdmission(forecast).admitted()); forecast.put("player_p90_hard_loss_fraction", .1); forecast.put("commander_or_knight_death_probability", .06); assertFalse(FixedContactForecast.contactAdmission(forecast).admitted()); forecast.put("commander_or_knight_death_probability", true); assertEquals("invalid_character_death_risk", FixedContactForecast.contactAdmission(forecast).toJson().path("reason").textValue());
        forecast.put("sample_count", true); assertEquals("incomplete_distribution", FixedContactForecast.contactAdmission(forecast).toJson().path("reason").textValue());
    }
    @Test void migrationFixPreservesLegalPublicSlotZeroWithoutConflatingNull() throws Exception {
        Case original = liveCase(); var base = object(original.payload().get("base_inputs"), "base");
        var first = object(base.path("armies").get(0), "first army"); first.put("army_id", 0);
        var zeroIds = array(); zeroIds.add(0); object(base.get("scenario"), "scenario").set("attacker_army_ids", zeroIds);
        var request = new FixedContactForecast.Request(original.request().targetProvinceId(), original.request().attackerEntryProvinceId(), List.of(BigInteger.ZERO), original.request().defenderArmyIds(), original.request().capture(), 4, 4);
        var value = new Case(original.payload(), request);
        assertEquals("estimated", FixedContactForecast.forecast(value.payload(), value.request()).toJson().path("status").textValue());
        assertEquals("input_or_encounter_mismatch", ForecastOriginalOracle.call(FORECAST, oracleInput(value)).path("status").textValue(), "legacy positive-only consumer bug is an explicit migration fix, not claimed original parity");
        assertEquals(BigInteger.ZERO, FixedContactForecast.Request.fromJson(request.toJson()).attackerArmyIds().getFirst());
        var malformed = request.toJson(); malformed.set("attacker_army_ids", array().add(-1)); assertThrows(CombatInputException.class, () -> FixedContactForecast.Request.fromJson(malformed));
        malformed.set("attacker_army_ids", array().add(BigInteger.ONE.shiftLeft(31))); assertThrows(CombatInputException.class, () -> FixedContactForecast.Request.fromJson(malformed));
        malformed.set("attacker_army_ids", array().addNull()); assertThrows(CombatInputException.class, () -> FixedContactForecast.Request.fromJson(malformed));
    }
    @Test void v2CharacterZeroIsSelectedWhileNullDisablesThatCommanderRoll() throws Exception {
        Case value = liveCase(); var base = object(value.payload().get("base_inputs"), "base");
        object(base.path("armies").get(0).get("commander"), "commander").put("character_id", 0); ObjectNode context = nativeV2(value);
        var selected = ConstructorAdvantage.readV2(value.payload(), CombatInputs.freeze(base, value.request().capture())).orElseThrow(); assertEquals(BigInteger.ZERO, selected.selectedCommanders().attackerCharacterId());
        assertEquals("estimated", FixedContactForecast.forecast(value.payload(), value.request()).toJson().path("status").textValue());
        object(context.path("sides").get(0), "side").putNull("selected_commander_character_id"); var absent = ConstructorAdvantage.readV2(value.payload(), CombatInputs.freeze(base, value.request().capture())).orElseThrow(); assertNull(absent.selectedCommanders().attackerCharacterId());
    }
}
