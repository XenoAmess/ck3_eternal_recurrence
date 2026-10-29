package org.xar.ck3.control.wave2.military.forecast;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec;
import org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime;

/** Actual original native-driver producer -> Java full normalizer/cache -> forecast/admission. */
final class CombatObservationCacheTest {
    private static final String PROGRAM = """
            import copy,hashlib,json,runpy
            from xar_autoplayer.simulation.general_battle_forecast import forecast_fixed_contact,contact_admission
            pins={
              'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py':'eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603',
              'ck3_autonomous_player/src/xar_autoplayer/bridge/combat_contract.py':'f2dde2b35d47037b60cf3079d639aed8af106f8ab08e463137aa598a39726468',
              'ck3_autonomous_player/src/xar_autoplayer/bridge/combat_phase_contract.py':'657a3bccd9b8ed8426ceffa4ba36ce69aff20e670b3f786e2ff4885e38888828',
              'ck3_autonomous_player/tests/unit/test_combat_simulation_inputs_bridge.py':'02fbab4b90a5bcefca34669c2cff79ec89005d9640636a84779b71234480d5a8',
              'ck3_autonomous_player/tests/unit/test_combat_phase_inputs_v3_bridge.py':'2ab86c8ca0333156e3c9a55c4b443be17bf9b3c49fe1f3fbb924afaff2087999',
              'ck3_autonomous_player/tests/unit/test_combat_phase_inputs_v3_production_contract.py':'8c925106ea6391a3ef002b8f9ee89f584f729ef4d7ba46cb2fa020a3ea118fc6'}
            def verify():
                for name,pin in pins.items():
                    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==pin,name
            verify()
            fields=('snapshot_id','revision','native_revision','date_raw','paused','episode_run_id','diagnostics','player_armies','active_wars')
            def semantic(snapshot):return {key:copy.deepcopy(snapshot[key]) for key in fields}
            cases=[]
            for version in (2,3):
                filename='test_combat_simulation_inputs_bridge.py' if version==2 else 'test_combat_phase_inputs_v3_bridge.py'
                module=runpy.run_path(str(root/'ck3_autonomous_player'/'tests'/'unit'/filename))
                for available in (True,False):
                    driver,endpoint=module['_native_driver']()
                    if version==2:
                        factory=module['_fixture_result'] if available else module['_partial_fixture_result']
                    else:
                        factory=lambda available=available:module['_fixture_result'](available=available)
                    module['_answer_with'](endpoint,factory)
                    starting=driver.take_snapshot()
                    result=driver.execute_step(module['STEP'],expected_revision=starting['revision'])
                    ending=driver.take_snapshot()
                    cache=driver._combat_simulation_inputs_cache_for_snapshot if version==2 else driver._combat_simulation_inputs_v3_cache_for_snapshot
                    projected=cache(ending,episode_run_id=ending['episode_run_id'])
                    assert projected is not None
                    payload=projected['combat_simulation_inputs']
                    base=payload if version==2 else payload['base_inputs']
                    scenario=base['scenario']
                    capture={key:starting[key] for key in ('snapshot_id','revision','native_revision','date_raw')}
                    forecast=forecast_fixed_contact(payload,target_province_id=base['target_province_id'],attacker_entry_province_id=scenario['attacker_entry_province_id'],attacker_army_ids=tuple(scenario['attacker_army_ids']),defender_army_ids=tuple(scenario['defender_army_ids']),capture=capture,sample_count=16,horizon_days=4)
                    raw={key:copy.deepcopy(result[key]) for key in ('step','accepted','status','query_sequence','combat_simulation_inputs','backend_id')}
                    cases.append({'version':version,'available':available,'starting':semantic(starting),'ending':semantic(ending),'receipt':raw,'projected':projected,'forecast':forecast,'admission':contact_admission(forecast)})
            verify()
            print(json.dumps({'producer':'unchanged-actual-native-driver-and-original-forecast','source_pins':pins,'cases':cases},ensure_ascii=False,separators=(',',':')))
            """;

    private static CombatObservationCache newCache() {
        CombatSimulationInputsCodec base = new CombatSimulationInputsCodec();
        return new CombatObservationCache(base, new CombatPhaseInputsCodec(base, new StockPhaseEventRuntime()));
    }
    private static CombatObservationCache.Version version(JsonNode row) {
        return row.path("version").intValue() == 2 ? CombatObservationCache.Version.V2 : CombatObservationCache.Version.V3;
    }
    private static CombatRequest request(JsonNode row) {
        String step = row.path("receipt").path("step").textValue();
        return version(row) == CombatObservationCache.Version.V2 ? CombatRequest.parseStep(step).orElseThrow() : CombatPhaseInputsCodec.parseStep(step).orElseThrow();
    }
    private static String episode(JsonNode snapshot) { return snapshot.path("episode_run_id").isNull() ? null : snapshot.path("episode_run_id").textValue(); }
    private static CombatObservationCache.Observation receive(CombatObservationCache cache, JsonNode row) {
        return cache.receive(version(row), row.get("receipt"), row.get("starting"), row.get("ending"), request(row), row.path("starting").path("revision").bigIntegerValue());
    }
    private static void equalJson(JsonNode expected, JsonNode actual) { assertArrayEquals(CombatJson.canonical(expected), CombatJson.canonical(actual)); }
    private static JsonNode corpus() throws Exception { return ForecastOriginalOracle.call(PROGRAM, CombatJson.object(), 8 * 1024 * 1024); }

    @Test void pureKnownReadReplayNeverPublishesOrRollsBackEitherCurrentVersionSlot() throws Exception {
        for (JsonNode row : corpus().path("cases")) {
            CombatObservationCache cache = newCache(); JsonNode ending = row.get("ending");
            CombatObservationCache.Observation replayed = cache.replay(version(row), row.get("receipt"), row.get("starting"), ending, request(row), row.path("starting").path("revision").bigIntegerValue());
            equalJson(row.get("projected"), replayed.toInternalJson());
            assertTrue(cache.projectV2(ending, episode(ending)).isEmpty()); assertTrue(cache.projectV3(ending, episode(ending)).isEmpty());
            // A controlled newer read sequence isolates publication from pure replay; it is not a native observation claim.
            ObjectNode newer = row.get("receipt").deepCopy(); java.math.BigInteger sequence = newer.get("query_sequence").bigIntegerValue().add(java.math.BigInteger.ONE); newer.put("query_sequence", sequence);
            cache.receive(version(row), newer, row.get("starting"), ending, request(row), row.path("starting").path("revision").bigIntegerValue());
            cache.replay(version(row), row.get("receipt"), row.get("starting"), ending, request(row), row.path("starting").path("revision").bigIntegerValue());
            CombatObservationCache.Observation current = version(row) == CombatObservationCache.Version.V2
                    ? cache.projectV2(ending, episode(ending)).orElseThrow() : cache.projectV3(ending, episode(ending)).orElseThrow();
            assertEquals(sequence, current.querySequence());
            ObjectNode crossed = ending.deepCopy(); crossed.put("revision", ending.get("revision").bigIntegerValue().add(java.math.BigInteger.ONE));
            assertThrows(IllegalArgumentException.class, () -> cache.replay(version(row), row.get("receipt"), row.get("starting"), crossed, request(row), null));
            current = version(row) == CombatObservationCache.Version.V2
                    ? cache.projectV2(ending, episode(ending)).orElseThrow() : cache.projectV3(ending, episode(ending)).orElseThrow();
            assertEquals(sequence, current.querySequence());
        }
    }

    @Test void actualOriginalQueryProducerFeedsBothRealCacheNormalizersAndForecastConsumers() throws Exception {
        JsonNode corpus = corpus();
        assertEquals("unchanged-actual-native-driver-and-original-forecast", corpus.path("producer").textValue());
        assertEquals(4, corpus.path("cases").size());
        for (JsonNode row : corpus.path("cases")) {
            CombatObservationCache cache = newCache();
            CombatObservationCache.Observation observation = receive(cache, row);
            equalJson(row.get("projected"), observation.toInternalJson());
            CombatObservationCache.Observation projected = version(row) == CombatObservationCache.Version.V2
                    ? cache.projectV2(row.get("ending"), episode(row.get("ending"))).orElseThrow()
                    : cache.projectV3(row.get("ending"), episode(row.get("ending"))).orElseThrow();
            equalJson(row.get("projected"), projected.toInternalJson());
            FixedContactForecast.Forecast forecast = projected.forecast(16, 4);
            equalJson(row.get("forecast"), forecast.toJson());
            equalJson(row.get("admission"), FixedContactForecast.contactAdmission(forecast).toJson());
            assertEquals(observation.frame(), CombatObservationCache.Frame.decode(row.get("ending")));
            ObjectNode detached = projected.normalizedJson(); detached.removeAll();
            equalJson(row.get("projected").get("combat_simulation_inputs"), projected.normalizedJson());
            JsonNode reloaded = CombatJson.parse(CombatJson.canonical(row.get("receipt")));
            CombatObservationCache roundtrip = newCache();
            equalJson(observation.toInternalJson(), roundtrip.receive(version(row), reloaded, row.get("starting"), row.get("ending"), request(row), null).toInternalJson());
        }
    }

    @Test void staleFrameEpisodeReconnectAndPublishedScopeInvalidateOnlyTheirOwnVersion() throws Exception {
        JsonNode corpus = corpus();
        for (JsonNode row : corpus.path("cases")) {
            for (String key : List.of("snapshot_id", "revision", "native_revision", "date_raw", "connection_generation", "episode_run_id", "scope")) {
                CombatObservationCache cache = newCache(); receive(cache, row);
                ObjectNode changed = row.get("ending").deepCopy();
                switch (key) {
                    case "snapshot_id" -> changed.put(key, "other:frame");
                    case "episode_run_id" -> changed.put(key, "other-episode");
                    case "connection_generation" -> ((ObjectNode) changed.get("diagnostics")).put(key, changed.path("diagnostics").path(key).bigIntegerValue().add(BigInteger.ONE));
                    case "scope" -> ((ObjectNode) changed.path("active_wars").get(0)).put("war_id", 31);
                    default -> changed.put(key, changed.path(key).bigIntegerValue().add(BigInteger.ONE));
                }
                assertTrue(version(row) == CombatObservationCache.Version.V2
                        ? cache.projectV2(changed, episode(changed)).isEmpty() : cache.projectV3(changed, episode(changed)).isEmpty(), key);
                assertTrue(version(row) == CombatObservationCache.Version.V2
                        ? cache.projectV2(row.get("ending"), episode(row.get("ending"))).isEmpty()
                        : cache.projectV3(row.get("ending"), episode(row.get("ending"))).isEmpty(), "stale cache must be consumed");
            }
            CombatObservationCache cache = newCache(); receive(cache, row);
            ObjectNode running = row.get("ending").deepCopy(); running.put("paused", false);
            assertTrue(cache.projectV2(running, episode(running)).isEmpty()); assertTrue(cache.projectV3(running, episode(running)).isEmpty());
            assertTrue(version(row) == CombatObservationCache.Version.V2
                    ? cache.projectV2(row.get("ending"), episode(row.get("ending"))).isPresent()
                    : cache.projectV3(row.get("ending"), episode(row.get("ending"))).isPresent(), "unpaused projection must not consume paused cache");
            cache.clear(); assertTrue(cache.projectV2(row.get("ending"), episode(row.get("ending"))).isEmpty()); assertTrue(cache.projectV3(row.get("ending"), episode(row.get("ending"))).isEmpty());
        }
    }

    @Test void strictNativeReceiptAndEveryIntegerIdentityRejectMissingNullBooleanAndFloat() throws Exception {
        JsonNode row = corpus().path("cases").get(0);
        for (String raw : List.of("true", "1.0", "0", "-1", "18446744073709551616", "null", "\"41\"")) {
            ObjectNode receipt = row.get("receipt").deepCopy(); receipt.set("query_sequence", CombatJson.parse(raw.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> newCache().receive(version(row), receipt, row.get("starting"), row.get("ending"), request(row), null), raw);
        }
        for (String key : List.of("step", "accepted", "status", "query_sequence", "combat_simulation_inputs")) {
            ObjectNode missing = row.get("receipt").deepCopy(); missing.remove(key);
            assertThrows(IllegalArgumentException.class, () -> newCache().receive(version(row), missing, row.get("starting"), row.get("ending"), request(row), null), key);
        }
        ObjectNode extra = row.get("receipt").deepCopy(); extra.put("unexpected", true);
        assertThrows(IllegalArgumentException.class, () -> newCache().receive(version(row), extra, row.get("starting"), row.get("ending"), request(row), null));
        ObjectNode noBackend = row.get("receipt").deepCopy(); noBackend.remove("backend_id");
        assertNotNull(newCache().receive(version(row), noBackend, row.get("starting"), row.get("ending"), request(row), null));
        ObjectNode blankBackend = row.get("receipt").deepCopy(); blankBackend.put("backend_id", "");
        assertThrows(IllegalArgumentException.class, () -> newCache().receive(version(row), blankBackend, row.get("starting"), row.get("ending"), request(row), null));
        ObjectNode wrongStatus = row.get("receipt").deepCopy(); wrongStatus.put("status", "partial");
        assertThrows(IllegalArgumentException.class, () -> newCache().receive(version(row), wrongStatus, row.get("starting"), row.get("ending"), request(row), null));
        ObjectNode rejected = row.get("receipt").deepCopy(); rejected.put("accepted", false);
        assertThrows(IllegalArgumentException.class, () -> newCache().receive(version(row), rejected, row.get("starting"), row.get("ending"), request(row), null));
        BigInteger wrongRevision = row.path("starting").path("revision").bigIntegerValue().add(BigInteger.ONE);
        assertThrows(IllegalArgumentException.class, () -> newCache().receive(version(row), row.get("receipt"), row.get("starting"), row.get("ending"), request(row), wrongRevision));
        for (String key : List.of("revision", "native_revision", "date_raw", "connection_generation")) for (String raw : List.of("true", "5.0", "null")) {
            ObjectNode bad = row.get("starting").deepCopy();
            ObjectNode target = key.equals("connection_generation") ? (ObjectNode) bad.get("diagnostics") : bad;
            target.set(key, CombatJson.parse(raw.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> CombatObservationCache.Frame.decode(bad), key + ":" + raw);
            target.remove(key); assertThrows(IllegalArgumentException.class, () -> CombatObservationCache.Frame.decode(bad), key + ":missing");
        }
        ObjectNode nullEpisode = row.get("starting").deepCopy(); nullEpisode.putNull("episode_run_id");
        assertNull(CombatObservationCache.Frame.decode(nullEpisode).episodeRunId());
        nullEpisode.remove("episode_run_id"); assertThrows(IllegalArgumentException.class, () -> CombatObservationCache.Frame.decode(nullEpisode));
    }

    @Test void exactUint64SequenceAndSnapshotRoundtripNeverPassThroughDouble() throws Exception {
        JsonNode row = corpus().path("cases").get(0);
        BigInteger maximum = new BigInteger("18446744073709551615");
        ObjectNode receipt = row.get("receipt").deepCopy(); receipt.put("query_sequence", maximum);
        ObjectNode snapshot = row.get("starting").deepCopy(); snapshot.put("revision", maximum).put("native_revision", maximum);
        ((ObjectNode) snapshot.get("diagnostics")).put("connection_generation", maximum);
        CombatObservationCache cache = newCache();
        var observation = cache.receive(version(row), receipt, snapshot, snapshot, request(row), maximum);
        assertEquals(maximum, observation.querySequence()); assertEquals(maximum, observation.frame().revision());
        JsonNode serialized = CombatJson.parse(CombatJson.canonical(observation.toInternalJson()));
        assertEquals(maximum, serialized.get("query_sequence").bigIntegerValue());
        assertEquals(maximum, serialized.get("queried_native_revision").bigIntegerValue());
        assertEquals(maximum, cache.projectV2(snapshot, episode(snapshot)).orElseThrow().capture().revision());
    }

    @Test void staleV2CannotDiscardTheIndependentlyStoredV3Observation() throws Exception {
        JsonNode cases = corpus().path("cases");
        JsonNode v2 = cases.get(0), v3 = cases.get(2);
        CombatObservationCache cache = newCache(); receive(cache, v2); receive(cache, v3);
        ObjectNode stale = v2.get("ending").deepCopy(); stale.put("snapshot_id", "expired:v2");
        assertTrue(cache.projectV2(stale, episode(stale)).isEmpty());
        assertTrue(cache.projectV3(v3.get("ending"), episode(v3.get("ending"))).isPresent());
        cache.clear();
        assertTrue(cache.projectV2(v2.get("ending"), episode(v2.get("ending"))).isEmpty());
        assertTrue(cache.projectV3(v3.get("ending"), episode(v3.get("ending"))).isEmpty());
    }
}
