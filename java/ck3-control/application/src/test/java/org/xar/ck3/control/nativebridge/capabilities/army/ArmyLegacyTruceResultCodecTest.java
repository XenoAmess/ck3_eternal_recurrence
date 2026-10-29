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
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Actual original legacy Driver/normalizer producer -> receipt DATA -> shared original formatter/serde.
 * No synthetic DATA receipt authorizes an installed family, new query, source, Game or current .4 proof.
 */
final class ArmyLegacyTruceResultCodecTest {
    @Test void actualLegacyProducerAndCurrentBuildMismatchRemainDifferentContracts() throws Exception {
        verifySources();ObjectNode cases=BattleOriginalOracle.call("""
                import copy,json
                import xar_autoplayer.bridge.native_driver as original
                snapshot=dict(snapshot_id='native:3',revision=2,native_revision=3,date_raw=77,paused=True,map_ready=True,played_character=dict(character_id=101,alive=True))
                result=dict(step='query-raiktor-actual-truce-expiry-v1-202',accepted=True,query_sequence=2**64-1,snapshot_revision=3,raiktor_actual_truce_expiry=dict(schema_version=1,backend_id='ck3-1.19.0.6-native-raiktor-actual-truce-expiry-v1',status='available',snapshot_revision=3,current_date_raw=77,owner_character_id=101,toward_character_id=202,native_has_truce=True,actual_expiry_observable=True,expiry_date_raw=177,same_frame_stable=True,readiness=True,temporal_semantics='post_application_persisted_relation_state',unavailable_reason=None))
                class Source:
                    def __init__(self,r):self.r=r
                    def take_internal_semantic_snapshot(self):return copy.deepcopy(snapshot)
                    def _execute_primitive_step(self,*a,**kw):return {**copy.deepcopy(self.r),'backend_id':'native-headless'}
                rows=[]
                def add(name,edit=None,build='1.19.0.6'):
                    r=copy.deepcopy(result)
                    if edit:edit(r)
                    try:value=original.NativeHeadlessGameplayDriver._execute_native_war_step(Source(r),r['step'],expected_revision=2);expected=dict(accepted=True,result=value)
                    except Exception:expected=dict(accepted=False)
                    rows.append(dict(name=name,native=r,build=build,expected=expected))
                add('legacy-available')
                add('legacy-no-truce',lambda r:r['raiktor_actual_truce_expiry'].update(status='no_truce',native_has_truce=False,actual_expiry_observable=False,expiry_date_raw=None,readiness=False,unavailable_reason='native_has_truce_false'))
                add('bool-query-sequence',lambda r:r.__setitem__('query_sequence',True))
                add('wrong-native-revision',lambda r:r.__setitem__('snapshot_revision',4))
                add('wrong-target',lambda r:r['raiktor_actual_truce_expiry'].__setitem__('toward_character_id',303))
                add('expiry-not-future',lambda r:r['raiktor_actual_truce_expiry'].__setitem__('expiry_date_raw',77))
                add('bool-state',lambda r:r['raiktor_actual_truce_expiry'].__setitem__('native_has_truce',1))
                add('extra-outer',lambda r:r.__setitem__('foreign',1))
                add('actual4-contract',lambda r:(r.__setitem__('date_raw',77),r['raiktor_actual_truce_expiry'].update(backend_id='ck3-1.20.0.4-native-player-truce-expiry-v1',ck3_build='1.20.0.4',executable_sha256='98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518')),build='1.20.0.4')
                print(json.dumps(dict(cases=rows),allow_nan=False))
                """,ArmyJson.empty());verifySources();int accepted=0;
        for(JsonNode row:cases.path("cases")) {
            ObjectNode nativeResult=(ObjectNode)row.path("native");String build=row.path("build").textValue();
            if(!row.path("expected").path("accepted").booleanValue()) {
                var failure=assertThrows(IllegalArgumentException.class,()->consume(nativeResult,build),row.path("name").textValue());
                if(build.equals("1.20.0.4"))assertTrue(failure.getMessage().contains("observed build 1.20.0.4"));continue;
            }
            RawJson actual=consume(nativeResult,build);sameJson(row.path("expected").path("result"),ArmyJson.parse(actual.bytes()));
            var value=DriverJson.object(actual.bytes(),DriverJson.MAX_NATIVE_BYTES);RawJson wire=ArmyPublicWire.encodeExactSourceBound(value,context(build));
            assertTrue(ArmyJson.parse(wire.bytes()).path("query_sequence").isTextual());assertEquals(value,ArmyPublicWire.decodeExactSourceBound(wire,context(build)));
            accepted++;
        }
        assertEquals(2,accepted);assertEquals(9,cases.path("cases").size());
    }
    private static RawJson consume(ObjectNode result,String build) {
        Context c=context(build);var call=new ArmyCalls.Truce(new ArmyCalls.Revision(new Present<>(BigInteger.TWO)),new PositiveId(202));
        var op=new OperationKey(result.path("step").textValue());var args=DriverJson.object(ArmyCallCodec.encode(call).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var request=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),op,args,c.deadline());
        var guard=new PlanningReadGuard(new GuardEvidence(c.before(),c.source(),c.sessionId(),BigInteger.ONE,op,c.source().sourceRef(),c.source().sourceRef(),
                "legacy-truce-data",Instant.parse("2026-10-24T00:00:00Z"),c.deadline()),true,true,true,"b".repeat(64));
        ObjectNode top=ArmyJson.empty().put("type","command_result").put("protocol_version",1).put("request_id","legacy-truce-data").put("ok",true);top.set("result",result);
        RawJson raw=new RawJson(ArmyJson.bytes(top));var ack=new NativeActionPort.AckReceived("legacy-truce-data",true,Optional.of(new RawJson(ArmyJson.bytes(result))),raw,ArmyOriginalPacketFixture.packet(raw));
        var receipt=new PlanningReadReceipt(request,"synthetic-legacy-no-authority","legacy-truce-data",guard,guard,ack);
        return ArmyLegacyTruceResultCodec.encode(call,c,receipt);
    }
    private static Context context(String build) {
        var ref = new ExactRef("synthetic-termination-no-game-source", 1, "a".repeat(64)); var source = new G2Source("synthetic-test-no-game", "2026-10-24T00:00:00Z", build, ref);
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(101), BigInteger.valueOf(3), BigInteger.valueOf(77)), "native:3", BigInteger.TWO, "termination-fixture");
        return new Context(new ObservationIdentity(source.machineId(), new GameGeneration(42, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1), source, "termination-fixture-session", Instant.parse("2026-10-24T00:01:00Z"));
    }
    private static void sameJson(JsonNode expected, JsonNode actual) { assertEquals(new String(StrictJson.canonical(expected), StandardCharsets.UTF_8), new String(StrictJson.canonical(actual), StandardCharsets.UTF_8)); }
    private static void verifySources() throws Exception {
        String configured=System.getProperty("xar.repository.root");
        if(configured==null||configured.isBlank())throw new IllegalStateException("actual original root required");
        Path root=Path.of(configured).toRealPath();
        for(String[] pin:new String[][] {
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_actual_truce_expiry_contract.py","55fe165e5c001cd6858c4c47345fc8343dc270c9d77b7db9678e2d5596cf405c"}}) {
            Path file=root.resolve(pin[0]).toRealPath();assertTrue(file.startsWith(root));
            assertTrue(Files.size(file)>0&&Files.size(file)<=2*1024*1024);
            assertEquals(pin[1],HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))));
        }
    }
}
