package org.xar.ck3.control.application.action;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.advance.PreparedCleanupEvidence;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual SDK return DATA; a public constructor grants no capability. A capture
 * exists only after its real CANCEL ACK, two independent IDLE queries and later
 * raw full-state sample have all returned before any slow canonical outcome append. */
public record PreparedCleanupNativeOutcome(String preparationNonce,NativeActionPort.DispatchOutcome original,
        Optional<PreparedCleanupEvidence.PostAckCaptured> captured,
        Optional<PreparedCleanupEvidence.FailureData> failure,Optional<Throwable> originalFailure) {
    public PreparedCleanupNativeOutcome(String nonce,NativeActionPort.DispatchOutcome original,
            Optional<PreparedCleanupEvidence.PostAckCaptured> captured) {
        this(nonce,original,captured,Optional.empty(),Optional.empty());
    }
    public PreparedCleanupNativeOutcome {
        StrictJson.text(preparationNonce);Objects.requireNonNull(original);captured=Objects.requireNonNull(captured);failure=Objects.requireNonNull(failure);originalFailure=Objects.requireNonNull(originalFailure);
        StrictJson.require(captured.isEmpty()||failure.isEmpty(),"a complete capture and incomplete failure cannot both classify one original");
        failure.ifPresent(value->StrictJson.require(value.original().equals(original)
                &&value.prepared().preparationNonce().equals(preparationNonce),"failure changed the actual SDK result or preparation nonce"));
        if(captured.isPresent())StrictJson.require(captured.orElseThrow().cancellationAcknowledgement().equals(original)
                &&captured.orElseThrow().binding().prepared().preparationNonce().equals(preparationNonce),
                "captured SDK outcome changed its actual cancellation ACK or durable preparation nonce");
    }
}
