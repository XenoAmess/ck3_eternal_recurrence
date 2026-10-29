package org.xar.ck3.control.wave2.military.combatwire;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime;
import org.xar.ck3.control.wave2.military.forecast.CombatInputs;
import org.xar.ck3.control.wave2.military.forecast.ConstructorAdvantage;
import org.xar.ck3.control.wave2.military.forecast.FixedContactForecast;

/** Actual unchanged Python producer -> Java v3 -> JSON/cache revalidation -> constructor consumer boundary. */
class CombatPhaseInputsParityTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final CombatPhaseInputsCodec CODEC = new CombatPhaseInputsCodec(new StockPhaseEventRuntime());
    private static ArrayNode originals;
    private static final String CAPTURE = """
        import copy,json,runpy,sys
        from pathlib import Path
        r=Path(sys.argv[1])
        m=runpy.run_path(str(r/'ck3_autonomous_player/tests/unit/test_combat_phase_inputs_v3_production_contract.py'))
        from xar_autoplayer.simulation.general_battle_forecast import forecast_fixed_contact,contact_admission,_native_precontact_advantage
        from xar_autoplayer.simulation.combat_input import freeze_combat_simulation_input
        cases=[]
        def add(name,p,s):
            try:
                normalized=m['_normalize'](p,s)
            except ValueError as e:
                cases.append({'name':name,'payload':p,'scope':s,'accepted':False,'error':str(e)})
                return
            base=normalized['base_inputs'];scenario=base['scenario']
            native=_native_precontact_advantage(normalized,freeze_combat_simulation_input(base,capture={}))
            forecast=forecast_fixed_contact(normalized,target_province_id=base['target_province_id'],attacker_entry_province_id=scenario['attacker_entry_province_id'],attacker_army_ids=tuple(scenario['attacker_army_ids']),defender_army_ids=tuple(scenario['defender_army_ids']),capture={},sample_count=16,horizon_days=4)
            cases.append({'name':name,'payload':p,'scope':s,'accepted':True,'normalized':normalized,'native_constructor_consumer':native,'forecast_consumer':forecast,'contact_admission_consumer':contact_admission(forecast)})
        def fresh(): return m['_production_payload']()
        p,s=fresh();add('full-original-producer',p,s)
        p,s=fresh();m['_swap_first_two_native_knights'](p);add('native-source-order-not-sorted-order',p,s)
        p,s=fresh();ph=p['phase_event_inputs'];ph.update(status='unavailable',raw=None,advantage_model=None,unavailable_reason='native phase inputs unavailable');add('unavailable-not-partial',p,s)
        p,s=fresh();raw=p['phase_event_inputs']['raw'];raw['characters'][0]['prowess']=-2147483648;raw['sides'][0]['side_strength_raw']=-2147483648;raw['sides'][1]['side_strength_raw']=2147483647;add('signed-q-truncation',p,s)
        p,s=fresh();raw=p['phase_event_inputs']['raw'];raw['sides'][0]['side_army_size_raw']=214748364700000;raw['sides'][1]['side_army_size_raw']=214748364700000;add('q-intermediate-exceeds-int64',p,s)
        p,s=fresh();raw=p['phase_event_inputs']['raw'];raw['characters'][0]['culture']={'status':'absent','value':None};add('absent-culture-is-not-missing',p,s)
        p,s=fresh();ph=p['phase_event_inputs'];ph['hard_casualty_winter']={'status':'available','source_target_province_id':p['base_inputs']['target_province_id'],'scale':100000,'first_original_guard':True,'second_original_guard':True,'raw':2**100,'unavailable_reason':None};add('guarded-unbounded-python-integer',p,s)
        p,s=fresh();ph=p['phase_event_inputs'];ph['hard_casualty_sides']={'status':'available','source_target_province_id':p['base_inputs']['target_province_id'],'scale':100000,'sides':[{'side_index':i,'encounter_role':q['encounter_role'],'ordered_army_ids':q['ordered_army_ids'],'commander_character_id':q['commander_character_id'] if q['commander_character_id'] is not None else -1,'own_modifier_raw':-9223372036854775808,'enemy_modifier_raw':9223372036854775807} for i,q in enumerate(ph['raw']['sides'])],'unavailable_reason':None};add('same-frame-private-sides-int64-boundaries',p,s)
        p,s=fresh();del p['phase_event_inputs']['raw']['characters'][0]['traits_or_groups']['brave'];add('missing-named-false-leaf',p,s)
        p,s=fresh();p['phase_event_inputs']['raw']['characters'][0]['character_id']=True;add('bool-character-id',p,s)
        p,s=fresh();p['phase_event_inputs']['raw']['sides'][0]['side_index']=True;add('wrong-side-index',p,s)
        p,s=fresh();p['phase_event_inputs']['raw']['sides'][0]['candidate_source_proof']['sequence_sha256']='0'*64;add('unbound-candidate-source',p,s)
        p,s=fresh();p['phase_event_inputs']['raw']['characters'][0]['wounded_rank_raw']=100000;add('wound-trait-disagreement',p,s)
        p,s=fresh();q=p['phase_event_inputs']['raw']['characters'][0];q['culture']={'status':'absent','value':None};q['innovations']['innovation_gunpowder']=True;add('absent-culture-owned-leaf',p,s)
        p,s=fresh();p['phase_event_inputs']['status']='unavailable';p['phase_event_inputs']['unavailable_reason']='failure';add('partial-unavailable',p,s)
        p,s=fresh();p['phase_event_inputs']['advantage_model']['resolved_dynamic']['original_total_helper_match']=False;add('helper-ack-not-equality',p,s)
        p,s=fresh();p['phase_event_inputs']['advantage_model']['constructor_sources'][0]['accumulator_after_raw']+=1;add('constructor-source-clamp-drift',p,s)
        p,s=fresh();normalized=m['_normalize'](p,s);normalized['phase_event_inputs']['evaluation_contexts'][0]['native_state_refs']['root.alive']=False;add('canonical-enriched-derivation-tamper',normalized,s)
        print(json.dumps({'schema':'original-combat-phase-v3-capture-v1','cases':cases},separators=(',',':')))
        """;
    @BeforeAll static void captureOriginalProducer() throws Exception {
        String source = requiredProperty("xar.repository.root"), python = requiredProperty("xar.python");
        requireFile(Path.of(source).resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/combat_phase_contract.py")); requireFile(Path.of(python));
        verifyPins(Path.of(source));
        Process process = new ProcessBuilder(python, "-I", "-c", CAPTURE, source).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        try {
            byte[] bytes = assertTimeoutPreemptively(Duration.ofSeconds(120), () -> process.getInputStream().readAllBytes());
            assertTrue(process.waitFor(10, TimeUnit.SECONDS), "original producer child did not finish"); assertEquals(0, process.exitValue(), "actual original Python producer failed");
            JsonNode captured = JSON.readTree(bytes); assertEquals("original-combat-phase-v3-capture-v1", captured.path("schema").asText()); originals = (ArrayNode) captured.get("cases"); assertEquals(18, originals.size());
            verifyPins(Path.of(source));
        } finally {
            process.getInputStream().close(); process.getOutputStream().close();
            if (process.isAlive()) { process.destroyForcibly(); assertTrue(process.waitFor(10, TimeUnit.SECONDS), "original producer child survived termination"); }
        }
    }
    @Test void rawProducerThroughJavaNormalizerFeedsActualForecastAndConstructorConsumers() {
        for (JsonNode original : originals) if (original.path("accepted").booleanValue()) {
            CombatRequest request = request(original.get("payload")); CombatEncounterScope scope = CombatEncounterScope.decode(original.get("scope"), request);
            CombatPhaseInputs normalized = CODEC.normalize(original.get("payload"), request, scope); CombatInputs.Capture capture = CombatInputs.Capture.empty();
            var frozen = CombatInputs.freeze(normalized.baseInputs().toJson(), capture); var nativeModel = ConstructorAdvantage.readV3(normalized.toJson(), frozen);
            JsonNode expectedNative = original.get("native_constructor_consumer");
            if (expectedNative.isNull()) assertTrue(nativeModel.isEmpty(), original.path("name").asText());
            else {
                var selection = nativeModel.orElseThrow(); assertEquals(expectedNative.get(0).bigIntegerValue(), selection.attackerArmyId()); assertEquals(expectedNative.get(1).bigIntegerValue(), selection.defenderArmyId());
                assertEquals(expectedNative.get(2).bigIntegerValue(), selection.zeroRollRaw()); assertEquals(expectedNative.get(4).asText(), selection.modelSha256());
                assertEquals(expectedNative.path(3).get(0).isNull() ? null : expectedNative.path(3).get(0).bigIntegerValue(), selection.selectedCommanders().attackerCharacterId());
                assertEquals(expectedNative.path(3).get(1).isNull() ? null : expectedNative.path(3).get(1).bigIntegerValue(), selection.selectedCommanders().defenderCharacterId());
            }
            FixedContactForecast.Request forecastRequest = new FixedContactForecast.Request(BigInteger.valueOf(request.targetProvinceId()), request.attackerEntryProvinceId() == null ? null : BigInteger.valueOf(request.attackerEntryProvinceId()),
                    request.attackerArmyIds().stream().map(BigInteger::valueOf).toList(), request.defenderArmyIds().stream().map(BigInteger::valueOf).toList(), capture, 16, 4);
            var forecast = FixedContactForecast.forecast(normalized, forecastRequest);
            assertTrue(CombatPhaseInputsCodec.sameJson(original.get("forecast_consumer"), forecast.toJson()), "whole forecast consumer parity: " + original.path("name").asText());
            assertTrue(CombatPhaseInputsCodec.sameJson(original.get("contact_admission_consumer"), FixedContactForecast.contactAdmission(forecast).toJson()), "contact admission consumer parity: " + original.path("name").asText());
        }
    }
    @Test void unchangedProducerFullNormalizedValuesAndRejectionsMatch() throws Exception {
        for (JsonNode original : originals) {
            CombatRequest request = request(original.get("payload")); CombatEncounterScope scope = CombatEncounterScope.decode(original.get("scope"), request);
            if (!original.path("accepted").booleanValue()) {
                assertThrows(IllegalArgumentException.class, () -> CODEC.normalize(original.get("payload"), request, scope), original.path("name").asText()); continue;
            }
            CombatPhaseInputs normalized = CODEC.normalize(original.get("payload"), request, scope);
            assertTrue(CombatPhaseInputsCodec.sameJson(original.get("normalized"), normalized.toJson()), original.path("name").asText());
            JsonNode reloaded = JSON.readTree(JSON.writeValueAsBytes(normalized.toJson()));
            assertTrue(CombatPhaseInputsCodec.sameJson(normalized.toJson(), CODEC.normalize(reloaded, request, scope).toJson()), "JSON/cache enriched revalidation drifted: " + original.path("name").asText());
            assertFalse(normalized.completeness().monteCarloReady()); assertFalse(normalized.completeness().plannerUsable()); assertFalse(normalized.completeness().activeAttackAllowed());
            ObjectNode detached = normalized.toJson(); detached.put("schema_version", 99); assertEquals(3, normalized.toJson().path("schema_version").intValue());
        }
    }
    @Test void integerTypesMissingNullAndFullFixedPartitionsRemainStrict() {
        JsonNode full = originals.get(0); CombatRequest request = request(full.get("payload")); CombatEncounterScope scope = CombatEncounterScope.decode(full.get("scope"), request);
        ObjectNode malformed = full.get("payload").deepCopy(); malformed.put("schema_version", 3.0);
        assertThrows(IllegalArgumentException.class, () -> CODEC.normalize(malformed, request, scope));
        ObjectNode missing = full.get("payload").deepCopy(); ((ObjectNode) missing.get("phase_event_inputs")).remove("raw");
        assertThrows(IllegalArgumentException.class, () -> CODEC.normalize(missing, request, scope));
        ObjectNode wrongCount = full.get("payload").deepCopy(); ((ObjectNode) wrongCount.path("phase_event_inputs").get("required_state_refs")).put("count", 132.0);
        assertThrows(IllegalArgumentException.class, () -> CODEC.normalize(wrongCount, request, scope));
        ObjectNode partition = CODEC.stateRefPartition(); assertEquals(81, partition.path("native_leaf_paths").size()); assertEquals(51, partition.path("offline_exact_paths").size());
        assertEquals(CombatPhaseSchema.NATIVE_SHA, PhaseRefPartition.digest(new java.util.HashSet<>(CombatWire.strings(partition.get("native_leaf_paths"), "native paths"))));
    }
    @Test void requestLiteralAndPublicZeroAreSharedWithV2() {
        CombatRequest request = new CombatRequest(100, null, List.of(0), List.of(2), 0); String step = CombatPhaseInputsCodec.toStep(request);
        assertEquals("query-combat-simulation-inputs-v3-100-ctor0-a-1-0-d-1-2", step); assertEquals(request, CombatPhaseInputsCodec.parseStep(step).orElseThrow());
        for (String bad : List.of(step.replace("a-1-0", "a-1-00"), step + "-3", step.replace("100-ctor0", "0100-ctor0"))) assertTrue(CombatPhaseInputsCodec.parseStep(bad).isEmpty());
        PhaseCandidateSourceProof.Source source = new PhaseCandidateSourceProof.Source(PhaseCandidateSourceProof.Role.KNIGHT, 0, 8, 9);
        String digest = PhaseCandidateSourceProof.digest(1, List.of(source)); PhaseCandidateSourceProof proof = new PhaseCandidateSourceProof(1, List.of(source), digest);
        assertEquals(proof, PhaseCandidateSourceProof.normalize(proof.toJson(), 1));
        assertThrows(IllegalArgumentException.class, () -> PhaseCandidateSourceProof.normalize(proof.toJson(), 0));
    }
    private static CombatRequest request(JsonNode payload) {
        JsonNode base = payload.get("base_inputs"), scenario = base.get("scenario"); JsonNode entry = scenario.get("attacker_entry_province_id");
        return CombatRequest.decode(base.get("target_province_id"), entry, scenario.get("attacker_army_ids"), scenario.get("defender_army_ids"), entry.isNull() ? JSON.getNodeFactory().numberNode(0) : JSON.getNodeFactory().nullNode());
    }
    private static String requiredProperty(String key) {
        String value = System.getProperty(key); if (value == null || value.isBlank()) throw new IllegalStateException(key + " is required for actual original producer parity; this check is not skipped"); return value;
    }
    private static void verifyPins(Path root) throws Exception {
        List<String> pins = List.of(
            "ck3_autonomous_player/src/xar_autoplayer/bridge/combat_phase_contract.py 657a3bccd9b8ed8426ceffa4ba36ce69aff20e670b3f786e2ff4885e38888828",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/combat_contract.py f2dde2b35d47037b60cf3079d639aed8af106f8ab08e463137aa598a39726468",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/candidate_source_proof.py f9651e2c7e7a73abc27fee0eb66bcbab06d3fc52ab300e81d186032fe58ff7ba",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/phase_event_evaluator.py 5c029f5887b538faa5f02c8ab1a422fcb7751c8d26ff14abf785616713e81d92",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/phase_event_manifest.py 124d5ba996c4c654b1931af34cb9ed63bb064dfc31da19900ecc944d7d853ddd",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/general_battle_forecast.py ff63be2dd75c0b1c8701479d2ee58ee152e8f835bb07e032ac92f3fdc0b430f3",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/combat_input.py 8b78e136f302432bf7fbeb05a631563ae6438b5904687bdfde046d634e7dbfe3",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/combat_core.py 15a9efce451e1830def6a7d93c87d0d00b7bb4e852fd75895780d289108a11b6",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/research_envelope.py fad22164c2dd8745aad220cad2409677366d2f52b4a8614a5c1bfa952414584f",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/battle_v2_constructor_advantage.py 2e6eb0992b5bc529e5c3ae47b74b9391164e582f1af69a033b8f54f21846493a",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_stock_combat_phase_events.json 749de2cb0ba7c4b072046db56bd5707a2ee4f7ebb6d7847f6851a88d74fdff8f",
            "ck3_autonomous_player/tests/unit/test_combat_phase_inputs_v3_production_contract.py 8c925106ea6391a3ef002b8f9ee89f584f729ef4d7ba46cb2fa020a3ea118fc6",
            "ck3_autonomous_player/tests/unit/test_combat_phase_inputs_v3_contract.py cb44040df2dc1f9d0de5284b3e181e01bceef17d1d7d32fc782570af9e7b6b25",
            "ck3_autonomous_player/tests/fixtures/combat_phase_events/v3_test_only_contract_recipe.json e5be4f2c8d5d8fb79dbb9ecec092d5e27fb25d6f7e9ba6f9fe2b3fca56dd78ee",
            "ck3_autonomous_player/tests/fixtures/combat_phase_events/v3_production_contract_recipe.json 2c7adcc9b9632bbac7804c0d289dae7a4b59e17c112b01c1781443c521d90a36",
            "ck3_autonomous_player/tests/fixtures/combat/live_rev4_vs_combined.json 90f05661a8b983a209980dacbdf6e286bab3765136989b322fe08c3111eb247f");
        for (String pin : pins) { String[] fields = pin.split(" "); Path file = root.resolve(fields[0]); requireFile(file);
            assertEquals(fields[1], HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))), "original producer/source pin drifted: " + fields[0]); }
    }
    private static void requireFile(Path path) throws IOException { if (!Files.isRegularFile(path)) throw new IOException("required parity input missing: " + path); }
}
