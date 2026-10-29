package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.*;

/** Original native result plus factual public/native query binding; no DTO-to-wire reconstruction. */
public final class InteractionReadPublications {
    private InteractionReadPublications() { }
    public static OpportunityJson.Obj ordinary(PlanningReadResult.Known<InteractionModels.OrdinaryContext> known) {
        need(known.receipt().request().operation().value().equals(OrdinaryInteractionCodec.QUERY_STEP),
                "ordinary publication must come from the original ordinary query");
        return publish(known.receipt());
    }
    public static OpportunityJson.Obj pending(PlanningReadResult.Known<PendingContext> known) {
        need(known.receipt().request().operation().value().equals(PendingContextCodec.STEP),
                "pending publication must come from the original pending query");
        return publish(known.receipt());
    }
    public static OpportunityJson.Obj publish(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);
        var request=receipt.request(); var before=request.before();
        ObjectNode original=result(receipt);
        eq(original,"step",request.operation().value());
        ObjectNode publication=original.deepCopy();
        bindText(publication,"queried_snapshot_id",before.frame().snapshotId());
        bindInteger(publication,"queried_revision",before.frame().revision());
        bindInteger(publication,"queried_native_revision",before.frame().identity().nativeRevision());
        return InteractionArguments.app(publication);
    }
    /** Every use of a stored receipt still checks the present held identity. */
    public static void sameRequest(PlanningReadReceipt receipt,PlanningRequest request) {
        need(receipt.request().before().equals(request.before())
                &&receipt.request().source().equals(request.source())
                &&receipt.request().sessionId().equals(request.sessionId()),
                "native read publication crossed current Game/source/session/frame");
    }
    private static void bindText(ObjectNode n,String field,String value) {
        if(n.has(field))eq(n,field,value); else n.put(field,value);
    }
    private static void bindInteger(ObjectNode n,String field,java.math.BigInteger value) {
        if(n.has(field))eq(n,field,value); else n.put(field,value);
    }
}

