package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Retained real Python public producers -> sole native domain codecs -> actual static Service encoder. Synthetic guards confer no qualification. */
final class ArmyForecastPublicResultCodecTest {
    @Test void threeOriginalPublicProducersFeedTheirActualJavaServiceConsumersAndSerde() throws Exception {
        ObjectNode vectors = vectors();
        for (JsonNode row : vectors.path("cases")) {
            var method = PublicMethod.valueOf(row.path("method").textValue());
            ObjectNode snapshot = (ObjectNode) row.path("snapshot"), nativeResult = (ObjectNode) row.path("native");
            var context = context(snapshot);
            ArmyCalls.Call call = ArmyCallCodec.decode(method, new RawJson(ArmyJson.bytes(row.path("arguments"))));
            var receipt = receipt(context, call, nativeResult);
            ForecastReadObservation observed = observed(call, context, snapshot, nativeResult, receipt);
            var complete = new Complete(context.before(), context.source(), context.sessionId(), BigInteger.ONE, immutable(snapshot),
                    context.source().sourceRef(), Instant.parse("2026-10-24T00:00:01Z"), "b".repeat(64));
            var current = new ArmyRetreatFrames.Current(complete, context.deadline());
            var known = new PlanningReadResult.Known<>(observed, receipt, context.source().sourceRef());
            var reply = new ArmyForecastService.Reply(current, current, known);
            assertEquals(ArmyForecastPublicResultCodec.Profile.ORIGINAL_PUBLIC_RESULT, ArmyForecastPublicResultCodec.profile(method));
            RawJson encoded = ArmyForecastService.encode(method, reply);
            Obj restored = ArmyPublicWire.decodeExactSourceBound(encoded, context);
            assertEquals(immutable((ObjectNode) row.path("expected")), restored, method.pythonName());
            assertEquals(encoded, ArmyPublicWire.encodeExactSourceBound(restored, context));
            assertEquals(encoded, ArmyForecastPublicResultCodec.encode(method, reply));
            ObjectNode publicValue = ArmyJson.parse(encoded.bytes());
            assertFalse(publicValue.has("queried_episode_run_id")); assertFalse(publicValue.has("queried_connection_generation"));
            PublicMethod wrong = method == PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS
                    ? PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1 : PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS;
            assertThrows(IllegalArgumentException.class, () -> ArmyForecastService.encode(wrong, reply));
            ObjectNode changed = (ObjectNode) OpportunityJson.toNode(observed.normalizedResult());
            changed.put("queried_revision", 999);
            ForecastReadObservation forged = switch (observed) {
                case ForecastReadObservation.WarEntry value -> new ForecastReadObservation.WarEntry(value.assessments(), value.targetScopes(), immutable(changed));
                case ForecastReadObservation.CurrentKnight value -> new ForecastReadObservation.CurrentKnight(value.knight(), immutable(changed));
                case ForecastReadObservation.PhaseTrace value -> new ForecastReadObservation.PhaseTrace(value.trace(), immutable(changed));
                default -> throw new AssertionError("not one of the three original public result fixtures");
            };
            var invalid = new ArmyForecastService.Reply(current, current,
                    new PlanningReadResult.Known<>(forged, receipt, context.source().sourceRef()));
            assertThrows(IllegalArgumentException.class, () -> ArmyForecastService.encode(method, invalid));
            if (method == PublicMethod.QUERY_WAR_ENTRY_ASSESSMENTS) {
                assertTrue(publicValue.path("war_entry_assessments").path("assessments").get(0).path("actor_power_base_raw").isTextual());
                assertTrue(publicValue.has("target_character_ids")); assertFalse(publicValue.has("target_province_ids"));
            }
            if (method == PublicMethod.QUERY_COMBAT_PHASE_EVENT_TRACE_V1) {
                assertFalse(publicValue.path("production_trace_ready").booleanValue());
                assertFalse(publicValue.path("qualified_win_probability_available").booleanValue());
            }
        }
    }

    @Test void completeCurrentCombatProfilesRequireTheService10AndKernel05SourceGroup() {
        assertEquals(ArmyForecastPublicResultCodec.Profile.ORIGINAL_PUBLIC_RESULT,
                ArmyForecastPublicResultCodec.profile(PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS));
        assertEquals(ArmyForecastPublicResultCodec.Profile.ORIGINAL_PUBLIC_RESULT,
                ArmyForecastPublicResultCodec.profile(PublicMethod.QUERY_COMBAT_SIMULATION_INPUTS_V3));
        assertThrows(IllegalArgumentException.class, () -> ArmyForecastPublicResultCodec.profile(PublicMethod.QUERY_DECLARABLE_WARS));
    }

    @Test void actualOccupationDriverAndPublicServiceFeedTheInstalledJavaServiceEncoder() throws Exception {
        verifySources();
        ObjectNode vector = original("""
                import copy,json,threading
                from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver as Driver
                from xar_autoplayer.bridge.service import GameplayBridgeService as Service
                from xar_autoplayer.bridge.version_identity import CK3_12004
                from xar_autoplayer.bridge.war_occupation_targets_contract import QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY
                snapshot=dict(snapshot_id='native:3',revision=2,native_revision=3,date_raw=77,paused=True,map_ready=True,episode_run_id='occupation-public',played_character=dict(character_id=101,alive=True),diagnostics=dict(connection_generation=1,bridge_pid=42),active_wars=[dict(war_id=77,player_side='attacker',primary_opponent_character_id=202)])
                domain=dict(schema='xar.ck3.war-occupation-targets.v1',schema_version=1,available=True,collection_complete=True,status='available',snapshot_revision=3,date_raw=77,war_id=77,actor_character_id=101,primary_attacker_character_id=101,primary_defender_character_id=202,player_side='attacker',game_version=CK3_12004.game_version,executable_sha256=CK3_12004.executable_sha256,unavailable_reason=None,side_counts=[dict(territory_side=side,eligible=0,occupied=0,native_candidate_count=0,collection_complete=True) for side in ('attacker','defender')],rows=[])
                native=dict(step='query-war-occupation-targets-v1-77',accepted=True,status='available',query_sequence=2**64-1,war_occupation_targets_v1=domain)
                class Source:
                    _driver_state_lock=threading.Lock()
                    def take_snapshot_without_native_command_history(self):return copy.deepcopy(snapshot)
                    def take_internal_semantic_snapshot(self):return copy.deepcopy(snapshot)
                    def _execute_primitive_step(self,*a,**kw):return {**copy.deepcopy(native),'backend_id':'native-headless'}
                published=Driver._execute_war_occupation_targets_v1_query(Source(),native['step'],expected_revision=2)
                class Public:
                    _execute_typed_war_step=Service._execute_typed_war_step
                    def capabilities(self):return dict(action_steps=[native['step']],bridge_capabilities=[QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY])
                    def snapshot(self,**kw):return copy.deepcopy(snapshot)
                    def execute_step(self,*a,**kw):return copy.deepcopy(published)
                expected=Service.query_war_occupation_targets_v1(Public(),77,expected_revision=2)
                print(json.dumps(dict(snapshot=snapshot,native=native,expected=expected),allow_nan=False))
                """);
        verifySources(); ObjectNode snapshot = (ObjectNode)vector.get("snapshot"); Context context = context(snapshot);
        var call = new ArmyCalls.War(PublicMethod.QUERY_WAR_OCCUPATION_TARGETS_V1,
                new ArmyCalls.Revision(new Present<>(context.before().frame().revision())), BigInteger.valueOf(77));
        var receipt = receipt(context, call, (ObjectNode)vector.get("native"));
        var scope = new ArmyWarReadCodec.Scope(call, context, immutable(snapshot), Optional.empty());
        var typed = ArmyWarReadCodec.decode(scope, receipt);
        var complete = new Complete(context.before(), context.source(), context.sessionId(), BigInteger.ONE, immutable(snapshot),
                context.source().sourceRef(), Instant.parse("2026-10-24T00:00:01Z"), "b".repeat(64));
        var current = new ArmyRetreatFrames.Current(complete, context.deadline());
        var reply = new ArmyWarReadService.Reply(new ArmyWarReads.Selection(call, current, Optional.empty()),
                new PlanningReadResult.Known<>(typed, receipt, context.source().sourceRef()));
        RawJson encoded = ArmyWarReadService.encode(reply);
        assertEquals(immutable((ObjectNode)vector.get("expected")), ArmyPublicWire.decodeExactSourceBound(encoded, context));
        assertEquals(encoded, ArmyWarReadService.encode(reply));
        ObjectNode publicValue = ArmyJson.parse(encoded.bytes());
        assertEquals("1", publicValue.path("queried_connection_generation").textValue());
        assertEquals("occupation-public", publicValue.path("queried_episode_run_id").textValue());
    }

    private static ForecastReadObservation observed(ArmyCalls.Call call, Context context, ObjectNode snapshot,
            ObjectNode raw, PlanningReadReceipt receipt) {
        ObjectNode enriched = raw.deepCopy();
        ForecastReadObservation.Kind kind;
        Obj value; OpportunityJson.Arr scopes = null;
        if (call instanceof ArmyCalls.WarEntry entry) {
            var targets = entry.targets().stream().map(PositiveId::value).toList();
            var domain = WarEntryAssessmentCodec.normalize(raw.get("war_entry_assessments"),
                    new WarEntryAssessmentCodec.Expected(targets, context.playerId(), context.nativeRevision(), context.dateRaw()));
            var targetScopes = WarEntryAssessmentCodec.targetScopes(snapshot, targets);
            enriched.set("war_entry_assessments", domain.toNativeJson()); enriched.set("target_scopes", targetScopes.toNativeJson());
            value = immutable(domain.toNativeJson()); scopes = (OpportunityJson.Arr) OpportunityJson.parse(ArmyJson.bytes(targetScopes.toNativeJson()));
            kind = ForecastReadObservation.Kind.WAR_ENTRY;
        } else if (call instanceof ArmyCalls.Knight knight) {
            BattleResponseCodec.knight(ArmyJson.bytes(raw), context, knight.selection());
            value = immutable((ObjectNode) raw.get("current_battle_knight")); kind = ForecastReadObservation.Kind.CURRENT_KNIGHT;
        } else {
            var trace = CombatPhaseEventTraceCodec.normalize(raw.get("combat_phase_event_trace"), ((ArmyCalls.CombatId) call).combat().value());
            enriched.set("combat_phase_event_trace", trace.toNativeJson()); value = immutable(trace.toNativeJson()); kind = ForecastReadObservation.Kind.PHASE_TRACE;
        }
        enriched.put("queried_snapshot_id", context.before().frame().snapshotId()).put("queried_revision", context.before().frame().revision())
                .put("queried_native_revision", context.nativeRevision()).put("queried_episode_run_id", context.before().frame().episodeRunId())
                .put("queried_connection_generation", receipt.before().binding().connectionGeneration());
        return switch (kind) {
            case WAR_ENTRY -> new ForecastReadObservation.WarEntry(value, scopes, immutable(enriched));
            case CURRENT_KNIGHT -> new ForecastReadObservation.CurrentKnight(value, immutable(enriched));
            case PHASE_TRACE -> new ForecastReadObservation.PhaseTrace(value, immutable(enriched));
            default -> throw new AssertionError("fixture domain kind changed");
        };
    }
    private static PlanningReadReceipt receipt(Context context, ArmyCalls.Call call, ObjectNode result) throws java.io.IOException {
        var operation = new OperationKey(result.path("step").textValue());
        var request = new PlanningReadRequest(context.before(), context.source(), context.sessionId(), operation,
                DriverJson.object(ArmyCallCodec.encode(call).bytes(), DriverJson.MAX_NATIVE_BYTES), context.deadline());
        var evidence = new GuardEvidence(context.before(), context.source(), context.sessionId(), BigInteger.ONE, operation,
                context.source().sourceRef(), context.source().sourceRef(), "synthetic-public-forecast-only", Instant.parse("2026-10-24T00:00:00Z"), context.deadline());
        var guard = new PlanningReadGuard(evidence, true, true, true, "b".repeat(64));
        ObjectNode top = ArmyJson.empty().put("type", "command_result").put("protocol_version", 1).put("request_id", "forecast-original").put("ok", true); top.set("result", result);
        RawJson packet = new RawJson(ArmyJson.bytes(top));
        var ack = new NativeActionPort.AckReceived("forecast-original", true, Optional.of(new RawJson(ArmyJson.bytes(result))), packet, NativeWire.packet(packet.bytes()));
        return new PlanningReadReceipt(request, "synthetic-forecast-no-authority", "forecast-original", guard, guard, ack);
    }
    private static Context context(ObjectNode snapshot) {
        String episode = snapshot.path("episode_run_id").textValue();
        var sourceRef = new ExactRef("synthetic-original-forecast-fixture", 1, "a".repeat(64));
        var source = new G2Source("synthetic-public-forecast-test", "2026-10-24T00:00:00Z", "retained-original-test-build", sourceRef);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(snapshot.path("played_character").path("character_id").bigIntegerValue(),
                snapshot.path("native_revision").bigIntegerValue(), snapshot.path("date_raw").bigIntegerValue()),
                snapshot.path("snapshot_id").textValue(), snapshot.path("revision").bigIntegerValue(), episode);
        return new Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1),
                source, "synthetic-forecast-public-session", Instant.parse("2026-10-24T00:01:00Z"));
    }
    private static Obj immutable(ObjectNode n) { return DriverJson.object(ArmyJson.bytes(n), DriverJson.MAX_NATIVE_BYTES); }
    private static ObjectNode vectors() throws Exception {
        verifySources();
        ObjectNode result = original("""
                import copy,json,runpy,sys
                sys.path.insert(0,str(root/'ck3_autonomous_player'/'tests'/'unit'))
                from xar_autoplayer.bridge.service import GameplayBridgeService as Service
                from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver as Driver
                from xar_autoplayer.bridge.combat_phase_event_trace_contract import QUERY_COMBAT_PHASE_EVENT_TRACE_V1_CAPABILITY
                w=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_war_entry_assessments_bridge.py'))
                d,e=w['_native_driver']();w['_answer'](e)
                try:
                    before=d.take_snapshot()
                    expected=Service(d).query_war_entry_assessments([808],expected_revision=before['revision'])
                    before['declarable_wars']=[w['_declaration'](808),w['_declaration'](42)]
                    cases=[dict(method='QUERY_WAR_ENTRY_ASSESSMENTS',snapshot=before,native=w['_result'](),arguments=dict(target_character_ids=[808],expected_revision=before['revision']),expected=expected)]
                finally:d.close()
                k=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_current_battle_knight_v1_port.py'))
                class Knight(k['FakeNative']):
                    def _execute_primitive_step(self,*a,**kw):return {**super()._execute_primitive_step(*a,**kw),'backend_id':'native-headless'}
                fake=Knight();native=k['raw_result']();snapshot=k['frame']()
                expected=Service.query_current_battle_knight_v1(type('Public',(),{'driver':fake})(),**k['REQUEST'])
                snapshot['map_ready']=True;snapshot['played_character']['alive']=True
                cases.append(dict(method='QUERY_CURRENT_BATTLE_KNIGHT_V1',snapshot=snapshot,native=native,arguments=k['REQUEST'],expected=expected))
                p=runpy.run_path(str(root/'ck3_autonomous_player/tests/unit/test_combat_phase_event_trace_query.py'))
                trace=p['available_trace']();combat=trace['combat_id']
                snapshot=dict(snapshot_id='native:3',revision=3,native_revision=3,date_raw=trace['date_raw'],paused=True,map_ready=True,episode_run_id='phase-public-fixture',played_character=dict(character_id=29829,alive=True),diagnostics=dict(connection_generation=1),active_wars=[],player_armies=[])
                native=dict(step='query-combat-phase-event-trace-v1-'+str(combat),accepted=True,status='evaluator_probe_available',query_sequence=7,combat_phase_event_trace=trace,backend_id='native-headless')
                class Phase:
                    def snapshot(self):return copy.deepcopy(snapshot)
                    def take_snapshot(self):return copy.deepcopy(snapshot)
                    def capabilities(self):return dict(bridge_capabilities=[QUERY_COMBAT_PHASE_EVENT_TRACE_V1_CAPABILITY])
                    def _execute_primitive_step(self,*a,**kw):return copy.deepcopy(native)
                    def execute_step(self,step,**kw):return Driver._execute_combat_phase_event_trace_v1_query(self,step,expected_revision=kw.get('expected_revision'))
                expected=Service.query_combat_phase_event_trace_v1(Phase(),combat,expected_revision=3)
                cases.append(dict(method='QUERY_COMBAT_PHASE_EVENT_TRACE_V1',snapshot=snapshot,native=native,arguments=dict(combat_id=combat,expected_revision=3),expected=expected))
                print(json.dumps(dict(cases=cases),allow_nan=False))
                """);
        verifySources(); return result;
    }
    private static ObjectNode original(String code) throws Exception {
        String repository = System.getProperty("xar.repository.root"), python = System.getProperty("xar.python");
        if (repository == null || python == null) throw new IllegalStateException("actual source root and original Python oracle executable required");
        Path root = Path.of(repository).toRealPath(), executable = Path.of(python).toRealPath();
        assertTrue(Files.isDirectory(root)); assertTrue(Files.isRegularFile(executable));
        String prefix = "import sys\nfrom pathlib import Path\nroot=Path(sys.argv[1])\nsys.path.insert(0,str(root/'ck3_autonomous_player'/'src'))\n";
        var builder = new ProcessBuilder(executable.toString(), "-B", "-I", "-X", "utf8", "-c", prefix + code, root.toString()).directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); var process = builder.start();
        try (var readers = java.util.concurrent.Executors.newVirtualThreadPerTaskExecutor()) {
            var out = readers.submit(() -> process.getInputStream().readNBytes(1048577));
            var err = readers.submit(() -> process.getErrorStream().readNBytes(16385));
            try {
                process.getOutputStream().close();
                assertTrue(process.waitFor(45, java.util.concurrent.TimeUnit.SECONDS), "original public forecast producer timed out");
                byte[] output = out.get(5, java.util.concurrent.TimeUnit.SECONDS), error = err.get(5, java.util.concurrent.TimeUnit.SECONDS);
                assertTrue(output.length <= 1048576 && error.length <= 16384, "bounded original producer output required");
                assertEquals(0, process.exitValue(), new String(error, java.nio.charset.StandardCharsets.UTF_8));
                return ArmyJson.parse(output);
            } finally { if (process.isAlive()) { process.destroyForcibly(); process.waitFor(5, java.util.concurrent.TimeUnit.SECONDS); } }
        }
    }
    private static void verifySources() throws Exception {
        String configured = System.getProperty("xar.repository.root");
        if (configured == null || configured.isBlank()) throw new IllegalStateException("actual original source root required");
        Path root = Path.of(configured).toRealPath();
        for (String[] pin : new String[][] {
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/service.py","a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"},
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},
                {"ck3_autonomous_player/tests/unit/test_war_entry_assessments_bridge.py","f7b743b252d85607f0009195c5002b2caf0ccfd15c451d15d88caea0769cd1de"},
                {"ck3_autonomous_player/tests/unit/test_current_battle_knight_v1_port.py","97a751d3e11a68866e9b410bbcbabafc9858665a049153d72e9fef0384250875"},
                {"ck3_autonomous_player/tests/unit/test_combat_phase_event_trace_query.py","983b49395d8559b355bc28603d74850e9e2ce06993b3b0e5d0e4f24326f012b5"}}) {
            Path file = root.resolve(pin[0]).toRealPath(); assertTrue(file.startsWith(root));
            assertEquals(pin[1], HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))), "original forecast source changed");
        }
    }
}

