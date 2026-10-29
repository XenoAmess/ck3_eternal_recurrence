package org.xar.ck3.control.application.action;

import java.util.Arrays;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.application.driver.DriverJson;

/** Archived late-read DATA. It cannot create a live ticket, guard, installed contract or read permission. */
public record PlanningReadAdoption(PlanningReadRequest currentRequest, OpportunityJson.Obj currentSemantic,
        NativeActionPort.Unknown originalUnknown, NativeRequest preparedRequest,
        long originalHeadSequence, String originalHeadDigest) {
    public PlanningReadAdoption {
        Objects.requireNonNull(currentRequest); Objects.requireNonNull(currentSemantic);
        Objects.requireNonNull(originalUnknown); Objects.requireNonNull(preparedRequest);
        StrictJson.safe(originalHeadSequence, 0);
        StrictJson.require(originalHeadDigest != null && originalHeadDigest.matches("[0-9a-f]{64}"), "original canonical writer head required");
        StrictJson.require(originalUnknown.originalRequestPacket().length > 0, "late adoption requires the retained actual UNKNOWN outbound packet");
        DriverJson.object(DriverJson.encode(currentSemantic), RawJson.MAXIMUM_BYTES);
    }

    /** Cross-request permission remains the sole source-owned ReadContract predicate's responsibility. */
    public void requireReceipt(PlanningReadReceipt receipt) {
        Objects.requireNonNull(receipt);
        PlanningReadRequest original = receipt.request();
        StrictJson.require(receipt.adoption().filter(this::equals).isPresent(), "adoption DATA differs from this original receipt");
        StrictJson.require(original.origin() instanceof CommandOrigin.Gameplay
                && original.origin().equals(currentRequest.origin())
                && original.source().equals(currentRequest.source()) && original.sessionId().equals(currentRequest.sessionId())
                && original.operation().equals(currentRequest.operation()) && original.arguments().equals(currentRequest.arguments()),
                "late read crossed its original exact gameplay frame/source/session/operation/arguments");
        StrictJson.require(receipt.before().guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && receipt.after().guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && receipt.before().paused() && receipt.before().mapReady() && receipt.before().playerAlive()
                && receipt.after().paused() && receipt.after().mapReady() && receipt.after().playerAlive()
                && receipt.before().binding().origin().equals(receipt.after().binding().origin())
                && receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256()),
                "late read requires the actual unchanged living paused map/modal binding");
        StrictJson.require(originalUnknown.requestId().equals(receipt.requestId()), "late read changed original UNKNOWN request identity");
        NativeActionPort.OutboundPacket outbound = receipt.original().outbound().orElseThrow(
                () -> new IllegalArgumentException("late read has no retained actual ACK outbound packet"));
        StrictJson.require(Arrays.equals(originalUnknown.originalRequestPacket(), outbound.originalPacket()),
                "late ACK does not belong to the original actual UNKNOWN outbound bytes");
        NativeStepDiscriminator.requireRequest(original.operation(), ExecutableStepBindings.Kind.READ, preparedRequest);
        StrictJson.require(receipt.original().custody().isPresent(), "late read cannot invent absent actual transport chronology");
    }
}
