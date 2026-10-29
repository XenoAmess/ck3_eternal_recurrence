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

/** Actual retained Python Driver method/normalizer -> typed Java receipt DATA -> original result and public serde.
 * Synthetic receipt DATA is explicitly not a central dispatch, current Root proof, permit or Game acceptance.
 */
final class ArmyWarOriginalResultCodecTest {
    @Test void originalWhitePeaceWholeResultKeepsItsOwnShapeAndExactSequence() throws Exception {
        verifySources();ObjectNode rows=BattleOriginalOracle.call("""
                import copy,json
                import xar_autoplayer.bridge.native_driver as original
                snapshot=dict(snapshot_id='native:3',revision=2,native_revision=3,date_raw=77,paused=True,map_ready=True,episode_run_id='termination-fixture',episode_character_id=101,played_character=dict(character_id=101,alive=True),active_wars=[dict(war_id=77,player_side='attacker',primary_opponent_character_id=202)],diagnostics=dict(connection_generation=1))
                native=dict(step='query-outbound-war-white-peace-status-v1-77',accepted=True,status='available',query_sequence=2**64-1,outbound_war_white_peace_status=dict(schema_version=1,war_id=77,actor_character_id=101,recipient_character_id=202,state='exact_absent',present=False,pending_interaction_id=-1))
                class Source:
                    def __init__(self,r,s):self.r=r;self.s=s
                    def _execute_primitive_step(self,*a,**kw):return {**copy.deepcopy(self.r),'backend_id':'native-headless'}
                    def take_internal_semantic_snapshot(self):return copy.deepcopy(self.s)
                cases=[]
                def add(name,edit=None):
                    r,s=copy.deepcopy(native),copy.deepcopy(snapshot)
                    if edit:edit(r,s)
                    try:
                        out=original.NativeHeadlessGameplayDriver._execute_outbound_war_white_peace_status_query(Source(r,s),r['step'],starting=s,selected_revision=2,war_id=77)
                        expected=dict(accepted=True,result=out)
                    except Exception:expected=dict(accepted=False)
                    cases.append(dict(name=name,snapshot=s,native=r,expected=expected))
                add('exact-absent-max-u64')
                add('exact-present',lambda r,s:r['outbound_war_white_peace_status'].update(present=True,state='exact_present',pending_interaction_id=501))
                add('bool-sequence',lambda r,s:r.__setitem__('query_sequence',True))
                add('missing-sequence',lambda r,s:r.pop('query_sequence'))
                add('wrong-actor',lambda r,s:r['outbound_war_white_peace_status'].__setitem__('actor_character_id',303))
                add('wrong-recipient',lambda r,s:r['outbound_war_white_peace_status'].__setitem__('recipient_character_id',303))
                add('missing-active-war',lambda r,s:s.__setitem__('active_wars',[]))
                add('state-disagrees',lambda r,s:r['outbound_war_white_peace_status'].__setitem__('state','exact_present'))
                add('pending-sentinel-disagrees',lambda r,s:r['outbound_war_white_peace_status'].__setitem__('pending_interaction_id',501))
                add('extra-top-field',lambda r,s:r.__setitem__('foreign',1))
                print(json.dumps(dict(cases=cases),allow_nan=False))
                """,ArmyJson.empty());verifySources();int accepted=0;
        for(JsonNode row:rows.path("cases")) {
            ObjectNode snapshot=(ObjectNode)row.path("snapshot"),nativeResult=(ObjectNode)row.path("native");
            if(!row.path("expected").path("accepted").booleanValue()) {
                assertThrows(IllegalArgumentException.class,()->consume(snapshot,nativeResult),row.path("name").textValue());continue;
            }
            RawJson actual=consume(snapshot,nativeResult);sameJson(row.path("expected").path("result"),ArmyJson.parse(actual.bytes()));
            assertFalse(ArmyJson.parse(actual.bytes()).has("war_id"),"Service-only outer ID must not enter Driver result");
            var data=DriverJson.object(actual.bytes(),DriverJson.MAX_NATIVE_BYTES);
            RawJson publicWire=ArmyPublicWire.encodeExactSourceBound(data,context());
            assertTrue(ArmyJson.parse(publicWire.bytes()).path("query_sequence").isTextual());
            assertEquals(data,ArmyPublicWire.decodeExactSourceBound(publicWire,context()));accepted++;
        }
        assertEquals(2,accepted);assertEquals(10,rows.path("cases").size());
    }
    private static RawJson consume(ObjectNode snapshot,ObjectNode result) {
        Context c=context();var call=new ArmyCalls.War(PublicMethod.QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS,
                new ArmyCalls.Revision(new Present<>(BigInteger.TWO)),BigInteger.valueOf(77));
        var scope=new ArmyWarReadCodec.Scope(call,c,DriverJson.object(ArmyJson.bytes(snapshot),DriverJson.MAX_NATIVE_BYTES),Optional.empty());
        var op=new OperationKey(result.path("step").textValue());
        var args=DriverJson.object(ArmyCallCodec.encode(call).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var request=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),op,args,c.deadline());
        var guard=new PlanningReadGuard(new GuardEvidence(c.before(),c.source(),c.sessionId(),BigInteger.ONE,op,
                c.source().sourceRef(),c.source().sourceRef(),"synthetic-white-result-data",Instant.parse("2026-10-24T00:00:00Z"),c.deadline()),true,true,true,"b".repeat(64));
        ObjectNode top=ArmyJson.empty().put("type","command_result").put("protocol_version",1).put("request_id","original-white-data").put("ok",true);top.set("result",result);
        RawJson raw=new RawJson(ArmyJson.bytes(top));
        var ack=new NativeActionPort.AckReceived("original-white-data",true,Optional.of(new RawJson(ArmyJson.bytes(result))),raw,ArmyOriginalPacketFixture.packet(raw));
        var receipt=new PlanningReadReceipt(request,"synthetic-white-no-history-authority","original-white-data",guard,guard,ack);
        return ArmyWarOriginalResultCodec.encode(scope,receipt,ArmyWarReadCodec.decode(scope,receipt));
    }
    private static Context context() {
        var ref = new ExactRef("synthetic-termination-no-game-source", 1, "a".repeat(64)); var source = new G2Source("synthetic-test-no-game", "2026-10-24T00:00:00Z", "1.20.0.4", ref);
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
                {"ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py","b1b14953f01d66c9f6720e4c92cb6b30c26eb1946b20e9b4ba932c9b5e1f7937"}}) {
            Path file=root.resolve(pin[0]).toRealPath();assertTrue(file.startsWith(root));
            assertTrue(Files.size(file)>0&&Files.size(file)<=2*1024*1024,"bounded original producer source required");
            assertEquals(pin[1],HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file))),"original producer source drift");
        }
    }
}
