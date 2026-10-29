package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.military.landcontext.LandContextCodec;

/** Actual unchanged original producers are mandatory. These pure fixtures never stand for native/Game qualification. */
final class ArmyStrengthsSupplyTest {
    private static final String ORACLE = """
            import copy,hashlib,json,pathlib,runpy,sys
            m=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
            def pins():
                for r in m['original_sources']:
                    b=pathlib.Path(r['path']).read_bytes()
                    if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise RuntimeError('SUPPLY original source drift: '+r['path'])
            pins();root=pathlib.Path(m['repository_root']);unit=root/'ck3_autonomous_player/tests/unit'
            sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(unit),str(root/'ck3_workshop_mcp/src'),str(root/'tools')]
            from xar_autoplayer.bridge.army_current_province_supply_contributors_contract import normalize_current_province_supply_contributors_v1 as province
            from xar_autoplayer.bridge.army_current_land_resupply_contract import normalize_current_land_resupply_v1 as resupply,project_land_resupply_gain_component_v1 as gain
            from xar_autoplayer.bridge.army_actual_supply_callback_observations_contract import normalize_actual_supply_callback_observations_v1 as callbacks
            from xar_autoplayer.bridge.army_actual_supply_callback_observation_summary import summarize_actual_supply_callback_observations_v1 as summary
            from xar_autoplayer.bridge.army_next_land_stock_supply_budget_projection import project_source_derived_next_land_stock_supply_budget_v1 as landstock
            from xar_autoplayer.bridge.service import GameplayBridgeService
            p=runpy.run_path(str(unit/'test_current_province_supply_contributors.py'))
            p['CurrentProvinceSupplyContributorTests']('test_production_query_counts_occurrences_after_one_selected_physical_refill').debug()
            l=runpy.run_path(str(unit/'test_current_land_resupply_observer.py'))
            l['CurrentLandResupplyObserverTests']('test_current_observation_and_distinct_gain_component').debug()
            f=runpy.run_path(str(unit/'test_current_full_land_supply_rate.py'))
            c=runpy.run_path(str(unit/'test_actual_supply_parent_join_12004.py'))
            normalized=[]
            def norm(kind,value):
                fn=province if kind=='province' else resupply
                before=copy.deepcopy(value);expected=fn(value)
                if before!=value:raise RuntimeError('normalizer mutated source')
                normalized.append(dict(kind=kind,input=value,expected=expected))
            norm('province',p['contributor_packet']()['current_province_supply_contributors_v1'])
            norm('province',f['row']()['current_province_supply_contributors_v1'])
            for changes in ({},{'status':'unavailable','current_observation_ready':False,'native_resupply_eligible':None},{'status':'not_land','current_observation_ready':False,'native_land_branch_applicable':False,'native_resupply_eligible':None}):norm('resupply',l['inputs'](**changes))
            gains=[]
            for inputs in [l['inputs'](),l['inputs'](loaded_gain_raw=0),l['inputs'](loaded_gain_raw=-17),l['inputs'](native_resupply_eligible=False),None]:
                for usage in [-2147483648,499,500,501,2147483647]:gains.append(dict(input=inputs,usage=usage,limit=500,expected=gain(inputs,usage_soldiers=usage,limit_soldiers=500)))
            base=c['joined_packet']();base={k:v for k,v in base.items() if k in {'army_id','native_carmy_id','actual_supply_callback_observations_v1'}}
            scenes=[]
            def scene(name,row,fence=0):
                untouched=copy.deepcopy(row);raw=row.get('actual_supply_callback_observations_v1')
                normalized=callbacks(raw,current_army_id=row['army_id'],current_native_carmy_id=row['native_carmy_id'])
                joined=copy.deepcopy(row)
                if 'actual_supply_callback_observations_v1' in row:joined['actual_supply_callback_observations_v1']=normalized
                expected=summary(joined,after_sequence=fence)
                service=GameplayBridgeService._current_callback_supply_projection_rows([joined])['actual_supply_callback_observation_summary_v1']
                if row!=untouched:raise RuntimeError('callback producer mutated source')
                scenes.append(dict(name=name,input=row,normalized=normalized,fence=fence,expected=expected,service=service))
            scene('joined_optional_parent',copy.deepcopy(base));scene('fenced',copy.deepcopy(base),1)
            absent=dict(army_id=0,native_carmy_id=16777216);scene('absent',absent)
            null=dict(absent,actual_supply_callback_observations_v1=None);scene('null',null)
            empty=copy.deepcopy(base);empty['actual_supply_callback_observations_v1'].update(event_count=0,events=[],oldest_available_sequence=0,latest_sequence=0);scene('empty',empty)
            five=copy.deepcopy(base);family=five['actual_supply_callback_observations_v1'];original=copy.deepcopy(family['events'][0]);events=[]
            for i,delta in enumerate([-125000,0,0,125000,None]):
                e=copy.deepcopy(original);e.update(sequence=i+1,same_instance_after=delta is not None,capture_failure_flags=9)
                e['before'].update(supply_raw=200000,province_id=None);e['after'].update(supply_raw=200000+(delta or 0),province_id=-2147483648)
                events.append(e)
            family.update(events=events,event_count=5,latest_sequence=5,observer_installed=False);scene('complete_partial_and_zero',five);scene('fence_three',copy.deepcopy(five),3)
            huge=copy.deepcopy(base);family=huge['actual_supply_callback_observations_v1'];e=family['events'][0]
            family.update(latest_sequence=(1<<64)-1,oldest_available_sequence=(1<<64)-1,overwritten_events=(1<<64)-1)
            e.update(sequence=(1<<64)-1,passed_date_raw64=(1<<64)-1,caller_return_rva=(1<<64)-1)
            e['before'].update(supply_raw=-(1<<63),last_supply_update_date_raw64=(1<<64)-1)
            e['after'].update(supply_raw=(1<<63)-1,last_supply_update_date_raw64=0)
            e['supply_parent_invocation_v1'].update(invocation_token=(1<<64)-1,nesting_depth=2,parent_invocation_token=7,callback_caller_return_rva=(1<<64)-1)
            scene('full_width_and_65bit_delta',huge);scene('arbitrary_sequence_fence',copy.deepcopy(huge),1<<100)
            duplicate=copy.deepcopy(base);family=duplicate['actual_supply_callback_observations_v1'];family.update(events=family['events']*2,event_count=2);scene('preserve_duplicate_occurrences',duplicate)
            stocks=[];D=43800024
            stockbase=f['row'](f['inputs']());stockbase.update(current_supply_raw=100000000,current_supply_capacity_raw=200000000)
            stockbase['monthly_loss_budget_inputs_v1']=dict(unit_native_170_raw=0,native_unit_in_combat=False,native_unit_gathering=False,army_gathering_count_raw=0,loaded_supply_state_levels=[2000,1000,0],loaded_supply_state_fractions_raw=[0,12500,25000],commander_valid=False,commander_supply_modifier_raw=None,native_fleet_supply_loss_suppressed=False)
            stockbase['loss_application_inputs_v1']=dict(supply_eligible_soldiers=100,current_supply_loss_budget=12)
            stockbase['army_update_clock_v1']=dict(current_date_raw=D,last_supply_update_date_raw=D-24,grace_anchor_date_raw=D-48,loaded_grace_days=0,last_supply_update_date_storage_raw64=D-24,grace_anchor_date_storage_raw64=D-48)
            stockbase['monthly_caller_effect_inputs_v1']=dict(army_byte_22_raw=1,current_date_storage_raw64=D)
            stockbase['source_derived_next_daily_supply_frame_inputs_v1']=dict(schema_version=1,source='native_source_derived_next_daily_supply_frame_inputs_12004',stage='source_derived_conditional_next_date_pair',status='available',ready=True,unavailable_reason=None,current_date_storage_raw64=D,current_date_raw_i32=D,current_native_day_index_raw_i32=1,source_derived_next_date_raw_i32=D+24,source_derived_next_native_day_index_raw_i32=2,subject_army_id_u32=11,subject_carmy_id_u32=12,actual_future_date_stage_observed=False,actual_future_callback_observed=False,future_bucket_mutations_reconstructed=False,future_stock_or_strength_ready=False,full_daily_supply_transition_ready=False,full_monthly_ready=False,source_derived_next_date_storage_raw64=1234567890123456789,source_derived_next_calendar_day_u8=2,source_derived_next_calendar_month_u8=3,source_derived_full_cdate64_ready=True)
            stockbase['current_fleet_supply_tick_inputs_v1']=dict(source='native_current_fleet_supply_tick_inputs',status='not_fleet',ready=True,unavailable_reason=None,scale=100000,subject_army_id=11,subject_carmy_id=12,province_id=1,current_native_date_low32=None,fleet_raw_full_id=None,fleet_resolved_full_id=None,fleet_day_raw=None,loaded_fleet_day_sentinel_raw=None,commander_raw_full_id=None,commander_resolved_full_id=None,terrain_modifier_772_raw=None,loaded_fleet_loss_raw=None,commander_modifier_1a9_raw=None,loaded_divisor_floor_raw=None,loaded_max_loss_raw=None,native_fleet_branch_applicable=False,fleet_used_native_fallback=None,commander_used_native_fallback=None,terrain_magic_38_raw=None,terrain_modifier_772_id=None)
            for name in ['admitted','rejected_zero','wrap_negative_no_capacity','missing_current_usage','unknown_admission','empty_state_levels','over_limit','diagnostic_wide_byte_observed']:
                row=copy.deepcopy(stockbase)
                if name=='rejected_zero':row['current_supply_raw']=0;row['monthly_loss_budget_inputs_v1']['unit_native_170_raw']=3
                if name=='wrap_negative_no_capacity':row.update(current_supply_raw=(1<<63)-1,current_supply_capacity_raw=None)
                if name=='missing_current_usage':row['current_province_supply_contributors_v1'].update(current_usage_ready=False,native_supply_usage_soldiers=None)
                if name=='unknown_admission':row['monthly_loss_budget_inputs_v1']['unit_native_170_raw']=None
                if name=='empty_state_levels':row['monthly_loss_budget_inputs_v1'].update(loaded_supply_state_levels=[],loaded_supply_state_fractions_raw=None)
                if name=='over_limit':row['current_province_supply_contributors_v1']['native_supply_usage_soldiers']=110
                if name=='diagnostic_wide_byte_observed':row['monthly_caller_effect_inputs_v1']['army_byte_22_raw']=(1<<63)-1
                before=copy.deepcopy(row);expected=landstock(row)
                if row!=before:raise RuntimeError('LAND outer producer mutated source')
                stocks.append(dict(name=name,input=row,expected=expected))
            pins();print(json.dumps(dict(normalizers=normalized,gains=gains,callbacks=scenes,stocks=stocks,whole_original_tests=2),separators=(',',':')))
            """;

    @Test void originalNormalizersNestedDataAndGainConsumerMatchTheSharedJavaContracts() throws Exception {
        JsonNode original = oracle(); assertEquals(2, original.path("whole_original_tests").intValue());
        for (JsonNode scene : original.path("normalizers")) {
            JsonNode actual = scene.path("kind").textValue().equals("province") ? LandContextCodec.encodeProvince(LandContextCodec.decodeProvince(scene.get("input")))
                    : LandContextCodec.encodeResupply(LandContextCodec.decodeResupply(scene.get("input")));
            same(scene.get("expected"), actual);
        }
        for (JsonNode scene : original.path("gains")) same(scene.get("expected"), ArmyStrengthsSupply.encodeGain(ArmyStrengthsSupply.projectGain(
                LandContextCodec.decodeResupply(scene.get("input")), scene.path("usage").intValue(), scene.path("limit").intValue())));
    }
    @Test void actualCallbackProducerSummaryAndServiceObservationFieldSurviveExactSerialization() throws Exception {
        for (JsonNode scene : oracle().path("callbacks")) {
            JsonNode row = scene.get("input"); var family = ArmyStrengthsSupply.decodeCallbacks(row.get("actual_supply_callback_observations_v1"), row.path("army_id").intValue(), row.path("native_carmy_id").intValue());
            same(scene.get("normalized"), ArmyStrengthsSupply.encodeCallbacks(family));
            JsonNode actual = ArmyStrengthsSupply.encodeSummary(ArmyStrengthsSupply.summarize(family, scene.path("fence").bigIntegerValue()));
            same(scene.get("expected"), actual); same(scene.get("service").get(0).get("observation"), ArmyStrengthsSupply.encodeSummary(ArmyStrengthsSupply.summarize(family, BigInteger.ZERO)));
            assertFalse(actual.path("actual_physical_soldier_loss_observed").booleanValue()); assertFalse(actual.path("future_supply_projected").booleanValue());
            same(actual, ArmyStrengthsCodec.parseValue(new RawJson(ArmyJson.bytes(actual))));
            if (family != null) assertThrows(UnsupportedOperationException.class, () -> family.events().clear());
        }
    }
    @Test void originalCompleteOuterLandProducerUsesTheExistingSharedPolicyAndExplicitDecimal64Paths() throws Exception {
        for (JsonNode scene : oracle().path("stocks")) {
            JsonNode row = scene.get("input"), before = row.deepCopy(); var value = ArmyStrengthsSupply.projectLandStock(row);
            JsonNode actual = LandContextCodec.encodeStockProjection(value); same(scene.get("expected"), actual); same(before, row);
            JsonNode publicValue = ArmyStrengthsCodec.parseValue(ArmyStrengthsPublicNumbers.encode(new RawJson(ArmyJson.bytes(actual)), ArmyStrengthsSupply.landStockRules()));
            assertTrue(publicValue.path("observed_current_stock_raw").isTextual());
            if (actual.path("source_next_date").isObject()) assertEquals(actual.path("source_next_date").path("source_derived_next_date_storage_raw64").asText(), publicValue.path("source_next_date").path("source_derived_next_date_storage_raw64").asText());
            assertTrue(publicValue.path("conditional_pre_rate_writes").get(0).get("conditional_value").isIntegralNumber());
            JsonNode rawDate = actual.path("conditional_pre_rate_writes").get(1).get("observed_value"), publicDate = publicValue.path("conditional_pre_rate_writes").get(1).get("observed_value");
            if (!rawDate.isNull()) assertEquals(rawDate.bigIntegerValue().toString(), publicDate.textValue());
        }
    }
    @Test void installedRegistryAndPipelineKeepNativePacketsAndPublicDecimal64Separate() throws Exception {
        JsonNode scene = oracle().path("callbacks").get(7), input = scene.get("input");
        var registry = new ArmyStrengthsFamilies.Registry(); var pipeline = new ArmyStrengthsPipeline(); ArmyStrengthsSupply.install(registry, pipeline, source()); registry.freeze(); pipeline.freeze();
        ObjectNode core = core(input.path("army_id").intValue(), input.path("native_carmy_id").intValue()); var typedCore = ArmyStrengthsCodec.core(core);
        var callback = registry.normalize(ArmyStrengthsFamilies.Key.ACTUAL_SUPPLY_CALLBACK_OBSERVATIONS_V1,
                new Present<>(new RawJson(ArmyJson.bytes(input.get("actual_supply_callback_observations_v1")))), new ArmyStrengths.RowContext(typedCore, new Missing<>()));
        same(scene.get("normalized"), ArmyStrengthsCodec.parseValue(callback.normalizedJson()));
        Row row = new Row(typedCore, List.of(), new Missing<>(), new Missing<>(), List.of(callback));
        Snapshot snapshot = snapshot(row.core().army().value()); Read read = new Read(Profile.ORDINARY_CORE_V1, Status.AVAILABLE, BigInteger.ONE, "pure-original-supply-fixture", List.of(row), new Missing<>(), new Missing<>(), receipt(snapshot));
        var results = pipeline.projectAvailable(new ArmyStrengthsPipeline.Input(snapshot, read, new Query(Profile.ORDINARY_CORE_V1, Mode.EXPLICIT_RICH, new Present<>(List.of(row.core().army())), EntryMode.OBSERVED_PREPARED, EntryMode.OBSERVED_PREPARED), List.of(row)));
        JsonNode service = results.topLevelJson().get("actual_supply_callback_observation_summary_v1");
        assertTrue(service.get(0).has("observation")); assertFalse(service.get(0).has("projection")); same(scene.get("service"), service);
        if (!(callback.value() instanceof Present<?> present)) throw new AssertionError("actual callback family must be present");
        JsonNode raw = ArmyStrengthsSupply.encodeCallbacks(assertInstanceOf(ArmyStrengthsSupply.CallbackFamily.class, present.value()));
        JsonNode publicValue = ArmyStrengthsCodec.parseValue(ArmyStrengthsPublicNumbers.encode(new RawJson(ArmyJson.bytes(raw)), ArmyStrengthsSupply.callbackRules()));
        assertEquals("18446744073709551615", publicValue.path("events").get(0).path("sequence").textValue());
        assertEquals("-9223372036854775808", publicValue.path("events").get(0).path("before").path("supply_raw").textValue());
        same(publicValue, ArmyStrengthsCodec.parseValue(callback.publicV2Json()));
        assertEquals("18446744073709551615", results.topLevelPublicV2Json().path("actual_supply_callback_observation_summary_v1").get(0).path("observation").path("sum_observed_supply_delta_raw").textValue());
        assertTrue(raw.path("events").get(0).path("sequence").isIntegralNumber());
        assertFalse(registry.coverage().complete()); assertFalse(pipeline.coverage().complete());
    }
    @Test void wrongFieldsTypesIdentityGenerationAndOptionalParentAreRejectedWithoutInventingOrderRules() throws Exception {
        ObjectNode row = oracle().path("callbacks").get(0).path("input").deepCopy(); ObjectNode valid = (ObjectNode) row.get("actual_supply_callback_observations_v1");
        for (String field : List.of("oldest_available_sequence", "latest_sequence", "event_count")) for (JsonNode token : List.of(ArmyJson.empty().booleanNode(true), ArmyJson.empty().numberNode(1.0), ArmyJson.empty().textNode("1"))) {
            ObjectNode bad = valid.deepCopy(); bad.set(field, token); assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsSupply.decodeCallbacks(bad, 0, 16777216));
        }
        ObjectNode missing = valid.deepCopy(); missing.remove("observer_installed"); assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsSupply.decodeCallbacks(missing, 0, 16777216));
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsSupply.decodeCallbacks(valid.deepCopy().put("unknown", 0), 0, 16777216));
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsSupply.decodeCallbacks(valid, 16777216, 16777216));
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsSupply.decodeCallbacks(valid, 0, 33554432));
        for (String field : List.of("invocation_token", "native_thread_id", "nesting_depth")) {
            ObjectNode bad = valid.deepCopy(); ((ObjectNode) bad.path("events").get(0).get("supply_parent_invocation_v1")).put(field, 0);
            assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsSupply.decodeCallbacks(bad, 0, 16777216));
        }
        ObjectNode badParent = valid.deepCopy(); ((ObjectNode) badParent.path("events").get(0)).putNull("supply_parent_invocation_v1");
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsSupply.decodeCallbacks(badParent, 0, 16777216));
        assertThrows(IllegalArgumentException.class, () -> ArmyStrengthsSupply.summarize(null, BigInteger.valueOf(-1)));
    }
    private static JsonNode cached;
    private static synchronized JsonNode oracle() throws Exception {
        if (cached != null) return cached.deepCopy(); String manifest = required("xar.strengths.supply.oracle.manifest"), sha = required("xar.strengths.supply.oracle.manifest.sha256");
        byte[] manifestBytes = Files.readAllBytes(Path.of(manifest)); assertEquals(sha, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(manifestBytes)), "SUPPLY original source manifest drift");
        Process child = new ProcessBuilder(required("xar.python"), "-B", "-I", "-X", "utf8", "-c", ORACLE, manifest).redirectErrorStream(true).start();
        var bytes = new java.io.ByteArrayOutputStream(); Thread reader = Thread.ofPlatform().daemon().start(() -> { try { child.getInputStream().transferTo(bytes); } catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); } });
        if (!child.waitFor(45, TimeUnit.SECONDS)) { child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); fail("actual original SUPPLY producer timed out"); }
        reader.join(5000); assertFalse(reader.isAlive(), "original producer stream did not complete"); assertEquals(0, child.exitValue(), bytes.toString(StandardCharsets.UTF_8));
        cached = ArmyStrengthsCodec.parseValue(new RawJson(bytes.toByteArray())); return cached.deepCopy();
    }
    private static ExactRef source() throws Exception {
        JsonNode value = ArmyStrengthsCodec.parseValue(new RawJson(Files.readAllBytes(Path.of(required("xar.strengths.supply.oracle.manifest"))))).get("java_bundle_source");
        return new ExactRef(value.path("path").textValue(), value.path("bytes").longValue(), value.path("sha256").textValue());
    }
    private static ObjectNode core(int army, int nativeArmy) { return ArmyJson.empty().put("status", "available").put("army_id", army).put("native_carmy_id", nativeArmy).put("scope_role", "player").put("regiment_count", 0).put("current_soldiers", 0).put("maximum_soldiers", 0).put("ai_base_power_raw", 0).put("ai_base_power_scale", 100000).putNull("unavailable_reason").set("war_ids", ArmyJson.empty().arrayNode()); }
    private static Snapshot snapshot(int army) {
        Instant now = Instant.now(); ExactRef ref = new ExactRef("pure-supply-fixture", 1, "a".repeat(64)); G2Source source = new G2Source("fixture-machine-not-live", now.toString(), "pure-source-bound", ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ZERO, BigInteger.valueOf(11), BigInteger.valueOf(53238336)), "native:11", BigInteger.valueOf(7), "fixture-episode");
        Context context = new Context(new ProposalLifecycle.ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "fixture-session", now.plusSeconds(60));
        ObjectNode raw = ArmyJson.empty().put("snapshot_id", "native:11").put("revision", 7).put("native_revision", 11).put("date_raw", 53238336).put("episode_run_id", "fixture-episode").put("paused", true).put("map_ready", true);
        raw.putObject("played_character").put("character_id", 0).put("alive", true); raw.putObject("diagnostics").put("connection_generation", 5); raw.putArray("player_armies").addObject().put("army_id", army); raw.putArray("active_wars"); return ArmyStrengthsCodec.snapshot(context, new RawJson(ArmyJson.bytes(raw)));
    }
    private static PlanningReadReceipt receipt(Snapshot snapshot) {
        Context c = snapshot.context(); OperationKey operation = new OperationKey(STEP); var request = new PlanningReadRequest(c.before(), c.source(), c.sessionId(), operation, new OpportunityJson.Obj(java.util.Map.of()), c.deadline());
        var guard = new PlanningReadGuard(new GuardEvidence(c.before(), c.source(), c.sessionId(), snapshot.binding().connectionGeneration(), operation, c.source().sourceRef(), c.source().sourceRef(), "pure-source-bound", Instant.now(), c.deadline()), true, true, true, "b".repeat(64));
        byte[] body = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"supply-pure\",\"ok\":true,\"result\":{}}".getBytes(StandardCharsets.UTF_8);
        try { return new PlanningReadReceipt(request, "supply-pure", "supply-pure", guard, guard, new NativeActionPort.AckReceived("supply-pure", true, Optional.of(new RawJson("{}".getBytes(StandardCharsets.UTF_8))), new RawJson(body), org.xar.ck3.control.nativebridge.NativeWire.packet(body))); }
        catch (java.io.IOException invalid) { throw new IllegalArgumentException(invalid); }
    }
    private static void same(JsonNode expected, JsonNode actual) { assertArrayEquals(StrictJson.canonical(expected, RawJson.MAXIMUM_BYTES), StrictJson.canonical(actual, RawJson.MAXIMUM_BYTES)); }
    private static String required(String name) { String value = System.getProperty(name); if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: mandatory original SUPPLY property missing: " + name); return value; }
}
