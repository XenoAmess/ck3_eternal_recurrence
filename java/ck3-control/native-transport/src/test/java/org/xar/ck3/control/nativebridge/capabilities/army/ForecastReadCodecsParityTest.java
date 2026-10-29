package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** The actual complete original contract tests/producers are required, never a replacement Python model or native/Game claim. */
final class ForecastReadCodecsParityTest {
    private static final String ORACLE = """
            import copy,hashlib,json,pathlib,runpy,sys,unittest
            m=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
            def pins():
                for r in m['original_sources']:
                    b=pathlib.Path(r['path']).read_bytes()
                    if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise RuntimeError('forecast original source drift: '+r['path'])
            pins();root=pathlib.Path(m['repository_root']);unit=root/'ck3_autonomous_player/tests/unit'
            sys.path[:0]=[str(root),str(root/'ck3_autonomous_player/src'),str(unit),str(root/'ck3_workshop_mcp/src'),str(root/'tools')]
            w=runpy.run_path(str(unit/'test_war_entry_contract.py'));p=runpy.run_path(str(unit/'test_combat_phase_event_trace_query.py'))
            from xar_autoplayer.bridge import war_entry_contract as contract,combat_phase_event_trace_contract as phase_contract,event_window_context_contract as event_contract
            for module in [contract,phase_contract,event_contract]:
                if pathlib.Path(module.__file__).resolve()!=root/'ck3_autonomous_player/src/xar_autoplayer/bridge'/pathlib.Path(module.__file__).name:raise RuntimeError('forecast original import route drift')
            war=[];phase=[]
            def wrap(fn,name,output):
                def invoke(*args,**kwargs):
                    item=dict(name=name,args=copy.deepcopy(args),kwargs=copy.deepcopy(kwargs))
                    try:result=fn(*args,**kwargs)
                    except ValueError:
                        item['error']=True;output.append(item);raise
                    item.update(error=False,expected=copy.deepcopy(result));output.append(item);return result
                return invoke
            wg=w['WarEntryRequestContractTests'].test_canonical_literal_round_trips_one_production_target.__globals__
            for name in ['normalize_war_entry_target_ids','query_war_entry_assessments_step','parse_query_war_entry_assessments_step','require_declarable_war_targets','require_war_entry_assessment_targets','raiktor_bookmark_saved_scope_target_v1','war_entry_assessment_target_scopes','normalize_war_entry_assessments']:wg[name]=wrap(wg[name],name,war)
            pg=p['CombatPhaseEventTraceQueryTest'].test_full_generation_literal.__globals__
            for name in ['normalize_combat_phase_event_trace_v1','normalize_experimental_counter_output_response_v1','normalize_runtime_counter_output_diagnostic_v1','parse_query_combat_phase_event_trace_v1_step','query_combat_phase_event_trace_v1_step']:pg[name]=wrap(pg[name],name,phase)
            suite=unittest.TestSuite()
            for cls in [w['WarEntryRequestContractTests'],w['WarEntryAvailableResultContractTests'],p['CombatPhaseEventTraceQueryTest']]:suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
            result=unittest.TextTestRunner(stream=sys.stderr,verbosity=0).run(suite)
            if not result.wasSuccessful():raise RuntimeError('complete original forecast read contract regression is RED')
            normalize=wg['normalize_war_entry_assessments']
            for provenance in contract._PROVENANCE_BY_BUILD.values():
                value=w['_payload']();value['provenance']=copy.deepcopy(provenance);normalize(value)
            huge=w['_payload']();huge['snapshot_revision']=(1<<63)-1
            row=huge['assessments'][0];row.update(actor_power_base_raw=(1<<63)-1,actor_network_contribution_raw=-(1<<63)+2,actor_power_total_raw=1,actual_power_ratio_raw=(1<<63)-1);normalize(huge)
            raw=p['available_trace']();raw['cadence']['period_days']=(1<<32)-1
            raw['characters'][0]['event_rows'][0].update(chance_raw=-(1<<63),int_weight=-(1<<31))
            raw['characters'][0]['event_rows'][1].update(chance_raw=(1<<63)-1,int_weight=(1<<31)-1)
            pg['normalize_combat_phase_event_trace_v1'](raw,combat_id=738197508)
            counter=p['managed_counter_trace']();counter['trace']['runtime_counter_output']['sides'][0].update(context_raw=-(1<<63),retention_raw=[-(1<<63),(1<<63)-1])
            pg['normalize_runtime_counter_output_diagnostic_v1'](counter)
            counter['trace']['failure_flags']=8;pg['normalize_runtime_counter_output_diagnostic_v1'](counter)
            experimental=p['experimental_counter_response']();experimental['result']['managed_daily_sequence_token']=(1<<64)-1
            pg['normalize_experimental_counter_output_response_v1'](experimental,combat_id=738197508)
            pins();print(json.dumps(dict(war=war,phase=phase,complete_original_test_count=result.testsRun),separators=(',',':')))
            """;
    @Test void completeOriginalWarRequestPowerAndEventScopeProducersMatchTheSoleJavaCodec() throws Exception {
        JsonNode corpus = corpus(); assertTrue(corpus.path("complete_original_test_count").intValue() >= 20); assertTrue(corpus.path("war").size() >= 35);
        for (JsonNode scene : corpus.path("war")) compare(scene, () -> war(scene));
    }
    @Test void completeOriginalPausedAndManagedCounterDiagnosticsMatchWithoutForecastPromotion() throws Exception {
        JsonNode corpus = corpus(); assertTrue(corpus.path("phase").size() >= 25);
        for (JsonNode scene : corpus.path("phase")) compare(scene, () -> phase(scene));
    }
    @Test void exactPowerIntegersAndAllBuildProvenanceSurviveNativeAndPublicDecimal64Serialization() throws Exception {
        int builds = 0; boolean huge = false;
        for (JsonNode scene : corpus().path("war")) if (!scene.path("error").booleanValue() && scene.path("name").textValue().equals("normalize_war_entry_assessments")) {
            var observed = WarEntryAssessmentCodec.normalize(scene.path("args").get(0)); JsonNode nativeValue = observed.toNativeJson(), publicValue = observed.toPublicV2Json();
            same(nativeValue, parse(bytes(nativeValue))); same(publicValue, parse(bytes(publicValue))); assertTrue(publicValue.path("snapshot_revision").isTextual());
            for (JsonNode row : publicValue.path("assessments")) assertTrue(row.path("actual_power_ratio_raw").isTextual());
            if (nativeValue.path("snapshot_revision").bigIntegerValue().equals(BigInteger.valueOf(Long.MAX_VALUE))) { huge = true; assertEquals("9223372036854775807", publicValue.path("snapshot_revision").textValue()); }
            builds |= switch (nativeValue.path("provenance").path("game_version").textValue()) { case "1.19.0.6" -> 1; case "1.20.0.2" -> 2; case "1.20.0.3" -> 4; case "1.20.0.4" -> 8; default -> 0; };
            assertThrows(UnsupportedOperationException.class, () -> observed.assessments().clear());
        }
        assertEquals(15, builds); assertTrue(huge);
    }
    @Test void phaseAndCounterWideValuesHaveAnExplicitPublicSchemaAndStayDiagnostic() throws Exception {
        boolean wideChance = false, wideCounter = false, wideToken = false;
        for (JsonNode scene : corpus().path("phase")) if (!scene.path("error").booleanValue()) {
            String name = scene.path("name").textValue(); JsonNode raw = scene.path("args").get(0);
            if (name.equals("normalize_combat_phase_event_trace_v1")) {
                var observed = CombatPhaseEventTraceCodec.normalize(raw, combat(scene)); JsonNode publicValue = observed.toPublicV2Json();
                assertFalse(publicValue.path("production_trace_ready").booleanValue());
                if (raw.path("cadence").path("period_days").longValue() == 0xffff_ffffL) { wideChance = true; assertEquals("-9223372036854775808", publicValue.path("characters").get(0).path("event_rows").get(0).path("chance_raw").textValue()); }
                same(observed.toNativeJson(), parse(bytes(observed.toNativeJson())));
            } else if (name.equals("normalize_runtime_counter_output_diagnostic_v1")) {
                var diagnostic = CombatPhaseEventTraceCodec.normalizeRuntimeCounterOutputDiagnostic(raw);
                if (diagnostic.isPresent()) { assertFalse(diagnostic.orElseThrow().forecastUsable()); JsonNode publicValue = diagnostic.orElseThrow().toPublicV2Json();
                    if (!diagnostic.orElseThrow().sides().isEmpty() && diagnostic.orElseThrow().sides().getFirst().contextRaw() == Long.MIN_VALUE) { wideCounter = true; assertEquals("-9223372036854775808", publicValue.path("sides").get(0).path("retention_raw").get(0).textValue()); }
                }
            } else if (name.equals("normalize_experimental_counter_output_response_v1")) {
                var diagnostic = CombatPhaseEventTraceCodec.normalizeExperimentalCounterOutputResponse(raw, combat(scene));
                if (diagnostic.isPresent() && diagnostic.orElseThrow().managedDailySequenceToken().bitLength() == 64) { wideToken = true; assertEquals("18446744073709551615", diagnostic.orElseThrow().toPublicV2Json().path("managed_daily_sequence_token").textValue()); }
            }
        }
        assertTrue(wideChance && wideCounter && wideToken);
    }
    @Test void newlyTypedNativeFieldsRejectPythonEqualityAliasesAndAllExpectedFrameDimensionsAreBound() throws Exception {
        ObjectNode war = validWar();
        for (JsonNode bad : List.of(empty().booleanNode(true), empty().numberNode(1.0), empty().textNode("1"))) {
            ObjectNode changed = war.deepCopy(); changed.set("schema_version", bad); assertThrows(IllegalArgumentException.class, () -> WarEntryAssessmentCodec.normalize(changed));
            ObjectNode unreadied = war.deepCopy(); ((ObjectNode) unreadied.get("readiness")).set("ready", bad); assertThrows(IllegalArgumentException.class, () -> WarEntryAssessmentCodec.normalize(unreadied));
        }
        var expected = new WarEntryAssessmentCodec.Expected(List.of(808), BigInteger.valueOf(29829), BigInteger.valueOf(17), BigInteger.valueOf(53171400));
        WarEntryAssessmentCodec.normalize(war, expected);
        assertThrows(IllegalArgumentException.class, () -> WarEntryAssessmentCodec.normalize(war, new WarEntryAssessmentCodec.Expected(List.of(808), expected.actorCharacterId(), expected.nativeRevision(), expected.dateRaw().add(BigInteger.ONE))));
        ObjectNode trace = validTrace(); ((ObjectNode) trace.get("cadence")).put("period_days", true); assertThrows(IllegalArgumentException.class, () -> CombatPhaseEventTraceCodec.normalize(trace, 738197508));
        ObjectNode role = validTrace(); ((ObjectNode) role.get("characters").get(0)).put("ordered_knight", 0); assertThrows(IllegalArgumentException.class, () -> CombatPhaseEventTraceCodec.normalize(role, 738197508));
        ObjectNode loadIndex = validTrace(); ((ObjectNode) loadIndex.get("characters").get(0).get("event_rows").get(1)).put("global_load_index", true); assertThrows(IllegalArgumentException.class, () -> CombatPhaseEventTraceCodec.normalize(loadIndex, 738197508));
        ObjectNode falseOpponent = empty(); falseOpponent.putArray("declarable_wars").addObject().put("target_character_id", 808); falseOpponent.putArray("active_wars").addObject().put("primary_opponent_character_id", false);
        assertThrows(IllegalArgumentException.class, () -> WarEntryAssessmentCodec.targetScopes(falseOpponent, List.of(808)));
    }
    @Test void eventScopeAndLiteralResultsAreImmutableAndNeverAuthorizeAnUnrelatedWarTarget() throws Exception {
        ObjectNode snapshot = empty(); snapshot.putArray("declarable_wars").addObject().put("target_character_id", 808); snapshot.putArray("active_wars").addObject().put("primary_opponent_character_id", 808);
        var scopes = WarEntryAssessmentCodec.targetScopes(snapshot, List.of(808)); assertEquals(2, scopes.targets().getFirst().sources().size()); assertThrows(UnsupportedOperationException.class, () -> scopes.targets().clear());
        assertThrows(IllegalArgumentException.class, () -> WarEntryAssessmentCodec.targetScopes(snapshot, List.of(809)));
        for (String malformed : List.of("query-war-entry-assessments-v1-1-0808", "query-war-entry-assessments-v1-1-８０８", "query-war-entry-assessments-v1-2-808-808", "query-war-entry-assessments-v1-1-2147483648")) assertTrue(WarEntryAssessmentCodec.parseStep(malformed).isEmpty());
        for (String malformed : List.of("query-combat-phase-event-trace-v1-01", "query-combat-phase-event-trace-v1-2147483648", "query-combat-phase-event-trace-v1-７")) assertTrue(CombatPhaseEventTraceCodec.parseStep(malformed).isEmpty());
        assertTrue(WarEntryAssessmentCodec.parseStep(WarEntryAssessmentCodec.step(List.of(Integer.MAX_VALUE))).isPresent()); assertEquals(Integer.MAX_VALUE, CombatPhaseEventTraceCodec.parseStep(CombatPhaseEventTraceCodec.step(Integer.MAX_VALUE)).orElseThrow());
    }
    private static JsonNode war(JsonNode scene) {
        JsonNode args = scene.path("args"), kw = scene.path("kwargs"); String name = scene.path("name").textValue(); JsonNode raw = args.get(0);
        return switch (name) {
            case "normalize_war_entry_target_ids" -> ints(WarEntryAssessmentCodec.normalizeTargetIds(raw));
            case "query_war_entry_assessments_step" -> empty().textNode(WarEntryAssessmentCodec.step(WarEntryAssessmentCodec.normalizeTargetIds(raw)));
            case "parse_query_war_entry_assessments_step" -> raw.isTextual() ? WarEntryAssessmentCodec.parseStep(raw.textValue()).<JsonNode>map(ForecastReadCodecsParityTest::ints).orElse(NullNode.getInstance()) : NullNode.getInstance();
            case "require_declarable_war_targets" -> ints(WarEntryAssessmentCodec.requireDeclarableTargets(raw, WarEntryAssessmentCodec.normalizeTargetIds(args.get(1))));
            case "war_entry_assessment_target_scopes" -> WarEntryAssessmentCodec.targetScopes(raw, WarEntryAssessmentCodec.normalizeTargetIds(args.get(1)), kw.get("event_context")).toNativeJson();
            case "require_war_entry_assessment_targets" -> { List<Integer> targets = WarEntryAssessmentCodec.normalizeTargetIds(args.get(1)); WarEntryAssessmentCodec.targetScopes(raw, targets, kw.get("event_context")); yield ints(targets); }
            case "raiktor_bookmark_saved_scope_target_v1" -> { var result = WarEntryAssessmentCodec.raiktorSavedScopeTarget(raw, args.get(1)); yield result.isPresent() ? empty().numberNode(result.getAsInt()) : NullNode.getInstance(); }
            case "normalize_war_entry_assessments" -> {
                if (kw.isEmpty()) yield WarEntryAssessmentCodec.normalize(raw).toNativeJson();
                List<Integer> targets = WarEntryAssessmentCodec.normalizeTargetIds(kw.hasNonNull("expected_target_character_ids") ? kw.get("expected_target_character_ids") : raw.get("requested_target_character_ids"));
                var expected = new WarEntryAssessmentCodec.Expected(targets, integer(kw.hasNonNull("expected_actor_character_id") ? kw.get("expected_actor_character_id") : raw.get("actor_character_id")), integer(kw.hasNonNull("expected_snapshot_revision") ? kw.get("expected_snapshot_revision") : raw.get("snapshot_revision")), integer(raw.get("date_raw")));
                yield WarEntryAssessmentCodec.normalize(raw, expected).toNativeJson();
            }
            default -> throw new AssertionError("unknown original war producer " + name);
        };
    }
    private static JsonNode phase(JsonNode scene) {
        JsonNode args = scene.path("args"), raw = args.get(0); return switch (scene.path("name").textValue()) {
            case "query_combat_phase_event_trace_v1_step" -> empty().textNode(CombatPhaseEventTraceCodec.step(i32(raw)));
            case "parse_query_combat_phase_event_trace_v1_step" -> { var result = raw.isTextual() ? CombatPhaseEventTraceCodec.parseStep(raw.textValue()) : java.util.OptionalInt.empty(); yield result.isPresent() ? empty().numberNode(result.getAsInt()) : NullNode.getInstance(); }
            case "normalize_combat_phase_event_trace_v1" -> CombatPhaseEventTraceCodec.normalize(raw, combat(scene)).toNativeJson();
            case "normalize_runtime_counter_output_diagnostic_v1" -> CombatPhaseEventTraceCodec.normalizeRuntimeCounterOutputDiagnostic(raw).<JsonNode>map(CombatPhaseEventTraceCodec.CounterDiagnostic::toNativeJson).orElse(NullNode.getInstance());
            case "normalize_experimental_counter_output_response_v1" -> CombatPhaseEventTraceCodec.normalizeExperimentalCounterOutputResponse(raw, combat(scene)).<JsonNode>map(CombatPhaseEventTraceCodec.ExperimentalCounterDiagnostic::toNativeJson).orElse(NullNode.getInstance());
            default -> throw new AssertionError("unknown original phase producer");
        };
    }
    private static int combat(JsonNode scene) { return i32(scene.path("kwargs").get("combat_id")); }
    private static ArrayNode ints(List<Integer> values) { var result = empty().arrayNode(); values.forEach(result::add); return result; }
    private interface Producer { JsonNode produce(); }
    private static void compare(JsonNode scene, Producer producer) {
        if (scene.path("error").booleanValue()) assertThrows(IllegalArgumentException.class, producer::produce, scene.path("name").textValue());
        else { JsonNode raw = scene.deepCopy(); same(scene.get("expected"), producer.produce()); same(raw, scene); }
    }
    private static ObjectNode validWar() throws Exception { for (JsonNode scene : corpus().path("war")) if (scene.path("name").asText().equals("normalize_war_entry_assessments") && !scene.path("error").booleanValue() && scene.path("args").get(0).path("snapshot_revision").intValue() == 17) return scene.path("args").get(0).deepCopy(); throw new AssertionError("actual original war fixture absent"); }
    private static ObjectNode validTrace() throws Exception { for (JsonNode scene : corpus().path("phase")) if (scene.path("name").asText().equals("normalize_combat_phase_event_trace_v1") && !scene.path("error").booleanValue() && scene.path("args").get(0).path("evaluator_probe_ready").booleanValue()) return scene.path("args").get(0).deepCopy(); throw new AssertionError("actual original phase fixture absent"); }
    private static JsonNode cached;
    private static synchronized JsonNode corpus() throws Exception {
        if (cached != null) return cached.deepCopy(); String manifest = required("xar.forecast.read.oracle.manifest"); byte[] raw = Files.readAllBytes(Path.of(manifest));
        assertEquals(required("xar.forecast.read.oracle.manifest.sha256"), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)), "forecast original source manifest changed");
        Process child = new ProcessBuilder(required("xar.python"), "-B", "-I", "-X", "utf8", "-c", ORACLE, manifest).start();
        var stdout = new java.io.ByteArrayOutputStream(); var stderr = new java.io.ByteArrayOutputStream();
        Thread output = Thread.ofPlatform().daemon().start(() -> transfer(child.getInputStream(), stdout)); Thread error = Thread.ofPlatform().daemon().start(() -> transfer(child.getErrorStream(), stderr));
        if (!child.waitFor(50, TimeUnit.SECONDS)) { child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly(); fail("actual original forecast read contracts timed out"); }
        output.join(5000); error.join(5000); assertFalse(output.isAlive() || error.isAlive()); assertEquals(0, child.exitValue(), stderr.toString(StandardCharsets.UTF_8)); cached = parse(stdout.toByteArray()); return cached.deepCopy();
    }
    private static void transfer(java.io.InputStream source, java.io.OutputStream target) { try { source.transferTo(target); } catch (java.io.IOException error) { throw new java.io.UncheckedIOException(error); } }
    private static void same(JsonNode expected, JsonNode actual) { assertArrayEquals(StrictJson.canonical(expected, RawJson.MAXIMUM_BYTES), StrictJson.canonical(actual, RawJson.MAXIMUM_BYTES)); }
    private static String required(String name) { String value = System.getProperty(name); if (value == null || value.isBlank()) throw new IllegalStateException("NOT EXECUTED: mandatory original forecast read property missing: " + name); return value; }
}
