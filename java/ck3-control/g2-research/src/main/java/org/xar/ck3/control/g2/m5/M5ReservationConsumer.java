package org.xar.ck3.control.g2.m5;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.util.Objects;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.Milestone;

/** Existing caller-side reservation phase after the pure same-host HTTP analysis. */
public final class M5ReservationConsumer {
    private M5ReservationConsumer() { }

    /**
     * Uses the caller's existing shared frame owner. A response, saved receipt or
     * HTTP acknowledgement can never construct a replacement reservation owner.
     * The returned reservation is analytic only; the formal submitter is unchanged.
     */
    public static M5FrameDispatcher.Dispatch reserve(G2Request originalRequest, G2Response response, M5FrameDispatcher owner) {
        Objects.requireNonNull(originalRequest); Objects.requireNonNull(response); Objects.requireNonNull(owner);
        require(originalRequest.milestone() == Milestone.M5 && response.milestone() == Milestone.M5
                && originalRequest.requestId().equals(response.requestId()) && originalRequest.source().equals(response.source()), "M5 response differs from its original request envelope");
        M5PayloadCodec.OperationRequest operation = M5PayloadCodec.decodeOperation(originalRequest.payload().bytes());
        require(operation instanceof M5PayloadCodec.ContextRequest, "only the actual decision-context collector has an observed reservation request");
        M5PayloadCodec.Request context = ((M5PayloadCodec.ContextRequest) operation).context();
        M5Research.Result result = M5PayloadCodec.decodeResult(response.result().bytes());
        require(M5Research.assess(context).equals(result), "M5 reservation result differs from its actual original producer");
        return owner.chooseObserved(originalRequest.source(), object(result.intakeAnalysis().get("selector_request"), "retained original selector request"));
    }
}
