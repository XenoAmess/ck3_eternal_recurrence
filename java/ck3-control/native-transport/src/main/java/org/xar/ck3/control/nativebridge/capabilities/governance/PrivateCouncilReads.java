package org.xar.ck3.control.nativebridge.capabilities.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.governance.council.CouncilModels;
import org.xar.ck3.control.governance.council.CouncilPrivateCodec;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Three actual wire operations, each with its own permit, request ID, original receipt and archive reference. */
public final class PrivateCouncilReads {
    private final ReadContract<CouncilPrivateCodec.Reply> query;
    private final ReadContract<CouncilPrivateCodec.Reply> gates;
    private final ReadContract<CouncilPrivateCodec.Reply> status;
    public PrivateCouncilReads(ExactRef actualNativeSource) {
        query = initial(actualNativeSource, CouncilPrivateCodec.QUERY);
        gates = initial(actualNativeSource, CouncilPrivateCodec.GATES);
        status = new ReadContract<>("council-private-mailbox-status-v1", new OperationKey(CouncilPrivateCodec.STATUS), Optional.empty(),
                "council-private-mailbox-status-v1", ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, actualNativeSource, (request, requestId) -> {
                    StrictJson.require(request.arguments().members().isEmpty(), "Council STATUS has no native fields, revision or ticket");
                    return new NativeRequest(CouncilPrivateCodec.STATUS, Optional.empty(), new RawJson(new byte[] {'{', '}'}));
                }, receipt -> decode(receipt, CouncilPrivateCodec.STATUS), receipt -> decode(receipt, CouncilPrivateCodec.STATUS));
    }
    private static ReadContract<CouncilPrivateCodec.Reply> initial(ExactRef source, String step) {
        return new ReadContract<>("council-" + step, new OperationKey(step), Optional.empty(), "council-" + step,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.EXECUTE_STEP, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, source,
                (request, requestId) -> {
                    ObjectNode arguments = StrictJson.object(StrictJson.parse(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(request.arguments())), Set.of("position_key"));
                    CouncilModels.Position role = CouncilModels.Position.exact(CouncilCodec.text(arguments, "position_key"));
                    // EXECUTE_STEP adds only expected_revision from the real ReadPermit. G2_PRIVATE_QUERY would add an unsupported field.
                    return new NativeRequest(step, Optional.empty(), new RawJson(StrictJson.canonical(StrictJson.object().put("position_key", role.key()))));
                }, receipt -> decode(receipt, step), receipt -> decode(receipt, step));
    }
    public ReadContract<CouncilPrivateCodec.Reply> query() { return query; }
    public ReadContract<CouncilPrivateCodec.Reply> gates() { return gates; }
    public ReadContract<CouncilPrivateCodec.Reply> status() { return status; }
    public List<ReadContract<?>> registeredContracts() { return List.of(query, gates, status); }
    private static CouncilPrivateCodec.Reply decode(PlanningReadReceipt receipt, String step) {
        GovernanceNativeReads.verifyGuards(receipt);
        requireOriginalWire(receipt,step);
        ObjectNode frame = StrictJson.object(StrictJson.parse(receipt.original().originalFrame().bytes()), Set.of("type", "protocol_version", "request_id", "ok", "result"));
        StrictJson.require(CouncilCodec.text(frame, "type").equals("command_result")
                && CouncilCodec.number(frame, "protocol_version", 1, 1) == 1
                && CouncilCodec.text(frame, "request_id").equals(receipt.requestId())
                && receipt.request().operation().value().equals(step), "Council mailbox command-result correlation mismatch");
        StrictJson.trueValue(frame.get("ok"));
        ObjectNode result = CouncilCodec.object(frame.get("result"));
        StrictJson.require(receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent()
                && StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes()).equals(result), "Council mailbox original token differs from full native frame");
        return CouncilPrivateCodec.decodeReply(StrictJson.canonical(result), step);
    }
    private static void requireOriginalWire(PlanningReadReceipt receipt,String step) {
        var outbound=receipt.original().outbound().orElseThrow(()->new IllegalArgumentException("original Council read outbound packet missing; no reconstruction allowed"));
        StrictJson.require(outbound.requestId().equals(receipt.requestId()),"original Council outbound request ID changed");
        requireOriginalWire(receipt.request(),receipt.requestId(),outbound.originalPacket(),step);
    }
    /** Identical original-packet validation for an archived failed READ; this issues no request. */
    static void requireOriginalWire(PlanningReadRequest request,String requestId,byte[] originalPacket,String step) {
        try {
            var wire=NativeWire.decodeExecuteRequest(originalPacket);
            boolean status=step.equals(CouncilPrivateCodec.STATUS);
            StrictJson.require(wire.requestId().equals(requestId)&&wire.step().equals(step)&&wire.expectedSnapshotRevision().isEmpty()
                    &&(status?wire.expectedRevision().isEmpty():wire.expectedRevision().filter(request.before().frame().identity().nativeRevision()::equals).isPresent()),
                    "original Council read wire operation/revision profile differs from its actual producer");
            var actual=StrictJson.parse(wire.normalizedAdditionalFields().value());
            StrictJson.require(actual.equals(StrictJson.parse(org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(request.arguments()))),
                    "original Council read wire queried different arguments");
            if(status) StrictJson.object(actual,Set.of());
            else {
                StrictJson.require(step.equals(CouncilPrivateCodec.QUERY)||step.equals(CouncilPrivateCodec.GATES),"only original Council QUERY/GATES/STATUS are read-only");
                ObjectNode fields=StrictJson.object(actual,Set.of("position_key"));
                CouncilModels.Position.exact(CouncilCodec.text(fields,"position_key"));
            }
        } catch(IOException malformed) {throw new IllegalArgumentException("original Council read packet cannot be decoded",malformed);}
    }
    public static CouncilModels.Frame nativeFrame(PlanningReadRequest request) {
        var current = request.before().frame(); var identity = current.identity();
        return new CouncilModels.Frame("native:" + identity.nativeRevision(), identity.nativeRevision(), identity.nativeRevision(),
                identity.dateRaw().intValueExact(), identity.player().intValueExact());
    }
}
