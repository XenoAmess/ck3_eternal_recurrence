package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Retained producer fixture and actual original Driver -> installed-codec DATA -> whole original result.
 * Missing existing fixture properties hard fail. No native/Root permission follows from these DATA tests.
 */
final class ArmyClosedOriginalResultCodecTest {
    @Test void retainedNativeDefaultRaiseFixturePassesOriginalDriverAndWholeMetadataProjection() throws Exception {
        verifySources();var call=new ArmyCalls.Frame(org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod.QUERY_PLAYER_DEFAULT_RAISE_V1,
                new ArmyCalls.Revision(new Present<>(BigInteger.valueOf(7))));
        Context context=ArmyClosedReadCodecTest.context("1.20.0.3",29829);
        for(String name:List.of("legal","illegal"))for(boolean nullable:List.of(false,true)) {
            ObjectNode raw=ArmyJson.object(ArmyClosedReadCodecTest.fixture().get(name)).deepCopy();raw.put("query_sequence",ArmyClosedReadCodecTest.MAX);
            ObjectNode frame=snapshot(context);
            if(nullable){frame.remove("diagnostics");frame.putNull("episode_run_id");}
            ObjectNode input=ArmyJson.empty();input.set("native",raw);input.set("snapshot",frame);
            ObjectNode expected=BattleOriginalOracle.call("""
                    import copy,json,sys
                    import xar_autoplayer.bridge.native_driver as original
                    value=json.load(sys.stdin)
                    class Source:
                        def capabilities(self):return {}
                        def take_snapshot(self):return copy.deepcopy(value['snapshot'])
                        def _execute_primitive_step(self,*a,**kw):return {**copy.deepcopy(value['native']),'backend_id':'native-headless'}
                    result=original.NativeHeadlessGameplayDriver._execute_step_unrecorded(Source(),'query-player-default-raise-v1',expected_revision=7)
                    print(json.dumps(result,allow_nan=False))
                    """,input);
            var receipt=receipt(call,context,raw);var observed=ArmyClosedReadCodec.decode(call,context,receipt);
            RawJson actual=ArmyClosedOriginalResultCodec.encode(call,context,receipt,observed,semantic(frame));
            assertEquals(StrictJson.parse(StrictJson.canonical(expected)),StrictJson.parse(actual.bytes()));
            for(String field:List.of("queried_snapshot_id","queried_revision","queried_native_revision","queried_episode_run_id","queried_connection_generation","queried_bridge_pid"))assertTrue(ArmyJson.parse(actual.bytes()).has(field));
            var data=DriverJson.object(actual.bytes(),DriverJson.MAX_NATIVE_BYTES);RawJson wire=ArmyPublicWire.encodeExactSourceBound(data,context);
            assertEquals(data,ArmyPublicWire.decodeExactSourceBound(wire,context));
            assertTrue(ArmyJson.parse(wire.bytes()).path("query_sequence").isTextual());
            ObjectNode changed=frame.deepCopy().put("native_revision",12);
            assertThrows(IllegalArgumentException.class,()->ArmyClosedOriginalResultCodec.encode(call,context,receipt,observed,semantic(changed)));
        }
        verifySources();
    }
    @Test void actual4ClosedDecoderRunsBeforeLegacyGenericVersionDiagnostic() throws java.io.IOException {
        Context c=ArmyClosedReadCodecTest.context("1.20.0.4",0);
        var call=new ArmyCalls.Truce(new ArmyCalls.Revision(new Present<>(BigInteger.valueOf(7))),new PositiveId(2));
        ObjectNode body=ArmyJson.empty().put("schema_version",1).put("backend_id","ck3-1.20.0.4-native-player-truce-expiry-v1").put("ck3_build","1.20.0.4")
                .put("executable_sha256",ArmyResponseCodec.ACTUAL4_SHA).put("status","no_truce").put("snapshot_revision",11).put("current_date_raw",53238336)
                .put("owner_character_id",0).put("toward_character_id",2).put("native_has_truce",false).put("actual_expiry_observable",false)
                .putNull("expiry_date_raw").put("same_frame_stable",true).put("readiness",false).put("temporal_semantics","post_application_persisted_relation_state").put("unavailable_reason","native_has_truce_false");
        ObjectNode token=ArmyJson.empty().put("step","query-raiktor-actual-truce-expiry-v1-2").put("accepted",true).put("query_sequence",ArmyClosedReadCodecTest.MAX)
                .put("snapshot_revision",11).put("date_raw",53238336).put("read_only",true).put("backend_id","native-headless");token.set("raiktor_actual_truce_expiry",body);
        var receipt=receipt(call,c,token);var observed=ArmyClosedReadCodec.decode(call,c,receipt);assertInstanceOf(ArmyClosedReads.Truce.class,observed);
        var failure=assertThrows(IllegalArgumentException.class,()->ArmyClosedOriginalResultCodec.encode(call,c,receipt,observed,semantic(snapshot(c))));
        assertTrue(failure.getMessage().contains("observed build 1.20.0.4"));
    }
    private static ObjectNode snapshot(Context c) {
        ObjectNode n=ArmyJson.empty().put("snapshot_id",c.before().frame().snapshotId()).put("revision",c.before().frame().revision())
                .put("native_revision",c.nativeRevision()).put("date_raw",c.dateRaw()).put("paused",true).put("map_ready",true)
                .put("episode_run_id",c.before().frame().episodeRunId());
        n.putObject("played_character").put("character_id",c.playerId()).put("alive",true);
        n.putObject("diagnostics").put("connection_generation",1).put("bridge_pid",42);return n;
    }
    private static OpportunityJson.Obj semantic(ObjectNode n){return DriverJson.object(ArmyJson.bytes(n),DriverJson.MAX_NATIVE_BYTES);}
    static PlanningReadReceipt receipt(ArmyCalls.Call call,Context c,ObjectNode result) throws java.io.IOException {
        var op=new OperationKey(result.path("step").textValue());var args=DriverJson.object(ArmyCallCodec.encode(call).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var request=new PlanningReadRequest(c.before(),c.source(),c.sessionId(),op,args,c.deadline());
        var guard=new PlanningReadGuard(new GuardEvidence(c.before(),c.source(),c.sessionId(),BigInteger.ONE,op,c.source().sourceRef(),c.source().sourceRef(),
                "synthetic-closed-data",ArmyClosedReadCodecTest.NOW,c.deadline()),true,true,true,"b".repeat(64));
        ObjectNode top=ArmyJson.empty().put("type","command_result").put("protocol_version",1).put("request_id","closed-result-data").put("ok",true);top.set("result",result);
        RawJson raw=new RawJson(ArmyJson.bytes(top));var ack=new NativeActionPort.AckReceived("closed-result-data",true,Optional.of(new RawJson(ArmyJson.bytes(result))),raw,NativeWire.packet(raw.bytes()));
        return new PlanningReadReceipt(request,"synthetic-closed-no-history-authority","closed-result-data",guard,guard,ack);
    }
    private static void verifySources() throws Exception {
        String configured=System.getProperty("xar.repository.root");
        if(configured==null||configured.isBlank())throw new IllegalStateException("actual original root required");
        java.nio.file.Path root=java.nio.file.Path.of(configured).toRealPath();
        for(String[] pin:new String[][] {
                {"native_driver.py","eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603"},
                {"player_default_raise.py","511c7d56b7592dd6a0f6b15d4d99537cc7564624cca3bd59a0320f91ea43f8d6"},
                {"timeline_blocker_private_transport.py","9a97a8f7b88bc6e2c4d26ce7fc9799900cc00d8fcc6868350bc4791b3f6429d7"},
                {"version_identity.py","9f7665ed680238f6904bc3ef22e1d67ef9b4ccd047e699542d5dbaff24b01086"}}) {
            var path=root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/"+pin[0]).toRealPath();
            assertTrue(path.startsWith(root)&&java.nio.file.Files.size(path)>0&&java.nio.file.Files.size(path)<=2*1024*1024);
            assertEquals(pin[1],java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(java.nio.file.Files.readAllBytes(path))));
        }
    }
}
