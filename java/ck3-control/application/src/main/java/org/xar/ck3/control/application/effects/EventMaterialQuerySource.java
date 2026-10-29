package org.xar.ck3.control.application.effects;

import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One installed typed material source for planning, after-observation and original archive replay. */
public interface EventMaterialQuerySource<T> {
    record Frame(ObservationIdentity before, G2Source source, String sessionId,
                 OpportunityJson.Obj semantic, Instant deadline) {
        public Frame {
            Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(sessionId);
            Objects.requireNonNull(semantic); Objects.requireNonNull(deadline);
        }
    }
    /** Dynamic families retain their actual selection preimage in this same archive before returning its exact ref. */
    record Resolved<T>(ReadContract<T> contract, PlanningReadRequest request,
                       Function<T,RawJson> encode, Optional<ExactRef> replayContext) {
        public Resolved {
            Objects.requireNonNull(contract); Objects.requireNonNull(request); Objects.requireNonNull(encode);
            Objects.requireNonNull(replayContext);
            StrictJson.require(contract.operation().equals(request.operation()), "material contract operation differs from request");
            replayContext.ifPresent(ref -> StrictJson.require(ref.bytes() > 0, "nonempty original material context required"));
        }
        public void requireFrame(Frame frame, OperationKey operation) {
            Objects.requireNonNull(frame); Objects.requireNonNull(operation);
            StrictJson.require(contract.operation().equals(operation) && request.operation().equals(operation)
                && request.before().equals(frame.before()) && request.source().equals(frame.source())
                && request.sessionId().equals(frame.sessionId()) && request.deadline().equals(frame.deadline()),
                "material query crossed its exact selected frame, source, session, deadline or operation");
        }
        public RawJson decode(PlanningReadReceipt original) {
            requireReceipt(original);
            return Objects.requireNonNull(encode.apply(contract.decode(original)));
        }
        /** Archive consumers must never invoke the live decoder. */
        public RawJson replay(PlanningReadReceipt original) {
            requireReceipt(original);
            return Objects.requireNonNull(encode.apply(contract.replay(original)));
        }
        private void requireReceipt(PlanningReadReceipt original) {
            Objects.requireNonNull(original);
            StrictJson.require(original.contractId().equals(contract.contractId()) && original.request().equals(request),
                "material original receipt differs from the exact issued family selection");
        }
    }
    OperationKey operation();
    Resolved<T> resolve(Frame current);
    /** Rebuild from original bytes only. The supplied frame uses original.request.deadline, never a fresh window. */
    Resolved<T> restore(Frame originalFrame, PlanningReadReceipt original, Optional<ExactRef> replayContext,
                        ActionPorts.OutcomeArchive archive);
}
