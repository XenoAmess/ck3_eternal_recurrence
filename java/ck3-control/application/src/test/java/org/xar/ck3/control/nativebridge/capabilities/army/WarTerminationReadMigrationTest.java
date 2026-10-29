package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Retained actual readonly producer methods -> sole Java receipt decoder, complete query projection and public serialization. Synthetic callbacks confer no Game/read authority. */
final class WarTerminationReadMigrationTest {
    @Test void originalOptionsAndUnsupportedTermsKeepOuterStatusWarBindingAndCompleteMetadata() throws Exception {
        verifySources(); ObjectNode captured = BattleOriginalOracle.call("""
                import ast,copy,hashlib,json,runpy,threading
                from pathlib import Path
                import xar_autoplayer.bridge.native_driver as original
                from xar_autoplayer.bridge.version_identity import CK3_12004
                root=Path(original.__file__).resolve().parents[3]
                make_options=runpy.run_path(str(root/'tests/unit/test_war_termination_contract.py'))['_termination_options']
                war=dict(war_id=77,player_side='attacker',player_is_primary_war_leader=True,primary_opponent_character_id=202,targeted_title_ids=[8,3],player_relative_war_score=41)
                other=dict(war_id=3,player_side='defender',player_is_primary_war_leader=None,primary_opponent_character_id=None,targeted_title_ids=[],player_relative_war_score=-7)
                snapshot=dict(snapshot_id='native:3',revision=2,native_revision=3,date_raw=77,paused=True,map_ready=True,episode_run_id='termination-fixture',episode_character_id=101,played_character=dict(character_id=101,alive=True),active_wars=[war,other],diagnostics=dict(connection_generation=1,bridge_pid=42,hello=dict(expected_ck3_version=CK3_12004.game_version,expected_ck3_sha256=CK3_12004.executable_sha256)))
                terms=dict(schema_version=1,status='unsupported',war_id=77,casus_belli=dict(database_index=91,canonical_key='raiktor_claim_cb'),supported_slice='claim_cb_claim_disposition',reason='casus_belli_not_claim_cb',readiness=dict(ready=False),provenance=dict(game_version=CK3_12004.game_version,executable_sha256=CK3_12004.executable_sha256,native_reader='CWar+0x270/+0x290;0x2B9ECB0',present_claim_lifecycle='present_only_vtable_slot_0_delete_flags_0',claim_script_sha256='887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4'))
                class Source:
                    def __init__(self,result,frame):self.result=result;self.frame=frame;self._driver_state_lock=threading.Lock();self._war_termination_options={};self._war_termination_terms={}
                    def _execute_primitive_step(self,*args,**kwargs):return copy.deepcopy(self.result)
                    def take_internal_semantic_snapshot(self):return copy.deepcopy(self.frame)
                from xar_autoplayer.bridge.driver import BridgeUnavailableError
                from xar_autoplayer.bridge.war_contract import query_war_termination_options_step,query_war_termination_terms_step
                service_source=root/'src/xar_autoplayer/bridge/service.py'
                service_bytes=service_source.read_bytes()
                assert len(service_bytes)<=2*1024*1024 and hashlib.sha256(service_bytes).hexdigest()=='a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e'
                service_class=next(n for n in ast.parse(service_bytes).body if isinstance(n,ast.ClassDef) and n.name=='GameplayBridgeService')
                methods=[n for n in service_class.body if isinstance(n,ast.FunctionDef) and n.name in {'query_war_termination_options','query_war_termination_terms'}]
                assert len(methods)==2
                namespace=dict(globals())
                exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*methods],type_ignores=[])),str(service_source),'exec'),namespace)
                rows=[]
                def add(kind,name,edit=None):
                    frame=copy.deepcopy(snapshot)
                    result=dict(step='query-war-termination-options-77' if kind=='options' else 'query-war-termination-terms-v1-77',accepted=True,status='available' if kind=='options' else 'unsupported',query_sequence=13,backend_id='native-headless')
                    result['war_termination_options' if kind=='options' else 'war_termination_terms']=make_options(war_id=77) if kind=='options' else copy.deepcopy(terms)
                    if edit:edit(result,frame)
                    producer=Source(result,frame)
                    try:
                        if kind=='options':value=original.NativeHeadlessGameplayDriver._execute_war_termination_step(producer,result['step'],starting=frame,selected_revision=2,query_war_id=77,surrender_war_id=None,white_peace_war_id=None)
                        else:value=original.NativeHeadlessGameplayDriver._execute_war_termination_terms_query(producer,result['step'],starting=frame,selected_revision=2,war_id=77)
                        class PublicSource:
                            def _execute_typed_war_step(self,step,**kwargs):
                                assert step==result['step'] and kwargs==dict(expected_revision=2,include_native_command_history=False)
                                return copy.deepcopy(value)
                        public=namespace['query_war_termination_'+kind](PublicSource(),77,expected_revision=2)
                        expected=dict(accepted=True,result=value,public_result=public)
                    except Exception:expected=dict(accepted=False)
                    native=copy.deepcopy(result);native.pop('backend_id')
                    rows.append(dict(name=name,kind=kind,snapshot=frame,native=native,expected=expected))
                add('options','complete-original-options-query-context')
                add('terms','actual4-unsupported-original-session-is-unavailable')
                add('options','missing-query-sequence',lambda r,s:r.pop('query_sequence'))
                add('options','bool-query-sequence',lambda r,s:r.__setitem__('query_sequence',True))
                add('options','wrong-outer-status',lambda r,s:r.__setitem__('status','unsupported'))
                add('options','wrong-active-war-side',lambda r,s:s['active_wars'][0].__setitem__('player_side','defender'))
                add('options','wrong-active-war-score',lambda r,s:s['active_wars'][0].__setitem__('player_relative_war_score',40))
                add('options','war-ended-before-read',lambda r,s:s.__setitem__('active_wars',[]))
                add('terms','unsupported-outer-union-disagrees',lambda r,s:r.__setitem__('status','available'))
                add('terms','missing-query-sequence',lambda r,s:r.pop('query_sequence'))
                add('terms','wrong-exact-build',lambda r,s:r['war_termination_terms']['provenance'].__setitem__('executable_sha256','A'*64))
                add('terms','war-ended-before-read',lambda r,s:s.__setitem__('active_wars',[]))
                print(json.dumps({'cases':rows},allow_nan=False))
                """, ArmyJson.empty()); verifySources(); int accepted = 0;
        for (JsonNode row : captured.path("cases")) {
            ObjectNode snapshot = (ObjectNode) row.path("snapshot"), nativeResult = (ObjectNode) row.path("native");
            boolean options = row.path("kind").textValue().equals("options");
            if (!row.path("expected").path("accepted").booleanValue()) {
                assertThrows(IllegalArgumentException.class, () -> consume(snapshot, nativeResult, options), row.path("name").textValue()); continue;
            }
            var consumed = consume(snapshot,nativeResult,options);var observed=consumed.observed(); JsonNode normalized = OpportunityJson.toNode(observed.normalizedResult());
            sameJson(row.path("expected").path("result"), normalized);
            sameJson(row.path("expected").path("result"),ArmyJson.parse(consumed.originalWire().bytes()));
            sameJson(row.path("expected").path("public_result"),OpportunityJson.toNode(ArmyPublicWire.decodeExactSourceBound(consumed.publicWire(),context())));
            var wire = ArmyPublicWire.encodeExactSourceBound(observed.normalizedResult(), context()); assertEquals(observed.normalizedResult(), ArmyPublicWire.decodeExactSourceBound(wire, context()));
            assertEquals(observed, consume(snapshot, nativeResult, options).observed());
            if (options) assertTrue(normalized.has("termination_query_context"));
            else { assertEquals("unsupported", normalized.path("status").textValue()); assertTrue(normalized.has("raiktor_surrender_aggregate_session")); }
            accepted++;
        }
        assertEquals(2, accepted); assertEquals(12, captured.path("cases").size());
    }
    private record Consumed(ArmyWarReadCodec.Observation observed,RawJson publicWire,RawJson originalWire) { }
    private static Consumed consume(ObjectNode snapshot, ObjectNode result, boolean options) {
        Context context = context(); var method = options ? PublicMethod.QUERY_WAR_TERMINATION_OPTIONS : PublicMethod.QUERY_WAR_TERMINATION_TERMS;
        var call = new ArmyCalls.War(method, new ArmyCalls.Revision(new Present<>(BigInteger.TWO)), BigInteger.valueOf(77));
        var scope = new ArmyWarReadCodec.Scope(call, context, DriverJson.object(ArmyJson.bytes(snapshot), DriverJson.MAX_NATIVE_BYTES), Optional.empty());
        var operation = new OperationKey(result.path("step").textValue());
        var arguments = OpportunityJson.object(OpportunityJson.parse(ArmyCallCodec.encode(call).bytes()), "original termination query arguments");
        var request = new PlanningReadRequest(context.before(), context.source(), context.sessionId(), operation, arguments, context.deadline());
        var guard = new PlanningReadGuard(new GuardEvidence(context.before(), context.source(), context.sessionId(), BigInteger.ONE, operation,
                context.source().sourceRef(), context.source().sourceRef(), "synthetic-termination", Instant.parse("2026-10-24T00:00:00Z"), context.deadline()), true, true, true, "b".repeat(64));
        ObjectNode top = ArmyJson.empty().put("type", "command_result").put("protocol_version", 1).put("request_id", "termination-original").put("ok", true); top.set("result", result);
        RawJson raw = new RawJson(ArmyJson.bytes(top)); var ack = new NativeActionPort.AckReceived("termination-original", true, Optional.of(new RawJson(ArmyJson.bytes(result))), raw, ArmyOriginalPacketFixture.packet(raw));
        var receipt=new PlanningReadReceipt(request,"synthetic-termination-no-history-qualification","termination-original",guard,guard,ack);
        var observed=ArmyWarReadCodec.decode(scope,receipt);
        return new Consumed(observed,ArmyWarPublicResultCodec.encode(scope,receipt,observed,Optional.empty()),ArmyWarOriginalResultCodec.encode(scope,receipt,observed));
    }
    private static Context context() {
        var ref = new ExactRef("synthetic-termination-no-game-source", 1, "a".repeat(64)); var source = new G2Source("synthetic-test-no-game", "2026-10-24T00:00:00Z", "1.20.0.4", ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101), BigInteger.valueOf(3), BigInteger.valueOf(77)), "native:3", BigInteger.TWO, "termination-fixture");
        return new Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "termination-fixture-session", Instant.parse("2026-10-24T00:01:00Z"));
    }
    private static void sameJson(JsonNode expected, JsonNode actual) { assertEquals(new String(StrictJson.canonical(expected), StandardCharsets.UTF_8), new String(StrictJson.canonical(actual), StandardCharsets.UTF_8)); }
    private static void verifySources() throws Exception {
        String configured = System.getProperty("xar.repository.root"); if (configured == null || configured.isBlank()) throw new IllegalStateException("actual original root required"); Path root = Path.of(configured).toRealPath();
        for (String[] pin : new String[][] {
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/service.py", "a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e"},
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py", "eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py", "b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937"},
                {"ck3_autonomous_player/tests/unit/test_war_termination_contract.py", "be4d7dbad8499632d433b43d6edbba901fba71ec848a3a6735911db07a8d5fc0"}}) {
            Path file = root.resolve(pin[0]).toRealPath(); assertTrue(file.startsWith(root));
            assertEquals(pin[1], HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))), "actual termination producer source drift");
        }
    }
}
