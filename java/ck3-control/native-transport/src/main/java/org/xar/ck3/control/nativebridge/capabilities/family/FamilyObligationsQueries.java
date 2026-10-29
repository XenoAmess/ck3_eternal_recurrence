package org.xar.ck3.control.nativebridge.capabilities.family;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.List;
import java.util.Objects;
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
import org.xar.ck3.control.nativebridge.capabilities.family.FamilyObligations.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** One real family read, installed in the shared coordinator and consumed by FamilyPorts.CHILD_HOUSE_PREVIEW. */
public final class FamilyObligationsQueries {
    public static final String CONTRACT_ID = "family/obligations12004/v1";
    private static final OperationKey OPERATION = new OperationKey(FamilyObligations.STEP);
    private FamilyObligationsQueries() { }
    /** Verifies current exact source/permission from Root's actual qualified read catalog. Constructor success is insufficient. */
    @FunctionalInterface public interface Admission { void verify(PlanningReadRequest request, Request arguments); }

    public static ReadContract<Obj> contract(ExactRef definitionSource, Admission admission) {
        Objects.requireNonNull(definitionSource); Objects.requireNonNull(admission);
        return new ReadContract<>(CONTRACT_ID, OPERATION, Optional.empty(), FamilyObligations.PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.G2_PRIVATE_QUERY, ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, definitionSource,
                (request, requestId) -> {
                    Request arguments = arguments(request); requireCurrentSource(request); admission.verify(request, arguments);
                    return new NativeRequest(FamilyObligations.STEP, Optional.empty(), new RawJson(StrictJson.canonical(FamilyObligationsCodec.wireFields(arguments))));
                }, FamilyObligationsQueries::decodeProjection, FamilyObligationsQueries::decodeProjection);
    }
    public static Request arguments(PlanningReadRequest request) {
        Objects.requireNonNull(request); StrictJson.require(request.operation().equals(OPERATION), "family read must use its exact registered operation");
        Request arguments = FamilyObligationsCodec.decodeRequest(OpportunityJson.toNode(request.arguments()));
        StrictJson.require(arguments.expectedRevision().equals(request.before().frame().revision()), "family public expected revision is stale");
        return arguments;
    }
    public static Observation decode(PlanningReadReceipt receipt) {
        requireOriginalEnvelope(receipt);
        Objects.requireNonNull(receipt); PlanningReadRequest request = receipt.request(); Request arguments = arguments(request); requireCurrentSource(request);
        StrictJson.require(receipt.contractId().equals(CONTRACT_ID) && receipt.original().nativeOk() && receipt.original().originalResultToken().isPresent(), "original successful registered family read required");
        for (var guard : List.of(receipt.before(), receipt.after())) {
            StrictJson.require(guard.paused() && guard.mapReady() && guard.playerAlive()
                    && guard.binding().operation().equals(OPERATION) && guard.binding().source().equals(request.source())
                    && guard.binding().sessionId().equals(request.sessionId()) && guard.binding().observed().equals(request.before()), "family read requires original same-session paused living guards");
        }
        StrictJson.require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())
                && receipt.before().binding().connectionGeneration().equals(receipt.after().binding().connectionGeneration()), "family read crossed original paused connection/source frame");
        var frame = request.before().frame(); var identity = frame.identity();
        Binding binding = new Binding(Build.CURRENT4, frame.snapshotId(), frame.revision(), identity.nativeRevision(), identity.dateRaw().intValueExact(), identity.player().longValueExact());
        return FamilyObligationsCodec.decodeNative(receipt.original().originalResultToken().orElseThrow(), binding, arguments);
    }
    /** This is the original private Python DTO shape for existing Java consumers; no public JS numeric conversion occurs here. */
    public static Obj project(Observation observation) {
        RawJson source = FamilyObligationsCodec.encodeNative(observation); ObjectNode n = (ObjectNode) StrictJson.parse(source.bytes(), 1_048_576);
        Binding b = observation.binding(); n.put("queried_snapshot_id", b.snapshotId()).put("queried_revision", b.publicRevision()).put("queried_native_revision", b.nativeRevision());
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(n, 1_048_576)), "validated complete family observation");
    }
    public static Obj arguments(Request request) {
        return OpportunityJson.object(OpportunityJson.parse(FamilyObligationsCodec.encodeRequest(request).bytes()), "family read arguments");
    }
    private static void requireCurrentSource(PlanningReadRequest request) {
        StrictJson.require(request.source().exactBuild().equals(Build.CURRENT4.exactBuild()), "actual exact current .4 source required for family obligations");
    }
    private static Obj decodeProjection(PlanningReadReceipt receipt) { return project(decode(receipt)); }
    /** Original packet and retained token remain one closed message in both live decoding and pure replay. */
    static void requireOriginalEnvelope(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);
        StrictJson.require(receipt.original().nativeOk() && receipt.original().requestId().equals(receipt.requestId()), "original successful family request identity differs");
        ObjectNode frame = StrictJson.object(StrictJson.parse(receipt.original().originalFrame().bytes(), 1_048_576), Set.of("type", "protocol_version", "request_id", "ok", "result"));
        StrictJson.require("command_result".equals(StrictJson.text(frame.get("type")))
                && StrictJson.integer(frame.get("protocol_version"), 1, 1) == 1 && booleanValue(frame.get("ok"))
                && receipt.requestId().equals(StrictJson.text(frame.get("request_id")))
                && frame.get("result").equals(StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes(), 1_048_576)),
                "family original packet/result token custody differs");
    }
    private static boolean booleanValue(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "exact JSON boolean required");
        return value.booleanValue();
    }

}
