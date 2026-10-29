package org.xar.ck3.control.nativebridge.capabilities.army;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** One strict argument/basis contract. Native envelope encoding remains the original transport's job. */
public final class ArmyStructuralActionCodec {
    public static final String SCHEMA="xar.java.army-structural-command/v1";
    public static final String PENDING_SCHEMA="xar.java.army-structural-pending-originals/v1";
    private ArmyStructuralActionCodec(){ }
    public static RawJson encode(ArmyStructuralActions.Call call) {
        return new RawJson(DriverJson.encode(new Obj(Map.of("schema",new Text(SCHEMA),"step",new Text(call.operation().value())))));
    }
    public static ArmyStructuralActions.Call decode(RawJson raw) {
        Obj row=DriverJson.object(raw.bytes(),65536);
        StrictJson.require(row.members().keySet().equals(Set.of("schema","step"))&&new Text(SCHEMA).equals(row.get("schema")),"exact structural arguments required");
        return ArmyStructuralActions.parse(new OperationKey(text(row.get("step"),"structural step")))
                .orElseThrow(()->new IllegalArgumentException("invalid structural selector"));
    }
    public static NativeRequest request(ArmyStructuralActions.Call call) {
        return new NativeRequest(call.operation().value(),java.util.Optional.of(call.capability()),new RawJson(new byte[]{123,125}));
    }
    /** Validates the actual outbound original; this method never emits a Native request packet. */
    public static Obj outbound(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,
            ActionPorts.OutcomeArchive archive) {
        StrictJson.require(attempt.requestId().equals(ack.requestId())&&ack.outbound().isPresent()&&ack.custody().isPresent()
                &&ack.equals(archive.load(archive.referenceOf(ack))),"structural result lacks original same-request transport custody");
        ArmyStructuralActions.Call call=decode(new RawJson(DriverJson.encode(command.arguments())));
        StrictJson.require(call.operation().equals(command.operation())&&request(call).equals(attempt.preparedRequest()),
                "structural request differs from original typed preparation");
        byte[] packet=ack.outbound().orElseThrow().originalPacket();
        StrictJson.require(packet.length>4&&packet.length<=65540
                &&ByteBuffer.wrap(packet,0,4).order(ByteOrder.LITTLE_ENDIAN).getInt()==packet.length-4,"native request framing changed");
        Obj row=DriverJson.object(Arrays.copyOfRange(packet,4,packet.length),65536);
        StrictJson.require(row.members().keySet().equals(Set.of("type","protocol_version","request_id","step","expected_revision"))
                &&new Text("execute_step").equals(row.get("type"))&&new IntegerValue(java.math.BigInteger.ONE).equals(row.get("protocol_version"))
                &&new Text(attempt.requestId()).equals(row.get("request_id"))&&new Text(command.operation().value()).equals(row.get("step"))
                &&new IntegerValue(command.before().frame().identity().nativeRevision()).equals(row.get("expected_revision")),
                "actual structural Native packet changed its source-bound request envelope");
        return row;
    }
    public record PendingBasis(String commandBodySha256,String requestId,ExactRef beforeNative,ExactRef beforeDriver,
            ExactRef afterNative,ExactRef afterDriver,ExactRef material) {
        public PendingBasis {
            StrictJson.require(commandBodySha256!=null&&commandBodySha256.matches("[0-9a-f]{64}"),"canonical command hash required");
            StrictJson.text(requestId);for(ExactRef ref:List.of(beforeNative,beforeDriver,afterNative,afterDriver,material))
                StrictJson.require(ref.bytes()>0,"nonempty original structural basis required");
        }
    }
    public static RawJson encode(PendingBasis basis) {
        var row=StrictJson.object().put("schema",PENDING_SCHEMA).put("command_body_sha256",basis.commandBodySha256()).put("request_id",basis.requestId());
        row.set("before_native",basis.beforeNative().toJson());row.set("before_driver",basis.beforeDriver().toJson());
        row.set("after_native",basis.afterNative().toJson());row.set("after_driver",basis.afterDriver().toJson());row.set("material",basis.material().toJson());
        return new RawJson(StrictJson.canonical(row));
    }
    public static PendingBasis decodeBasis(RawJson body) {
        var row=StrictJson.object(StrictJson.parse(body.bytes()),Set.of("schema","command_body_sha256","request_id","before_native","before_driver","after_native","after_driver","material"));
        StrictJson.require(PENDING_SCHEMA.equals(StrictJson.text(row.get("schema"))),"exact structural pending basis required");
        return new PendingBasis(StrictJson.text(row.get("command_body_sha256")),StrictJson.text(row.get("request_id")),
                ExactRef.fromJson(row.get("before_native")),ExactRef.fromJson(row.get("before_driver")),
                ExactRef.fromJson(row.get("after_native")),ExactRef.fromJson(row.get("after_driver")),ExactRef.fromJson(row.get("material")));
    }
}

