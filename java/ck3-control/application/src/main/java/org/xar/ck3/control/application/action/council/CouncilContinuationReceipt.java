package org.xar.ck3.control.application.action.council;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.application.action.council.CouncilContinuationModel.*;

/** Each reference is an actually archived body or canonical event, never a reconstructed native packet. */
public record CouncilContinuationReceipt(Request request, Status status, Optional<NativeActionPort.DispatchOutcome> outcome,
        IssuedCustody issued, ExactRef latestRecord, ExactRef resultDomainPayload, ExactRef resultEvent) {
    public CouncilContinuationReceipt {
        Objects.requireNonNull(request); Objects.requireNonNull(status); Objects.requireNonNull(outcome); Objects.requireNonNull(issued);
        Objects.requireNonNull(latestRecord); Objects.requireNonNull(resultDomainPayload); Objects.requireNonNull(resultEvent);
        org.xar.ck3.control.contracts.StrictJson.require(status != Status.ISSUED && outcome.isPresent(), "continuation call returns a durable ACK or UNKNOWN, never send permission");
    }
}
