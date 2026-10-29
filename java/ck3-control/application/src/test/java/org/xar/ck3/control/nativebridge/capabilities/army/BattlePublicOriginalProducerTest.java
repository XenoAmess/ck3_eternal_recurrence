package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Original Python Service -> Java strict domain -> actual public presenter -> declared JSON roundtrip. Software evidence only. */
final class BattlePublicOriginalProducerTest {
    private record Pin(String relative, String sha256) { }
    private static final List<Pin> PINS = List.of(
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/service.py", "a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_retained_geometry.py", "fd6c3576ca46565fc66659e928dbc7d3103608ee637ad347ea7582fc95d98cf4"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_current_dynamic_components_fields.py", "31cb043a2b916348580bb6127cb7fdf33a6a1c627a43bfc3d3a1e1a0f57dabc5"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_opposite_effect_eligibility_fields.py", "6ed73f9cd38ebae8992c316fa14014d8d30c62e0b59ae1e168ac51626df545fa"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_current_own_nested_modifier_fields.py", "cf018f50c34568675c889e5c33eda99bb22757087b6cc4f43f5c3ded6a01227a"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_retained_current_rule_contributions.py", "e86f959e354057865f01e844ec148084dc6b1072617f638ca838f13af8a6cd8e"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_actual_stored_advantage_sources.py", "db322dff0fd692e74949eaa5b67f03eabbbca21408f52c3bd86b94b59db66519"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_actual_current_dynamic_advantage.py", "8ba7708a44308132a4ab8493400fffac194624106c87261f653c7917f2db1785"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_actual_current_dynamic_components.py", "9ba7a9a9281fcd553c718d1b24cc0a293b3cb8db192af4010c6c3f1a66ea8474"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_actual_opposite_effect_eligibility.py", "fddb9d1ea48cf8db7724d5d2f6dad083858f968f5025ef252fd2504b79477228"),
            new Pin("ck3_autonomous_player/src/xar_autoplayer/simulation/battle_actual_own_nested_modifier.py", "7289d66fb38cab1aea353534e980fe951a6e3ca74fb9a4bec5be968b658ef824"),
            new Pin("ck3_autonomous_player/tests/unit/test_retained_constructor_geometry_v1.py", "d405b64e3cac7b2db6dac78a612403a2263dce4dbb06f0d816b9e5b26e865e1a"),
            new Pin("ck3_autonomous_player/tests/unit/test_retained_loaded_rule_effects_v1.py", "b9419b30b59ae681e23ef2510f4c600b0331960af4d33a45810ae674c5d0845b"),
            new Pin("ck3_autonomous_player/tests/unit/test_retained_current_rule_contributions_v1.py", "9af8989e990dbd0d100b5f4d999601abba3219692cd1f583e1ea52cafb63b948"),
            new Pin("ck3_autonomous_player/tests/unit/test_actual_stored_advantage_sources_v1.py", "99db0b9198ea646d3847daea90d049a60a69fffc622d814d43307ee966903123"),
            new Pin("ck3_autonomous_player/tests/unit/test_actual_opposite_effect_eligibility_v1.py", "9b7d983372c66dc672ad7164432d68e67f02776429b906ba2fed9e7cd1bf8306"),
            new Pin("ck3_autonomous_player/tests/unit/test_actual_current_dynamic_advantage_v1.py", "54acf3bdabbbe6d9d79f6c52b31bff85ca936d08969f474f5a55a4fc38cbc213"),
            new Pin("ck3_autonomous_player/tests/unit/test_actual_current_dynamic_components_v1.py", "982f16e2b4bad5592855d48ca82adcba1e308d13af80c56aef46eabb0bfe27a3"),
            new Pin("ck3_autonomous_player/tests/unit/test_actual_own_nested_modifier_v1.py", "153d82939536747588f909417af8edd806181942e49c81e0e0c8420deb9ca5a2"),
            new Pin("ck3_autonomous_player/tests/fixtures/battle_retained_geometry/foreign-available.json", "d8f1e4541e5020719d732527a3570d93be7e510bd5ee9844ee6c7636391dcbcd"),
            new Pin("ck3_autonomous_player/tests/fixtures/battle_retained_geometry/foreign-unavailable.json", "7f6ad150ba3f096ed9fda34055481ab660a75d3d2a9055207bad1bd2d5aee3e3"),
            new Pin("ck3_autonomous_player/tests/fixtures/battle_retained_geometry/owned-available.json", "9863ba0ba7b33295a6d6bca4493d45a4e0f73e9b454b78b4477a83b6e00610a6"),
            new Pin("ck3_autonomous_player/tests/fixtures/battle_retained_geometry/PROVENANCE.json", "83718f65b84982a96a1013ca7e95cc96ac57c7c5bc3e16eeccbfaa6a37de48ae"));
    private record Observation(ArmyBattleReadValue.Kind kind, Obj normalized, BigInteger sequence, Obj extensions) implements ArmyBattleReadValue { }
    private static Obj obj(JsonNode n) { return DriverJson.object(ArmyJson.bytes(n), DriverJson.MAX_NATIVE_BYTES); }
    private static void pins() throws Exception { for (Pin pin : PINS) ArmyOriginalSourcePins.verify(pin.relative(), pin.sha256()); }
    private static ObjectNode corpus() throws Exception {
        pins(); ObjectNode result = BattleOriginalOracle.call("""
                import copy,json,sys
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'tests'/'unit'))
                from test_retained_constructor_geometry_v1 import load_fixture,service_query,OfflineProducerDriver
                from test_retained_loaded_rule_effects_v1 import loaded_effects
                from test_retained_current_rule_contributions_v1 import current_context
                from test_actual_stored_advantage_sources_v1 import stored_sources
                from test_actual_opposite_effect_eligibility_v1 import flagged_sources
                from test_actual_current_dynamic_advantage_v1 import current_values
                from test_actual_current_dynamic_components_v1 import component_values
                from test_actual_own_nested_modifier_v1 import own_sources
                rows=[]
                modes=('bare','all','excluded','no_holding','inactive','nonpositive','missing_multiplier',
                       'adjacency_absent','missing_flags','zero_scopes','missing_commander','dynamic_unavailable',
                       'empty_ledger','stored_unavailable','no_stored','wrapped_dynamic','geometry_null','geometry_missing')
                for fixture in ('foreign-available.json','owned-available.json'):
                    for version in ('1.20.0.3','1.20.0.4'):
                        for mode in modes:
                            frame=load_fixture(fixture)
                            geometry=frame['actual_geography_v1']
                            if mode!='bare':
                                geometry.update(constructor_adjacency_kind_raw=2,holding_defender=True,
                                    constructor_rule_effects_v1=loaded_effects(2),
                                    current_rule_context_v1=current_context(frame['attacker']['selected_commander_character_id'] if fixture.startswith('owned') else 70766),
                                    stored_advantage_sources_v1=flagged_sources(),
                                    current_dynamic_advantage_v1=current_values(),
                                    current_dynamic_components_v1=component_values(),
                                    current_own_nested_modifier_v1=own_sources())
                                context=geometry['current_rule_context_v1'];holding=context['holding_multiplier'];commander=context['commander_exclusion']
                                if mode=='excluded':commander['defender_adjacency_excluded']=True
                                elif mode=='no_holding':holding.update(province_has_holding=False,holding_modifier_raw=None)
                                elif mode=='inactive':
                                    geometry['holding_defender']=False
                                    holding.update(status='not_applicable',province_multiplier_raw=None,province_has_holding=None,holding_modifier_raw=None)
                                elif mode=='nonpositive':holding.update(province_multiplier_raw=-5000,holding_modifier_raw=0)
                                elif mode=='missing_multiplier':holding.update(status='unavailable',province_multiplier_raw=None,province_has_holding=None,holding_modifier_raw=None,unavailable_reason='current_province_multiplier_unavailable')
                                elif mode=='adjacency_absent':
                                    geometry['constructor_rule_effects_v1']['rows'][1].update(status='not_selected',key=None,advantage_points=None)
                                    commander.update(status='not_applicable',used_native_fallback=None,defender_adjacency_excluded=None)
                                elif mode=='missing_flags':geometry['stored_advantage_sources_v1']['sides'][1]['rows'][1].pop('effect_flags_v1')
                                elif mode=='zero_scopes':
                                    for side in geometry['current_own_nested_modifier_v1']['sides']:
                                        for scope in ('combat_side_aggregate','selected_character_aggregate'):side[scope]['amount_raw']=0
                                    geometry['stored_advantage_sources_v1']['sides'][1]['rows'][1].pop('effect_flags_v1')
                                elif mode=='missing_commander':geometry['current_dynamic_components_v1']['sides'][0]['commander'].update(status='unavailable',total_raw=None,unavailable_reason='current_commander_getter_2589E10_output_unavailable')
                                elif mode=='dynamic_unavailable':geometry['current_dynamic_advantage_v1']['sides'][0].update(status='unavailable',side_dynamic_total_raw=None,unavailable_reason='current_side_dynamic_getter_258A470_output_unavailable')
                                elif mode=='empty_ledger':geometry['stored_advantage_sources_v1']['sides'][0]['rows']=[]
                                elif mode=='stored_unavailable':geometry['stored_advantage_sources_v1']['sides'][0].update(status='unavailable',rows=None,unavailable_reason='stored_advantage_source_vector_unavailable')
                                elif mode=='no_stored':geometry['stored_advantage_sources_v1']=None
                                elif mode=='wrapped_dynamic':
                                    geometry['current_dynamic_advantage_v1'].update(base_advantage_raw=(1<<63)-1,stored_resolved_advantage_raw=-(1<<63))
                                    geometry['current_dynamic_advantage_v1']['sides'][0]['side_dynamic_total_raw']=1
                                    geometry['current_dynamic_advantage_v1']['sides'][1]['side_dynamic_total_raw']=0
                                elif mode=='geometry_null':frame['actual_geography_v1']=None
                                elif mode=='geometry_missing':frame.pop('actual_geography_v1')
                            driver=OfflineProducerDriver(frame,game_version=version)
                            snapshot=driver.take_snapshot();native=driver.execute_step(driver.step,expected_revision=4)
                            original=copy.deepcopy(frame);result=service_query(frame,game_version=version)
                            assert original==frame
                            rows.append({'name':fixture+':'+version+':'+mode,'snapshot':snapshot,'native':native,'frame':frame,'expected':result})
                print(json.dumps({'rows':rows},allow_nan=False))
                """, ArmyJson.empty()); pins(); return result;
    }
    static ArmyPublicSnapshot captured(ObjectNode snapshot) {
        var reference = new ExactRef("software-original-public-producer", 1, "a".repeat(64));
        String version = snapshot.path("diagnostics").path("hello").path("game_version").asText("1.20.0.4");
        var source = new G2Source("fixture-original-public-machine", "2026-10-24T00:00:00Z", version, reference);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, snapshot.get("native_revision").bigIntegerValue(), snapshot.get("date_raw").bigIntegerValue()), snapshot.get("snapshot_id").textValue(), snapshot.get("revision").bigIntegerValue(), "offline-fixture");
        Context context = new Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "original-public-software-session", Instant.parse("2026-10-24T00:01:00Z"));
        return new ArmyPublicSnapshot(context, obj(snapshot));
    }
    @Test void originalControlAndTransitionAllCurrentDiagnosticBranchesHaveTheSamePublicObjectAndIntegerDomains() throws Exception {
        var original = corpus(); assertEquals(72, original.get("rows").size());
        for (JsonNode row : original.get("rows")) {
            String name = row.get("name").textValue(); ObjectNode raw = (ObjectNode)row.get("frame"); var captured = captured((ObjectNode)row.get("snapshot"));
            var kind = raw.get("contract_stage").textValue().equals("production_exact_ongoing_combat") ? ArmyBattleReadValue.Kind.CONTROL : ArmyBattleReadValue.Kind.TRANSITION;
            Obj normalized = kind == ArmyBattleReadValue.Kind.CONTROL ? BattleResponseCodec.normalizeControl(obj(raw), raw.get("subject_public_cunit_id").intValue(), captured.context().nativeRevision(), captured.context().dateRaw().longValueExact())
                    : BattleResponseCodec.normalizeTransition(obj(raw), raw.get("combat_id").intValue(), captured.context().nativeRevision(), captured.context().dateRaw().longValueExact());
            var observed = new Observation(kind, normalized, row.get("native").get("query_sequence").bigIntegerValue(), new Obj(java.util.Map.of()));
            var wire = ArmyBattlePublicPresenter.encode(observed, obj(row.get("native")), captured); var restored = ArmyPublicWire.decode(wire, captured.context());
            ObjectNode expected = ((ObjectNode)row.get("expected")).deepCopy(); expected.remove(List.of("queried_snapshot_id", "queried_revision", "queried_native_revision"));
            assertEquals(obj(expected), restored, name); assertEquals(wire, ArmyPublicWire.encode(restored, captured.context()), name);
            ObjectNode publicValue = ArmyJson.parse(wire.bytes()); assertTrue(publicValue.get("schema_version").isIntegralNumber(), name);
            assertTrue(publicValue.get("query_sequence").isTextual(), name); assertFalse(publicValue.has("integer_paths"), name); assertFalse(publicValue.has("public_wire_schema"), name);
            if (name.contains(":1.20.0.4:") && publicValue.has("retained_constructor_geometry_v1")) {
                assertFalse(publicValue.get("retained_constructor_geometry_v1").get("retained_geometry_ready").booleanValue(), name);
                if (publicValue.has("current_dynamic_advantage_v1")) assertTrue(publicValue.get("current_dynamic_advantage_v1").get("current_advantage").isNull(), name);
            }
            assertEquals(raw, row.get("frame"), "original raw fixture changed: " + name);
        }
    }
    @Test void originalSixStageProducerReachesTheSameStrictQueryAndAllOrderedAppendConsumersAfterPublicSerialization() throws Exception {
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_person_six_stage_capture_12004.py", "84bda389a1b8f1fd1807d2a0e05b77c380f60d6eb5d9630e52aa2d11cb11d58b");
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/tests/test_battle_person_six_stage_capture_12004.py", "95a78a24f3f4b2c1b0c58720a309bd5e74e17677cc5c2302ec970865c424791d");
        ObjectNode original = BattleOriginalOracle.call("""
                import importlib.util,json
                from xar_autoplayer.bridge.battle_person_six_stage_capture_12004 import normalize_person_six_stage_query_12004,select_person_six_stage_capture_12004,emit_captured_person_six_stage_requests_12004
                path=root/'ck3_autonomous_player'/'tests'/'test_battle_person_six_stage_capture_12004.py'
                spec=importlib.util.spec_from_file_location('xar_public_original_six_stage',path)
                fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
                query=normalize_person_six_stage_query_12004(fixture._query(),expected_snapshot_revision=23,expected_observed_date_raw=53288784,expected_character_ids=[29829])
                section=select_person_six_stage_capture_12004(query,29829)
                print(json.dumps({'query':query,'requests':emit_captured_person_six_stage_requests_12004(section)},allow_nan=False))
                """, ArmyJson.empty());
        var query = BattlePersonSixStageCaptureCodec.decode(original.get("query"), "original six stages", BigInteger.valueOf(23), 53288784, List.of(29829L));
        ObjectNode snapshot = ArmyJson.empty().put("snapshot_id", "original-six-stage:23").put("revision", 4).put("native_revision", 23).put("date_raw", 53288784).put("paused", true).put("episode_run_id", "offline-fixture");
        var context = captured(snapshot).context(); ObjectNode root = ArmyJson.empty(); root.set("person_six_stage_captures", query.toJson());
        var wire = ArmyPublicWire.encode(obj(root), context); Obj restored = ArmyPublicWire.decode(wire, context); ObjectNode restoredJson = (ObjectNode)OpportunityJson.toNode(restored);
        var typed = BattlePersonSixStageCaptureCodec.decode(restoredJson.get("person_six_stage_captures"), "restored six stages", BigInteger.valueOf(23), 53288784, List.of(29829L));
        assertEquals(query.owners(), typed.owners());
        ObjectNode expected = ArmyJson.empty(), actual = ArmyJson.empty(); expected.set("requests", original.get("requests"));
        actual.set("requests", BattlePersonSixStageConsumers.emitRequests(BattlePersonSixStageCaptureCodec.select(typed.toJson(), 29829)));
        assertEquals(obj(expected), obj(actual)); assertEquals(wire, ArmyPublicWire.encode(restored, context));
        var leaf = ArmyJson.parse(wire.bytes()).get("person_six_stage_captures").get("character_captures").get(0);
        assertTrue(leaf.get("character_id").isIntegralNumber()); assertTrue(leaf.get("capture_thread_id").isIntegralNumber()); assertTrue(leaf.get("capture_sequence").isTextual());
        assertTrue(leaf.get("character_identity").textValue().matches("0|[1-9][0-9]*"));
        assertTrue(leaf.get("stages").get(0).get("first_pc").get("count_i32").isIntegralNumber());
        assertTrue(leaf.get("stages").get(0).get("first_pc").get("properties").get("values_q64").get(0).isTextual());
    }
    @Test void declaredRaw64AndPointerBitArraysRoundTripWithoutConvertingBoundedIdsOrNativeBitDomains() {
        ObjectNode snapshot = ArmyJson.empty().put("snapshot_id", "raw64-boundary:1").put("revision", 1).put("native_revision", 1).put("date_raw", 1).put("paused", true).put("episode_run_id", "offline-fixture");
        var context = captured(snapshot).context(); ObjectNode original = ArmyJson.empty();
        original.put("combat_width_multiplier_raw", Long.MIN_VALUE).put("contribution_raw", Long.MAX_VALUE).put("weight_q64", Long.MIN_VALUE).put("base430_q64", Long.MAX_VALUE).put("selected_character_id_raw", Integer.MIN_VALUE);
        var physical = original.putObject("person_installed_transfers").putArray("records").addObject().putObject("physical_postimage");
        physical.putArray("values_q64_raw_bits").add("0x0000000000000000").add("0xffffffffffffffff");
        physical.putArray("ordered_payload_raw64").add("0x8000000000000000");
        var encoded = ArmyPublicWire.encode(obj(original), context); ObjectNode publicObject = ArmyJson.parse(encoded.bytes());
        assertEquals("-9223372036854775808", publicObject.get("combat_width_multiplier_raw").textValue()); assertEquals("9223372036854775807", publicObject.get("contribution_raw").textValue());
        assertTrue(publicObject.get("selected_character_id_raw").isIntegralNumber());
        assertEquals("18446744073709551615", publicObject.get("person_installed_transfers").get("records").get(0).get("physical_postimage").get("values_q64_raw_bits").get(1).textValue());
        assertEquals(obj(original), ArmyPublicWire.decode(encoded, context));
        ObjectNode malformed = publicObject.deepCopy(); ((ObjectNode)malformed.get("person_installed_transfers").get("records").get(0).get("physical_postimage")).putArray("ordered_payload_raw64").add("018446744073709551615");
        assertThrows(IllegalArgumentException.class, () -> ArmyPublicWire.decode(new org.xar.ck3.control.application.action.RawJson(ArmyJson.bytes(malformed)), context));
    }
    @Test void originalTerminalServiceAvailableUnresolvedAndJournalGapPreserveEveryOuterMirrorAndTheActualSource() throws Exception {
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/tests/unit/test_battle_terminal_transition_v1_bridge.py", "7ef0593f14e211a132eeb0a3d0fe67e604c98f97ea351803ed7599b8e9b0ec08");
        ArmyOriginalSourcePins.verify("ck3_autonomous_player/src/xar_autoplayer/bridge/battle_terminal_transition_contract.py", "f8a0c5d4513eee9a0c918dfa244b72613f13479b2d2ecb68c225f02847dd81db");
        ObjectNode original = BattleOriginalOracle.call("""
                import importlib.util,json
                path=root/'ck3_autonomous_player'/'tests'/'unit'/'test_battle_terminal_transition_v1_bridge.py'
                spec=importlib.util.spec_from_file_location('xar_terminal_public_original',path)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                rows=[]
                for frame in (module._normal_frame(),module._membership_unavailable_frame(),module._unavailable_frame()):
                    driver=module._ServiceDriver(frame);service=module.GameplayBridgeService(driver)
                    snapshot=driver.take_snapshot();native=driver.execute_step(module.STEP,expected_revision=module.PUBLIC_REVISION)
                    expected=service.query_battle_terminal_transition_v1(module.PRIOR_COMBAT_ID,module.SUBJECT_CUNIT_ID,expected_revision=module.PUBLIC_REVISION,after_terminal_sequence=module.CURSOR)
                    rows.append({'snapshot':snapshot,'native':native,'frame':frame,'expected':expected})
                print(json.dumps({'rows':rows},allow_nan=False))
                """, ArmyJson.empty());
        assertEquals(3, original.get("rows").size());
        for (JsonNode row : original.get("rows")) {
            ObjectNode frame = (ObjectNode)row.get("frame"); var captured = captured((ObjectNode)row.get("snapshot")); var cursor = java.util.Optional.of(frame.get("terminal_journal").get("requested_after_sequence").bigIntegerValue());
            Obj normalized = BattleTerminalCodec.normalizeTerminal(obj(frame), frame.get("prior_combat_id").intValue(), frame.get("subject_public_cunit_id").intValue(), cursor, List.of(), captured.context().nativeRevision(), captured.context().dateRaw().longValueExact());
            var read = new Observation(ArmyBattleReadValue.Kind.TERMINAL, normalized, row.get("native").get("query_sequence").bigIntegerValue(), new Obj(java.util.Map.of()));
            var wire = ArmyBattlePublicPresenter.encode(read, obj(row.get("native")), captured); ObjectNode expected = ((ObjectNode)row.get("expected")).deepCopy(); expected.remove(List.of("queried_snapshot_id", "queried_revision", "queried_native_revision"));
            assertEquals(obj(expected), ArmyPublicWire.decode(wire, captured.context()));
            assertFalse(ArmyJson.parse(wire.bytes()).has("retained_constructor_geometry_v1"), "terminal does not produce a control geometry adjunct");
        }
    }
}
