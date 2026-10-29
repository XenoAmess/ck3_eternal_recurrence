package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual Driver/assembler DATA projection and original reply shape; no private issuer or live permission is fabricated. */
final class OperatorBeforeOriginTest {
    private static final Instant NOW=Instant.parse("2026-10-24T10:00:00Z");
    private static ExactRef ref(String name){return new ExactRef(name,1,"a".repeat(64));}
    private record Input(DriverObservationAssembler.FullSnapshot full,ExactRef driver){}
    private static Input input(BigInteger oldActor,LifecycleIdentity.CurrentPlayer actual,String build){
        return input(oldActor,actual,build,BigInteger.valueOf(8));
    }
    private static Input input(BigInteger oldActor,LifecycleIdentity.CurrentPlayer actual,String build,BigInteger publicRevision){
        var source=new G2Source("operator-before",NOW.toString(),build,ref("source.java"));
        var game=new GameGeneration(123,new PythonOnlyUInt64(BigInteger.valueOf(1001)));
        var raw=new LinkedHashMap<String,OpportunityJson.Value>();
        raw.put("date_raw",new OpportunityJson.IntegerValue(BigInteger.valueOf(100)));
        raw.put("paused",new OpportunityJson.Bool(true));raw.put("map_ready",new OpportunityJson.Bool(true));
        raw.put("speed",new OpportunityJson.IntegerValue(BigInteger.ONE));
        raw.put("active_event",OpportunityJson.Nil.INSTANCE);
        raw.put("pending_character_interaction",OpportunityJson.Nil.INSTANCE);
        raw.put("active_wars",new OpportunityJson.Arr(List.of()));
        raw.put("player_armies",new OpportunityJson.Arr(List.of()));
        raw.put("diagnostics",new OpportunityJson.Obj(Map.of()));
        if(actual instanceof LifecycleIdentity.Null)raw.put("played_character",OpportunityJson.Nil.INSTANCE);
        if(actual instanceof LifecycleIdentity.Character player)raw.put("played_character",new OpportunityJson.Obj(Map.of(
                "character_id",new OpportunityJson.IntegerValue(player.characterId()),"alive",new OpportunityJson.Bool(player.alive()))));
        byte[] state=DriverJson.encode(new OpportunityJson.Obj(raw));
        String envelope="{\"protocol_version\":1,\"type\":\"state_snapshot\",\"snapshot_id\":\"native:5\",\"revision\":5,\"state\":"+new String(state,StandardCharsets.UTF_8)+"}";
        byte[] payload=envelope.getBytes(StandardCharsets.UTF_8);
        byte[] packet=ByteBuffer.allocate(payload.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
        var transport=new NativeObservationPort.TransportSession(source.machineId(),game,BigInteger.ONE,"operator-session");
        var observed=new NativeObservationPort.ObservedFrame(transport,"native:5",BigInteger.valueOf(5),new RawJson(state),packet,NOW);
        var nil=new DriverStateSnapshot.NullValue();
        var driver=new DriverStateSnapshot.Complete(new DriverStateSnapshot.Session("pipe",123,oldActor,"same-run"),
                List.of(),nil,nil,nil,nil,nil,nil,nil);
        var fields=new LinkedHashMap<String,OpportunityJson.Value>(raw);
        fields.put("snapshot_id",new OpportunityJson.Text("native:5"));fields.put("native_revision",new OpportunityJson.IntegerValue(BigInteger.valueOf(5)));
        fields.put("revision",new OpportunityJson.IntegerValue(publicRevision));fields.put("episode_run_id",new OpportunityJson.Text("same-run"));
        fields.put("one_life_terminal_reason",new OpportunityJson.Text(LifecycleIdentity.TerminalReason.DEAD.wire()));
        fields.put("succession_reconciliation",OpportunityJson.Nil.INSTANCE);fields.put("one_life_settlement",OpportunityJson.Nil.INSTANCE);
        var semantic=new OpportunityJson.Obj(fields);
        var facts=new DriverObservationFacts(driver,7,3,transport,observed.snapshotId(),observed.nativeRevision(),ActionCodec.sha256(state),
                publicRevision,1,source,semantic,ref("facts.json"));
        var nativeRef=new ExactRef("native.packet",packet.length,ActionCodec.sha256(packet));
        var full=new DriverObservationAssembler().projectFull(observed,facts,nativeRef);
        var exactDriver=new ExactRef("driver.json",driver.encode().length,ActionCodec.sha256(driver.encode()));
        return new Input(full,exactDriver);
    }
    @Test void explicitOperatorBeforePreservesHistoricalDeadReasonWhileDerivingActualChangedActorAndSerializes(){
        var input=input(BigInteger.valueOf(3),new LifecycleIdentity.Character(BigInteger.valueOf(7),true),"1.19.0.6");
        var request=new OperatorPlayerSwitch.Request(7,BigInteger.valueOf(8));
        assertInstanceOf(LifecycleOriginFactory.Unavailable.class,LifecycleOriginFactory.project(input.full(),ref("hello"),input.driver(),ref("qualification")));
        var projected=assertInstanceOf(LifecycleOriginFactory.Projected.class,LifecycleOriginFactory.projectOperatorBefore(
                input.full(),ref("hello"),input.driver(),ref("qualification"),request));
        assertEquals(LifecycleIdentity.TerminalReason.CHANGED,projected.identity().terminalReason());
        var provenance=OpportunityJson.object(projected.semantic().get("lifecycle_origin_reason_projection"),"operator provenance");
        assertEquals(new OpportunityJson.Text(LifecycleIdentity.TerminalReason.DEAD.wire()),provenance.get("original_value"));
        assertEquals(provenance.get("original_value"),provenance.get("original_semantic_value"));
        assertEquals(input.full().originalEvidence(),projected.identity().evidence().nativePacket());
        assertEquals(projected.identity(),LifecycleIdentityCodec.decode(LifecycleIdentityCodec.encode(projected.identity())));
        assertInstanceOf(LifecycleOriginFactory.Unavailable.class,LifecycleOriginFactory.projectOperatorBefore(
                input.full(),ref("hello"),input.driver(),ref("qualification"),new OperatorPlayerSwitch.Request(7,BigInteger.valueOf(9))));
        var sourceLabel=input(BigInteger.valueOf(3),new LifecycleIdentity.Character(BigInteger.valueOf(7),true),"qualified-bundle-20261024");
        // G2Source.exactBuild is a source label. Actual HELLO/EXE support is qualified only by Root private source.
        assertInstanceOf(LifecycleOriginFactory.Projected.class,LifecycleOriginFactory.projectOperatorBefore(
                sourceLabel.full(),ref("hello"),sourceLabel.driver(),ref("qualification"),request));
    }
    @Test void observedSignedSubjectIsValidatedWithoutInventingATerminalReasonForTheSameLivingActor(){
        for(BigInteger old:List.of(BigInteger.ZERO,BigInteger.valueOf(-2),BigInteger.valueOf(Integer.MIN_VALUE)))
            assertEquals(LifecycleIdentity.TerminalReason.CHANGED,LifecycleOriginFactory.deriveReason(
                    new LifecycleIdentity.Character(BigInteger.valueOf(7),true),old));
        for(BigInteger bad:List.of(BigInteger.valueOf(-1),BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)))
            assertThrows(IllegalArgumentException.class,()->LifecycleOriginFactory.deriveReason(new LifecycleIdentity.Missing(),bad));
        var same=input(BigInteger.valueOf(7),new LifecycleIdentity.Character(BigInteger.valueOf(7),true),"1.19.0.6");
        assertInstanceOf(LifecycleOriginFactory.Unavailable.class,LifecycleOriginFactory.projectOperatorBefore(
                same.full(),ref("hello"),same.driver(),ref("qualification"),new OperatorPlayerSwitch.Request(9,BigInteger.valueOf(8))));
    }
    @Test void realDriverFullSnapshotToOperatorOriginAndLifecycleCodecPreserveWideIntegerRevisions(){
        for(BigInteger revision:List.of(new BigInteger("9007199254740993"),StrictJson.UINT64_MAX)){
            var original=input(BigInteger.valueOf(3),new LifecycleIdentity.Character(BigInteger.valueOf(7),true),"qualified-source-label",revision);
            var request=OperatorPlayerSwitch.decode(new RawJson(("{\"character_id\":7,\"expected_revision\":\""+revision+"\"}").getBytes(StandardCharsets.UTF_8)));
            var projected=assertInstanceOf(LifecycleOriginFactory.Projected.class,LifecycleOriginFactory.projectOperatorBefore(
                    original.full(),ref("hello"),original.driver(),ref("qualification"),request));
            assertEquals(revision,projected.identity().frame().revision());
            assertEquals(projected.identity(),LifecycleIdentityCodec.decode(LifecycleIdentityCodec.encode(projected.identity())));
            assertEquals(new OpportunityJson.IntegerValue(revision),projected.semantic().get("revision"));
            assertEquals(original.full().originalEvidence(),projected.identity().evidence().nativePacket());
            var wrong=new OperatorPlayerSwitch.Request(7,revision.subtract(BigInteger.ONE));
            assertInstanceOf(LifecycleOriginFactory.Unavailable.class,LifecycleOriginFactory.projectOperatorBefore(
                    original.full(),ref("hello"),original.driver(),ref("qualification"),wrong));
        }
    }
    private static NativeActionPort.AckReceived ack(String request,boolean ok,String json){
        byte[] payload=json.getBytes(StandardCharsets.UTF_8);
        byte[] packet=ByteBuffer.allocate(payload.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(payload.length).put(payload).array();
        return new NativeActionPort.AckReceived(request,ok,Optional.empty(),new RawJson(payload),packet);
    }
    @Test void originalTenExactNativeRejectionsDecodeWhileUnknownWrongTypeAndQueryDecorationsRemainUnavailable(){
        for(var code:OperatorPlayerSwitch.RejectionCode.values()){
            String json="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"request\",\"ok\":false,\"error\":\""+code.wire()+"\"}";
            assertEquals(Optional.of(code),OperatorPlayerSwitch.knownRejection(ack("request",false,json)));
        }
        for(String tail:List.of("\"error\":\"new_unknown\"","\"error\":true","\"error\":null","\"result\":{}",
                "\"error\":\"target_dead\",\"typed_query_failure_v1\":{}")){
            String json="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"request\",\"ok\":false,"+tail+"}";
            assertTrue(OperatorPlayerSwitch.knownRejection(ack("request",false,json)).isEmpty());
        }
        String exact="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"request\",\"ok\":false,\"error\":\"target_dead\"}";
        assertTrue(OperatorPlayerSwitch.knownRejection(ack("another-request",false,exact)).isEmpty());
        assertTrue(OperatorPlayerSwitch.knownRejection(ack("request",true,exact)).isEmpty());
    }
}

